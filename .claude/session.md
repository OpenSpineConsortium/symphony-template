# Session checkpoint

Written 2026-10-09 by the main account's cloud session. Read this first,
then experiment/README.md and docs/history/experiment-research/README.md.

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

- Team mode (#14) is merged to main (#15): a lead plans an epic into
  pre-assigned sub-issues, members work them in parallel and land by
  auto-merge, the lead unblocks and integrates. A review in three lenses
  with two skeptics per finding confirmed 13 defects; all are fixed in
  the merged code. Not yet run live on a repository.
- #10, on claude/10 (draft pull request #13), now has experiment/: a kit
  that runs CooperBench's four-arm ablation in one Claude Code cloud
  session with CooperBench's own runner and scorer under Docker inside
  the session's container. Checked in this session with no Claude usage:
  dockerd runs; images pull from mirror.gcr.io (Docker Hub answers 429);
  the overlay adds claude, the redis client and the proxy CA; the gold
  patches grade (click 2068 12/12, jinja 1621 10/10); a team run with a
  shared remote came up whole and stopped only at the API's 401 for a
  placeholder token. experiment/README.md has the steps, cost and
  differences from the authors' run.
- The kit needs CLAUDE_CODE_OAUTH_TOKEN (from `claude setup-token`) in the
  cloud environment's settings, and a new session started after it is
  added. Nothing has spent usage on the experiment yet.
- #11 (draft #12) is unchanged: the guard rewrite as work in progress.

## Remaining tasks

1. Owner: create the token, add it to the environment as
   CLAUDE_CODE_OAUTH_TOKEN, start a new session on this repository.
2. In that session: `bash experiment/setup.sh`, then the pilot on
   pallets_click/2068 (prepare_task.sh, run_arms.sh), read the four
   summary.json files and the usage it took, and only then the rest of
   the flash subset, one task at a time.
3. A report tool that puts the four arms' results side by side per pair,
   with the authors' numbers for comparison.
4. #11: cut the rewrite back to the newline fix with its tests, or close
   it and rely on branch protection.
5. Owner's settings, by hand: import docs/setup/ruleset-main.json, turn on
   "Automatically delete head branches", secret scanning and push
   protection; run /install-github-app; for team mode set CLAUDE_WORKER
   and CLAUDE_TEAM and allow auto-merge.
6. Re-make the test repository (sdlc-template-test) from the current
   template.

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
