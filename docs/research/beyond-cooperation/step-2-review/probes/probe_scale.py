"""Time profile_keys' actions_runs filter at the usage cache's largest size:
200 new records a run kept for the 60-day look-back is 12,000 records, and
those a workflow uploads as the coordinator in the window, naming nothing,
are all overhead."""
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

TREE = Path(__file__).resolve().parent / "tree"
sys.path.insert(0, str(TREE / "tools"))
import economics  # noqa: E402

prof = {"calls": 1, "peak": 1}
look_back = [{"workflow": "coordinator", "job": "plan", "issue": 1_000_000 + i, "pull": None, "seconds": 0.0,
              "models": {}, "profile": prof} for i in range(6000)]
window = [{"workflow": "coordinator", "job": "plan", "issue": 2_000_000 + i, "pull": None, "seconds": 0.0,
           "models": {}, "profile": prof} for i in range(6000)]
records_all, in_window = look_back + window, window
now = datetime(2026, 10, 10, tzinfo=timezone.utc)
works = [economics.Work(n, claim=n + 5000, start=now - timedelta(days=1), end=now) for n in range(400)]

start = time.perf_counter()
overhead = economics.overhead(works, in_window)
t_overhead = time.perf_counter() - start
start = time.perf_counter()
summed = [record for record in records_all if record["profile"] and (
    any(record is run for run in overhead) or any(economics.names(record, w) for w in works))]
t_summed = time.perf_counter() - start
print(f"overhead {len(overhead)} in {t_overhead:.2f}s; summed {len(summed)} in {t_summed:.2f}s")
ids = {id(run) for run in overhead}
start = time.perf_counter()
fast = [record for record in records_all if record["profile"] and (
    id(record) in ids or any(economics.names(record, w) for w in works))]
print(f"with a set of ids: {len(fast)} in {time.perf_counter() - start:.2f}s")
