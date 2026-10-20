"""Stale branches: what it cost every pull request that the default branch
moved under it, read from GitHub's own history.

The default branch's rules here require a branch to be up to date before it
merges (the required check's strict policy), so each landing makes every
other open pull request stale: its branch has to take the default branch in,
by a merge, the Update branch button or a rebase, and its check runs again
on the new head before it may land. That is the price of working in
parallel paid at landing, the curse of coordination in its mechanical form,
and this tool counts it per pull request so the repository's own history is
a field record beside coordbench's runs (docs/research/stale-branch-failures.md).

  collect  read the pull requests, each closed one's timeline and its runs
           of the check's workflow, and write STALENESS.json: one record per
           closed pull request and the summary over them. With --previous,
           records already kept for closed pull requests are kept as they
           are and only newly closed ones are read, so a run after each merge
           costs a few calls. GITHUB_TOKEN is enough.
  snapshot run on each push to the default branch: for every open pull
           request, what GitHub says of it now (behind, dirty, clean...),
           appended as one line to SNAPSHOTS.jsonl. A conflict is the one
           thing history keeps no trace of, and this is where it is caught
           as it happens.
  report   write the summary of a STALENESS.json as Markdown.

What GitHub's history gives and what it does not is in the research note;
in short, a catch-up commit (a merge of the default branch into the branch)
and a forced push are recorded, the runs on each head are recorded, and
whether a merge had conflicts to resolve, or a forced push was a rebase onto
the default branch or new work, is not.

Standard library only, like every tool here; GitHub's REST calls go through
the vendored protocol's client.
"""

import argparse
import json
import re
import statistics
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from sdlc_protocol import board  # noqa: E402

FORMAT = 1
CI_WORKFLOW = "ci.yml"
CLAIM_BRANCH = re.compile(r"claude/[1-9][0-9]{0,8}")
MAIN_MOVED_PREFIX = board.MAIN_MOVED_MARKER.split("{sha}")[0]
CONFLICT_WORDS = "conflicting with"
# GitHub's own Update branch button, and the API call behind it, commit as
# GitHub; any other catch-up was made in a clone.
GITHUB_COMMITTER = "GitHub"
# A run's head pushed within this many seconds of the pull request's life
# still belongs to it: a run is created a moment after the push.
SLACK_SECONDS = 120


def parse_time(text):
    if not text:
        return None
    return datetime.fromisoformat(text.replace("Z", "+00:00"))


def iso(moment):
    return moment.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ") if moment else None


def seconds(earlier, later):
    if earlier is None or later is None:
        return None
    return max(0.0, (later - earlier).total_seconds())


# Reading GitHub.

def paged(api, path, params=None, key=None):
    """Every item of a list endpoint, asked page by page by number. GitHub's
    Link header names a renamed repository by its id, which some proxies
    refuse, so the next page is asked under the name given."""
    items, page = [], 1
    while True:
        data = api.get(path, dict(params or {}, per_page=100, page=page)) or []
        batch = data.get(key, []) if key else data
        items.extend(batch)
        if len(batch) < 100:
            return items
        page += 1


def read_pulls(api):
    return paged(api, f"/repos/{api.repo}/pulls", {"state": "all", "sort": "created", "direction": "asc"})


def read_timeline(api, number):
    return paged(api, f"/repos/{api.repo}/issues/{number}/timeline")


def read_runs(api, workflow, branch, **filters):
    """The check workflow's runs on one branch; none where the repository
    has no such workflow, as a site with no checks has none."""
    from sdlc_protocol.adapters.github import GitHubError
    try:
        return paged(api, f"/repos/{api.repo}/actions/workflows/{workflow}/runs", dict(filters, branch=branch), key="workflow_runs")
    except GitHubError as problem:
        if problem.status == 404:
            return []
        raise


def mergeable_state(api, number, sleep, tries=4):
    """GitHub works the state out after it is asked, so an unknown answer is
    asked again a few seconds later. The state alone can hide a conflict or
    a branch behind under blocked, so mergeable (false is a conflict) is
    kept beside it."""
    detail = {}
    for attempt in range(tries):
        detail = api.get(f"/repos/{api.repo}/pulls/{number}") or {}
        if detail.get("mergeable_state") not in (None, "unknown"):
            break
        sleep(3 * (attempt + 1))
    return detail.get("mergeable_state") or "unknown", detail.get("mergeable")


