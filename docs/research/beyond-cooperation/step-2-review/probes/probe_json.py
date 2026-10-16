"""Probe crafted profile blocks and trailers: crashes, time, text in the output."""
import json
import sys
import time
from pathlib import Path

TREE = Path(__file__).resolve().parent / "tree"
sys.path.insert(0, str(TREE / "tools"))
import economics  # noqa: E402
import usage  # noqa: E402

profile = usage.profiler()

blocks = [
    {"calls": 2 ** 53 - 1, "peak": 2 ** 53 - 1},
    {"calls": 2 ** 53},
    {"calls": -0},
    {"calls": 1e3},
    {"calls": True},
    {"calls": "1"},
    {"calls": [1]},
    {"calls": {"x": 1}},
    {"calls": None},
    {"Calls": 5},
    {"calls ": 5},
    {"__proto__": 5, "calls": 1},
    {"calls": 10 ** 400},
    {k: 1 for k in profile.TRAILER_FIELDS},
]
for block in blocks:
    try:
        print(repr(block)[:60], "->", economics.profile_counts(block))
    except Exception as problem:  # noqa: BLE001
        print(repr(block)[:60], "-> RAISED", type(problem).__name__, problem)

# A record JSON that json reads into a huge int (1e999 is inf, 9 * 4000 digits is an int json refuses?)
for text in ['{"v": 1, "source": "actions", "profile": {"calls": 1e999}}',
             '{"v": 1, "source": "actions", "profile": {"calls": NaN}}',
             '{"v": 1, "source": "actions", "profile": {"calls": ' + "9" * 4000 + '}}']:
    try:
        data = json.loads(text)
        print(text[:70], "->", economics.actions_record(data)["profile"])
    except Exception as problem:  # noqa: BLE001
        print(text[:70], "-> json/read RAISED", type(problem).__name__, str(problem)[:80])

# Trailers: values that must be passed over.
message = ("Work.\n\nSymphony-Profile: v1 session=../../etc calls=5 calls=6 reads=x read_bytes=99999999999999999 "
           "peak=-1 drops=1e3 tool_seconds=\u0661\u0662 failed=0x10 repeated=007 rereads=+3 compactions= \n"
           "symphony-profile:v1 session=Ab-1 calls=1\n"
           "SYMPHONY-PROFILE:\tv1\tsession=\u00e9\u00e9 calls=2")
print(profile.parse_trailer(message))

# Time: a long last paragraph of profile lines, and one line with a huge number of parts.
lines = "\n".join(f"Symphony-Profile: v1 session=s{i % 99999:05d} calls=9007199254740991 peak=9007199254740991"
                  for i in range(50000))
start = time.perf_counter()
found = profile.parse_trailer("Work.\n\n" + lines)
print(f"50000 lines ({len(lines)} chars): {len(found)} found in {time.perf_counter() - start:.2f}s")
one = "Work.\n\nSymphony-Profile: v1 " + " ".join(f"k{i}=1" for i in range(200000))
start = time.perf_counter()
profile.parse_trailer(one)
print(f"one line of 200000 parts ({len(one)} chars): {time.perf_counter() - start:.2f}s")
blank = "Work.\n" + (" \t" * 500000) + "x\n" + ("\n" + " " * 1000) * 1000
start = time.perf_counter()
profile.parse_trailer(blank)
print(f"blank runs ({len(blank)} chars): {time.perf_counter() - start:.2f}s")
hdr = "Work.\n\n" + ("symphony-profile:" + " \t" * 2000 + "\n") * 500
start = time.perf_counter()
profile.parse_trailer(hdr)
print(f"headers with blanks and no v1 ({len(hdr)} chars): {time.perf_counter() - start:.2f}s")

# pull_profile over a work whose commits carry those lines, and a big sum's JSON.
work = economics.Work(1, commits=[{"commit": {"message": "Work.\n\n" + lines}}] * 250)
start = time.perf_counter()
total = profile.pull_profile(work, [])
print(f"pull_profile over 250 such commits: calls={total['calls']} in {time.perf_counter() - start:.2f}s;"
      f" json ok={bool(json.dumps(total))}")
row = profile.group([work], {1: total})
print("group row calls digits:", len(str(row["calls"])), "peak_median:", row["peak_median"])
