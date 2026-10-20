"""The test suite in parts, so CI can run the parts side by side.

The required check spent most of its minutes in one unittest run, one
module after another (docs/research/faster-backend-than-actions.md), so
.github/workflows/ci.yml runs the suite as several jobs at once and the
job named check waits for all of them. Each module goes to exactly one
part: the parts are cut from the same list unittest's discovery finds
(tests/test*.py), longest first into the part with least so far, by the
seconds tests/durations.json records for each module. A module the file
does not name counts as one second, so a stale or missing file only makes
the parts less even, never leaves a test out.

  python3 tools/test_shard.py run          every module, as check.sh runs it
  python3 tools/test_shard.py run 2/4      the second of four parts
  python3 tools/test_shard.py list 2/4     the modules of that part
  python3 tools/test_shard.py measure      time each module alone and
                                           rewrite tests/durations.json
"""

import json
import os
import sys
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TESTS = ROOT / "tests"
DURATIONS = TESTS / "durations.json"
UNKNOWN_SECONDS = 1.0


def modules():
    """The modules unittest's default discovery would load, by name."""
    return sorted(path.stem for path in TESTS.glob("test*.py"))


def recorded_seconds():
    try:
        return json.loads(DURATIONS.read_text(encoding="ascii"))
    except (OSError, ValueError):
        return {}


def parts(names, count, seconds):
    """names cut into count parts, longest first into the lightest part."""
    loads = [0.0] * count
    cut = [[] for _ in range(count)]
    for name in sorted(names, key=lambda name: (-float(seconds.get(name, UNKNOWN_SECONDS)), name)):
        lightest = loads.index(min(loads))
        cut[lightest].append(name)
        loads[lightest] += float(seconds.get(name, UNKNOWN_SECONDS))
    return [sorted(part) for part in cut]


def chosen(which):
    """The modules of part "k/n", or all of them for no part."""
    names = modules()
    if not which:
        return names
    number, _, count = which.partition("/")
    if not (number.isdigit() and count.isdigit() and 1 <= int(number) <= int(count) <= 64):
        raise SystemExit(f"a part is k/n with 1 <= k <= n <= 64, not {which!r}")
    return parts(names, int(count), recorded_seconds())[int(number) - 1]


def suite_of(names):
    """The tests of names, loaded as discovery loads them, with tests/ as the
    top level, so a module imports its neighbours as it does in a full run."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    for name in names:
        suite.addTests(loader.discover(str(TESTS), pattern=f"{name}.py", top_level_dir=str(TESTS)))
    return suite


def run(which):
    names = chosen(which)
    print(f"tests: {len(names)} modules{' in part ' + which if which else ''}", flush=True)
    result = unittest.TextTestRunner(verbosity=2).run(suite_of(names))
    return 0 if result.wasSuccessful() else 1


def measure():
    seconds = {}
    for name in modules():
        started = time.monotonic()
        with open(os.devnull, "w", encoding="ascii") as quiet:
            unittest.TextTestRunner(verbosity=0, stream=quiet).run(suite_of([name]))
        seconds[name] = round(time.monotonic() - started, 1)
    DURATIONS.write_text(json.dumps(seconds, indent=2, sort_keys=True) + "\n", encoding="ascii")
    return 0


def main(argv=None):
    args = sys.argv[1:] if argv is None else argv
    command, which = (args + [""])[0], (args[1] if len(args) > 1 else "")
    if command == "run":
        return run(which)
    if command == "list":
        print("\n".join(chosen(which)))
        return 0
    if command == "measure":
        return measure()
    raise SystemExit(__doc__)


if __name__ == "__main__":
    sys.exit(main())
