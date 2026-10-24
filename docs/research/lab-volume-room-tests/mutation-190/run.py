"""Each mutation of grid/size-rule.sh in turn, in place, with the D2 tests run against it; the file
is restored after each, and at the end. A mutation the tests do not catch prints SURVIVED."""
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path("/home/claude/schwingnet")
RULE = ROOT / "grid" / "size-rule.sh"
OUT = Path(sys.argv[1])
TESTS = [
    "tests.test_xray_chain.SizeRuleTest.test_a_quota_above_the_volume_on_its_mount_binds_where_it_leaves_the_least",
    "tests.test_xray_chain.SizeRuleTest.test_a_folder_above_the_volume_holds_the_larger_of_its_figure_and_the_sum_of_its_entries",
    "tests.test_xray_chain.SizeRuleTest.test_every_quota_up_to_the_root_of_the_mount_is_counted_the_least_room_binding",
    "tests.test_xray_chain.SizeRuleTest.test_the_room_is_the_smaller_of_two_readings_a_settle_apart_from_one_figure",
    "tests.test_xray_chain.SizeRuleTest.test_the_grids_layout_reads_each_folder_by_the_sum_where_its_figure_is_no_count",
    "tests.test_xray_chain.QuotaReadoutTest.test_each_folder_above_the_volume_is_shown_where_a_quota_there_stands_or_is_not_read",
    "tests.test_xray_chain.QuotaReadoutTest.test_a_quota_below_the_volumes_leaves_no_room_for_a_new_fetch",
    "tests.test_xray_chain.SlurmScriptsTest.test_both_scripts_refuse_beside_a_quota_below_the_volumes",
]
MUTATIONS = [
    ("larger-not-taken",
     'if [ -n "$held" ] && [ "$held" -gt "$sum" ]; then echo "$held attribute"; else echo "$sum entries"; fi',
     'echo "$sum entries"'),
    ("attribute-floor-dropped", '[ -n "$held" ] && [ "$held" -ge "$3" ] || return 1', '[ -n "$held" ] || return 1'),
    ("stat-count-dropped", '[ -n "$seen" ] && [ "$(size_by_stat "$1")" = "$entries" ] || return 1',
     '[ -n "$seen" ] || return 1'),
    ("seen-dropped", '[ -n "$seen" ] && [ "$(size_by_stat "$1")" = "$entries" ] || return 1',
     '[ "$(size_by_stat "$1")" = "$entries" ] || return 1'),
    ("mount-check-dropped", '    ! is_mount_point "$points" "$entry" || return 1\n', ''),
    ("overflow-check-dropped",
     'bytes=$(entry_bytes "$entry" "$device") && [ -n "$bytes" ] && fits_in_count "$sum" "$bytes" || return 1',
     'bytes=$(entry_bytes "$entry" "$device") && [ -n "$bytes" ] || return 1'),
    ("device-check-dropped", 'bytes=$(entry_bytes "$entry" "$device") && [ -n "$bytes" ]',
     'bytes=$(entry_bytes "$entry" "$("$RULE_STAT" -c %d "$entry")") && [ -n "$bytes" ]'),
    ("least-is-most", 'if [ -z "$least" ] || [ "$room" -lt "$least" ]; then least=$room at=$height; fi',
     'if [ -z "$least" ] || [ "$room" -gt "$least" ]; then least=$room at=$height; fi'),
    ("above-never-binds", 'if [ -n "$above" ] && [ "$above" -lt "$free" ]; then',
     'if [ -n "$above" ] && [ "$above" -gt "$free" ]; then'),
    ("intermediate-skipped", 'for (( height = 1; height <= top; height++ )); do',
     'for (( height = top; height <= top; height++ )); do'),
    ("child-not-carried", '    child=$folder\n  done\n  printf', '  done\n  printf'),
    ("settle-kind-whole", '[ "${second_from%%-*}" = "${first_from%%-*}" ]', '[ "$second_from" = "$first_from" ]'),
    ("settle-kind-ignored", '[ "${second_from%%-*}" = "${first_from%%-*}" ]', 'true'),
    ("zero-quota-counted", '    [ -z "$quota" ] || [ "$quota" = 0 ] || echo "$height $quota"',
     '    [ -z "$quota" ] || echo "$height $quota"'),
    ("df-beside-above", '  [ -z "$used" ] && [ "$below" = 1 ] || return 1', '  [ -z "$used" ] || return 1'),
    ("above-unread-ignored", '      above=$(room_above "$volume" "$used") || return 1',
     '      above=$(room_above "$volume" "$used")'),
    ("readout-tie-to-above", '    if [ "$left" -lt "$least" ]; then', '    if [ "$left" -le "$least" ]; then'),
    ("readout-unread-ignored", '    [ -z "$ABOVE_UNREAD" ] || below=$ABOVE_UNREAD', '    :'),
    ("mount-root-not-read",
     '    quota=$(xattr_whole ceph.quota.max_bytes "${folder:-/}") || return 1',
     '    ! is_mount_point "$points" "${folder:-/}" || break\n    quota=$(xattr_whole ceph.quota.max_bytes "${folder:-/}") || return 1'),
    ("quota-unread-as-none", '    quota=$(xattr_whole ceph.quota.max_bytes "${folder:-/}") || return 1',
     '    quota=$(xattr_whole ceph.quota.max_bytes "${folder:-/}")'),
    ("use-unread-as-zero", '    if ! said=$(use_above "$folder" "$child" "$use"); then',
     '    if ! said=$(use_above "$folder" "$child" "$use") && false; then'),
    ("room-words-volume", '    quota-*) echo "under a quota above the volume" ;;', '    quota-*) echo "under the quota" ;;'),
]


def main():
    original = RULE.read_text(encoding="utf-8")
    try:
        only = {int(n) for n in os.environ.get("ONLY", "").split()}
        for number, (name, old, new) in enumerate(MUTATIONS, 1):
            if only and number not in only:
                continue
            if original.count(old) != 1:
                print(f"{number} {name}: not applied ({original.count(old)} matches)", flush=True)
                continue
            RULE.write_text(original.replace(old, new), encoding="utf-8")
            done = subprocess.run([sys.executable, "-m", "unittest", *TESTS], cwd=ROOT, capture_output=True,
                                  text=True, timeout=900)
            (OUT / f"out-{number}.txt").write_text(done.stdout + done.stderr, encoding="utf-8")
            if done.returncode == 0:
                print(f"{number} {name}: SURVIVED", flush=True)
            else:
                failing = sum(line.startswith(("FAIL:", "ERROR:")) for line in done.stderr.splitlines())
                print(f"{number} {name}: killed ({failing} failing)", flush=True)
    finally:
        RULE.write_text(original, encoding="utf-8")
    print("done", flush=True)


main()
