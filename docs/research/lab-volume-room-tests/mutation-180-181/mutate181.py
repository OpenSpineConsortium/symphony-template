"""Each mutant of the #180 changes, in a scratch copy, must fail a test; prints SURVIVED otherwise.
A mutant is (file, [(old, new), ...]) with each old found exactly once in that file."""
import concurrent.futures
import shutil
import subprocess
import sys
from pathlib import Path

SRC = Path("/tmp/claude-0/-home-claude/ecdd0a20-c17e-5671-b6da-4109dc513c50/scratchpad/snap181")
WORK = Path(sys.argv[1])
RULE_TESTS = ["tests.test_xray_chain.QuotaReadoutTest", "tests.test_xray_chain.SizeRuleTest",
              "tests.test_xray_chain.SlurmScriptsTest"]
GATE_TESTS = ["tests.test_gate"]

U = "grid/unpack.sbatch"
R, B, X, P, G = "grid/size-rule.sh", "grid/platform-fetch.sbatch", "grid/run-xray-chain.sh", "grid/run-platform-fetch.sh", "grid/gate.sh"
ELSE = '  RULE_GETFATTR=getfattr RULE_STAT=stat RULE_SQUEUE=squeue RULE_DF=df\n  RULE_MOUNTINFO=/proc/self/mountinfo RULE_SETTLE=60\n'
OWED_FIRST = ('  if ! said=$(owed_by_running "$job"); then\n    exec 8>&-\n    size_refused "$id" "the queue of slurm could not be read so what the running fetches owe is not known"\n'
              '    return\n  fi\n  read -r owed n unsized <<< "$said"\n  if [ -n "$unsized" ]; then\n    exec 8>&-\n'
              '    size_refused "$id" "the running fetch of $unsized states no size so nothing is admitted beside it"\n    return\n  fi\n')
ROOM = ('  read -r room from <<< "$(settled_room "$VOLUME")"\n  if [ -z "$room" ]; then\n    exec 8>&-\n'
        '    size_refused "$id" "$(room_unread_words "$VOLUME")"\n    return\n  fi\n')
CHAIN_OWED = ('owed=$(owed_by_running "") || { echo "cannot read what the running fetches owe: squeue did not answer; nothing was queued"; exit 2; }\n'
              'read -r owed_bytes owed_n owed_unsized <<< "$owed"\n')
CHAIN_ROOM = ('read -r free_bytes free_from <<< "$(settled_room "$VOLUME")"\nif [ -z "$free_bytes" ]; then\n  why=$(quota_below_words "$VOLUME")\n'
              '  echo "cannot read the free space of $VOLUME: ${why:-neither its CephFS quota nor df answered}; nothing was queued"\n  exit 2\nfi\n')
PLATFORM_OWED = ('if owed=$(owed_by_running ""); then\n  read -r owed_bytes owed_n owed_unsized <<< "$owed"\n'
                 '  owed="$(gb_up "$owed_bytes") GB of it owed to $(running_fetches "$owed_n")${owed_unsized:+, and the running fetch of $owed_unsized states no size}"\n'
                 'else\n  owed="what the running fetches owe not read (squeue did not answer)"\nfi\n')
PLATFORM_ROOM = ('read -r free_gb free_from <<< "$(volume_free_gb "$VOLUME")"\nif [ -z "$free_gb" ]; then\n  why=$(quota_below_words "$VOLUME")\n'
                 '  echo "cannot read the free space of $VOLUME: ${why:-neither its CephFS quota nor df answered}"\n  exit 2\nfi\n')
README_OWED = '  said=$(owed_by_running "")\n  owed_read=$?\n'
README_USED = '  read -r used how entries folders held floor <<< "$(volume_used "$volume")"\n'
LOOP = ('  while [ "$folder" != "$volume" ] && [ "${#folder}" -gt "${#volume}" ]; do\n'
        '    value=$(xattr_whole ceph.quota.max_bytes "$folder") || return 2\n'
        '    [ -z "$value" ] || [ "$value" = 0 ] || return 0\n    folder=${folder%/*}\n  done\n')
SBATCH_ELSE = '  SIZER="$ACQ_ENV/bin/python $REPO/grid/fetch_size.py"\n  XATTR_PYTHON=$ACQ_ENV/bin/python\n  CURL=curl\n'

