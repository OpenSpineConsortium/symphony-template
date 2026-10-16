"""Run the workflow's write step for real, as GitHub runs it (bash --noprofile
--norc -eo pipefail), against local bare origins, in the cases the tests
leave out."""
import json
import os
import subprocess
import sys
import tempfile
from functools import partial
from pathlib import Path
from unittest import mock

TREE = Path(__file__).resolve().parent / "tree"
sys.path.insert(0, str(TREE / "tests"))
import test_metrics as T  # noqa: E402

metrics = T.metrics
SHELL = ["bash", "--noprofile", "--norc", "-eo", "pipefail", "-c"]


def step(folder, origin, record, sums=None, extra_env=None, shell=SHELL):
    work = T.clone_of(folder, origin, "work")
    (work / "tools").symlink_to(TREE / "tools")
    temp = Path(folder) / "runner"
    temp.mkdir()
    (temp / "METRICS.json").write_text(json.dumps(record, indent=2) + "\n")
    if sums is not None:
        (temp / "PROFILE.json").write_text(json.dumps(sums, indent=2) + "\n")
    env = {**os.environ, **T.GIT_ENV, "RUNNER_TEMP": str(temp), **(extra_env or {})}
    script = T.run_block(T.step_lines(T.WRITE_STEP))
    return subprocess.run([*shell, script], cwd=work, env=env, capture_output=True, text=True)


def show(label, done, origin):
    try:
        tree = sorted(T.tree_of(origin, "metrics"))
    except AssertionError:
        tree = "no branch"
    print(f"{label}: exit={done.returncode} out={done.stdout.strip()!r} err={done.stderr.strip()[:200]!r} tree={tree}")


def race_env(folder, origin, seeded, judge_text):
    race = T.clone_of(folder, origin, "race")
    judge = Path(folder) / "JUDGE.json"
    judge.write_text(judge_text)
    T.git(race, "fetch", "--quiet", "origin", "metrics")
    with mock.patch.dict(os.environ, T.GIT_ENV):
        race_commit = metrics.judge_commit(partial(T.run_in, race), judge, seeded)
    shim = Path(folder) / "bin"
    shim.mkdir()
    (shim / "git").write_text(T.RACE_GIT)
    (shim / "git").chmod(0o755)
    real = subprocess.run(["bash", "-c", "command -v git"], capture_output=True, text=True).stdout.strip()
    return {"PATH": f"{shim}{os.pathsep}{os.environ['PATH']}", "REAL_GIT": real,
            "RACE_DONE": str(Path(folder) / "race-done"), "RACE_CLONE": str(race), "RACE_COMMIT": race_commit}


OLD, NEW_TIME, MOVED = T.OLD, T.NEW_TIME, T.MOVED
SUMS_OLD, SUMS_NEW_TIME, SUMS_MOVED = T.SUMS_OLD, T.SUMS_NEW_TIME, T.SUMS_MOVED
dumped = lambda value: json.dumps(value, indent=2) + "\n"  # noqa: E731

with tempfile.TemporaryDirectory() as folder:
    origin, _ = T.seeded_origin(folder, {"PROFILE.json": dumped(SUMS_OLD)})
    show("1 branch with PROFILE.json alone, run writes both", step(folder, origin, NEW_TIME, SUMS_NEW_TIME), origin)

with tempfile.TemporaryDirectory() as folder:
    origin, _ = T.seeded_origin(folder, {"PROFILE.json": dumped(SUMS_OLD), "JUDGE.json": '{"n": 1}\n'})
    done = step(folder, origin, NEW_TIME, SUMS_OLD)
    show("2 branch PROFILE+JUDGE, no METRICS", done, origin)

