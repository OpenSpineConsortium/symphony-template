# Your Claude accounts as Actions secrets: the token wizard

Every Claude run in GitHub Actions draws on one of your Claude accounts
through a subscription token, the output of `claude setup-token`, a
browser sign-in that prints a token good for about a year and saves it
nowhere. By hand, each token goes from that terminal through a clipboard
into a settings page, once per account, and again a year later. The
wizard `python3 scripts/tokens.py` does that part for you, for every
account you have, without the token ever being shown.

## What runs on which secret

| Secret or variable | One per | Read by |
| --- | --- | --- |
| CLAUDE_CODE_OAUTH_TOKEN | repository, or organization | @claude, the workers in Actions and the coordinator workflow of every repository that sees it (docs/setup/claude-action.md) |
| SYMPHONY_CLAUDE_1 to SYMPHONY_CLAUDE_8 | account: one slot each | a benchmark in Actions, which spreads its agents over the slots, one account per job at a time (OpenSpineConsortium/coordbench's bench.yml); any workflow that names a slot |
| SYMPHONY_CLAUDE_ACCOUNTS | the place | the slots in use, as a list such as `1,2,3`; the wizard keeps it equal to the slots whose secret exists |
| SYMPHONY_CLAUDE_<slot>_LABEL | slot, optional | nothing; a word of your own so that `status` can say which account a slot is. A variable is readable by anyone who can read the repository's workflows, so never an e-mail address |

A secret on an organization reaches the repositories on its list (GitHub's
"Selected repositories"), or all of them; a repository's own secret of the
same name outranks the organization's. The slots are the owner's own
accounts: the project never holds anyone else's credential
(docs/setup/crowdsourcing.md), and the owner decided on 2026-10-13 to run
their own several accounts as one pool.

## One run of the wizard

On your own computer, in a clone, with the GitHub CLI signed in as an admin
of the organization or the repository and Claude Code installed:

```
python3 scripts/tokens.py
```

1. It checks that gh is signed in and, for an organization, that its
   token carries the scope `admin:org`, which organization secrets need;
   if not, it says to run `gh auth refresh -h github.com -s admin:org`
   and stops before any sign-in is spent.
2. It prints the state: each slot that is set, when, and when to renew
   it (a year later), the slots that are free, the list of slots, and
   whether CLAUDE_CODE_OAUTH_TOKEN is set. Nothing but names, dates and
   counts; GitHub gives nobody a secret's value back.
3. It asks which slot to fill (the first free one by default; a set
   slot's number replaces its token) and for a label.
4. It tells you to sign in to claude.ai in your browser as the account
   that slot is for, and waits for Enter. The sign-in page that follows
   names the account it approves: if the browser is signed in to another
   of your accounts, sign out there first, or open the link claude prints
   in a private window and sign in as the right one. While
   CLAUDE_CODE_OAUTH_TOKEN is not set, it asks whether the same token
   should be stored under that name too, the one the workflows run on.
5. It settles everything that could fail after the sign-in before it:
   that each repository named is one your login can see, and the
   visibility and the list each secret will be written with; a token
   minted and then not stored would be a year's token lost with the
   process. Then it runs `claude setup-token` behind a pseudo-terminal of
   its own: the browser opens, or the link is printed for you to open,
   you approve the access, and if the page shows a code you paste it at
   claude's prompt, all as if you had run the command yourself. The
   token claude prints is taken out of the output before it reaches your
   screen and shown as
   `sk-ant-oat**-**************** (kept by the wizard, not shown)`.
6. It hands the token to `gh secret set` on a pipe. gh encrypts it on your
   machine with the organization's or the repository's public key and
   sends only the sealed value; the token is never on a command line, in
   a file, in a log or in the wizard's output.
7. It stores the label, reads GitHub's listing back and confirms the
   secret is there, by name and date, and keeps the list of slots equal
   to the slots whose secret exists; then it asks whether there is
   another account.

The same, one step at a time, without questions:

```
python3 scripts/tokens.py status
python3 scripts/tokens.py add --slot 2 --label work
python3 scripts/tokens.py add --also-main
python3 scripts/tokens.py main
python3 scripts/tokens.py remove 2
```

Where the secrets go is read from the clone's origin: a repository of an
organization takes the organization level with that repository on the
list, a personal repository its own level. Say it instead with
`--org ORG --repos NAME,NAME` (the repositories that see the secrets;
`--visibility all` for every repository of the organization) or
`--repo OWNER/NAME`. A secret that exists keeps its visibility and its
list, which grows by what `--repos` names; the wizard takes nothing off
a list.

What it never does: show a token, write one to disk, put one on a command
line, keep one after the run, or read one back (GitHub cannot). It refuses
an API key on sight, since runs bill nothing here (docs/project.md), and
anything else that is not a token from `claude setup-token`. It refuses to
run for a repository in crowd mode, which holds no Claude token
(docs/setup/crowdsourcing.md).

## Where it runs

Linux, macOS and WSL have the pseudo-terminal the sign-in runs behind;
claude opens the browser where it can and prints the link otherwise, and
in WSL the link is opened in the Windows browser. A Windows shell has no
pseudo-terminal, and a machine may have gh but not claude: there, run
`claude setup-token` wherever claude is and give the wizard the token with
`add --paste` or `main --paste`, at a hidden prompt that echoes nothing,
as gh's own prompt would; the wizard takes the paste path by itself when
it cannot run claude, and refuses a paste in a window that cannot hide it
(Git Bash's own window is one: run it there through winpty, or from cmd,
PowerShell or Windows Terminal). A token that claude wrapped over two
lines, or a piece of one, is refused rather than stored, and the wizard
says so.

## By hand, where the wizard cannot run

Each secret is one page; the values come from `claude setup-token`, run
while signed in to the account the secret is for.

- An organization secret: open
  https://github.com/organizations/{{OWNER}}/settings/secrets/actions,
  press "New organization secret", type the name (SYMPHONY_CLAUDE_1, or
  CLAUDE_CODE_OAUTH_TOKEN), paste the token as the value, set Repository
  access to "Selected repositories", press the gear beside it and tick
  each repository that should see it, then "Add secret".
- A repository secret: open
  https://github.com/{{REPO}}/settings/secrets/actions/new, type the
  name, paste the value, press "Add secret".
- The list of slots: open
  https://github.com/organizations/{{OWNER}}/settings/variables/actions
  (or https://github.com/{{REPO}}/settings/variables/actions for one
  repository), press "New organization variable" (or "New repository
  variable"), name SYMPHONY_CLAUDE_ACCOUNTS, value the slots in use such
  as `1,2,3`, the same repositories as the secrets, "Add variable".

Then `python3 scripts/tokens.py status` says what GitHub lists.

## Renewing and removing

A token lasts about a year. `status` says "renew soon" within a month of
that and "renew now" past it; `add --slot N` for that slot replaces the
token in place, with the slot's label and list kept. `remove N` deletes
the slot's secret and its label and takes it off the list; delete
CLAUDE_CODE_OAUTH_TOKEN on its page to turn @claude, the workers in
Actions and the coordinator workflow off (docs/setup/claude-action.md).
Deleting or replacing a secret takes the old token out of Actions and
does not revoke it: it stays good until a year after it was made, and
the Claude Code documentation names no page that revokes a setup-token
token on its own (docs/research/token-wizard.md, open items), one more
reason the wizard keeps every token off every screen.