def up_to_date_required(api, default_branch):
    """Whether a rule on the default branch requires a branch to be up to
    date before it merges, the setting that makes every landing stale every
    other pull request; None where GitHub will not say. Each snapshot keeps
    it, so the record shows when the setting changed without the ruleset
    history, which only an administrator may read."""
    from sdlc_protocol.adapters.github import GitHubError
    try:
        rules = api.get(f"/repos/{api.repo}/rules/branches/{default_branch}") or []
    except GitHubError:
        return None
    return any(r.get("type") == "required_status_checks"
               and (r.get("parameters") or {}).get("strict_required_status_checks_policy") for r in rules)


def snapshot(api, default_branch, sleep=time.sleep):
    open_pulls = [p for p in paged(api, f"/repos/{api.repo}/pulls", {"state": "open", "base": default_branch})]
    return {
        "at": iso(datetime.now(timezone.utc)),
        "up_to_date_required": up_to_date_required(api, default_branch),
        "pulls": [shot_of(api, p, sleep) for p in open_pulls],
    }


def shot_of(api, pull, sleep):
    state, mergeable = mergeable_state(api, pull["number"], sleep)
    return {"number": pull["number"], "branch": pull["head"]["ref"], "draft": bool(pull.get("draft")),
            "state": state, "mergeable": mergeable}


def read_snapshots(path):
    if not path or not Path(path).is_file():
        return []
    rows = []
    for line in Path(path).read_text().splitlines():
        try:
            rows.append(json.loads(line))
        except ValueError:
            continue
    return rows


def seen_states(snapshots):
    seen = defaultdict(Counter)
    for shot in snapshots:
        for pull in shot.get("pulls", []):
            seen[pull.get("number")][pull.get("state")] += 1
            if pull.get("mergeable") is False:
                seen[pull.get("number")]["conflict"] += 1
    return seen


# Facts drawn from what was read.

def same_repository(pull, repo):
    """A pull request from a fork runs its check in no run this repository
    lists under its branch's name, so only the repository's own are read."""
    head = (pull.get("head") or {}).get("repo") or {}
    return (head.get("full_name") or "").lower() == repo.lower() if "repo" in (pull.get("head") or {}) else True


def landings(pulls, default_branch):
    """Every pull request merged into the default branch, oldest first, as
    the moves of the default branch the others had to take in."""
    landed = [p for p in pulls if p.get("merged_at") and p["base"]["ref"] == default_branch]
    return sorted(({"number": p["number"], "branch": p["head"]["ref"], "at": parse_time(p["merged_at"]),
                    "sha": p.get("merge_commit_sha") or ""} for p in landed), key=lambda l: l["at"])


def catch_up_message(message, default_branch):
    first = (message or "").splitlines()[0] if message else ""
    name = re.escape(default_branch)
    return bool(re.match(rf"Merge (remote-tracking )?branch '(origin/)?{name}'", first)
                or re.match(rf"Merge (branch )?'?(origin/)?{name}'? into ", first))


def commits_of(timeline):
    return [e for e in timeline if e.get("event") == "committed"]


def main_parent(commit, main_shas):
    for parent in commit.get("parents") or []:
        if parent.get("sha") in main_shas:
            return parent["sha"]
    return None


def is_catch_up(commit, default_branch, main_shas):
    parents = commit.get("parents") or []
    if len(parents) < 2:
        return False
    return catch_up_message(commit.get("message"), default_branch) or main_parent(commit, main_shas) is not None


def commit_time(commit):
    return parse_time((commit.get("committer") or {}).get("date") or (commit.get("author") or {}).get("date"))


def runs_of(pull, runs, shas):
    """The check's runs on the pull request's own heads in its own life: a
    thread's branch can carry several pull requests one after another, and a
    run's own list of pull requests names the ones open on its branch now,
    not the one it ran for, so the run's time and its head, one of the pull
    request's own commits, decide."""
    opened, closed = parse_time(pull["created_at"]), parse_time(pull.get("closed_at"))
    mine = []
    for run in runs:
        created = parse_time(run.get("created_at"))
        if created is None or run.get("head_sha") not in shas:
            continue
        if (created - opened).total_seconds() < -SLACK_SECONDS:
            continue
        if closed and (created - closed).total_seconds() > SLACK_SECONDS:
            continue
        mine.append(run)
    return sorted(mine, key=lambda r: r["created_at"])