with tempfile.TemporaryDirectory() as folder:
    origin, seeded = T.seeded_origin(folder, {"METRICS.json": dumped(OLD), "PROFILE.json": dumped(SUMS_OLD),
                                              "JUDGE.json": '{"n": 1}\n'})
    env = race_env(folder, origin, seeded, '{"n": 2}\n')
    done = step(folder, origin, MOVED, SUMS_MOVED, env)
    show("3 judge push meanwhile, run writes both", done, origin)
    print("   JUDGE:", T.git(origin, "show", "metrics:JUDGE.json"), " PROFILE moved:",
          json.loads(T.git(origin, "show", "metrics:PROFILE.json")) == SUMS_MOVED,
          " commits:", T.git(origin, "rev-list", "--count", "metrics"))

with tempfile.TemporaryDirectory() as folder:
    origin, seeded = T.seeded_origin(folder, {"METRICS.json": dumped(OLD), "PROFILE.json": dumped(SUMS_OLD),
                                              "JUDGE.json": '{"n": 1}\n'})
    blob = T.tree_of(origin, seeded)["PROFILE.json"]
    env = race_env(folder, origin, seeded, '{"n": 2}\n')
    done = step(folder, origin, MOVED, None, env)
    show("4 judge push meanwhile, run wrote no PROFILE", done, origin)
    print("   PROFILE kept:", T.tree_of(origin, "metrics")["PROFILE.json"] == blob,
          " JUDGE:", T.git(origin, "show", "metrics:JUDGE.json"))

with tempfile.TemporaryDirectory() as folder:
    origin, _ = T.seeded_origin(folder, {"METRICS.json": dumped(OLD), "PROFILE.json": dumped(SUMS_OLD)})
    done = step(folder, origin, metrics.OFF_RECORD, metrics.PROFILE_OFF)
    show("5 sharing turned off", done, origin)
    print("   PROFILE:", T.git(origin, "show", "metrics:PROFILE.json"))

with tempfile.TemporaryDirectory() as folder:
    origin, _ = T.seeded_origin(folder, {"METRICS.json": dumped(OLD), "PROFILE.json": dumped(SUMS_OLD),
                                         "notes.txt": "the project's own\n"})
    show("6 foreign file beside PROFILE.json", step(folder, origin, MOVED, SUMS_MOVED), origin)

with tempfile.TemporaryDirectory() as folder:
    origin, _ = T.seeded_origin(folder, {"METRICS.json": dumped(NEW_TIME), "PROFILE.json": "not json"})
    show("7 branch PROFILE.json not JSON, run's same METRICS", step(folder, origin, NEW_TIME, SUMS_NEW_TIME), origin)

with tempfile.TemporaryDirectory() as folder:
    origin, _ = T.seeded_origin(folder, {"METRICS.json": dumped(OLD), "PROFILE.json": dumped(SUMS_OLD)})
    show("8 same, under bash -e alone (the tests' shell)",
         step(folder, origin, NEW_TIME, SUMS_NEW_TIME, shell=["bash", "-e", "-c"]), origin)

# 9: the old workflow (before this commit) meeting a branch the new one wrote.
BASE = Path(__file__).resolve().parent / "base"
old_lines = (BASE / ".github" / "workflows" / "metrics.yml").read_text().splitlines()
start = old_lines.index("      - name: Write METRICS.json to the branch metrics when it changed")
end = next(i for i in range(start + 1, len(old_lines)) if old_lines[i].startswith("      - ") or i == len(old_lines) - 1)
old_script = T.run_block(old_lines[start:end + 1])
with tempfile.TemporaryDirectory() as folder:
    origin, _ = T.seeded_origin(folder, {"METRICS.json": dumped(OLD), "PROFILE.json": dumped(SUMS_OLD)})
    work = T.clone_of(folder, origin, "work")
    (work / "tools").symlink_to(BASE / "tools")
    temp = Path(folder) / "runner"
    temp.mkdir()
    (temp / "METRICS.json").write_text(dumped(MOVED))
    done = subprocess.run([*SHELL, old_script], cwd=work, env={**os.environ, **T.GIT_ENV, "RUNNER_TEMP": str(temp)},
                          capture_output=True, text=True)
    show("9 the old step on a branch holding PROFILE.json", done, origin)
