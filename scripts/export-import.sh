#!/usr/bin/env bash
# One export's way back, for .github/workflows/import.yml: clone the public
# target with READ_TOKEN, let tools/public_export.py copy its versions of
# the export's listed files over this checkout, and when any differ commit
# them on symphony/import/$NAME and open or update that pull request here
# with GH_TOKEN. Each token goes as a header, never into a clone's config.
# Reads READ_TOKEN, GH_TOKEN, APP_SLUG, NAME, TARGET and RUNNER_TEMP.
set -euo pipefail

header() { printf 'AUTHORIZATION: basic %s' "$(printf 'x-access-token:%s' "$1" | base64 -w0)"; }
read_auth=$(header "$READ_TOKEN")
write_auth=$(header "$GH_TOKEN")
echo "::add-mask::$read_auth"
echo "::add-mask::$write_auth"
branch="symphony/import/$NAME"

git -c "http.https://github.com/.extraheader=$read_auth" clone --quiet --depth 1 "https://github.com/$TARGET" "$RUNNER_TEMP/target"
base=$(git rev-parse --abbrev-ref HEAD)
git switch --quiet -c "$branch"
python3 tools/public_export.py import "$NAME" "$RUNNER_TEMP/target"
git add -A
if git diff --cached --quiet; then
  echo "import $NAME: nothing changed in $TARGET"
  exit 0
fi
git -c user.name="$APP_SLUG[bot]" -c user.email="$APP_SLUG[bot]@users.noreply.github.com" \
  commit --quiet -m "Take back $NAME's changes from $TARGET"
# The branch belongs to the import alone and is rebuilt from the default
# branch on every run, so replacing it loses nothing.
git -c "http.https://github.com/.extraheader=$write_auth" push --quiet --force origin "HEAD:refs/heads/$branch"
pr=$(gh pr list --repo "$GITHUB_REPOSITORY" --head "$branch" --state open --json number --jq '.[0].number // empty')
if [ -z "$pr" ]; then
  gh pr create --repo "$GITHUB_REPOSITORY" --base "$base" --head "$branch" \
    --title "Take back $NAME's changes from $TARGET" \
    --body "Contributors changed files that .github/symphony/public.json publishes to $TARGET and marks importable; this brings their versions back. Only those files can appear here."
fi
