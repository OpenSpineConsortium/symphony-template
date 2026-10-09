# {{PROJECT_NAME}}

This repository is a Claude project kept as files: its instructions, its goal, its shared memory and its board live here, and Claude Code reads them in every session, local or cloud. The repository is the source of truth for every Claude session and every account; a claude.ai Project only links it and says to read this file.

## Read first

- docs/project.md: the goal, the scope and who owns what.
- The board: the file STATE.md on the branch `board`, rewritten by the board workflow from the open issues, the claim branches and the pull requests. Read it with `git fetch origin board && git show origin/board:STATE.md`; the session hook prints it at the start of every session, and docs/agents/STATE.md on {{DEFAULT_BRANCH}} only describes it.
- docs/agents/PROTOCOL.md: how work is claimed, done in the open and finished.

Before any work: fetch, read the board, check the claim on the issue you mean to take. One issue, one branch `claude/<issue>`, one pull request.

## When this repository is linked to a Project

If you are a thread of a claude.ai Project whose instructions do not contain "Read CLAUDE.md first", the Project was just linked and is not set up yet: run the bootstrap skill (.claude/skills/bootstrap) before anything else, then carry on with what you were started for. It writes the Project's instructions and makes the worker routine from the repository, so the person types nothing. A terminal session has no Project and skips this.

## Shared memory

@docs/memory/MEMORY.md

A fact worth keeping is one file under docs/memory/ with one index line in MEMORY.md, added in the same pull request as the change it came from.

## Conventions

- The board first (.claude/rules/board.md): fetch, read the board (STATE.md on the branch `board`) and PROTOCOL.md, check the claim; never push to another account's branch; never force-push the default branch or any branch that is not your own claim.
- Memory (.claude/rules/memory.md): one fact per file, a kebab-case name, a one-line description first, one index line; never a secret.
- Writing (.claude/rules/writing.md): plain prose that says why, short functions, names that read as English, no emoji, ASCII and LF, no new dependencies; tag a durable fact in conversation as Decision: or Constraint: so a checkpoint keeps it.
- Skills: .claude/skills/bootstrap sets a Project up from the repository; .claude/skills/claim, .claude/skills/remember and .claude/skills/checkpoint are the three procedures a piece of work meets, in that order.
- The block at the end of this file, between the cswap markers, is rewritten by the checkpoint skill and by `cswap checkpoint write`; do not edit it by hand.

## Checks

Run `bash scripts/check.sh` before opening or updating a pull request. CI runs the same script as the check named "check", and the default branch takes only pull requests that pass it.

<!-- cswap:checkpoint:begin -->
## Session checkpoint (kept by cswap)

Read `.claude/session.md` at the start of a session: it holds the completed work, the current state and the remaining tasks. Tag durable facts in conversation as `Decision:` or `Constraint:` so the next `cswap checkpoint write` keeps them.

### Durable decisions
- (none recorded)
### Constraints
- (none recorded)
<!-- cswap:checkpoint:end -->
