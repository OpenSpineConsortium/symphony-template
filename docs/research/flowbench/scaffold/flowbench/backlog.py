"""The work list of a run: one JSON line per (instance, arm) item, under a
file lock, so several lanes take items from one queue and no item is
taken twice.

Items are ordered instance by instance, arm by arm, so every arm advances
together and a run cut short still holds the same instances under every
arm, which the paired tests need. `shuffle` draws each instance's order
of arms from the seed and the instance, so no arm always meets a lane's
first minutes or the end of a usage window. `requeue` puts failed items
back as pending, up to --max-attempts (three) tries each, so a run that
breaks the same way every time stops rather than spending usage on it
again; with --harness-only, only those whose run the audit called a
harness error, since an agent that ran out of time is its arm's result.
`reset --lane` puts a dead lane's running items back as pending, for a
lane whose process was killed with an item in hand. `pause` and `resume`
hold and release the pending items, all or the instances named, which is
how a run grows one batch at a time with the owner's word on each
(PLAN.md).

    python3 flowbench/backlog.py add Q --tag TAG --arms symphony,script,solo --instances a,b,c [--option K=V]
    python3 flowbench/backlog.py take Q --lane lane-1
    python3 flowbench/backlog.py finish Q --instance I --arm A --attempt N --verdict resolved|failed|error --run-dir DIR [--harness-error]
    python3 flowbench/backlog.py requeue Q [--harness-only] [--max-attempts 3]
    python3 flowbench/backlog.py reset Q --lane lane-1
    python3 flowbench/backlog.py pause Q [--instances a,b]    resume the same way
    python3 flowbench/backlog.py shuffle Q --seed 1
    python3 flowbench/backlog.py status Q
"""

import argparse
import fcntl
import json
import os
import random
import sys
import time
from contextlib import contextmanager
from pathlib import Path

STATES = ("pending", "paused", "running", "done", "failed")
VERDICTS = ("resolved", "failed", "error")
DEFAULT_MAX_ATTEMPTS = 3


class BacklogError(ValueError):
    pass