def one_per_head(runs):
    """The run that decided each head: the check runs on a push and on
    every pull request event (opened, synchronize, ready_for_review, edited),
    and a newer push cancels the run still going, so a head counts once, by
    its last run that finished other than cancelled."""
    kept = {}
    for run in runs:
        if run.get("conclusion") in (None, "cancelled", "skipped"):
            continue
        kept[run.get("head_sha")] = run
    return sorted(kept.values(), key=lambda r: r["created_at"])


def run_seconds(run):
    return seconds(parse_time(run.get("run_started_at") or run.get("created_at")), parse_time(run.get("updated_at")))


def events(timeline, name):
    return [e for e in timeline if e.get("event") == name]


def board_marks(timeline):
    marks = [e for e in events(timeline, "commented") if MAIN_MOVED_PREFIX in (e.get("body") or "")]
    return marks, [e for e in marks if CONFLICT_WORDS in (e.get("body") or "")]


def landed_between(moves, after, upto, number):
    return [m for m in moves if m["number"] != number and (after is None or m["at"] > after) and m["at"] <= upto]


def causes(commits, catch_ups, moves, started, number):
    """Which landings each catch-up took in: those between the branch's
    last sync with the default branch and this one, by the main parent's
    place in the order of landings where it names one, else by time."""
    order = {m["sha"]: i for i, m in enumerate(moves) if m["sha"]}
    first_parent = ((commits[0].get("parents") or [{}])[0].get("sha") if commits else None)
    last_index = order.get(first_parent)
    last_time = None if last_index is not None else started
    caused = []
    for commit in catch_ups:
        parent = main_parent(commit, order)
        when = commit_time(commit) or started
        if parent is not None and last_index is not None:
            taken = [m for m in moves[last_index + 1: order[parent] + 1] if m["number"] != number]
        else:
            if last_time is None and last_index is not None:
                last_time = moves[last_index]["at"]
            taken = landed_between(moves, last_time, when, number)
        last_index = order.get(parent)
        last_time = moves[last_index]["at"] if last_index is not None else when
        caused.append([m["number"] for m in taken])
    return caused


def landings_since_base(commits, moves, started, end, number):
    """The landings between the commit the branch was made from and the
    pull request's end: a session's clone is often older than its first
    commit, so the base, where it is a landing, says more than the time."""
    order = {m["sha"]: i for i, m in enumerate(moves) if m["sha"]}
    base = (commits[0].get("parents") or [{}])[0].get("sha") if commits else None
    after = moves[order[base]]["at"] if base in order else started
    return landed_between(moves, after, end, number)


def is_claim(branch):
    """A branch of the claim protocol, claude/<issue>, as against a thread's
    or a person's branch that claims nothing."""
    return bool(CLAIM_BRANCH.fullmatch(branch or ""))


