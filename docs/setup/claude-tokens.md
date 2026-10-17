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
| SYMPHONY_CLAUDE_ACCOUNTS | the place | the slots in use, as a list such as `1,2,3`; the wizard keeps it equal to the slots whose secret exists. The bench stops a real run on any other word, such as `01` or `9`, so the wizard writes such a list again |
| SYMPHONY_CLAUDE_<slot>_LABEL | slot, optional | nothing; a word of your own so that `status` can say which account a slot is. A variable is readable by anyone who can read the repository's workflows, so never an e-mail address |

A secret on an organization reaches the repositories on its list (GitHub's
"Selected repositories"), or all of them; a repository's own secret or
variable of the same name outranks the organization's. `status` reads the
repositories the wizard names and the ones GitHub lists as seeing the list
of slots or a token. It names each one's own secret of a name the
organization gives it, and its own SYMPHONY_CLAUDE_ACCOUNTS, with the page
to delete it on, where the organization's list reaches it or the wizard
names it: a list made there by hand would hide the one the wizard keeps
from that repository's workflows. The slots are the owner's own accounts: the
project never holds anyone else's credential (docs/setup/crowdsourcing.md),
and the owner decided on 2026-10-13 to run their own several accounts as
one pool.

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
   slot's number replaces its token). Where claude-swap (cswap) keeps a
   list of accounts on this machine, it shows that list and asks which
   account the slot is for, by cswap's number. Then it asks for a label;
   `y` takes the account's cswap alias where it has a label's shape, and
   Enter leaves the slot with none, since a label is public.
