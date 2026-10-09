#!/usr/bin/env bash
# Set up the GitHub side of a repository made from this template, in one
# command.
#
# "Use this template" copies files and nothing else: the new repository has
# no branch rules, none of the toggles, no labels, no secret and no
# variable, and GitHub lets only a person with admin rights set them.
# docs/setup/github.md says what each setting is for and
# docs/setup/owner-checklist.md gathers every step; this script does the
# GitHub steps through the GitHub CLI, so they are one run instead of six
# settings pages. Run it once on your own computer, from a clone, with gh
# signed in (gh auth login) as a user with admin rights on the repository.
# A cloud session cannot run it: it has no gh and no admin rights. Running
# it again does nothing twice: a ruleset that exists is skipped, a toggle
# that is on stays on, a label is updated in place.
#
# What it does, in order, one line of output per step:
#   1. finds the repository (the argument, or the clone's remote) and its
#      default branch;
#   2. creates the ruleset docs/setup/ruleset-main.json unless one of that
#      name is already listed for the repository; on GitHub Free a private
#      repository's ruleset is written but not enforced (docs/setup/tiers.md),
#      and the script says so when the repository is private;
#   3. turns on "Automatically delete head branches" and "Allow auto-merge"
#      (auto-merge does nothing until a pull request asks for it, and team
#      mode needs it);
#   4. turns on secret scanning, then push protection, which GitHub accepts
#      only once scanning is on; where the plan or the visibility offers
#      neither (a Free organization's private repository has no Secret
#      Protection) it prints why and carries on;
#   5. creates or updates the labels, read from LABELS in
#      tools/template_init.py, so the list lives in one place;
#   6. sets each repository variable given as --var NAME=VALUE; the ones
#      this repository reads are CLAUDE_WORKER, CLAUDE_TEAM,
#      CLAUDE_MAX_ROUNDS and CLAUDE_ALLOWED_TOOLS (docs/setup/claude-action.md);
#   7. with --token, stores the repository secret CLAUDE_CODE_OAUTH_TOKEN:
#      you run `claude setup-token` in another terminal and paste the token
#      at gh's hidden prompt. The token is never on a command line, never in
#      a file and never in this script's output: gh reads it without echo
#      (or from standard input when no terminal is attached), encrypts it on
#      your machine and sends only the sealed value. Without --token the
#      step prints the alternative, /install-github-app in Claude Code.
#
# Usage: bash scripts/setup-repo.sh [OWNER/NAME] [--var NAME=VALUE]... [--token]
set -euo pipefail
cd "$(dirname "$0")/.."

RULESET=docs/setup/ruleset-main.json
SECRET=CLAUDE_CODE_OAUTH_TOKEN

usage() {
  cat <<'EOF'
Usage: bash scripts/setup-repo.sh [OWNER/NAME] [--var NAME=VALUE]... [--token]

Sets up the GitHub side of a repository made from this template: the
default branch's ruleset, delete-branch-on-merge, auto-merge, secret
scanning with push protection, the labels, the variables asked for and,
with --token, the secret CLAUDE_CODE_OAUTH_TOKEN. Needs the GitHub CLI
signed in (gh auth login) with admin rights on the repository.

  OWNER/NAME        the repository; by default the one this clone's
                    remote points at
  --var NAME=VALUE  set a repository variable; repeatable. The variables
                    this repository reads: CLAUDE_WORKER, CLAUDE_TEAM,
                    CLAUDE_MAX_ROUNDS, CLAUDE_ALLOWED_TOOLS
                    (docs/setup/claude-action.md)
  --token           store the secret CLAUDE_CODE_OAUTH_TOKEN from a hidden
                    prompt: run `claude setup-token` in another terminal
                    first and paste what it prints
  -h, --help        this text
EOF
}

die() {
  printf 'setup-repo: %s\n' "$1" >&2
  exit "${2:-1}"
}

REPO=""
VARIABLES=()
TOKEN=no
while [ $# -gt 0 ]; do
  case "$1" in
    -h|--help) usage; exit 0 ;;
    --var) [ $# -ge 2 ] || die "--var needs NAME=VALUE" 2; VARIABLES+=("$2"); shift 2 ;;
    --var=*) VARIABLES+=("${1#--var=}"); shift ;;
    --token) TOKEN=yes; shift ;;
    -*) usage >&2; die "unknown option $1" 2 ;;
    *) [ -z "$REPO" ] || die "one repository at a time: $REPO and $1" 2; REPO="$1"; shift ;;
  esac