def pull_record(pull, timeline, runs, moves, default_branch):
    number = pull["number"]
    opened, merged = parse_time(pull["created_at"]), parse_time(pull.get("merged_at"))
    closed = parse_time(pull.get("closed_at"))
    main_shas = {m["sha"] for m in moves if m["sha"]}
    commits = commits_of(timeline)
    catch_ups = [c for c in commits if is_catch_up(c, default_branch, main_shas)]
    catch_up_shas = {c["sha"] for c in catch_ups}
    own = [c for c in commits if c["sha"] not in catch_up_shas]
    every_run = runs_of(pull, runs, {c["sha"] for c in commits})
    mine = one_per_head(every_run)
    redone = [r for r in mine if r.get("head_sha") in catch_up_shas]
    last_own = own[-1]["sha"] if own else None
    finished_heads = {last_own} | {c["sha"] for c in commits[[c["sha"] for c in commits].index(last_own) + 1:]} \
        if last_own else {c["sha"] for c in commits}
    greens = sorted(parse_time(r["updated_at"]) for r in mine
                    if r.get("conclusion") == "success" and r.get("head_sha") in finished_heads)
    first_green = greens[0] if greens else None
    after_green = [c for c in catch_ups if first_green and (commit_time(c) or opened) >= first_green]
    end = merged or closed
    # A thread often works on its branch, and takes the default branch in,
    # before it opens the pull request, so the branch's life starts at its
    # first commit where that came first.
    started = min([opened] + [t for t in (commit_time(c) for c in commits) if t])
    marks, conflict_marks = board_marks(timeline)
    ready = [parse_time(e["created_at"]) for e in events(timeline, "ready_for_review")]
    auto = [parse_time(e["created_at"]) for e in events(timeline, "auto_merge_enabled")]
    return {
        "number": number,
        "branch": pull["head"]["ref"],
        "base": pull["base"]["ref"],
        "claim": is_claim(pull["head"]["ref"]),
        "opened": iso(opened),
        "started": iso(started),
        "ready": iso(ready[-1] if ready else (None if pull.get("draft") else opened)),
        "merged": iso(merged),
        "closed": iso(closed),
        "commits": len(commits),
        "catch_ups": len(catch_ups),
        "catch_ups_by_button": sum(1 for c in catch_ups if (c.get("committer") or {}).get("name") == GITHUB_COMMITTER),
        "force_pushes": len(events(timeline, "head_ref_force_pushed")),
        "landings_during_life": len(landings_since_base(commits, moves, started, end, number)) if end else None,
        "landings_after_green": len(landed_between(moves, first_green, merged, number)) if first_green and merged else 0,
        "check_runs": len(mine),
        "check_runs_redone": len(redone),
        "check_seconds": round(sum(run_seconds(r) or 0 for r in mine)),
        "check_seconds_redone": round(sum(run_seconds(r) or 0 for r in redone)),
        "reruns": sum(max(0, (r.get("run_attempt") or 1) - 1) for r in every_run),
        "runs_cancelled": sum(1 for r in every_run if r.get("conclusion") == "cancelled"),
        "first_green": iso(first_green),
        "catch_ups_after_green": len(after_green),
        "stale_seconds": round(seconds(first_green, merged)) if after_green and merged else 0,
        "board_main_moved": len(marks),
        "board_conflicts": len(conflict_marks),
        "auto_merge_enabled": iso(auto[-1]) if auto else None,
        "caused_by": [[c["sha"], taken] for c, taken in zip(catch_ups, causes(commits, catch_ups, moves, started, number))],
    }


# The summary.

def median(values):
    return statistics.median(values) if values else None


def mean(values):
    return round(statistics.fmean(values), 2) if values else None


def share(part, whole):
    return round(part / whole, 3) if whole else None


def overlapping(record, records):
    """How many other pull requests were at work at some moment of this
    one's life, from their first commit: the parallel work it shared the
    default branch with."""
    start, end = parse_time(record["started"]), parse_time(record["closed"])
    count = 0
    for other in records:
        if other["number"] == record["number"]:
            continue
        o_start, o_end = parse_time(other["started"]), parse_time(other["closed"])
        if o_start < end and (o_end is None or o_end > start):
            count += 1
    return count


BUCKETS = ("0", "1-2", "3-5", "6-10", "11+")


def bucket(count):
    return "0" if count == 0 else "1-2" if count <= 2 else "3-5" if count <= 5 else "6-10" if count <= 10 else "11+"


def group_stats(rows):
    return {
        "merged": len(rows),
        "with_catch_up": sum(1 for r in rows if r["catch_ups"]),
        "share_with_catch_up": share(sum(1 for r in rows if r["catch_ups"]), len(rows)),
        "catch_ups": sum(r["catch_ups"] for r in rows),
        "stale_after_green": sum(1 for r in rows if r["catch_ups_after_green"]),
        "check_runs": sum(r["check_runs"] for r in rows),
        "check_runs_redone": sum(r["check_runs_redone"] for r in rows),
        "stale_hours": round(sum(r["stale_seconds"] for r in rows) / 3600, 2),
    }


def main_health(runs):
    """The check's runs on the default branch after each landing, by day:
    with the up-to-date rule off a pull request is checked against an older
    default branch, so two that pass alone can fail together, and this is
    where that shows, the safety side of turning the rule off."""
    by_day = defaultdict(Counter)
    for run in runs:
        if run.get("conclusion") in ("success", "failure"):
            by_day[(run.get("created_at") or "")[:10]][run["conclusion"]] += 1
    return {day: dict(c) for day, c in sorted(by_day.items())}


