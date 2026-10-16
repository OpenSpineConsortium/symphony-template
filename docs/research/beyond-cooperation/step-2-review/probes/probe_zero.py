"""A run that failed before any API call (a spent usage limit, a bad token):
what its record carries, and what it does to PROFILE.json against what it
does to economics' coordination."""
import copy
import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "tree" / "tests"))
import test_metrics as T  # noqa: E402

usage = T.metrics.usage
with tempfile.TemporaryDirectory() as folder:
    execution = Path(folder) / "claude-execution-output.json"
    execution.write_text(json.dumps([
        {"type": "system", "subtype": "init", "session_id": "x", "tools": [], "model": "claude-opus-5-5"},
        {"type": "result", "subtype": "error_during_execution", "is_error": True, "num_turns": 0,
         "duration_ms": 900, "total_cost_usd": 0, "usage": {}},
    ]))
    profiled = usage.run_profile(str(execution))
    record = usage.actions_record(json.loads(execution.read_text()), "worker", "workers", "w", 505, None)
print("failed run: models", record["models"], "| profile", profiled)

routes = T.world_routes()
arts = copy.deepcopy(T.WORLD_ARTIFACTS)
arts["artifacts"].insert(0, T.artifact(9200, "symphony-usage-9200-1-worker", "2026-10-08T01:00:00Z"))
routes[f"{T.API}/actions/artifacts"] = arts
routes[f"{T.API}/actions/artifacts/9200/zip"] = T.Redirect(f"{T.STORAGE}/usage/9200.zip?sig=x")
routes["/usage/9200.zip"] = T.usage_record("workers", "worker", record["models"], 0.9, issue=505, profile=profiled)
with tempfile.TemporaryDirectory() as folder:
    _, metrics_record, text, _ = T.collect_profile(folder, routes=routes)
prof = json.loads(text)
row = prof["by_setting"]["one_session"]
print("PROFILE one_session (304 and 305):", {k: row[k] for k in ("pull_requests", "profiled", "profiled_merged",
                                                                   "calls", "peak_median")},
      "| world had profiled=1 peak_median=120000")
par = prof["coordination"]["parallel"]
print("PROFILE parallel:", {k: par[k] for k in ("profiled", "profiled_merged", "calls", "peak_median")},
      "| world had 7, 7, 236, 120000")
econ = metrics_record["coordination"]["parallel"]
print("economics parallel:", {k: econ[k] for k in ("measured", "measured_merged", "tokens")},
      "| world had 6, 6, 4504400")
