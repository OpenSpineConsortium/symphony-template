"""Each mutant of the review's fixes for #181, in a scratch copy, must fail a test; prints SURVIVED
otherwise. A mutant is (file, [(old, new), ...]) with each old found exactly once in that file."""
import concurrent.futures
import shutil
import subprocess
import sys
from pathlib import Path

SRC = Path("/tmp/claude-0/-home-claude/ecdd0a20-c17e-5671-b6da-4109dc513c50/scratchpad/snap181b")
WORK = Path(sys.argv[1])
RULE_TESTS = ["tests.test_xray_chain.QuotaReadoutTest", "tests.test_xray_chain.SizeRuleTest",
              "tests.test_xray_chain.SlurmScriptsTest"]
R = "grid/size-rule.sh"
WALK_UP = ('''  points=$(mount_points) || return 4
  folder=$volume
  until is_mount_point "$points" "${folder:-/}"; do
    [ -n "$folder" ] || return 4
    folder=${folder%/*}
    value=$(xattr_whole ceph.quota.max_bytes "${folder:-/}") || return 4
    [ -z "$value" ] || [ "$value" = 0 ] || return 3
  done
''')
UNSET = "  unset -f getfattr stat squeue df python3 sleep id awk tr readlink mktemp sed sort rm tail date mkdir cut od\n"
PY_EXIT = "    sys.exit(0 if error.errno in (errno.ENODATA, errno.EOPNOTSUPP) else 3)"
NOT_THERE = '''    case $said in *": $1: No such attribute" | *": $1: Operation not supported") return 0 ;; esac
    return 2
'''

MUTANTS = {
    "baseline": (R, []),
    "N01-outside-data-root-is-none": (R, [('  data_root_on "$1" || return 5\n', '  data_root_on "$1" || return 1\n')]),
    "N02-no-walk-above": (R, [(WALK_UP, "")]),
    "N03-above-quota-is-none": (R, [("    [ -z \"$value\" ] || [ \"$value\" = 0 ] || return 3\n", "    [ -z \"$value\" ] || [ \"$value\" = 0 ] || return 1\n")]),
    "N04-above-unread-ignored": (R, [('    value=$(xattr_whole ceph.quota.max_bytes "${folder:-/}") || return 4\n', '    value=$(xattr_whole ceph.quota.max_bytes "${folder:-/}")\n')]),
    "N05-table-unread-ignored": (R, [("  points=$(mount_points) || return 4\n", "  points=$(mount_points)\n")]),
    "N06-walk-skips-volume-mount-check": (R, [("  folder=$volume\n  until", "  folder=${volume%/*}\n  until")]),
    "N07-mount-root-not-read": (R, [('    folder=${folder%/*}\n    value=$(xattr_whole ceph.quota.max_bytes "${folder:-/}") || return 4\n',
                                      '    folder=${folder%/*}\n    ! is_mount_point "$points" "${folder:-/}" || break\n    value=$(xattr_whole ceph.quota.max_bytes "${folder:-/}") || return 4\n')]),
    "N08-no-mount-on-path-is-none": (R, [('    [ -n "$folder" ] || return 4\n', '    [ -n "$folder" ] || return 1\n')]),
    "N09-getfattr-error-is-none": (R, [(NOT_THERE, '    return 0\n')]),
    "N10-getfattr-no-c-locale": (R, [('{ said=$(LC_ALL=C "$RULE_GETFATTR"', '{ said=$("$RULE_GETFATTR"')]),
    "N11-getfattr-unsupported-is-error": (R, [(' | *": $1: Operation not supported") return 0', ') return 0')]),
    "N12-python-error-is-none": (R, [(PY_EXIT, "    sys.exit(0)")]),
    "N13-python-unsupported-is-error": (R, [(PY_EXIT, "    sys.exit(0 if error.errno == errno.ENODATA else 3)")]),
    "N14-python-enodata-is-error": (R, [(PY_EXIT, "    sys.exit(0 if error.errno == errno.EOPNOTSUPP else 3)")]),
    "N15-no-unset": (R, [(UNSET, "")]),
    "N16-unset-misses-awk": (R, [(UNSET, UNSET.replace(" awk", ""))]),
    "N17-squeue-user-from-env": (R, [('"${RULE_USER:-$(id -un)}"', '"${USER:-$(id -un)}"')]),
    "N18-switch-user-ignored": (R, [("RULE_PYTHON=${XATTR_PYTHON:-python3} RULE_USER=${USER:-}", "RULE_PYTHON=${XATTR_PYTHON:-python3} RULE_USER=\"\"")]),
    "N19-off-user-from-env": (R, [('RULE_PYTHON=python3 RULE_USER=""', 'RULE_PYTHON=python3 RULE_USER=${USER:-}')]),
    "N20-words-3-dropped": (R, [('    3) echo "a folder above the volume on its mount carries a quota of its own, which the size rule does not read" ;;\n', '')]),
    "N21-words-4-dropped": (R, [('    4) echo "a quota on a folder above the volume on its mount could not be read" ;;\n', '')]),
    "N22-words-5-dropped": (R, [('    5) echo "the data root is no folder inside the volume on its mount, so the volume\'s quota is not the one a fetch there meets" ;;\n', '')]),
    "N23-redirect-order": (R, [('2>&1 >&3 3>&-)', '>&3 2>&1 3>&-)')]),
    "N24-free-bytes-takes-3-as-none": (R, [('  quota_below "$volume"\n  [ "$?" = 1 ] || return 1\n', '  quota_below "$volume"\n  case $? in 1|3) ;; *) return 1 ;; esac\n')]),
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
    done = subprocess.run([sys.executable, "-m", "unittest", "-f", *RULE_TESTS], cwd=copy, capture_output=True, text=True,
                          timeout=1800)
    (WORK / f"{name}.log").write_text(done.stdout + done.stderr)
    failed = [line for line in done.stderr.splitlines() if line.startswith(("FAIL:", "ERROR:"))]
    return ("SURVIVED: " if done.returncode == 0 else f"killed ({len(failed)}): ") + name


names = sys.argv[2:] or list(MUTANTS)
with concurrent.futures.ThreadPoolExecutor(4) as pool:
    for line in pool.map(run, names):
        print(line, flush=True)