def snapshot_summary(snapshots):
    seen = seen_states(snapshots)
    return {
        "snapshots": len(snapshots),
        "pulls_seen": len(seen),
        "pulls_seen_behind": sum(1 for c in seen.values() if c["behind"]),
        "pulls_seen_dirty": sum(1 for c in seen.values() if c["dirty"] or c["conflict"]),
        "since": snapshots[0].get("at") if snapshots else None,
    }


def owned_catch_ups(records):
    """Each catch-up once: a branch made from another thread's branch
    carries that branch's catch-ups in its own timeline too, so a catch-up
    is the earliest-merged pull request's that holds it."""
    owner = {}
    for r in sorted(records, key=lambda r: r["merged"] or r["closed"] or ""):
        for sha, _ in r["caused_by"]:
            owner.setdefault(sha, r["number"])
    return {r["number"]: [(sha, taken) for sha, taken in r["caused_by"] if owner[sha] == r["number"]] for r in records}


def summary(records, snapshots=(), default_branch=None):
    records = [r for r in records if default_branch is None or r["base"] == default_branch]
    owned = owned_catch_ups(records)
    records = [dict(r, catch_ups=len(owned[r["number"]])) for r in records]
    merged = [r for r in records if r["merged"]]
    unmerged = [r for r in records if not r["merged"] and r["closed"]]
    merged_branches = {(r["branch"], r["merged"]) for r in merged}
    landed_later = sum(1 for r in unmerged
                       if any(b == r["branch"] and m > r["closed"] for b, m in merged_branches))
    runs = sum(r["check_runs"] for r in merged)
    redone = sum(r["check_runs_redone"] for r in merged)
    stale = [r["stale_seconds"] for r in merged if r["stale_seconds"]]
    pairs = Counter()
    branch_of = {r["number"]: r["branch"] for r in records}
    for r in merged:
        for _, taken in owned[r["number"]]:
            for number in taken:
                pairs[(number, r["number"])] += 1
    caused = Counter(n for (n, _), k in pairs.items() for _ in range(k))
    by_day, by_parallel = defaultdict(list), defaultdict(list)
    for r in merged:
        by_day[r["merged"][:10]].append(r)
        by_parallel[bucket(overlapping(r, records))].append(r)
    return {
        "merged": len(merged),
        "closed_unmerged": len(unmerged),
        "closed_unmerged_branch_landed_later": landed_later,
        "with_catch_up": sum(1 for r in merged if r["catch_ups"]),
        "share_with_catch_up": share(sum(1 for r in merged if r["catch_ups"]), len(merged)),
        "catch_ups": sum(r["catch_ups"] for r in merged),
        "catch_ups_by_button": sum(r["catch_ups_by_button"] for r in merged),
        "catch_ups_max": max((r["catch_ups"] for r in merged), default=0),
        "force_pushes": sum(r["force_pushes"] for r in merged),
        "landings_during_life_median": median([r["landings_during_life"] for r in merged]),
        "landings_during_life_mean": mean([r["landings_during_life"] for r in merged]),
        "stale_after_green": sum(1 for r in merged if r["catch_ups_after_green"]),
        "share_stale_after_green": share(sum(1 for r in merged if r["catch_ups_after_green"]), len(merged)),
        "landings_after_green_total": sum(r["landings_after_green"] for r in merged),
        "check_runs": runs,
        "check_runs_redone": redone,
        "share_runs_redone": share(redone, runs),
        "check_hours": round(sum(r["check_seconds"] for r in merged) / 3600, 2),
        "check_hours_redone": round(sum(r["check_seconds_redone"] for r in merged) / 3600, 2),
        "reruns": sum(r["reruns"] for r in merged),
        "stale_hours_total": round(sum(stale) / 3600, 2),
        "stale_minutes_median": round(median(stale) / 60, 1) if stale else None,
        "board_main_moved": sum(r["board_main_moved"] for r in records),
        "board_conflicts": sum(r["board_conflicts"] for r in records),
        "with_board_conflict": sum(1 for r in records if r["board_conflicts"]),
        "auto_merge_used": sum(1 for r in merged if r["auto_merge_enabled"]),
        "by_day": {day: group_stats(rows) for day, rows in sorted(by_day.items())},
        "live": snapshot_summary(list(snapshots)),
        "by_protocol": {"claim": group_stats([r for r in merged if r["claim"]]),
                        "no_claim": group_stats([r for r in merged if not r["claim"]])},
        "by_parallel_work": {k: group_stats(by_parallel[k]) for k in BUCKETS if k in by_parallel},
        "top_causes": [{"number": n, "branch": branch_of.get(n), "catch_ups_caused": k} for n, k in caused.most_common(10)],
        "top_pairs": [{"landed": a, "made_stale": b, "times": k} for (a, b), k in pairs.most_common(10)],
    }


