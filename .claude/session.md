# Session checkpoint

Written 2026-10-09 by the main account's cloud session. This is the full
checkpoint of the work on claude/10; main's own .claude/session.md points
here. Read this first, then experiment/README.md,
experiment/coordbench/README.md (the plug-in contract) and
experiment/coordbench/REVIEW.md (what to fix first).

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

1. Fix experiment/coordbench/REVIEW.md, blocking ones first, then delete it; run check.sh; push.
2. Owner: `claude setup-token`, add CLAUDE_CODE_OAUTH_TOKEN to the environment, start a new session.
3. Pilot on pallets_click/2068: CooperBench's runner (experiment/run_arms.sh) and coordbench (run.py) for the same arm, to calibrate the harness; then the arms on the 42 pairs; experiment/report.py.
4. #11: cut the guard rewrite to the newline fix, or close it.
5. Owner's settings by hand: import docs/setup/ruleset-main.json, auto-delete head branches, secret scanning and push protection, /install-github-app; for team mode CLAUDE_WORKER, CLAUDE_TEAM and auto-merge.

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
