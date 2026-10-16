"""SWE-bench's instances, read from its task repository, and the order a
run takes them in.

The task repository, github.com/SWE-bench/swe-bench-tasks, holds one
directory per instance under tasks/: task.yaml (the repository, the base
commit, the image, the datasets the instance is in, the difficulty the
Verified annotators gave it), problem_statement.md, tests.json (the
FAIL_TO_PASS and PASS_TO_PASS lists), gold.patch, test.patch and eval.sh.
It is what SWE-bench's harness reads with --task-repo, so nothing here
needs HuggingFace, which the project's cloud sessions cannot reach.

task.yaml is read by a small reader of its own rather than a YAML
library, since the files use flat keys, quoted scalars and one list, and
the project takes no dependency; a file this reader cannot make sense of
is refused by name rather than guessed at.

The order is nested and stratified (PLAN.md): the pool's instances are
grouped by stratum (the repository and the difficulty by default), each
stratum is shuffled by the seed, and the order takes one instance from
each stratum in turn, strata in name order, so the first N instances of
the order are a balanced sample for every N and a run grows by taking
more of the same order.

    python3 flowbench/tasks.py TASK_REPO table [--pool verified,lite]
    python3 flowbench/tasks.py TASK_REPO order --seed 0 [--sample N]
    python3 flowbench/tasks.py TASK_REPO show INSTANCE
"""

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path

DATASETS = {
    "full": "SWE-bench/SWE-bench",
    "verified": "SWE-bench/SWE-bench_Verified",
    "lite": "SWE-bench/SWE-bench_Lite",
}
DEFAULT_POOL = ("verified", "lite")
DEFAULT_STRATA = ("repo", "difficulty")
REQUIRED_KEYS = ("instance_id", "repo", "base_commit", "image")


class TaskError(ValueError):
    """A task directory this reader will not guess at."""


@dataclass
class Task:
    instance_id: str
    repo: str
    base_commit: str
    image: str
    datasets: tuple = ()
    split: str = ""
    version: str = ""
    difficulty: str = ""
    created_at: str = ""
    log_parser: str = ""
    problem_statement: str = ""
    fail_to_pass: int = 0
    pass_to_pass: int = 0
    gold_patch_lines: int = 0
    directory: str = ""
    fields: dict = field(default_factory=dict)

    @property
    def owner(self):
        """The repository's owner, the stratum key "repo" uses, since the
        instance id names the owner and the repository (django__django)."""
        return self.repo.split("/")[0]

    def in_dataset(self, name):
        return DATASETS.get(name, name) in self.datasets

    def stratum(self, keys=DEFAULT_STRATA):
        """The instance's stratum under the keys: repo (the owner),
        difficulty (the annotators' band, or unknown), size (the gold
        patch's line count, bucketed later by the pool's terciles)."""
        parts = []
        for key in keys:
            if key == "repo":
                parts.append(self.owner)
            elif key == "difficulty":
                parts.append(self.difficulty or "unknown")
            elif key == "size":
                parts.append(f"size:{self.gold_patch_lines}")
            else:
                raise TaskError(f"unknown stratum key {key!r}")
        return "/".join(parts)


def unquote(value):
    """A YAML scalar as text: quotes stripped, the rest as written."""
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "'\"":
        inner = value[1:-1]
        return inner.replace("''", "'") if value[0] == "'" else inner.replace('\\"', '"')
    return value


def read_yaml_flat(text, where):
    """The flat key: value pairs and the one kind of list task.yaml uses
    (a key followed by "- item" lines); anything else is refused."""
    found = {}
    key = None
    for number, raw in enumerate(text.splitlines(), start=1):
        line = raw.rstrip()
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line.startswith("- ") or line.startswith("  - "):
            if key is None or not isinstance(found.get(key), list):
                raise TaskError(f"{where}: line {number} lists under no key")
            found[key].append(unquote(line.split("- ", 1)[1]))
            continue
        if line[0] in " \t":
            raise TaskError(f"{where}: line {number} is indented in a way this reader does not know")
        name, sep, value = line.partition(":")
        if not sep or not name.strip():
            raise TaskError(f"{where}: line {number} is not a key: value line")
        key = name.strip()
        found[key] = [] if value.strip() == "" else unquote(value)
    return found


def patch_lines(text):
    """The lines a patch adds or removes, its size for the strata."""
    count = 0
    for line in text.splitlines():
        if (line.startswith("+") and not line.startswith("+++")) or (line.startswith("-") and not line.startswith("---")):
            count += 1
    return count