@contextmanager
def locked(path):
    """The queue's lines while its lock file is held: a lane that wants the
    queue waits for the lock, so a take and a finish never interleave."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    lock = open(str(path) + ".lock", "w")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX)
        items = read_items(path)
        yield items
        write_items(path, items)
    finally:
        fcntl.flock(lock, fcntl.LOCK_UN)
        lock.close()


def read_items(path):
    path = Path(path)
    if not path.is_file():
        return []
    items = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            items.append(json.loads(line))
        except ValueError as error:
            raise BacklogError(f"{path}: line {number} is not JSON: {error}") from error
    return items


def write_items(path, items):
    """Written whole to a temporary file and renamed over the queue, so a
    reader never sees half a line."""
    path = Path(path)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text("".join(json.dumps(item, sort_keys=True) + "\n" for item in items), encoding="utf-8")
    os.replace(temporary, path)


def now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def item_key(item):
    return (item["instance"], item["arm"])


def add(path, tag, instances, arms, options=None, state="pending"):
    """Queue every (instance, arm) not queued yet, in the instances' order,
    arm by arm; the count added."""
    if not tag or not instances or not arms:
        raise BacklogError("add needs a tag, instances and arms")
    added = 0
    with locked(path) as items:
        present = {item_key(item) for item in items}
        for instance in instances:
            for arm in arms:
                if (instance, arm) in present:
                    continue
                items.append({
                    "tag": tag, "instance": instance, "arm": arm, "state": state, "attempt": 0,
                    "options": dict(options or {}), "lane": None, "run_dir": None, "verdict": None,
                    "harness_error": False, "updated": now(),
                })
                present.add((instance, arm))
                added += 1
    return added


def take(path, lane):
    """The first pending item, now running under the lane with its attempt
    counted; None when nothing is pending."""
    with locked(path) as items:
        for item in items:
            if item["state"] == "pending":
                item.update({"state": "running", "lane": lane, "attempt": item["attempt"] + 1,
                             "run_dir": None, "verdict": None, "harness_error": False, "updated": now()})
                return dict(item)
    return None


def finish(path, instance, arm, attempt, verdict, run_dir=None, harness_error=False):
    """The item's verdict: done when the run was scored, failed when it
    ended in error; a harness error is marked so requeue --harness-only
    finds it."""
    if verdict not in VERDICTS:
        raise BacklogError(f"a verdict is one of {', '.join(VERDICTS)}, not {verdict!r}")
    with locked(path) as items:
        for item in items:
            if item_key(item) == (instance, arm):
                if item["attempt"] != attempt:
                    raise BacklogError(f"{instance} {arm}: attempt {attempt} is not the queue's {item['attempt']}")
                item.update({"state": "failed" if verdict == "error" else "done", "verdict": verdict,
                             "run_dir": run_dir, "harness_error": bool(harness_error), "updated": now()})
                return dict(item)
    raise BacklogError(f"{instance} {arm}: not in the queue")


def requeue(path, harness_only=False, max_attempts=DEFAULT_MAX_ATTEMPTS):
    """Failed items, or only the harness errors, back to pending while
    they have attempts left: {"requeued": n, "kept": m}, kept being the
    failed items at the cap, left as they are for a person to look at."""
    counts = {"requeued": 0, "kept": 0}
    with locked(path) as items:
        for item in items:
            if item["state"] != "failed" or (harness_only and not item["harness_error"]):
                continue
            if item["attempt"] >= max_attempts:
                counts["kept"] += 1
                continue
            item.update({"state": "pending", "lane": None, "run_dir": None, "verdict": None,
                         "harness_error": False, "updated": now()})
            counts["requeued"] += 1
    return counts


def reset(path, lane):
    """The lane's running items back to pending, for a lane that died
    with an item in hand; the count. The item's next take counts a new
    attempt, and the runner gives it a directory of its own."""
    count = 0
    with locked(path) as items:
        for item in items:
            if item["state"] == "running" and item["lane"] == lane:
                item.update({"state": "pending", "lane": None, "updated": now()})
                count += 1
    return count


def instance_open(path, instance):
    """Whether an item of the instance is still to run or running, so the
    instance's image is still needed."""
    return any(item["instance"] == instance and item["state"] in ("pending", "paused", "running")
               for item in read_items(path))


def set_state(path, from_state, to_state, instances=None):
    count = 0
    with locked(path) as items:
        for item in items:
            if item["state"] == from_state and (instances is None or item["instance"] in instances):
                item["state"] = to_state
                item["updated"] = now()
                count += 1
    return count


def pause(path, instances=None):
    return set_state(path, "pending", "paused", instances)


def resume(path, instances=None):
    return set_state(path, "paused", "pending", instances)


def shuffle(path, seed):
    """Each instance's arms in an order drawn from the seed and the
    instance; items of other states keep their place, and the instances
    keep theirs."""
    with locked(path) as items:
        by_instance = {}
        for item in items:
            by_instance.setdefault(item["instance"], []).append(item)
        shuffled = []
        for instance, members in by_instance.items():
            drawn = list(members)
            random.Random(f"{seed}:{instance}").shuffle(drawn)
            shuffled.extend(drawn)
        items[:] = shuffled
    return len(items)


def status(path):
    """Counts by state, and by arm and verdict."""
    items = read_items(path)
    counts = {state: 0 for state in STATES}
    arms = {}
    for item in items:
        counts[item["state"]] = counts.get(item["state"], 0) + 1
        record = arms.setdefault(item["arm"], {"items": 0, "resolved": 0, "failed": 0, "error": 0, "harness_errors": 0})
        record["items"] += 1
        if item["verdict"]:
            record[item["verdict"]] += 1
        if item["harness_error"]:
            record["harness_errors"] += 1
    return {"states": counts, "arms": arms, "items": len(items)}


