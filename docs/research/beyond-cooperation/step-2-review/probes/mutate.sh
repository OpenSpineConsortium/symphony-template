#!/bin/bash
# Each mutant is one plausible wrong implementation; a mutant that survives
# the changed test modules is behavior no test pins.
set -u
# S holds tree/, an export of the commit under review; it is this folder unless set.
S="${S:-$(cd "$(dirname "$0")" && pwd)}"
run_mutant() {
  local name="$1" file="$2" old="$3" new="$4"
  rm -rf "$S/mutant" && cp -r "$S/tree" "$S/mutant"
  python3 - "$S/mutant/$file" "$old" "$new" <<'EOF'
import sys
path, old, new = sys.argv[1:]
text = open(path).read()
assert text.count(old) == 1, (path, old, text.count(old))
open(path, "w").write(text.replace(old, new))
EOF
  if (cd "$S/mutant" && timeout 900 python3 -m unittest tests.test_metrics tests.test_profile tests.test_economics tests.test_usage >/dev/null 2>&1); then
    echo "SURVIVED: $name"
  else
    echo "killed:   $name"
  fi
}
run_mutant "runs naming a pull request read from the window alone" tools/metrics.py \
  "profiles = {work.number: profile.pull_profile(work, records.all) for work in works}" \
  "profiles = {work.number: profile.pull_profile(work, records.in_window) for work in works}"
run_mutant "actions_runs counts every record with a profile" tools/metrics.py \
  '"actions_runs": len(summed)' \
  '"actions_runs": len([r for r in records.all if r["profile"]])'
run_mutant "actions_runs leaves the overhead out" tools/metrics.py \
  "any(record is run for run in overhead) or any(economics.names(record, w) for w in works))]" \
  "any(economics.names(record, w) for w in works))]"
run_mutant "the overhead taken from every record, the look-back's too" tools/metrics.py \
  '"coordination": profile.coordination(working, profiles, window.end, others, records.in_window)}' \
  '"coordination": profile.coordination(working, profiles, window.end, others, records.all)}'
run_mutant "the sides take no others (work open or ended before the window)" tools/metrics.py \
  '"coordination": profile.coordination(working, profiles, window.end, others, records.in_window)}' \
  '"coordination": profile.coordination(working, profiles, window.end, (), records.in_window)}'
run_mutant "sessions counted from lines with no count too" tools/profile.py \
  'return [(session, counts) for session, counts in parse_trailer(message) if counts]' \
  'return [(session, counts) for session, counts in parse_trailer(message)]'
run_mutant "sessions over the commits made in the window alone" tools/metrics.py \
  'sessions = {session for work in works for commit in work.commits for session, _ in profile.commit_lines(commit)}' \
  'sessions = {session for work in works for commit in work.commits if window.holds(commit_time(commit, "committer")) for session, _ in profile.commit_lines(commit)}'
run_mutant "peak_median the median of all pull requests, unprofiled as 0" tools/profile.py \
  'row["peak_median"] = economics.median_seconds([profiles[w.number]["peak"] for w in profiled])' \
  'row["peak_median"] = economics.median_seconds([(profiles.get(w.number) or {}).get("peak", 0) for w in works])'
run_mutant "write step: no PROFILE.json from the run drops the branch's" .github/workflows/metrics.yml \
  'elif [ -n "$previous" ] && sums="$(git rev-parse --verify --quiet "$previous:PROFILE.json")"; then' \
  'elif false; then'
run_mutant "write step: the unchanged test ignores PROFILE.json" .github/workflows/metrics.yml \
  '&& { [ ! -e "$profile" ] || same_as_branch PROFILE.json "$profile"; }; then' \
  '; then'
run_mutant "cache: a v1 cache still read" tools/metrics.py \
  'data.get("v") == USAGE_CACHE_VERSION else None' \
  'data.get("v") in (1, USAGE_CACHE_VERSION) else None'
run_mutant "the fold keeps an MCP server's name" tools/profile.py \
  'return MCP_TOOLS if name.startswith("mcp__") else OTHER_TOOLS' \
  'return name.split("__")[1] if name.startswith("mcp__") else OTHER_TOOLS'
