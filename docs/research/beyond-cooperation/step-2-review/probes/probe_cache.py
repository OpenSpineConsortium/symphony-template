"""The first run after the upgrade, over a version 1 cache an older run wrote.

Run as: python3 probe_cache.py write   (with the base tree: writes the v1 cache)
        python3 probe_cache.py read    (with either tree: collects once from it)

Scenario 1, retention shorter than the look-back: the cache holds the runs
9001 and 9002, and by the next run their artifacts have expired, as they do
in a repository whose artifact retention is under 60 days.
Scenario 2, more than USAGE_LIMIT records in the look-back: 250 artifacts,
all still downloadable."""
import copy
import io
import json
import sys
import tempfile
from contextlib import redirect_stdout
from pathlib import Path

HERE = Path(__file__).resolve().parent
TREE = HERE / sys.argv[2]
sys.path.insert(0, str(TREE / "tests"))
import test_metrics as T  # noqa: E402

metrics = T.metrics
CACHE = HERE / f"cache-{sys.argv[3]}.json"


def collect(routes, cache):
    with tempfile.TemporaryDirectory() as folder:
        out = Path(folder) / "METRICS.json"
        args = metrics.parse_args(["collect", "--repo", T.REPO, "--out", str(out), "--root", folder, "--now", T.NOW,
                                   "--usage-cache", str(cache)])
        opener = T.FakeGitHub(routes)
        with redirect_stdout(io.StringIO()) as shown:
            metrics.collect(args, {"GITHUB_TOKEN": "t"}, opener=opener, sleep=lambda s: None)
        return json.loads(out.read_text()), shown.getvalue(), opener


def many_routes(count):
    routes = T.world_routes()
    arts = {"total_count": count, "artifacts": []}
    for i in range(count):
        number = 20000 + i
        made = f"2026-10-{1 + i % 9:02d}T{i % 24:02d}:00:00Z"
        arts["artifacts"].append(T.artifact(number, f"symphony-usage-{number}-1-plan", made))
        routes[f"{T.API}/actions/artifacts/{number}/zip"] = T.Redirect(f"{T.STORAGE}/usage/{number}.zip?sig=x")
        routes[f"/usage/{number}.zip"] = T.usage_record("coordinator", "plan", {"claude-opus-5-5": [1000, 0, 0, 0, 0]},
                                                        10.0, issue=900 + i)
    arts["artifacts"].sort(key=lambda a: a["created_at"], reverse=True)
    routes[f"{T.API}/actions/artifacts"] = arts
    return routes


def expired_routes():
    routes = T.world_routes()
    arts = copy.deepcopy(T.WORLD_ARTIFACTS)
    for item in arts["artifacts"]:
        item["expired"] = True
    routes[f"{T.API}/actions/artifacts"] = arts
    return routes


def report(label, record, shown, opener):
    econ = record["economics"]
    print(f"{label}: actions_runs={econ['actions_runs']} unread={econ['actions_runs_unread']} "
          f"tokens_total={econ['tokens_total']} coordinator_usd={econ['coordinator_usd']} "
          f"downloads={sum(p.endswith('/zip') for p in opener.calls)}")


mode, scenario = sys.argv[1], sys.argv[3]
if mode == "write":
    routes = T.world_routes() if scenario == "expired" else many_routes(250)
    CACHE.unlink(missing_ok=True)
    for _ in range(3):
        record, shown, opener = collect(routes, CACHE)
    report(f"older runs ({sys.argv[2]}) built the cache", record, shown, opener)
    print("   cache version:", json.loads(CACHE.read_text())["v"], "records:",
          len(json.loads(CACHE.read_text())["records"]))
else:
    routes = expired_routes() if scenario == "expired" else many_routes(250)
    work = HERE / f"cache-{scenario}-{sys.argv[2]}.json"
    work.write_text(CACHE.read_text())
    record, shown, opener = collect(routes, work)
    report(f"next run with {sys.argv[2]}", record, shown, opener)
