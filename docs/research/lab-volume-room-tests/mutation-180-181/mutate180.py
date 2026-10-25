"""Each mutant of the #180 changes, in a scratch copy, must fail a test; prints SURVIVED otherwise.
A mutant is (file, [(old, new), ...]) with each old found exactly once in that file."""
import concurrent.futures
import shutil
import subprocess
import sys
from pathlib import Path

SRC = Path("/tmp/claude-0/-home-claude/ecdd0a20-c17e-5671-b6da-4109dc513c50/scratchpad/snap180")
WORK = Path(sys.argv[1])
RULE_TESTS = ["tests.test_xray_chain.QuotaReadoutTest", "tests.test_xray_chain.SizeRuleTest",
              "tests.test_xray_chain.SlurmScriptsTest"]
GATE_TESTS = ["tests.test_gate"]

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
    "baseline-gate": (G, []),
    # the switch
    "S01-switch-always-on": (R, [('if [ "${SIZE_RULE_STAND_INS:-}" = yes ]; then\n  RULE_GETFATTR', 'if true; then\n  RULE_GETFATTR')]),
    "S02-off-reads-stat": (R, [(ELSE, ELSE.replace("RULE_STAT=stat", "RULE_STAT=${STAT:-stat}"))]),
    "S03-off-reads-getfattr": (R, [(ELSE, ELSE.replace("RULE_GETFATTR=getfattr", "RULE_GETFATTR=${GETFATTR:-getfattr}"))]),
    "S04-off-reads-squeue": (R, [(ELSE, ELSE.replace("RULE_SQUEUE=squeue", "RULE_SQUEUE=${SQUEUE:-squeue}"))]),
    "S05-off-reads-df": (R, [(ELSE, ELSE.replace("RULE_DF=df", "RULE_DF=${DF:-df}"))]),
    "S06-off-reads-mountinfo": (R, [(ELSE, ELSE.replace("RULE_MOUNTINFO=/proc/self/mountinfo", "RULE_MOUNTINFO=${MOUNTINFO:-/proc/self/mountinfo}"))]),
    "S07-off-reads-settle": (R, [(ELSE, ELSE.replace("RULE_SETTLE=60", "RULE_SETTLE=${SIZE_RULE_SETTLE:-60}"))]),
    "S08-size-by-stat-env": (R, [('  size=$("$RULE_STAT" -L -c %s "$1" 2>/dev/null) || return 0', '  size=$("${STAT:-stat}" -L -c %s "$1" 2>/dev/null) || return 0')]),
    "S09-mount-kind-env": (R, [('  kind=$("$RULE_STAT" -f -c %T "$1"', '  kind=$("${STAT:-stat}" -f -c %T "$1"')]),
    "S10-getfattr-bytes-env": (R, [('  "$RULE_GETFATTR" --only-values -n "$1" "$2" 2>/dev/null | od', '  "${GETFATTR:-getfattr}" --only-values -n "$1" "$2" 2>/dev/null | od')]),
    "S11-df-env": (R, [('  avail=$("$RULE_DF" -B1', '  avail=$("${DF:-df}" -B1')]),
    "B01-off-reads-sizer": (B, [(SBATCH_ELSE, SBATCH_ELSE.replace('SIZER="$ACQ_ENV', 'SIZER="${SIZER:-$ACQ_ENV').replace('fetch_size.py"', 'fetch_size.py}"'))]),
    "B02-off-reads-curl": (B, [(SBATCH_ELSE, SBATCH_ELSE.replace("CURL=curl", "CURL=${CURL:-curl}"))]),
    "B03-off-reads-python": (B, [(SBATCH_ELSE, SBATCH_ELSE.replace("XATTR_PYTHON=$ACQ_ENV/bin/python", "XATTR_PYTHON=${XATTR_PYTHON:-$ACQ_ENV/bin/python}"))]),
    "B04-curl-env-at-download": (B, [('      "$CURL" -sS -K "$cfg"; rc=$?', '      "${CURL:-curl}" -sS -K "$cfg"; rc=$?')]),
    # whole readings
    "W01-use-by-digits": (R, [('  used=$(xattr_whole ceph.dir.rbytes "$1")\n  rc=$?', '  used=$(xattr_digits ceph.dir.rbytes "$1")\n  rc=$?')]),
    "W02-landing-by-digits": (R, [('  xattr_whole ceph.dir.rbytes "$DATA/$1"\n}', '  xattr_digits ceph.dir.rbytes "$DATA/$1"\n}')]),
    "W03-quota-by-digits": (R, [('  quota=$(xattr_whole ceph.quota.max_bytes "$volume") || return 1', '  quota=$(xattr_digits ceph.quota.max_bytes "$volume") || return 1')]),
    "W04-readout-quota-by-digits": (R, [('  quota=$(xattr_whole ceph.quota.max_bytes "$volume")\n  read -r used', '  quota=$(xattr_digits ceph.quota.max_bytes "$volume")\n  read -r used')]),
    "W05-stat-before-by-digits": (R, [('  before=$(xattr_whole ceph.dir.rbytes "$DATA")', '  before=$(xattr_digits ceph.dir.rbytes "$DATA")')]),
    "W06-stat-after-by-digits": (R, [('  after=$(xattr_whole ceph.dir.rbytes "$DATA")', '  after=$(xattr_digits ceph.dir.rbytes "$DATA")')]),
    "W07-whole-no-exit-2": (R, [("tr -c '0-9' 'x'; exit \"${PIPESTATUS[0]}\") || return 2", "tr -c '0-9' 'x')")]),
    "W08-gate-by-digits": (G, [('  xattr_whole ceph.dir.rbytes "$1"\n}', '  xattr_digits ceph.dir.rbytes "$1"\n}')]),
    "W09-words-no-case-2": (R, [('''    2) echo "ceph.dir.rbytes reads $value, and the data root's inside it was not read, so nothing shows it is a reading of the volume"
       return 4 ;;
''', '')]),
    "W10-whole-words-3-as-value": (R, [('''    3) value=$(xattr_bytes "$1" "$2" | LC_ALL=C tr -c '0-9' 'x')
       others=${value//[0-9]/}
       echo "$1 reads as no count: ${#value} bytes, ${#others} of them no digit, where a count is at most 18 digits and nothing else" ;;
''', '')]),
    "W11-stat-words-by-digits": (R, [('       data_bytes=$(xattr_whole ceph.dir.rbytes "$DATA")', '       data_bytes=$(xattr_digits ceph.dir.rbytes "$DATA")')]),
    # owed before the room
    "O01-job-room-first": (R, [(OWED_FIRST + '  # VOLUME is the caller\'s, as DATA is.\n  # shellcheck disable=SC2153\n' + ROOM,
                               '  # VOLUME is the caller\'s, as DATA is.\n  # shellcheck disable=SC2153\n' + ROOM + OWED_FIRST)]),
    "O02-chain-room-first": (X, [(CHAIN_OWED + CHAIN_ROOM, CHAIN_ROOM + CHAIN_OWED)]),
    "O03-platform-room-first": (P, [(PLATFORM_OWED + PLATFORM_ROOM, PLATFORM_ROOM + PLATFORM_OWED)]),
    "O04-readout-use-first": (R, [(README_OWED + '  quota=$(xattr_whole ceph.quota.max_bytes "$volume")\n' + README_USED,
                                   '  quota=$(xattr_whole ceph.quota.max_bytes "$volume")\n' + README_USED + README_OWED)]),
    # the room read twice
    "R01-job-once": (R, [('  read -r room from <<< "$(settled_room "$VOLUME")"', '  read -r room from <<< "$(volume_free_bytes "$VOLUME")"')]),
    "R02-keeps-larger": (R, [('  [ "$second" -ge "$first" ] || first=$second', '  [ "$second" -le "$first" ] || first=$second')]),
    "R03-no-same-source": (R, [('  [ -n "$first" ] && [ -n "$second" ] && [ "$second_from" = "$first_from" ] || return 1', '  [ -n "$first" ] && [ -n "$second" ] || return 1')]),
    "R04-failed-second-ok": (R, [('  [ -n "$first" ] && [ -n "$second" ] && [ "$second_from" = "$first_from" ] || return 1\n  [ "$second" -ge "$first" ] || first=$second\n',
                                  '  [ -n "$first" ] || return 1\n  if [ -n "$second" ]; then\n    [ "$second_from" = "$first_from" ] || return 1\n    [ "$second" -ge "$first" ] || first=$second\n  fi\n')]),
    "R05-no-sleep": (R, [('    sleep "$RULE_SETTLE"\n', '')]),
    "R06-chain-once": (X, [('read -r free_bytes free_from <<< "$(settled_room "$VOLUME")"', 'read -r free_bytes free_from <<< "$(volume_free_bytes "$VOLUME")"')]),
    "R07-second-is-first": (R, [('    read -r second second_from <<< "$(volume_free_bytes "$1")"', '    second=$first second_from=$first_from')]),
    "R08-first-failure-ok": (R, [('  [ -n "$first" ] && [ -n "$second" ] && [', '  [ -n "$second" ] && [')]),
    # the census carried from the first reading to the second
    "C01-no-larger": (R, [('    if [ -n "$bytes" ] && [ -n "$before" ] && [ "$before" -gt "$bytes" ]; then bytes=$before; fi\n', '')]),
    "C02-no-gone": (R, [('    [ -z "${listed["$key"]:-}" ] || continue\n', '    continue\n')]),
    "C03-load-no-count-skipped": (R, [('        if ! is_count "$bytes"; then\n          unread=$(( unread + 1 ))\n          continue\n        fi\n', '        is_count "$bytes" || continue\n')]),
    "C04-cut-short-ok": (R, [('      [ -z "$name" ] || unread=$(( unread + 1 ))\n', '')]),
    "C05-unreadable-ok": (R, [("    else\n      unread=$(( unread + 1 ))\n    fi\n  fi\n  while IFS= read -r -d '' entry; do", "    fi\n  fi\n  while IFS= read -r -d '' entry; do")]),
    "C06-write-failure-ok": (R, [("printf '%s\\0%s\\0' \"$name\" \"$bytes\" >> \"$RULE_CENSUS_OUT\" || bytes=\"\"", "printf '%s\\0%s\\0' \"$name\" \"$bytes\" >> \"$RULE_CENSUS_OUT\"")]),
    "C07-census-from-env": (R, [("# (entries_census): its own, never the environment's.\nRULE_CENSUS_IN=\"\" RULE_CENSUS_OUT=\"\"\n", "# (entries_census): its own, never the environment's.\n")]),
    "C08-second-without-first": (R, [('    RULE_CENSUS_IN=$census\n', '')]),
    "C09-not-local": (R, [('  local first first_from second="" second_from="" census RULE_CENSUS_IN="" RULE_CENSUS_OUT=""', '  local first first_from second="" second_from="" census')]),
    "C10-census-left": (R, [('  rm -f -- "$census"\n', '')]),
    "C11-no-mktemp-check": (R, [('census=$(mktemp "${TMPDIR:-/tmp}/size-rule-census.XXXXXX" 2>/dev/null) || return 1', 'census=$(mktemp "${TMPDIR:-/tmp}/size-rule-census.XXXXXX" 2>/dev/null)')]),
    "C12-first-not-kept": (R, [('  RULE_CENSUS_OUT=$census\n', '')]),
    "C13-load-keeps-last": (R, [('        [ -n "$before" ] && [ "$before" -ge "$bytes" ] || earlier["$name"]=$bytes', '        earlier["$name"]=$bytes')]),
    "C14-held-from-raw": (R, [('    before=${earlier["$name"]:-}\n    if [ -n "$bytes" ]', '    before=${earlier["$name"]:-}\n    raw=$bytes\n    if [ -n "$bytes" ]'),
                              ('    [ "$name" != "$holding" ] || held=$bytes\n    else', '    [ "$name" != "$holding" ] || held=$raw\n    else')]),
    "C15-gone-counts-listing": (R, [('    [ -z "${listed["$key"]:-}" ] || continue\n', '    [ -z "${listed["$key"]:-}" ] || continue\n    entries=$(( entries + 1 ))\n')]),
    # quota below the volume's
    "Q01-free-ignores-below": (R, [('  quota_below "$volume"\n  [ "$?" = 1 ] || return 1\n', '')]),
    "Q02-zero-is-a-quota": (R, [('    [ -z "$value" ] || [ "$value" = 0 ] || return 0\n', '    [ -z "$value" ] || return 0\n')]),
    "Q03-skips-data-root": (R, [(LOOP, LOOP.replace('  while [', '  folder=${folder%/*}\n  while ['))]),
    "Q04-data-root-only": (R, [(LOOP, '  value=$(xattr_whole ceph.quota.max_bytes "$folder") || return 2\n  [ -z "$value" ] || [ "$value" = 0 ] || return 0\n')]),
    "Q05-counts-the-volume": (R, [(LOOP, LOOP.replace('  while [ "$folder" != "$volume" ] && [ "${#folder}" -gt "${#volume}" ]; do', '  while [ "${#folder}" -ge "${#volume}" ]; do'))]),
    "Q06-unread-is-none": (R, [('    value=$(xattr_whole ceph.quota.max_bytes "$folder") || return 2\n', '    value=$(xattr_whole ceph.quota.max_bytes "$folder") || return 1\n')]),
    "Q07-unresolved": (R, [('  volume=$(readlink -f -- "$1" 2>/dev/null) && folder=$(readlink -f -- "$DATA" 2>/dev/null) || return 2\n', '  volume=$1 folder=$DATA\n')]),
    "Q08-by-digits": (R, [('    value=$(xattr_whole ceph.quota.max_bytes "$folder") || return 2\n', '    value=$(xattr_digits ceph.quota.max_bytes "$folder") || return 2\n')]),
    "Q09-readout-room-anyway": (R, [('    if (why != "") printf "Room  =         none for a new fetch, since %s\\n", why\n    else printf', '    printf')]),
    "Q10-readout-failure-no-below": (R, [('    [ -z "$below" ] || echo "  and $below"\n', '')]),
    "Q11-chain-no-words": (X, [('  why=$(quota_below_words "$VOLUME")\n  echo "cannot read the free space of $VOLUME: ${why:-neither', '  why=""\n  echo "cannot read the free space of $VOLUME: ${why:-neither')]),
    "Q12-platform-no-words": (P, [('  why=$(quota_below_words "$VOLUME")\n  echo "cannot read the free space of $VOLUME: ${why:-neither', '  why=""\n  echo "cannot read the free space of $VOLUME: ${why:-neither')]),
    "Q13-job-no-words": (R, [('    size_refused "$id" "$(room_unread_words "$VOLUME")"', '    size_refused "$id" "the room under the quota could not be read"')]),
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