def read_task(directory):
    """One instance from its directory; TaskError when a required file or
    key is missing or unreadable."""
    directory = Path(directory)
    where = directory / "task.yaml"
    try:
        fields = read_yaml_flat(where.read_text(encoding="utf-8"), where)
    except OSError as error:
        raise TaskError(f"{where}: {error.strerror}") from error
    for key in REQUIRED_KEYS:
        if not fields.get(key):
            raise TaskError(f"{where}: no {key}")
    if fields["instance_id"] != directory.name:
        raise TaskError(f"{where}: instance_id {fields['instance_id']} is not the directory's name")
    datasets = fields.get("datasets", [])
    if not isinstance(datasets, list):
        datasets = [datasets]
    tests = {}
    tests_file = directory / "tests.json"
    if tests_file.is_file():
        try:
            tests = json.loads(tests_file.read_text(encoding="utf-8"))
        except ValueError as error:
            raise TaskError(f"{tests_file}: {error}") from error
    statement = directory / "problem_statement.md"
    gold = directory / "gold.patch"
    return Task(
        instance_id=fields["instance_id"],
        repo=fields["repo"],
        base_commit=fields["base_commit"],
        image=fields["image"],
        datasets=tuple(datasets),
        split=fields.get("split", ""),
        version=str(fields.get("version", "")),
        difficulty=fields.get("difficulty", ""),
        created_at=fields.get("created_at", ""),
        log_parser=fields.get("log_parser", ""),
        problem_statement=statement.read_text(encoding="utf-8") if statement.is_file() else "",
        fail_to_pass=len(tests.get("FAIL_TO_PASS", [])),
        pass_to_pass=len(tests.get("PASS_TO_PASS", [])),
        gold_patch_lines=patch_lines(gold.read_text(encoding="utf-8", errors="replace")) if gold.is_file() else 0,
        directory=str(directory),
        fields=fields,
    )


def read_tasks(task_repo):
    """Every instance of the task repository, by id; a directory the
    reader refuses stops the read, since a silently skipped instance
    would change the pool."""
    root = Path(task_repo) / "tasks"
    if not root.is_dir():
        raise TaskError(f"{task_repo}: no tasks/ directory; is it a checkout of SWE-bench/swe-bench-tasks?")
    tasks = []
    for directory in sorted(root.iterdir()):
        if directory.is_dir() and (directory / "task.yaml").is_file():
            tasks.append(read_task(directory))
    return tasks


def pool(tasks, names=DEFAULT_POOL):
    """The instances in every named dataset (verified and lite by default:
    human-verified and well specified, PLAN.md)."""
    return [task for task in tasks if all(task.in_dataset(name) for name in names)]


def size_terciles(tasks):
    """The two cut points that split the gold patch sizes into thirds."""
    sizes = sorted(task.gold_patch_lines for task in tasks)
    if not sizes:
        return (0, 0)
    return (sizes[len(sizes) // 3], sizes[(2 * len(sizes)) // 3])


def stratum_of(task, keys, terciles):
    """The stratum with the size key bucketed by the pool's terciles."""
    name = task.stratum(keys)
    if "size" in keys:
        low, high = terciles
        bucket = "small" if task.gold_patch_lines < low else "large" if task.gold_patch_lines >= high else "medium"
        name = name.replace(f"size:{task.gold_patch_lines}", f"size:{bucket}")
    return name


def strata(tasks, keys=DEFAULT_STRATA):
    """The pool grouped by stratum, strata in name order, instances in id
    order inside each."""
    terciles = size_terciles(tasks)
    groups = {}
    for task in sorted(tasks, key=lambda t: t.instance_id):
        groups.setdefault(stratum_of(task, keys, terciles), []).append(task)
    return dict(sorted(groups.items()))


def order(tasks, seed=0, keys=DEFAULT_STRATA):
    """The nested stratified order: each stratum shuffled by the seed and
    its name, then one instance from each stratum in turn until every
    stratum is spent. The sample of size N is the first N."""
    groups = strata(tasks, keys)
    queues = []
    for name, members in groups.items():
        drawn = list(members)
        random.Random(f"{seed}:{name}").shuffle(drawn)
        queues.append(drawn)
    ordered = []
    while any(queues):
        for queue in queues:
            if queue:
                ordered.append(queue.pop(0))
    return ordered


def table(groups):
    """The strata and their counts, one line each."""
    lines = [f"{len(members):4d}  {name}" for name, members in groups.items()]
    lines.append(f"{sum(len(m) for m in groups.values()):4d}  in all, {len(groups)} strata")
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description="SWE-bench's instances and the order a run takes them in.")
    parser.add_argument("task_repo", help="a checkout of github.com/SWE-bench/swe-bench-tasks")
    parser.add_argument("--pool", default=",".join(DEFAULT_POOL),
                        help="the datasets an instance must be in, comma separated (default verified,lite)")
    parser.add_argument("--strata", default=",".join(DEFAULT_STRATA),
                        help="the stratum keys: repo, difficulty, size (default repo,difficulty)")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("table", help="the strata and their counts")
    ordering = commands.add_parser("order", help="the nested stratified order, one instance id per line")
    ordering.add_argument("--seed", type=int, default=0)
    ordering.add_argument("--sample", type=int, default=0, help="only the first N")
    showing = commands.add_parser("show", help="one instance's fields as JSON")
    showing.add_argument("instance")
    args = parser.parse_args(argv)
    try:
        tasks = read_tasks(args.task_repo)
        keys = tuple(k for k in args.strata.split(",") if k)
        chosen = pool(tasks, tuple(n for n in args.pool.split(",") if n))
        if args.command == "table":
            print(table(strata(chosen, keys)))
        elif args.command == "order":
            ordered = order(chosen, args.seed, keys)
            if args.sample:
                ordered = ordered[: args.sample]
            for task in ordered:
                print(task.instance_id)
        else:
            found = [t for t in tasks if t.instance_id == args.instance]
            if not found:
                print(f"{args.instance}: not in {args.task_repo}", file=sys.stderr)
                return 1
            shown = {k: v for k, v in found[0].__dict__.items() if k not in ("problem_statement", "fields")}
            print(json.dumps(shown, indent=2, sort_keys=True))
    except TaskError as error:
        print(error, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