4. Where this machine has Chrome, Edge or Brave (Chrome or Edge under
   C:\Program Files in WSL), it asks which browser
   profile the slot's sign-in opens in: a new profile named "Symphony"
   and the slot's number by default, one of the browser's own by its
   number in the list it shows, or `n` for the default browser (see
   "A browser profile per account" below). Without a profile, it tells
   you to sign in to claude.ai in your browser as the account that slot
   is for, and waits for Enter. The sign-in page that follows
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
python3 scripts/tokens.py order 3,1,2
python3 scripts/tokens.py profiles
python3 scripts/tokens.py forget 2
python3 scripts/tokens.py show 2
python3 scripts/tokens.py show main --copy
python3 scripts/tokens.py share coordbench
```

Where the secrets go is read from the clone's origin: a repository of an
organization takes the organization level with that repository on the
list, a personal repository its own level. Say it instead with
`--org ORG --repos NAME,NAME` (the repositories that see the secrets;
`--visibility all` for every repository of the organization) or
`--repo OWNER/NAME`. A secret that exists keeps its visibility and its
list, which grows by what `--repos` names; the wizard takes nothing off
a list.

What it never does: show a token unasked, write one to a file, put one on
a command line, or read one back from GitHub (GitHub cannot); on Windows
it keeps a copy in Credential Manager, which only `show` reads (below). It refuses
an API key on sight, since runs bill nothing here (docs/project.md), and
anything else that is not a token from `claude setup-token`. It refuses to
run for a repository in crowd mode, which holds no Claude token
(docs/setup/crowdsourcing.md).

## A browser profile per account

`claude setup-token` cannot be told which Claude account to approve: the
browser's signed-in account decides. With several accounts, the wizard
gives each slot a browser profile of its own. On Linux, macOS and WSL it
hands claude a small launcher through BROWSER, the variable claude opens
its sign-in link with, and the launcher opens the link in that profile;
the launcher lives in a folder of the run's own and is gone when the
sign-in ends. In a Windows shell it opens the profile first, on a blank
page so that no second sign-in shows, and then starts claude, whose link
Chrome and Edge send to the profile used last; if it lands in another profile, copy the link claude
prints into the right one.
The first time, a new profile shows claude.ai's sign-in page: sign in
there as the slot's account, then Approve. The profile keeps that
sign-in, so every later token for the slot, a year on, is one Approve.

The wizard remembers each slot's profile and its cswap account number in
tokens.json in your own settings folder (`%APPDATA%\symphony` on
Windows, `~/.config/symphony` elsewhere), never in the repository and
never with an address in it, and offers them as the defaults next time.
`add --profile "Profile 2"` opens one sign-in in a profile without
questions. Set SYMPHONY_BROWSER to a Chromium browser's program to use
one the wizard does not find by itself. In WSL the wizard finds Chrome
or Edge under C:\Program Files and names a profile by its folder; the
Windows browser should reach the sign-in's callback in WSL through WSL's
localhost forwarding, which is not yet tried.

cswap's accounts cannot stand in for a sign-in. cswap keeps each
account's interactive login, whose refresh token changes each time it is
used, so a copy in Actions would sign one side out; and it is a full
login, where `claude setup-token` makes a year-long token that can only
run Claude. The wizard reads only cswap's list of accounts, its
sequence.json, and opens none of its credentials.

## Where it runs

Linux, macOS and WSL have the pseudo-terminal the sign-in runs behind;
claude opens the browser where it can and prints the link otherwise, and
in WSL the link is opened in the Windows browser. A Windows shell has no
pseudo-terminal: there claude runs in the same window, keeping its
keyboard, and its output reaches the screen through the wizard on a pipe,
masked as behind a terminal, so the token should be caught and stored by
itself there too: claude 2.1.302 writes to a pipe as to a terminal, its
link opened and no line wrapped, as measured on Linux; the owner's first
Windows run is the test. That needs a console claude can read its
keyboard from (cmd, PowerShell or Windows Terminal); in Git Bash's own
window or an IDE the wizard says so and takes a pasted token instead. A
machine
may have gh but not claude: there, run `claude setup-token` wherever
claude is and give the wizard the token with `add --paste` or
`main --paste`; the wizard takes the paste path by itself when it cannot
run claude, and refuses a paste where Python says it cannot hide what is
typed. In Git Bash's own window (mintty) a hidden prompt may
hang or echo instead, so run the wizard there through winpty, or from
cmd, PowerShell or Windows Terminal. claude is given a terminal 400
columns wide, so it never wraps the token; were it ever to, the cut token
would be refused rather than stored, and the wizard would say that the
screen may show part of it.

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

## A copy on your PC

GitHub never gives a secret back, so on Windows the wizard keeps a copy
of each token it stores in Windows Credential Manager, under
`symphony/org:<organization>/<secret>` (or `symphony/repo:<owner>/<name>/<secret>`).
Windows encrypts it under your own Windows sign-in, and only a program
running as you reads it back. `python3 scripts/tokens.py show N` prints
slot N's token, `show main` the workflows' token, and `--copy` puts it on
the clipboard instead, so it never reaches the screen or the terminal's
scrollback; Windows' clipboard history (Win+V) keeps it after you paste,
so clear it there (Clear all), and a clipboard synced across devices sends
it to them. `profiles` says which slots have a copy. `remove N` deletes a
slot's copy along with its secret, and the copy of CLAUDE_CODE_OAUTH_TOKEN
is deleted by hand, as below; `add --no-copy` and `main --no-copy` keep
none. To see or delete a copy by hand: Control Panel, Credential Manager,
Windows Credentials, the entries that start with `symphony/`. A token
stored before 2026-10-17, or on another machine, has no copy: `add --slot N`
mints a new one that does. Elsewhere than Windows no copy is kept.

## Which secrets a benchmark uses

A benchmark in Actions reads only the slots, never CLAUDE_CODE_OAUTH_TOKEN:
coordbench's bench.yml takes `SYMPHONY_CLAUDE_<slot>` for each slot in the
dispatch's "accounts" box, or in SYMPHONY_CLAUDE_ACCOUNTS when the box is
empty, and refuses a real run when one of them is unset or unseen by
coordbench. So:

- To pick the accounts for one run, type the slots in the "accounts" box
  when you press Run workflow, such as `2,3`; only those are used.
- To keep an account away from the benchmarks, give it no slot: an
  account only in CLAUDE_CODE_OAUTH_TOKEN (`main`) serves @claude and the
  workers alone.
- The benchmark's repository must see the slots. A secret on the
  organization reaches only the repositories on its list, so
  `python3 scripts/tokens.py share coordbench` adds coordbench to every
  slot's secret, its label and the list of slots, with no sign-in, and
  `status` then lists it under "seen by". A benchmark run by a cloud
  session itself, as flowbench's pilot is, uses that session's own
  subscription and reads no secret.

## Renewing and removing

A token lasts about a year. `status` says "renew soon" within a month of
that and "renew now" past it; `add --slot N` for that slot replaces the
token in place, with the slot's label and list kept. `remove N` deletes
the slot's secret and its label, takes it off the list and forgets the
slot's profile and cswap account on this machine; `forget N` does only
the last. `order 3,1,2` rewrites the list of slots in that order, every
slot that is set once: the bench deals its jobs to the slots in the
list's order, one to each in turn (coordbench's plan.py), so the order
says which account takes the first job, not which is used up first; a
slot added later joins the end, and the order stays; delete
CLAUDE_CODE_OAUTH_TOKEN on its page to turn @claude, the workers in
Actions and the coordinator workflow off (docs/setup/claude-action.md).
Deleting or replacing a secret takes the old token out of Actions and
does not revoke it: it stays good until a year after it was made, and
the Claude Code documentation names no page that revokes a setup-token
token on its own (docs/research/token-wizard.md, open items), one more
reason the wizard keeps every token off every screen.
