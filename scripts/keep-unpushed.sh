#!/usr/bin/env bash
# Run by .github/workflows/workers.yml after a worker's Claude step that did not end well: the job's
# 90 minute limit, a cancel or a failure cut it off, and what it had not pushed would go with the
# runner. It commits what the worker left in its own claim branch and pushes that branch as it is,
# never forced, so the next run of the worker carries the work on (docs/agents/routines/worker.md,
# step 1) and the push keeps the claim alive. It does nothing on any branch but claude/<issue>, on a
# claim whose file on origin names another worker or none, or when a changed file looks like a secret
# (tools/check_docs.py's shapes). docs/research/grid-and-cloud-workers-review.md, rank 10.
# Reads WORKER from the environment; KEEP_TOOLS names the copy of tools/ to take the secret shapes
# from, since the run may have checked out a branch whose tools differ.
set -uo pipefail
say() { echo "keep-unpushed: $*"; }

branch=$(git symbolic-ref --quiet --short HEAD) || { say "not on a branch; nothing kept"; exit 0; }
[[ "$branch" =~ ^claude/([1-9][0-9]{0,8})$ ]] || { say "on $branch, which is no claim; nothing kept"; exit 0; }
issue=${BASH_REMATCH[1]}
[[ "${WORKER:-}" =~ ^[A-Za-z0-9._-]{1,64}$ ]] || { say "no worker name; nothing kept"; exit 0; }

git fetch -q origin "+refs/heads/$branch:refs/remotes/origin/$branch" 2>/dev/null || { say "origin has no $branch; nothing kept"; exit 0; }
holder=$(git show "origin/$branch:docs/agents/claims/$issue.md" 2>/dev/null | sed -n 's/^- Worker:[[:space:]]*\([A-Za-z0-9._-]*\).*/\1/p' | head -1)
[ "$holder" = "$WORKER" ] || { say "the claim on origin names ${holder:-nobody}, not $WORKER; nothing kept"; exit 0; }

git add -A
if ! git diff --cached --quiet; then
  if ! python3 - "${KEEP_TOOLS:-tools}" <<'PY'
import subprocess, sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
import check_docs
files = [Path(p) for p in subprocess.run(["git", "diff", "--cached", "--name-only", "--diff-filter=AM", "-z"],
                                         capture_output=True, text=True, check=True).stdout.split("\0") if p]
problems = check_docs.check_secrets(Path("."), files)
for line in problems:
    print("keep-unpushed: " + line)
sys.exit(1 if problems else 0)
PY
  then
    git reset -q
    say "a changed file looks like a secret; nothing kept"
    exit 0
  fi
  git -c user.name="github-actions[bot]" -c user.email="41898282+github-actions[bot]@users.noreply.github.com" \
    commit -q -m "Work in progress kept when the run ended before pushing it

The worker's run was cut off by its time limit, a cancel or a failure
with this work not yet pushed; the next run carries it on." || { say "could not commit; nothing kept"; exit 0; }
fi

ahead=$(git rev-list --count "origin/$branch..HEAD")
if [ "$ahead" = 0 ]; then say "nothing unpushed on $branch"; exit 0; fi
if git push -q origin "HEAD:refs/heads/$branch"; then
  say "kept $ahead commit(s) on $branch"
else
  say "origin's $branch moved on; nothing forced, nothing kept"
fi
exit 0
