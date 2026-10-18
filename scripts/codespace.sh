#!/usr/bin/env bash
# Set up a repository made from this template from a browser tab alone: a
# GitHub Codespace on the repository runs this script, so the steps that
# needed gh and claude on a computer of your own (scripts/setup-repo.sh and
# scripts/tokens.py) run in the Codespace's terminal, and every sign-in they
# ask for opens in a tab of the browser the Codespace runs in.
#
#   bash scripts/codespace.sh install   what .devcontainer/devcontainer.json
#                                       runs once when the Codespace is made:
#                                       Claude Code, and the first terminal
#                                       that opens starts the setup
#   bash scripts/codespace.sh           the setup: a GitHub sign-in of your
#                                       own, the repository's settings, then
#                                       the token wizard, one account at a time
#
# Why a sign-in of your own: the token a Codespace is given (GITHUB_TOKEN)
# reaches only its repository's contents, so it can set no ruleset, no
# repository setting and no organization secret. gh is signed in again, in
# the browser with a one-time code, as you; that sign-in stays in this
# Codespace and goes when you delete it. The Claude token is never on the
# screen or in a file: tokens.py catches what claude setup-token prints and
# hands it to gh, which seals it for GitHub, as on a computer of your own.
set -euo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
DONE_MARK="$HOME/.symphony-setup-started"
SCOPES="repo,workflow,admin:org"

install() {
  # a Codespace's folder may belong to another user than the one its
  # terminals run as, and git then refuses to read it ("dubious ownership"),
  # which hid the repository from gh and the wizard on the owner's first run
  git config --global --add safe.directory "$ROOT"
  if ! command -v claude >/dev/null 2>&1; then
    npm install -g @anthropic-ai/claude-code
  fi
  # the first interactive terminal starts the setup once; later ones are
  # ordinary shells, and the setup is run again by hand
  if ! grep -q "scripts/codespace.sh" "$HOME/.bashrc" 2>/dev/null; then
    cat >>"$HOME/.bashrc" <<HOOK

# Symphony: start the setup in the first terminal of this Codespace
if [ -t 0 ] && [ ! -e "$DONE_MARK" ]; then
  touch "$DONE_MARK"
  bash "$ROOT/scripts/codespace.sh"
fi
HOOK
  fi
}

github_sign_in() {
  # the Codespace's own token would win over a sign-in, so gh is run without it
  if env -u GITHUB_TOKEN -u GH_TOKEN gh auth status >/dev/null 2>&1; then
    echo "gh is signed in as you already."
    return
  fi
  echo "Sign in to GitHub as yourself: gh shows a one-time code and opens github.com/login/device in a tab."
  env -u GITHUB_TOKEN -u GH_TOKEN gh auth login --web --git-protocol https --scopes "$SCOPES"
}

# The repository this Codespace is on: GitHub names it in GITHUB_REPOSITORY,
# so nothing depends on the clone's remote, and the clone's origin otherwise.
repository() {
  if [[ "${GITHUB_REPOSITORY:-}" =~ ^[A-Za-z0-9-]+/[A-Za-z0-9._-]+$ ]]; then
    echo "$GITHUB_REPOSITORY"
    return
  fi
  git -C "$ROOT" remote get-url origin 2>/dev/null | sed -E -n 's#^.*github\.com[:/]([^/]+/[^/]+)/?$#\1#p' | sed 's/\.git$//'
}

# Where the tokens go, as tokens.py takes it: an organization's secrets seen
# by this repository, or a personal account's repository's own.
token_place() {
  local repo=$1 kind
  kind=$(as_you gh api "repos/$repo" --jq .owner.type)
  if [ "$kind" = "Organization" ]; then
    echo "--org ${repo%%/*} --repos ${repo#*/}"
  else
    echo "--repo $repo"
  fi
}

as_you() { env -u GITHUB_TOKEN -u GH_TOKEN "$@"; }

setup() {
  cd "$ROOT"
  git config --global --get-all safe.directory 2>/dev/null | grep -qx "$ROOT" || git config --global --add safe.directory "$ROOT"
  local repo place
  repo=$(repository)
  if [ -z "$repo" ]; then
    echo "This Codespace does not say which repository it is on; run: bash scripts/codespace.sh OWNER/NAME" >&2
    exit 1
  fi
  echo "Symphony setup for $repo: its GitHub settings, then its Claude tokens. Ctrl-C stops it; run 'bash scripts/codespace.sh' to start again."
  github_sign_in
  echo
  echo "== 1 of 2: the repository's settings (the ruleset, auto-merge, the labels, scanning)"
  as_you bash scripts/setup-repo.sh "$repo" || echo "The settings stopped at the line above; the tokens come next."
  echo
  echo "== 2 of 2: Claude tokens, one account at a time"
  # shellcheck disable=SC2046 # the place is two or four words, split on purpose
  as_you python3 scripts/tokens.py $(token_place "$repo")
  echo "Done. Run 'bash scripts/codespace.sh' to do it again, and delete this Codespace when you have finished:"
  echo "https://github.com/codespaces"
}

case "${1:-}" in
  install) install ;;
  "") setup ;;
  */*) GITHUB_REPOSITORY=$1 setup ;;
  -h|--help) sed -n '2,22p' "${BASH_SOURCE[0]}" ;;
  *) echo "usage: bash scripts/codespace.sh [install | OWNER/NAME]" >&2; exit 2 ;;
esac
