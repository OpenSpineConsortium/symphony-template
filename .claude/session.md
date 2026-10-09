# Session checkpoint

Written 2026-10-09 by the main account's cloud session, before the owner
moved the work to another account to save this one's usage. Read this
first, then docs/history/experiment-research/README.md.

## Completed work

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

- #10, the experiment harness: claimed on claude/10 with a draft pull
  request. Only research so far: docs/history/experiment-research/ holds
  the summary, every claim with its source and verdicts (claims.json) and
  the workflow script. The run was stopped part way: CooperBench and the
  related evidence are fully verified, GitHub mechanics partly, Claude
  mechanics not at all. Nothing of the harness is built.
- #11, the push guard's newline hole: claimed on claude/11 with a draft
  pull request (#12) that carries a rewrite as work in progress and every
  finding of four adversarial rounds. main still has the guard from #3,
  which lets a push to main through when it sits on a later line of a
  multi-line command; branch protection still stops it on GitHub.
- No background workflow is running; both were stopped.

## Remaining tasks

1. #10: decide the arms with the owner in light of the research (see
   below), then build: a task suite with acceptance tests, a seeding
   tool, per-arm worker prompts and workflow, auto-merge for the PR-gated
   arm, usage capture from claude-code-action, and a deterministic report
   tool. Finish verifying the Claude-side mechanics first, cheaply.
2. #11: cut the rewrite back to the newline fix alone with its tests, or
   close the issue and rely on branch protection.
3. Owner's settings, by hand: import docs/setup/ruleset-main.json, turn on
   "Automatically delete head branches", secret scanning and push
   protection; run /install-github-app as the main account to turn on
   @claude; optionally set CLAUDE_WORKER=true.
4. Re-make the test repository (sdlc-template-test) from the current
   template rather than back-porting; it came from an older layer.

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
