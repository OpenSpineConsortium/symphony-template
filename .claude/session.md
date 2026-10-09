# Session checkpoint

Written 2026-10-09 by the main account's cloud session, when its usage ran
out, for whoever continues on any account. A session asked to "continue"
does this:

1. `git fetch origin && git checkout claude/10`. The work in progress is
   on that branch (draft pull request #13, issue #10), not on main.
2. Read that branch's own `.claude/session.md`: it is the full checkpoint
   (what is built, what is pushed, the remaining tasks in order).
3. Start on its first remaining task: fix the confirmed review findings
   listed in `experiment/coordbench/REVIEW.md`, the blocking ones first,
   with `bash scripts/check.sh` passing before every push to claude/10.

## Completed work

- Merged to main: the push guard, edit check and permission allowlist (#3),
  the claim protocol checked in CI and the opt-in Actions worker (#5), the
  plan ladder (#7), the ruleset and one-flow Claude setup (#9), team mode
  with a lead, members and integration (#15).
- On claude/10, pushed, CI green: experiment/ (CooperBench's four-arm
  ablation in one cloud session with the authors' runner; 42 of the 50
  flash pairs grade in this environment) and experiment/coordbench/
  (coordination as a plug-in: arms that are Claude Code plugins, served
  over MCP by a hub; README.md there is the contract).

## Current state

- claude/10 (#13): draft; 28 confirmed review findings open in
  experiment/coordbench/REVIEW.md; no agent has run a task yet.
- claude/11 (#12): draft; the push guard's rewrite, work in progress.
- Running agents on tasks needs CLAUDE_CODE_OAUTH_TOKEN (from
  `claude setup-token`) in the cloud environment's settings, then a new
  session; the session cannot see a variable added after it started.

## Remaining tasks

1. claude/10: the remaining tasks in its own .claude/session.md.
2. claude/11: cut the guard rewrite back to the newline fix with its
   tests, or close #11 and rely on branch protection.
3. Owner's settings by hand (docs/setup/github.md, docs/setup/claude-action.md).

## Decisions

- Prefer GitHub's native settings over workflows, to save CI minutes and
  Claude usage.
- No API billing: Claude in CI and in the experiment runs on a
  subscription OAuth token.
- A claude.ai Project's own fields stay blank; the repository is the one
  source of instructions, goal and memory.

## Constraints

- The cloud environment's network policy blocks deb.debian.org,
  deb.nodesource.com, huggingface.co, pypi.nvidia.com and
  openaipublic.blob.core.windows.net; Docker Hub rate-limits it, so images
  come from mirror.gcr.io.
- This file is the template repository's own checkpoint; template-init
  resets it to the blank one in every new copy.