def collect(api, default_branch, workflow, previous=None, snapshots=(), max_new=None, log=print):
    pulls = [p for p in read_pulls(api) if same_repository(p, api.repo)]
    moves = landings(pulls, default_branch)
    closing = {p["number"]: (iso(parse_time(p.get("closed_at"))), iso(parse_time(p.get("merged_at")))) for p in pulls}
    kept = {r["number"]: r for r in (previous or {}).get("pulls", []) if r.get("closed")}
    # A pull request closed, then reopened and merged, is read again.
    kept = {n: r for n, r in kept.items() if (r["closed"], r["merged"]) == closing.get(n)}
    runs_by_branch, records, unread = {}, [], 0
    closed = [p for p in pulls if p["state"] == "closed"]
    fresh = [p["number"] for p in closed if p["number"] not in kept]
    # The newest first, so a run that stops at its bound leaves the oldest
    # for the next run, and the record is never missing the latest landing.
    allowed = set(sorted(fresh, reverse=True)[:max_new] if max_new is not None else fresh)
    for pull in closed:
        if pull["number"] in kept:
            records.append(kept[pull["number"]])
            continue
        if pull["number"] not in allowed:
            unread += 1
            continue
        branch = pull["head"]["ref"]
        if branch not in runs_by_branch:
            runs_by_branch[branch] = read_runs(api, workflow, branch)
        records.append(pull_record(pull, read_timeline(api, pull["number"]), runs_by_branch[branch], moves, default_branch))
    # The default branch's own runs, read again only from the last day the
    # record holds, so a run after each merge reads a page, not the history.
    health = dict(((previous or {}).get("summary") or {}).get("default_branch_checks") or {})
    since = max(health) if health else None
    main_runs = read_runs(api, workflow, default_branch, event="push", **({"created": f">={since}"} if since else {}))
    health = {day: c for day, c in health.items() if since is None or day < since}
    health.update(main_health(main_runs))
    log(f"{len(records)} closed pull requests kept, {len(allowed)} read now, {unread} left for the next run")
    return {
        "format": FORMAT,
        "repository": api.repo,
        "default_branch": default_branch,
        "workflow": workflow,
        "generated_at": iso(datetime.now(timezone.utc)),
        "unread": unread,
        "summary": dict(summary(records, snapshots, default_branch), default_branch_checks=health),
        "pulls": records,
    }


def hours(value):
    return f"{value:.1f} h" if value is not None else "-"