done
for pair in ${VARIABLES[@]+"${VARIABLES[@]}"}; do
  case "$pair" in
    [A-Za-z_]*=*) ;;
    *) die "--var takes NAME=VALUE, not $pair" 2 ;;
  esac
done

# 1. The repository and its default branch, in one call. gh reads the
# clone's remote when no repository is named.
if [ -n "$REPO" ]; then
  view=$(gh repo view "$REPO" --json nameWithOwner,defaultBranchRef,visibility --jq '[.nameWithOwner, .defaultBranchRef.name, .visibility] | @tsv')
else
  view=$(gh repo view --json nameWithOwner,defaultBranchRef,visibility --jq '[.nameWithOwner, .defaultBranchRef.name, .visibility] | @tsv')
fi
IFS=$'\t' read -r REPO DEFAULT_BRANCH VISIBILITY <<<"$view"
VISIBILITY=$(printf '%s' "$VISIBILITY" | tr '[:upper:]' '[:lower:]')
printf 'repository: %s (default branch %s, %s)\n' "$REPO" "$DEFAULT_BRANCH" "$VISIBILITY"

# 2. The ruleset, from the file the docs ship, unless its name is already
# listed. GitHub would make a second ruleset of the same name, so the check
# is this script's job.
name=$(python3 -c 'import json, sys; print(json.load(open(sys.argv[1]))["name"])' "$RULESET")
existing=$(gh api "repos/$REPO/rulesets" --jq '.[].name')
if grep -Fxq -- "$name" <<<"$existing"; then
  printf 'ruleset "%s": exists, skipped\n' "$name"
else
  gh api --method POST "repos/$REPO/rulesets" --input "$RULESET" --silent
  printf 'ruleset "%s": created from %s\n' "$name" "$RULESET"
fi
if [ "$VISIBILITY" = "private" ]; then
  echo "  note: on GitHub Free a private repository's ruleset is written but not enforced (docs/setup/tiers.md)"
fi

# 3. The two toggles under General. Both are idempotent PATCHes.
gh repo edit "$REPO" --delete-branch-on-merge --enable-auto-merge
echo "general: delete head branches on merge, allow auto-merge: on"

# 4. Secret scanning, then push protection. A failure here is the plan or
# the visibility, not the script, so it is reported and the run goes on.
if answer=$(gh repo edit "$REPO" --enable-secret-scanning 2>&1); then
  echo "secret scanning: on"
  if answer=$(gh repo edit "$REPO" --enable-secret-scanning-push-protection 2>&1); then
    echo "push protection: on"
  else
    printf 'push protection: not available here (%s); turn it on by hand if the plan offers it\n' "$(tr '\n' ' ' <<<"$answer")"
  fi
else
  printf 'secret scanning: not available here (%s); a Free organization'"'"'s private repository has no Secret Protection, docs/setup/github.md section 5\n' "$(tr '\n' ' ' <<<"$answer")"
fi

# 5. The labels, from the one list in tools/template_init.py. --force
# updates a label that exists instead of failing on it.
while IFS=$'\t' read -r label color description; do
  gh label create "$label" --repo "$REPO" --color "$color" --description "$description" --force
  printf 'label %s: created or updated\n' "$label"
done < <(python3 -c '
import sys
sys.path.insert(0, "tools")
from template_init import LABELS
for name, color, description in LABELS:
    print(name, color, description, sep="\t")
')

# 6. The variables asked for.
if [ ${#VARIABLES[@]} -eq 0 ]; then
  echo "variables: none asked for (--var NAME=VALUE; docs/setup/claude-action.md names them)"
fi
for pair in ${VARIABLES[@]+"${VARIABLES[@]}"}; do
  gh variable set "${pair%%=*}" --repo "$REPO" --body "${pair#*=}"
  printf 'variable %s: set\n' "${pair%%=*}"
done

# 7. The secret, from gh's own hidden prompt; nothing is echoed or saved.
if [ "$TOKEN" = yes ]; then
  echo "In another terminal, run: claude setup-token"
  echo "Approve it in the browser, copy the token it prints, and paste it at the prompt below."
  echo "Nothing you paste is shown or saved; gh encrypts it on this machine before it is sent."
  gh secret set "$SECRET" --repo "$REPO"
  printf 'secret %s: set\n' "$SECRET"
else
  printf 'secret %s: skipped; run again with --token, or run /install-github-app in Claude Code, which installs the app and stores the secret in one OAuth flow (docs/setup/claude-action.md)\n' "$SECRET"
fi