MUTANTS = {
    "baseline": (R, []),
    "B03b-off-reads-python": (B, [("  RULE_PYTHON=$ACQ_ENV/bin/python\n", "  RULE_PYTHON=${XATTR_PYTHON:-$ACQ_ENV/bin/python}\n")]),
    "B05-unpack-off-reads-python": (U, [("  RULE_PYTHON=$PYDRV\n", "  RULE_PYTHON=${XATTR_PYTHON:-$PYDRV}\n")]),
    "B06-rule-off-reads-python": (R, [("RULE_SETTLE=60 RULE_PYTHON=python3", "RULE_SETTLE=60 RULE_PYTHON=${XATTR_PYTHON:-python3}")]),
    "B07-job-switch-before-rule": (B, [('# shellcheck source=grid/size-rule.sh\n. "$REPO/grid/size-rule.sh"\n', ''), ('  CURL=curl\nfi\n', '  CURL=curl\nfi\n# shellcheck source=grid/size-rule.sh\n. "$REPO/grid/size-rule.sh"\n')]),
    "B08-unpack-switch-before-rule": (U, [('# shellcheck source=grid/size-rule.sh\n. "$REPO/grid/size-rule.sh"\n', ''), ('  RULE_PYTHON=$PYDRV\nfi\n', '  RULE_PYTHON=$PYDRV\nfi\n# shellcheck source=grid/size-rule.sh\n. "$REPO/grid/size-rule.sh"\n')]),
    "B09-reader-reads-env": (R, [("""  "$RULE_PYTHON" -c '""", """  "${XATTR_PYTHON:-python3}" -c '""")]),
    "W04-readout-quota-by-digits": (R, [('  quota=$(xattr_whole ceph.quota.max_bytes "$volume")\n  read -r used', '  quota=$(xattr_digits ceph.quota.max_bytes "$volume")\n  read -r used')]),
    "W05-stat-before-by-digits": (R, [('  before=$(xattr_whole ceph.dir.rbytes "$DATA")', '  before=$(xattr_digits ceph.dir.rbytes "$DATA")')]),
    "W06-stat-after-by-digits": (R, [('  after=$(xattr_whole ceph.dir.rbytes "$DATA")', '  after=$(xattr_digits ceph.dir.rbytes "$DATA")')]),
    "W11-stat-words-by-digits": (R, [('       data_bytes=$(xattr_whole ceph.dir.rbytes "$DATA")', '       data_bytes=$(xattr_digits ceph.dir.rbytes "$DATA")')]),
    "W12-stat-words-no-count-unread": (R, [(' || [ $? != 3 ] || data_bytes="no count"', '')]),
    "Q14-no-data-root-check": (R, [('  local volume folder value\n  data_root_on "$1" || return 1\n', '  local volume folder value\n')]),
}


def run(name):
    path, pairs = MUTANTS[name]
    copy = WORK / name
    shutil.rmtree(copy, ignore_errors=True)
    copy.mkdir(parents=True)
    for part in ("grid", "tests", "tools", "data/splits"):
        shutil.copytree(SRC / part, copy / part, ignore=shutil.ignore_patterns("__pycache__", "logs", "LAST_*"))
    (copy / "grid" / "logs").mkdir(exist_ok=True)
    script = copy / path
    text = script.read_text()
    for old, new in pairs:
        if text.count(old) != 1:
            return f"NO MATCH ({text.count(old)}): {name}: {old[:70]!r}"
        text = text.replace(old, new)
    script.write_text(text)
    tests = GATE_TESTS if path == G else RULE_TESTS
    done = subprocess.run([sys.executable, "-m", "unittest", "-f", *tests], cwd=copy, capture_output=True, text=True,
                          timeout=1800)
    (WORK / f"{name}.log").write_text(done.stdout + done.stderr)
    failed = [line for line in done.stderr.splitlines() if line.startswith(("FAIL:", "ERROR:"))]
    return ("SURVIVED: " if done.returncode == 0 else f"killed ({len(failed)}): ") + name


names = sys.argv[2:] or list(MUTANTS)
with concurrent.futures.ThreadPoolExecutor(4) as pool:
    for line in pool.map(run, names):
        print(line, flush=True)