def report(record):
    s = record["summary"]
    lines = [
        f"# Stale branches in {record['repository']}",
        "",
        f"Read {record['generated_at']} from GitHub's history: {s['merged']} merged pull requests, "
        f"{s['closed_unmerged']} closed without a merge"
        + (f"; {record.get('unread')} older ones are left for the next run." if record.get("unread") else "."),
        "",
        "| measure | value |",
        "|---|---|",
        f"| merged pull requests that had to take {record['default_branch']} in | {s['with_catch_up']} ({s['share_with_catch_up']}) |",
        f"| catch-up merges in all (by GitHub's Update branch) | {s['catch_ups']} ({s['catch_ups_by_button']}) |",
        f"| forced pushes (rebases or amends, not told apart) | {s['force_pushes']} |",
        f"| landings under a pull request in its life, median / mean | {s['landings_during_life_median']} / {s['landings_during_life_mean']} |",
        f"| finished and green, then made stale before landing | {s['stale_after_green']} ({s['share_stale_after_green']}) |",
        f"| wall-clock from first green to merge where it went stale | {hours(s['stale_hours_total'])}, median {s['stale_minutes_median'] or 0} min |",
        f"| check runs / on catch-up heads alone | {s['check_runs']} / {s['check_runs_redone']} ({s['share_runs_redone']}) |",
        f"| runner hours of the check / redone | {hours(s['check_hours'])} / {hours(s['check_hours_redone'])} |",
        f"| re-runs of a run | {s['reruns']} |",
        f"| board's main-moved comments / conflicting | {s['board_main_moved']} / {s['board_conflicts']} |",
        f"| seen live: snapshots / pull requests behind / in conflict | {s['live']['snapshots']} / {s['live']['pulls_seen_behind']} / {s['live']['pulls_seen_dirty']} |",
        f"| closed unmerged / whose branch landed later | {s['closed_unmerged']} / {s['closed_unmerged_branch_landed_later']} |",
        "",
        "## By the parallel work beside each pull request",
        "",
        "| other pull requests open in its life | merged | took main in | stale after green | runs | redone | stale hours |",
        "|---|---|---|---|---|---|---|",
    ]
    for key in [k for k in BUCKETS if k in s["by_parallel_work"]]:
        g = s["by_parallel_work"][key]
        lines.append(f"| {key} | {g['merged']} | {g['with_catch_up']} ({g['share_with_catch_up']}) | {g['stale_after_green']} "
                     f"| {g['check_runs']} | {g['check_runs_redone']} | {g['stale_hours']} |")
    lines += ["", "## Claim branches against other branches", "",
              "| branch | merged | took main in | stale after green | runs | redone | stale hours |",
              "|---|---|---|---|---|---|---|"]
    for key, g in s["by_protocol"].items():
        lines.append(f"| {key} | {g['merged']} | {g['with_catch_up']} ({g['share_with_catch_up']}) | {g['stale_after_green']} "
                     f"| {g['check_runs']} | {g['check_runs_redone']} | {g['stale_hours']} |")
    lines += ["", "## By day of merge", "",
              "| day | merged | took main in | stale after green | runs | redone | stale hours |",
              "|---|---|---|---|---|---|---|"]
    for day, g in s["by_day"].items():
        lines.append(f"| {day} | {g['merged']} | {g['with_catch_up']} | {g['stale_after_green']} "
                     f"| {g['check_runs']} | {g['check_runs_redone']} | {g['stale_hours']} |")
    lines += ["", "## The landings that made the most others catch up", ""]
    for c in s["top_causes"]:
        lines.append(f"- #{c['number']} ({c['branch']}): {c['catch_ups_caused']}")
    return "\n".join(lines) + "\n"


def client(repo, token=None):
    from sdlc_protocol.adapters.github import GitHub
    return GitHub(token, repo)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = parser.add_subparsers(dest="command", required=True)
    c = sub.add_parser("collect")
    c.add_argument("--repo", required=True)
    c.add_argument("--default-branch", default="main")
    c.add_argument("--workflow", default=CI_WORKFLOW)
    c.add_argument("--previous")
    c.add_argument("--out", required=True)
    c.add_argument("--snapshots")
    c.add_argument("--max-new", type=int)
    n = sub.add_parser("snapshot")
    n.add_argument("--repo", required=True)
    n.add_argument("--default-branch", default="main")
    n.add_argument("--append", required=True)
    r = sub.add_parser("report")
    r.add_argument("path")
    args = parser.parse_args(argv)
    if args.command == "report":
        sys.stdout.write(report(json.loads(Path(args.path).read_text())))
        return 0
    if args.command == "snapshot":
        shot = snapshot(client(args.repo), args.default_branch)
        with open(args.append, "a") as out:
            out.write(json.dumps(shot, sort_keys=True) + "\n")
        return 0
    previous = None
    if args.previous and Path(args.previous).is_file():
        previous = json.loads(Path(args.previous).read_text())
        if previous.get("format") != FORMAT or previous.get("repository") != args.repo:
            previous = None
    record = collect(client(args.repo), args.default_branch, args.workflow, previous, read_snapshots(args.snapshots), args.max_new)
    Path(args.out).write_text(json.dumps(record, indent=1, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
