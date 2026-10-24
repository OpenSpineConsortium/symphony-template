#!/bin/bash
# Each mutation of grid/size-rule.sh in turn, in place, with the D2 tests run against it; the file is
# restored after each. A mutation the tests do not catch is printed as SURVIVED.
cd /home/claude/schwingnet || exit 1
S=/tmp/claude-0/-home-claude/ecdd0a20-c17e-5671-b6da-4109dc513c50/scratchpad/mut
cp grid/size-rule.sh "$S/size-rule.sh.orig"
tests="tests.test_xray_chain.SizeRuleTest.test_a_quota_above_the_volume_on_its_mount_binds_where_it_leaves_the_least
tests.test_xray_chain.SizeRuleTest.test_a_folder_above_the_volume_holds_the_larger_of_its_figure_and_the_sum_of_its_entries
tests.test_xray_chain.SizeRuleTest.test_every_quota_up_to_the_root_of_the_mount_is_counted_the_least_room_binding
tests.test_xray_chain.SizeRuleTest.test_the_room_is_the_smaller_of_two_readings_a_settle_apart_from_one_figure
tests.test_xray_chain.QuotaReadoutTest.test_each_folder_above_the_volume_is_shown_where_a_quota_there_stands_or_is_not_read
tests.test_xray_chain.QuotaReadoutTest.test_a_quota_below_the_volumes_leaves_no_room_for_a_new_fetch
tests.test_xray_chain.SlurmScriptsTest.test_both_scripts_refuse_beside_a_quota_below_the_volumes"
n=0
while IFS='|' read -r name from to; do
  [ -n "$name" ] || continue
  n=$((n + 1))
  cp "$S/size-rule.sh.orig" grid/size-rule.sh
  python3 - "$from" "$to" <<'PY'
import sys
from pathlib import Path
p = Path("grid/size-rule.sh")
text = p.read_text(encoding="utf-8")
old, new = sys.argv[1], sys.argv[2]
if text.count(old) != 1:
    print(f"NOT APPLIED ({text.count(old)} matches): {old}")
    sys.exit(3)
p.write_text(text.replace(old, new), encoding="utf-8")
PY
  if [ $? != 0 ]; then echo "$n $name: not applied"; continue; fi
  # shellcheck disable=SC2086
  if timeout 600 python3 -m unittest $tests > "$S/out-$n.txt" 2>&1; then
    echo "$n $name: SURVIVED"
  else
    echo "$n $name: killed ($(grep -c '^FAIL:\|^ERROR:' "$S/out-$n.txt") failing)"
  fi
done < "$S/mutations.txt"
cp "$S/size-rule.sh.orig" grid/size-rule.sh
echo done
