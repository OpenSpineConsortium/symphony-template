# Setting up from the browser: a Codespace

The two setup steps that needed a computer of your own, the repository's
GitHub settings (scripts/setup-repo.sh) and the Claude tokens the workflows
run on (scripts/tokens.py), also run in a GitHub Codespace, so that the
whole setup happens in browser tabs: no install, no terminal of your own and
no token copied by hand. .devcontainer/devcontainer.json makes the
Codespace, and scripts/codespace.sh is what runs in it.

## The steps

1. Open https://codespaces.new/OWNER/NAME, with your repository's owner and
   name, and press **Create codespace**. The control panel's Tokens page
   links it for the repository it shows.
2. Wait for the editor to open. The task "Symphony setup"
   (.vscode/tasks.json) starts the setup in a terminal by itself the first
   time; if it does not, type `bash scripts/codespace.sh` in the terminal
   and press Enter.
3. Sign in to GitHub when asked: gh shows a one-time code and opens
   github.com/login/device in a new tab; paste the code there and press
   **Authorize**. The Codespace's own token cannot change settings or
   secrets, so this sign-in is yours, and it stays in this Codespace only.
4. The settings come next by themselves (the ruleset, auto-merge, the
   labels, secret scanning), on the repository the Codespace is on, which
   GitHub names in GITHUB_REPOSITORY.
5. Then the token wizard: it asks for a slot, a label and whether the same
   token is also `main`; then `claude setup-token` opens claude.ai's
   sign-in in a new tab. Sign in as the account the slot is for and press
   **Authorize**; where claude.ai shows a code instead, paste it into the
   terminal. The token goes straight from claude to GitHub, sealed, and is
   never on the screen. A repository of an organization keeps the tokens as
   the organization's secrets, seen by this repository.
6. When you are done, delete the Codespace at https://github.com/codespaces
   (the three dots beside it, then **Delete**), which also drops the GitHub
   sign-in it held.

## One button: the Tokens page

The control panel's Tokens page has "Add with one press", which does the
above for one account and one slot with no terminal to type in:

1. The page saves three of your Codespaces secrets, seen by this repository
   alone: SYMPHONY_GITHUB_TOKEN (the page's own GitHub sign-in, so the
   Codespace needs no GitHub sign-in of its own), SYMPHONY_SLOT and
   SYMPHONY_LABEL.
2. It creates a Codespace on the repository and opens it in a new tab.
3. The setup task sees the three and runs only `scripts/tokens.py add` for
   that slot: claude.ai's sign-in opens in another tab, and you press
   **Authorize** as the account the slot is for.
4. The page watches the slot's secret; once GitHub lists it as updated, it
   deletes the three Codespaces secrets and says so, and the Codespace can
   be deleted.

It needs the SymphonyBoard App's user permission Codespaces user secrets
and its repository permission Codespaces, both read and write.

## What it costs and where it runs

A Codespace on a repository of your personal account runs on your account's
free monthly Codespaces hours. On an organization's repository the
organization pays, and only once an owner allows Codespaces for its members
at https://github.com/organizations/ORG/settings/codespaces. The setup takes
minutes on the smallest machine, two cores.

## What is not measured yet

Whether claude.ai's sign-in hands its answer back to `claude setup-token`
in a Codespace opened in the browser, or shows a code to paste, has not
been tried from a cloud session, which cannot open a Codespace; step 5
covers both. The Tokens page's "Add or renew a slot" stays the way to store
a token printed anywhere else.
