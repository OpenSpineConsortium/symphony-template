# {{PROJECT_NAME}}

This repository is a Claude project kept as files: its instructions, its goal, its shared memory and its board live here, and Claude Code reads them in every session, local or cloud. The repository is the source of truth for every Claude session and every account; a claude.ai Project only links it, its own fields stay blank, and Claude Code loads this file and what it imports at the start of every session, a Project's thread and a cloud session opened on the repository alike.

## Read first

- The goal, the scope and who owns what, loaded into every session by this line: @docs/project.md
- How work is claimed, done in the open and finished, loaded the same way: @docs/agents/PROTOCOL.md
- The board: the file STATE.md on the branch `board`, rewritten by the board workflow from the open issues, the claim branches and the pull requests. It lives on another branch, which no import reaches: read it with `git fetch origin board && git show origin/board:STATE.md`; the session hook prints it at the start of every session, and docs/agents/STATE.md on {{DEFAULT_BRANCH}} only describes it.

Before any work: fetch, read the board, check the claim on the issue you mean to take. One issue, one branch `claude/<issue>`, one pull request.

## Shared memory

@docs/memory/MEMORY.md

A fact worth keeping is one file under docs/memory/ with one index line in MEMORY.md, added in the same pull request as the change it came from.

## Conventions

- The board first (.claude/rules/board.md): fetch, read the board (STATE.md on the branch `board`) and PROTOCOL.md, check the claim; never push to another account's branch; never force-push the default branch or any branch that is not your own claim. A hook refuses the pushes this rule forbids, and /board (.claude/commands/board.md) reprints the whole board mid-session.
- Memory (.claude/rules/memory.md): one fact per file, a kebab-case name, a one-line description first, one index line; never a secret.
- Writing (.claude/rules/writing.md): plain prose that says why, short functions, names that read as English, no emoji, ASCII and LF, no new dependencies; tag a durable fact in conversation as Decision: or Constraint: so a checkpoint keeps it.
- Skills: .claude/skills/claim, .claude/skills/remember and .claude/skills/checkpoint are the three procedures, in the order a piece of work meets them.
- The block at the end of this file, between the cswap markers, is rewritten by the checkpoint skill and by `cswap checkpoint write`; do not edit it by hand.

## Checks

Run `bash scripts/check.sh` before opening or updating a pull request. CI runs the same script as the check named "check", and the default branch takes only pull requests that pass it.

<!-- cswap:checkpoint:begin -->
## Session checkpoint (kept by cswap)

Read `.claude/session.md` at the start of a session: it holds the completed work, the current state and the remaining tasks. Tag durable facts in conversation as `Decision:` or `Constraint:` so the next `cswap checkpoint write` keeps them.

### Durable decisions
- Prefer GitHub's native, free features; no API billing: Claude in CI runs on a subscription OAuth token.
- A protocol change is made in OpenSpineConsortium/sdlc-protocol and reaches every consumer by its sync on one push (ecosystem.json, sync.yml).
- coordbench measures what CooperBench measures, as CooperBench 63b9d44 does, differing only with a stated reason (PARITY.md); model-judged measures run only on purpose, never with ANTHROPIC_API_KEY.
- Crowdsourcing: each contributor works under their own Claude account and the project never holds anyone's credential; crowd mode (scripts/crowd.py, CLAUDE_CROWD) enforces it.
- Field metrics: no hosted server; on by default, disclosed, one switch off; aggregates only, a repository only as a salted hash; the failure-mode judge runs client side.
- "Free to use" is not "free access to the source": the template stays private and is adopted through the public OpenSpineConsortium/sdlc-start, which holds no file of it.
### Constraints
- The cloud environment blocks cooperbench.com, arxiv.org, cursor.com and docs.github.com; CooperBench's paper and data come from the GitHub repository cooperbench/website.
- The cloud environment withholds CLAUDE_CODE_OAUTH_TOKEN; coordbench reads COORDBENCH_CLAUDE_TOKEN, each account its own.
- sdlc-template is internal to its enterprise; outsiders need a public copy or sdlc-start.
- sdlc-start and its Actions logs are public: nothing of the template may be committed or printed there.
<!-- cswap:checkpoint:end -->
