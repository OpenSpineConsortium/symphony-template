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

ask_yes() {
  local answer
  read -r -p "$1 [Y/n] " answer
  [[ -z "$answer" || "$answer" =~ ^[Yy] ]]
}

setup() {
  cd "$ROOT"
  echo "Symphony setup in this Codespace: GitHub's settings for the repository, then its Claude tokens."
  github_sign_in
  if ask_yes "Apply the repository's settings now (scripts/setup-repo.sh: the ruleset, auto-merge, the labels, scanning)?"; then
    env -u GITHUB_TOKEN -u GH_TOKEN bash scripts/setup-repo.sh || echo "setup-repo.sh stopped; its last line says why. The tokens come next."
  fi
  if ask_yes "Store your Claude accounts' tokens now (scripts/tokens.py: claude setup-token, one account at a time)?"; then
    env -u GITHUB_TOKEN -u GH_TOKEN python3 scripts/tokens.py
  fi
  echo "Done. Run 'bash scripts/codespace.sh' to do it again, and delete this Codespace when you have finished:"
  echo "https://github.com/codespaces"
}

case "${1:-}" in
  install) install ;;
  "") setup ;;
  -h|--help) sed -n '2,22p' "${BASH_SOURCE[0]}" ;;
  *) echo "usage: bash scripts/codespace.sh [install]" >&2; exit 2 ;;
esac
