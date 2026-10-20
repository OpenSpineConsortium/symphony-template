#!/usr/bin/env bash
# One export's publishing, for .github/workflows/export.yml: clone the
# target with the App's token (sent as a header, never written into the
# clone's config), rebuild symphony/export/$NAME from its default branch,
# apply the stage tools/public_export.py wrote, and when anything changed
# push the branch and open or update its pull request, which the target's
# own checks and its own merge rules then decide. Reads GH_TOKEN, APP_SLUG,
# NAME, TARGET and RUNNER_TEMP.
set -euo pipefail

branch="symphony/export/$NAME"
clone="$RUNNER_TEMP/target"
auth="AUTHORIZATION: basic $(printf 'x-access-token:%s' "$GH_TOKEN" | base64 -w0)"
echo "::add-mask::$auth"

git -c "http.https://github.com/.extraheader=$auth" clone --quiet --depth 1 "https://github.com/$TARGET" "$clone"
base=$(git -C "$clone" rev-parse --abbrev-ref HEAD)
git -C "$clone" switch --quiet -c "$branch"
python3 tools/public_export.py apply "$NAME" "$RUNNER_TEMP/stage" "$clone"
git -C "$clone" add -A
if git -C "$clone" diff --cached --quiet; then
  echo "export $NAME: $TARGET already holds it"
  # an export pull request still open would now carry stale files
  stale=$(gh pr list --repo "$TARGET" --head "$branch" --state open --json number --jq '.[0].number // empty')
  if [ -n "$stale" ]; then
    gh pr close "$stale" --repo "$TARGET" --comment "Closed by $GITHUB_REPOSITORY's export: $TARGET already holds what it publishes as of $GITHUB_SHA."
  fi
  exit 0
fi
git -C "$clone" -c user.name="$APP_SLUG[bot]" -c user.email="$APP_SLUG[bot]@users.noreply.github.com" \
  commit --quiet -m "Publish $NAME from $GITHUB_REPOSITORY at ${GITHUB_SHA:0:7}"
# The branch belongs to the export alone and is rebuilt from the target's
# default branch on every run, so replacing it loses nothing.
git -C "$clone" -c "http.https://github.com/.extraheader=$auth" push --quiet --force origin "HEAD:refs/heads/$branch"
pr=$(gh pr list --repo "$TARGET" --head "$branch" --state open --json number --jq '.[0].number // empty')
if [ -z "$pr" ]; then
  gh pr create --repo "$TARGET" --base "$base" --head "$branch" \
    --title "Publish $NAME from $GITHUB_REPOSITORY" \
    --body "Published by $GITHUB_REPOSITORY's export workflow from commit $GITHUB_SHA, as its .github/symphony/public.json lists. Change the source there, not these files here; the next export replaces them."
  pr=$(gh pr list --repo "$TARGET" --head "$branch" --state open --json number --jq '.[0].number')
fi
echo "export $NAME: pull request #$pr in $TARGET"
