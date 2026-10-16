"""Probe profile_keys against economics on odd inputs, over the tests' world."""
import copy
import io
import json
import sys
import tempfile
from contextlib import redirect_stdout
from pathlib import Path

TREE = Path(__file__).resolve().parent / "tree"
sys.path.insert(0, str(TREE / "tests"))
import test_metrics as T  # noqa: E402

metrics = T.metrics


def run(routes):
    with tempfile.TemporaryDirectory() as folder:
        code, record, text, shown = T.collect_profile(folder, routes=routes)
    return record, json.loads(text), shown


def summary(label, record, prof):
    par, cpar = prof["coordination"]["parallel"], record["coordination"]["parallel"]
    by_calls = sum(r["calls"] for r in prof["by_setting"].values())
    print(f"{label}: actions_runs={prof['actions_runs']} sessions={prof['sessions']} "
          f"by_setting.calls={by_calls} parallel.calls={par['calls']} parallel.profiled={par['profiled']} "
          f"| econ.parallel.tokens={cpar['tokens']} econ.actions_runs={record['economics']['actions_runs']} "
          f"econ.measured={cpar['measured']}")


base_record, base_prof, _ = run(T.world_routes())
summary("world", base_record, base_prof)


def with_record(number, rec):
    routes = T.world_routes()
    arts = copy.deepcopy(T.WORLD_ARTIFACTS)
    arts["artifacts"].insert(0, T.artifact(number, f"symphony-usage-{number}-1-x", "2026-10-08T01:00:00Z"))
    arts["total_count"] += 1
    routes[f"{T.API}/actions/artifacts"] = arts
    routes[f"{T.API}/actions/artifacts/{number}/zip"] = T.Redirect(f"{T.STORAGE}/usage/{number}.zip?sig=x")
    routes[f"/usage/{number}.zip"] = rec
    return routes


prof10 = T.run_profile(10, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0)
models = {"claude-opus-5-5": [1, 0, 0, 0, 0]}

# A: a run naming 309 by pull and by its claim's issue (509): once.
r, p, _ = run(with_record(9100, T.usage_record("claude", "claude", models, 1.0, issue=509, pull=309, profile=prof10)))
summary("A pull+own claim", r, p)

# B: a run naming 301 by pull and 304 by 304's claim (504): counted in both.
r, p, _ = run(with_record(9101, T.usage_record("workers", "worker", models, 1.0, issue=504, pull=301, profile=prof10)))
summary("B pull 301 + issue 504", r, p)

# C: 301's first commit (profile line, calls=40) listed in 304's commits too.
routes = T.world_routes()
routes[f"{T.API}/pulls/304/commits"] = routes[f"{T.API}/pulls/304/commits"] + [T.WORLD_COMMITS[301][0]]
r, p, _ = run(routes)
summary("C commit in two PRs", r, p)

# D: a coordinator run in the window naming dependabot's 319 (automation).
r, p, _ = run(with_record(9102, T.usage_record("coordinator", "settle", models, 1.0, pull=319, profile=prof10)))
summary("D coordinator names automation 319", r, p)
print("   by_setting.automation:", {k: p["by_setting"]["automation"][k] for k in ("profiled", "calls")})

# E: a run whose profile has peak alone, naming 305 (unprofiled).
r, p, _ = run(with_record(9103, T.usage_record("claude", "claude", models, 1.0, pull=305,
                                                profile={"peak": 5, "junk": "x", "calls": "7"})))
summary("E peak-only profile on 305", r, p)
print("   one_session:", p["by_setting"]["one_session"])

# F: a coordinator run in the look-back (before the window), naming nothing.
routes = T.world_routes()
arts = copy.deepcopy(T.WORLD_ARTIFACTS)
arts["artifacts"].append(T.artifact(9104, "symphony-usage-9104-1-plan", "2026-09-01T00:00:00Z"))
routes[f"{T.API}/actions/artifacts"] = arts
routes[f"{T.API}/actions/artifacts/9104/zip"] = T.Redirect(f"{T.STORAGE}/usage/9104.zip?sig=x")
routes["/usage/9104.zip"] = T.usage_record("coordinator", "plan", models, 1.0, issue=900, profile=prof10)
r, p, _ = run(routes)
summary("F look-back coordinator", r, p)
