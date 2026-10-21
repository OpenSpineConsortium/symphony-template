# Several Claude accounts on the grid, managed from the control panel

Source: the thread "Beethoven grid node wait", 2026-10-21, from the owner's message of 01:50 UTC: sign
in to Claude on the grid remotely and automatically, keep several Claude accounts signed in there,
swap between them as claude-swap (cswap) does on his own machine, and run autonomous jobs on those
sign-ins instead of on year-long setup tokens held as secrets, all manageable from a control panel
tab. Read on the day: OpenSpineConsortium/hpcworker at framework 20 (bin/hpcworker, jobs/
worker.sbatch.tpl, lib/login_plain.sh, tools/grid_gate.sh, interface/contract/cli.json),
beethoven-extension 23.0.0's sign-in flow, symphony-template's tools/pool.py and
docs/research/claude-token-pool.md. Built on 2026-10-21 as hpcworker framework 21, grid-accounts.yml and the control panel's Grid tab (the section Built, at the end). The thread that owns the token pool and
the Tokens tab ("Tokens and adopted repositories") is told before any pool code changes.

## What already exists, and is reused whole

- A sign-in on the grid is one sitting of `claude auth login` on a compute node inside the worker's
  image (`hpcworker claude login`, or the panel's `connect --login`, lib/login_plain.sh). It prints
  `AUTH-URL: <link>`; the student signs in on Anthropic's page in their own browser, and pastes the
  code back. Beethoven already drives this over the portal's shell: it opens the link and sends the
  pasted code. That is remote sign-in, built and shipped; it was never the missing piece.
- Claude Code keeps one sign-in per folder: `CLAUDE_CONFIG_DIR`. The grid's sign-in lives in the
  profile's `claude_config_dir`, `$HOME/.beethoven/claude`. cswap on the owner's machine is exactly
  this, one folder per account and a switch of which one is current.
- Claude Code refuses Remote Control to an account whose plan has none ("Remote Control isn't
  enabled for this account"), which framework 20 now reads as fatal, and a worker started on the
  wrong account says so at once.
- Symphony's token pool (tools/pool.py, the branch `pool`, SYMPHONY_CLAUDE_SETTINGS, the Tokens
  tab) already names slots 1 to 32, each with an id, an owner, a model, an effort, paused and
  resume, and reads each slot's five-hour and seven-day windows from Claude's own rate_limit_event.
  The pool is the registry of accounts; this design adds where a slot's sign-in lives, not a second
  list.
- The ssh gate (hpcworker tools/grid_gate.sh, symphony-template grid-gate.yml) lets GitHub Actions
  say exactly three words to the grid, start, status and stop, through a key whose forced command
  takes nothing else, and never a shell, a password or a credential.

## The design: one folder per account, chosen by slot

On the grid, under the student's own home:

    ~/.beethoven/claude            the current sign-in, as today (a link from framework 21 on)
    ~/.beethoven/accounts/<slot>/  one Claude Code config folder per signed-in account
    ~/.beethoven/accounts/current  the slot the link points at, one line

`<slot>` is the pool's slot number (1 to 32), so a sign-in on the grid and a token in the pool that
belong to one Claude account carry one number, and the Tokens tab shows one tile for both. A slot
with a token and no grid sign-in runs in Actions only; a slot with a grid sign-in and no token runs
on the grid only; a slot with both runs anywhere.

hpcworker framework 21 adds one verb, `hpcworker accounts`, with four words:

- `list`: each slot folder, whether `claude auth status` there says a subscription and which
  e-mail and plan, the consent recorded, and which is current. Read through the image on a compute
  node as `claude login` is, since `claude` is not on the login node; never a credential.
- `add <slot>`: the sign-in sitting of today, with `CLAUDE_CONFIG_DIR` set to that slot's folder.
  The panel's `connect --login` takes `--account <slot>` and does the same, so Beethoven signs a new
  account in with the flow it has.
- `use <slot>`: moves the link `~/.beethoven/claude` to the slot's folder and writes `current`. A
  running worker keeps the folder it started with (the job reads `CCD` once); the next start takes
  the new one.
- `remove <slot>`: refuses while a worker runs on it, then deletes that one folder under
  `~/.beethoven/accounts/` and nothing else, only from a terminal with no agent marker, as every
  destructive verb here does. It never runs `claude auth logout`.

`hpcworker worker start` and `connect` take `--account <slot>`, default `current`, and write the
slot into status.json (`account_slot`) beside `claude_login`, so the panel's log says which account
a worker is on. The worker's rate_limit_event, which Claude Code prints in stream-json, is written
to the run directory as `slot-<N>.grid.json` in the pool's own shape, and the Symphony repository's
grid.yml job copies it to the branch `pool` as a fourth kind of reading beside run, probe and cswap,
so the Tokens tab's five-hour and seven-day bars are right for a slot that works on the grid.

## Who manages it from where

Two surfaces, each doing what it can reach, with no third store.

- Beethoven, the surface with a shell on the grid (the portal's shell, VPN on): the sign-in of a
  new slot, since a sign-in needs Anthropic's page in a browser and a pasted code, and that is
  what Beethoven does already; the switch of the current slot; and the Stop and Connect of the
  worker. Its Settings page gets an Accounts section: the list, one Add (the sign-in flow with the
  next free slot), Use on each row, Remove behind a confirm.
- The control panel's Tokens tab, the surface with GitHub's API and no shell: the same slots as
  tiles, each tile saying where the slot is signed in (Actions, grid, both), its windows, and a
  Use on the grid button that dispatches grid-gate.yml with a new word, `account <slot>`, which the
  forced command passes to `hpcworker accounts use`. The gate stays three words plus this one, each
  a fixed string with a number, never a shell. A sign-in cannot be done from the panel, since the
  panel has no shell and the gate must never carry one; the tile says "Sign in from Beethoven" and
  deep-links the extension's Settings page.

The Tokens tab is the one place for both kinds of slot, as the coordinator asked; the extension's
Accounts section is the grid's own view of the same numbers.

## Autonomous jobs on grid sign-ins instead of year-long tokens

A job in Actions runs on a token held as an organization secret, minted by `claude setup-token`
(one year, inference only); a job on the grid runs Claude Code where a sign-in already is, and
holds no token at all. Both are in place. What changes is the choice:

- symphony-template's grid.yml dispatch takes `account: <slot>` (default `current`) and starts its
  chain with `--account <slot>`; a worker's or an agent's line in .github/symphony/accounts.json
  may say `"grid": "<slot>"` beside its Actions slot, and workers.yml sends such a worker's run
  through grid.yml instead of claude-code-action.
- pool.py's pick treats a grid-signed-in slot as any other, with the readings grid jobs write; a
  slot whose grid sign-in Claude refuses ("Remote Control isn't enabled", or a sign-in that is no
  longer a subscription) is written `paused` with the reason by the job that saw it, so auto never
  picks it again until a person signs it in afresh.
- Nothing of any account goes into a repository: a slot's folder is on the grid under the student's
  home, 0700; the pool branch carries numbers and resets only; the Tokens tab reads secrets' names,
  never values. A setup token in an organization secret stays allowed for a repository with no grid.

## What Anthropic's terms say, as far as this session can read them

Not fetched: anthropic.com is unreachable from the cloud session. From memory of the Consumer Terms
of Service and the Usage Policy, to be checked by the owner on the live pages
(https://www.anthropic.com/legal/consumer-terms, https://www.anthropic.com/legal/aup):

- One person may hold several paid subscriptions of their own. Sharing one account's credentials
  with another person, or letting another person's work run on it, is what the terms forbid; this
  design keeps one person's accounts in one person's home and never hands a sign-in to anyone else.
- The Usage Policy forbids circumventing rate limits. Using several of one's own subscriptions in
  parallel for separate work is, in this reading, use of what was paid for; an auto mode whose only
  purpose is to hop to another account the moment one is throttled is the part closest to what the
  policy names, and the owner decided on 2026-10-13 to run his own accounts from one orchestrator
  knowing that question. The design keeps the choice visible (a slot per job, written in
  accounts.json and the dispatch) and auto mode optional, so a person can run it as plain
  assignment with no rotation at all.
- Claude Code's own rule, read from its binary on 2026-10-17: a setup token is inference only and
  carries Remote Control for nothing; a grid sign-in is a full login. Neither is ever written to a
  repository.

## Order of work

1. hpcworker framework 21: `accounts list|add|use|remove`, `--account` on start and connect,
   `account_slot` in status.json, the grid reading file, the gate's fourth word; the contract
   export's version raised; vectors and tests.
2. beethoven-extension 24.0.0: the Accounts section in Settings on the new contract pin; the
   sign-in flow takes a slot; privacy statement unchanged if no new data leaves the grid (the slot
   number and the e-mail Claude Code reports are shown, as the plan is today).
3. symphony-template: grid.yml's `account` input, the pool's grid reading kind, accounts.json's
   `grid` key, in agreement with the Tokens thread; the site's Tokens tab tiles and the Use on the
   grid button in the site repository.
4. Not before the owner's word: the first sign-in of a second slot on the grid, which spends an
   allocation for the sitting.

## Built (2026-10-21)

The owner asked the same night for all of it from the control panel: see each account's use, the resets, a swap, auto mode, low latency. Built as designed above, with three choices made on the way:

- The accounts are numbered folders beside the profile's folder, which becomes a link to the one in use (hpcworker's lib/accounts.sh). A worker runs Claude Code in the folder the link named when it started, never through the link, and moves when the link moves; tested against stand-ins in hpcworker's tests/test_job.py.
- The panel reaches the grid through the ssh gate's new accounts words, not a fourth single word: a list, use, login, code (on standard input), link, usage, auto on and off, forget. Words that only touch files have a floor of three seconds, so a press answers in one workflow run, about half a minute.
- The sign-in link is sealed with RSA-OAEP and AES for the page that asked, since an issue or a log would show it to everyone who may read the repository, and whoever opens it first could sign their own account into the owner's grid.

## Several workers at once (framework 22, 2026-10-21)

The owner asked next for several Claude Code workers on the grid at once, from all his accounts, each launched, tracked, cancelled and reached from the panel, coordinating through git like the cloud sessions. Each is a named worker (hpcworker's worker start --name, which already existed) with a file account.pin in its run folder: the job runs Claude Code in that account's folder and never follows the link, so Use and auto mode move only the main worker. The gate's words accounts start N [NAME] and accounts stop NAME start and stop one; the list carries every worker of the last day with its state, node, link, account and pin. Each worker's environment sets SYMPHONY_WORKER to grid-<name>, so its claims carry a name of their own and the board's claim lock (one branch push per issue) keeps it from racing a cloud session or another grid worker. Each worker is its own Slurm chain, so it spends allocation like the main one.

Not yet measured on the grid: the detached sign-in's job end to end, auto mode against a real limit, and how fast a swapped worker's new link appears.