def parse_options(pairs):
    options = {}
    for pair in pairs or []:
        key, sep, value = pair.partition("=")
        if not sep or not key:
            raise BacklogError(f"an option is KEY=VALUE, not {pair!r}")
        options[key] = value
    return options


def split(text):
    return [part.strip() for part in (text or "").split(",") if part.strip()]


def main(argv=None):
    parser = argparse.ArgumentParser(description="The work list of a flowbench run.")
    commands = parser.add_subparsers(dest="command", required=True)
    adding = commands.add_parser("add")
    adding.add_argument("queue")
    adding.add_argument("--tag", required=True)
    adding.add_argument("--arms", required=True)
    adding.add_argument("--instances", required=True, help="comma separated, or @FILE with one per line")
    adding.add_argument("--option", action="append", help="KEY=VALUE run options, repeatable")
    adding.add_argument("--paused", action="store_true", help="queue the items paused, for a batch released later")
    taking = commands.add_parser("take")
    taking.add_argument("queue")
    taking.add_argument("--lane", required=True)
    finishing = commands.add_parser("finish")
    finishing.add_argument("queue")
    finishing.add_argument("--instance", required=True)
    finishing.add_argument("--arm", required=True)
    finishing.add_argument("--attempt", type=int, required=True)
    finishing.add_argument("--verdict", required=True, choices=VERDICTS)
    finishing.add_argument("--run-dir")
    finishing.add_argument("--harness-error", action="store_true")
    requeuing = commands.add_parser("requeue")
    requeuing.add_argument("queue")
    requeuing.add_argument("--harness-only", action="store_true")
    requeuing.add_argument("--max-attempts", type=int, default=DEFAULT_MAX_ATTEMPTS,
                           help="an item at this many attempts is kept failed")
    resetting = commands.add_parser("reset", help="a dead lane's running items back to pending")
    resetting.add_argument("queue")
    resetting.add_argument("--lane", required=True)
    for name in ("pause", "resume"):
        holding = commands.add_parser(name)
        holding.add_argument("queue")
        holding.add_argument("--instances")
    shuffling = commands.add_parser("shuffle")
    shuffling.add_argument("queue")
    shuffling.add_argument("--seed", type=int, required=True)
    showing = commands.add_parser("status")
    showing.add_argument("queue")
    args = parser.parse_args(argv)
    try:
        if args.command == "add":
            instances = split(args.instances)
            if args.instances.startswith("@"):
                instances = [line.strip() for line in Path(args.instances[1:]).read_text(encoding="utf-8").splitlines()
                             if line.strip()]
            count = add(args.queue, args.tag, instances, split(args.arms), parse_options(args.option),
                        "paused" if args.paused else "pending")
            print(f"added {count}")
        elif args.command == "take":
            item = take(args.queue, args.lane)
            print(json.dumps(item))
        elif args.command == "finish":
            item = finish(args.queue, args.instance, args.arm, args.attempt, args.verdict, args.run_dir, args.harness_error)
            print(json.dumps(item))
        elif args.command == "requeue":
            counts = requeue(args.queue, args.harness_only, args.max_attempts)
            print(f"requeued {counts['requeued']}, kept {counts['kept']} at the cap")
        elif args.command == "reset":
            print(f"reset {reset(args.queue, args.lane)}")
        elif args.command in ("pause", "resume"):
            chosen = set(split(args.instances)) if args.instances else None
            count = pause(args.queue, chosen) if args.command == "pause" else resume(args.queue, chosen)
            print(f"{args.command}d {count}")
        elif args.command == "shuffle":
            print(f"shuffled {shuffle(args.queue, args.seed)}")
        else:
            print(json.dumps(status(args.queue), indent=2, sort_keys=True))
    except (BacklogError, OSError) as error:
        print(error, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
