# Session checkpoint

Written 2026-10-09 by the main account's cloud session. This is the full
checkpoint of the work on claude/10; main's own .claude/session.md points
here. Read this first, then experiment/README.md,
experiment/coordbench/README.md (the plug-in contract) and
experiment/coordbench/REVIEW.md (what to fix first). The owner's
steps (accounts, tokens, secrets, variables) are in
docs/setup/owner-checklist.md.

## Completed work

- Merged to main: #15, team mode (#14), with the fixes from its review.

- Merged to main, in order: #3 (push guard hook, edit check, permission
  allowlist, /board, tidy workflow, @claude on the subscription OAuth
  token), #5 (claim protocol checked in CI by tools/check_protocol.py,
  opt-in Actions worker behind the CLAUDE_WORKER variable), #7 (the plan
  ladder in docs/setup/tiers.md, the board's fallback cut to six-hourly),
  #9 (the default branch's rules as docs/setup/ruleset-main.json, the
  Claude side in one OAuth flow through /install-github-app, the
  rewritten setup issue, release-audit fixes). CI was green on each.
- The repository is already marked as a template, so "Use this template"
  works now.
- A business report on what each dollar buys, as a Claude doc: "The
  Dollar-per-Feature Ladder" (the owner has the link).

## Current state

- Team mode (#14) is merged to main (#15). Not yet run live.
- #10, on claude/10 (draft pull request #13), all pushed, `bash scripts/check.sh` green (414 tests):
  - experiment/: the kit that runs CooperBench's four-arm ablation in one cloud session with CooperBench's own runner (setup.sh, prepare_task.sh, run_arms.sh, report.py). The whole flash subset was prepared and its gold patches checked: 42 of 50 pairs grade here; 7 need hosts the network policy blocks (README table).
  - experiment/coordbench/: coordination as a plug-in. An arm is a Claude Code plugin plus arm.py; the hub serves its tools over MCP (HTTP), a stdio bridge and shell commands; built-in arms solo, coop, coop-git, team (CooperBench's, prompt-parity tested) and sdlc (this repository's claim protocol with a real merge gate); drivers claude-cli and session; scoring by CooperBench's own evaluation. README.md is the contract.
  - experiment/coordbench/REVIEW.md: 28 confirmed review findings, not yet fixed.
- Nothing has run an agent on a task yet. The claude-cli driver needs CLAUDE_CODE_OAUTH_TOKEN in the environment's settings and a new session.
- The plan's usage ran out on 2026-10-09 (weekly limit resets 2026-10-15, 11:00 UTC).
- #11 (draft #12) is unchanged.

## Remaining tasks

A session told to "continue" works through ALL of these, in order, across
both open pull requests; it does not stop after the first. The flash
gradeability survey is finished (experiment/README.md has its table) and
needs no more work.

1. claude/10 (#13): fix the 28 findings in experiment/coordbench/REVIEW.md,
   blocking ones first; tests with each fix; then delete REVIEW.md. The
   review's usability lens (a newcomer writing a new arm from the README)
   produced findings that could not be verified before usage ran out:
   re-run that one lens cheaply (one agent writes a "pair-review" arm from
   the README alone and reports friction) and fix what it finds.
2. Make the owner's checklist (docs/setup/owner-checklist.md) as close to
   one click as GitHub and Claude allow, and keep the page in step:
   - scripts/setup-repo.sh, run once by the owner on their own computer
     with the GitHub CLI signed in (`gh auth login`): imports
     docs/setup/ruleset-main.json, turns on delete-branch-on-merge,
     auto-merge, secret scanning and push protection, creates the seven
     labels, sets the optional variables it is asked for, and stores the
     repository secret CLAUDE_CODE_OAUTH_TOKEN straight from
     `claude setup-token` without the token ever being shown or saved.
     The cloud session cannot run it: it has no gh and no admin rights.
   - Preshipped settings: a template copies files, never settings, so
     check and document the ways settings can still arrive with zero
     steps: organization rulesets and organization Actions secrets and
     variables (every repository OpenSpineConsortium makes, copies
     included, inherits them; say which GitHub plan each needs), and
     settings-as-code (.github/settings.yml read by a settings app,
     which is a new dependency, so an issue first).
   - template-init's setup issue: one link per remaining step, prefilled
     where GitHub allows (settings pages, the app install, new-secret
     and new-variable pages).
   - Claude side: /install-github-app already does the app and the
     secret in one OAuth flow; the cloud-environment variable and the
     claude.ai Project have no API, so they stay links with exact steps.
3. claude/11 (#12, issue #11): cut the push guard rewrite back to the
   newline fix with its tests and finish that pull request, or close it
   and issue #11 with a note that branch protection covers the case.
   Decide by whether the newline fix stands alone in under ~100 lines.
4. Session-driver pilot, needs no token: run one pair (pallets_click 2068,
   features 1,6) through coordbench with --driver session for the arms
   coop and team: `run.py prepare`, spawn one subagent per prompt file
   (Workflow tool), `run.py finish`. This is the owner's original ask:
   every arm evaluated by one session's own subagents.
5. When the owner has added CLAUDE_CODE_OAUTH_TOKEN (docs/setup/
   owner-checklist.md, section 2) and opened a new session: the pilot on
   pallets_click 2068 with CooperBench's own runner (experiment/run_arms.sh)
   and with coordbench's claude-cli driver for the same arms, to measure
   how much the harness itself moves the scores; then all five arms (solo,
   coop, coop-git, team, sdlc) on the 42 gradable pairs, one task at a
   time; experiment/report.py; a second seed on the pairs where arms
   disagree.
6. Write up the result for the owner: does the PR-gated way of working
   (the sdlc arm, this template's protocol) beat or trail shared
   collaboration (coop-git, team) and solo, at what usage. That answers
   the question the template was built for.
7. Before #13 merges: condense or delete docs/history/experiment-research/;
   ask the owner whether experiment/ (with coordbench) should move to a
   repository of its own, since everything on main ships in every copy of
   the template; then delete the claim file, mark ready, merge.
8. Team mode live run on a repository made from the template, once the
   owner has set CLAUDE_WORKER, CLAUDE_TEAM and auto-merge (checklist,
   section 4).
9. Re-make the test repository (sdlc-template-test) from the current
   template.
10. Owner's own steps, which no session can do: docs/setup/owner-checklist.md.

## Decisions

Stated by the owner in conversation, not tagged, so recorded here and not
in CLAUDE.md:

- Prefer GitHub's native settings over workflows wherever they cover the
  case, to save CI minutes and Claude usage.
- No API billing: Claude in CI runs on a subscription OAuth token.
- A claude.ai Project's own fields stay blank; the repository is the one
  source of instructions, goal and memory.
- The template should serve the owner's experiment: PR-gated agents
  against a shared project, after CooperBench.

What the research found that the owner should weigh before building:
CooperBench's losing Coop arm is already isolated branches with messages
only; the paper never tested a shared workspace; and the authors' later,
unreviewed ablation had a shared git remote (56%) and team mode (62%)
beating solo (48%), with messaging-only isolation worst (26%). This
template's branches are visible on the shared remote, so it sits nearer
the shared-remote arm.

## Constraints

- Background research in this session was expensive: three skeptics per
  claim over 130 claims. Verify fewer claims, with one skeptic, unless
  the owner asks for more.
- The cloud session's network policy blocked arxiv.org, openreview.net
  and docs.github.com; sources were read from GitHub-hosted copies.
