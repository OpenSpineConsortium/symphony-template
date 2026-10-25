# Shared multi-account Claude project: plan

Oct 8, 2026 · @greg

## Short answer

Build it around the repository, not around a shared Project. A redesigned Project belongs to one account and cannot be shared, and no Claude product lets one account's agent talk live to another account's agent. So the GitHub repo and Linear become the shared space, and each account gets its own Project pointed at the same repo.

- **Shared state:** the repo holds the code, the rules (`CLAUDE.md`, `.claude/rules/`) and the shared memory (`docs/memory/`). Linear holds the work queue and the conversation about each task.
- **Claiming work:** a task is claimed by pushing a branch named after its Linear issue (`claude/LIN-123`). Git accepts only the first push of a new branch, so two accounts cannot both claim one issue. The open PR is the progress, and a merged PR plus a Done issue is the shared record of finished work.
- **The coordinator:** a routine on your main account that wakes on PR events, on every push to main (through a small GitHub Action) and once an hour. It triages Linear, spots overlapping PRs and asks for rebases. Nothing first-party stays running and reachable by other accounts, so the coordinator is event-driven, with its continuity kept in repo files.
- **Staying current:** cloud threads always start from a fresh clone of main. When main moves, the Action comments on every PR it now conflicts with, and branch protection refuses a merge that isn't up to date.
- **Risk to weigh first:** running several subscription accounts as one swarm is a grey zone. Multiple accounts are not forbidden, but bans were reported in February 2026 for several accounts on one device, and the plans' limits assume ordinary individual use (section 2).

## What the Claude products allow across accounts

Every Claude surface that could host a coordinator is scoped to one account, so cross-account coordination has to go through GitHub and Linear.

| Piece | What it does | Across accounts? |
| --- | --- | --- |
| Redesigned Project ([docs](https://code.claude.com/docs/en/claude-projects)) | One coordinating conversation plus cloud threads; every thread starts with the project's repos, instructions and memory | No. "A project belongs to one user. You can't share a project or its threads with another user." Pro and Max beta only, not on Team or Enterprise yet |
| Project coordinator conversation | Plans and starts threads | Has no connectors, so Linear work must be sent to a thread |
| Project memory | Files with a `MEMORY.md` index that each thread reads at start | Per project. Separate from Claude Code's auto memory and from `CLAUDE.md`; a thread run on your PC through Remote Control doesn't get it |
| Cloud threads and sessions ([docs](https://code.claude.com/docs/en/claude-code-on-the-web)) | New branch from main, a PR, then auto-fix on CI failures and review comments | A shared session is a snapshot, not live. No webhook fires when main moves, so a rebase has to be asked for |
| Routines ([docs](https://code.claude.com/docs/en/routines)) | A saved prompt run on a schedule (at most hourly), on GitHub PR or release events, or by an HTTP POST with a bearer token | Belong to one account and act as it. Every event starts a fresh session. API fires are capped at 30 an hour per routine and 100 an hour per account |
| Remote Control ([docs](https://code.claude.com/docs/en/remote-control)) | Drives Claude Code on your own computer; server mode runs up to 32 sessions, each in its own worktree with `--spawn worktree` | One account only. Cross-session messaging covers only your own sessions. The local process has to stay up |
| Agent teams ([docs](https://code.claude.com/docs/en/agent-teams)) | A lead plus teammates with a shared task list and file-locked claims | One local session on one machine, experimental |
| Claude Tag in Slack ([docs](https://claude.com/docs/claude-tag/overview)) | The one first-party product where several people drive one Claude | Team and Enterprise only; not on Pro or Max |
| Linear connector ([docs](https://linear.app/docs/mcp)) | Find, create and update issues and comments | Each account signs in with OAuth on its own. No documented atomic claim or lease |

**Terms.** Free, Pro and Max fall under the [Consumer Terms](https://www.anthropic.com/legal/consumer-terms). They forbid sharing a login or making an account available to anyone else, and accessing the services "through automated or non-human means" unless Anthropic permits it, as it does for routines and cloud sessions. Claude Code's [legal page](https://code.claude.com/docs/en/legal-and-compliance) says the advertised Pro and Max limits "assume ordinary, individual usage", and that no tool may collect or relay claude.ai credentials. A Claude Code team member was quoted saying several Max accounts are not against the terms. In mid-February 2026 users [reported bans](https://metricnexus.ai/blog/anthropic-banning-multiple-claude-accounts) of accounts held alongside other Max accounts; the article's guess, which Anthropic has not confirmed, is that several accounts on one device or IP set off the filter. So: every account signs in itself, only in Anthropic's own apps, and nothing scripts claude.ai.

## Architecture

&#91;embedded content: shared space · 3 accounts, the repo, Linear, the coordinator\]

Each account works through its own Project, and all of them read and write the same two places, the repo and Linear. The coordinator is a routine on your main account, so it acts as that account.

The claim protocol, kept in `docs/agents/PROTOCOL.md`:

1. **Pick** a Todo issue in Linear that `docs/agents/STATE.md` shows as free and unblocked.
2. **Claim** it by pushing a new branch `claude/<issue id>` from main, whose first commit adds `docs/agents/claims/<issue id>.md` with the account, the plan and the files it will touch. If the push is refused because the branch already exists, another account has the issue; pick another.
3. **Announce** it: move the issue to Claimed, add the account's label, and post the same plan as a comment.
4. **Work in the open**: open a draft PR at once, push often, and rebase when the coordinator or the Action asks.
5. **Finish**: the PR deletes its claim file before merging. The merged PR and the Done issue are the shared record of finished work.
6. **Blockers**: a bug that stops everyone becomes an issue labelled blocker, claimed like any other. Nobody else fixes it in parallel.

## Keeping every account's view of the repo current

Stale context comes mostly from long-running threads and local checkouts. Every new cloud thread already starts from a fresh clone of main, so keep each unit of work short: one Linear issue, one branch, one PR.

1. **When main moves, tell the PRs.** GitHub sends no event when main advances and a PR starts to conflict, so auto-fix can't notice on its own. A GitHub Action on every push to main lists the open PRs, and comments "main moved; rebase onto main" on each one that is now out of date or conflicting. Auto-fix sessions act on review comments, so the owning account's session should pick it up. Whether a comment posted by a bot wakes auto-fix is not yet tested.
2. **Refuse stale merges.** Turn on "Require branches to be up to date before merging" with a required CI check. GitHub offers protected branches on a private repository only with a paid plan (Pro, Team or Enterprise); on GitHub Free the repository has to be public ([docs](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)).
3. **Read the board before starting.** The rule in `CLAUDE.md`: before any work, `git fetch origin`, read `docs/agents/STATE.md` and the open PRs, and check Linear for the issue's claim. Committed `CLAUDE.md` and `.claude/rules/` reach every cloud session. Because the repo is the Project's only resource, its threads also load the repo's hooks, permission rules and `.mcp.json`, so a `SessionStart` hook in `.claude/settings.json` can run the fetch and print how far behind main the branch is. In a Project with several repos the hooks are not loaded, and the rule has to stay an instruction.
4. **Keep the coordinator's picture in the repo.** After each run it rewrites `docs/agents/STATE.md`: active claims, the files each open PR touches, what merged since the last run, and known conflicts. Each new session reads that one file instead of rebuilding the picture.

## Shared memory

The only memory every account sees is what is committed to the repo, so `docs/memory/` in the repo is the shared memory. Each Project's own memory and each machine's auto memory stay private to that account.

| Kind | Where it lives | Seen by |
| --- | --- | --- |
| Rules and conventions | `CLAUDE.md`, `.claude/rules/*.md` (committed) | Every account, every cloud and local session |
| Shared facts and decisions | `docs/memory/MEMORY.md` index plus one file per fact, pulled in from `CLAUDE.md` with `@docs/memory/MEMORY.md` | Every account |
| Project memory | Each account's own Project | That Project's threads only |
| Auto memory | `~/.claude/projects/<repo>/memory/` on each machine | That machine only; `autoMemoryDirectory` can move it, though [a bug report](https://github.com/anthropics/claude-code/issues/36636) says the setting was not respected |

How writes work without conflicts:

- **One fact per file**, with a name and a one-line description, and the index line beside it. Two accounts adding different facts then touch different files, and only the index can conflict, which is one line each.
- **Memory rides with the work.** A thread adds or corrects a memory file in the same PR as the change it learned from, so the memory merges with the code it describes.
- **The coordinator tidies.** Its hourly run merges duplicate facts, deletes wrong ones, and keeps `MEMORY.md` under the 200 lines or 25 KB that are loaded at start.
- **Your own Project points at it.** Your main Project's instructions say that `docs/memory/` is the shared memory, and that a fact worth keeping goes there by PR rather than only into Project memory. Nothing can write into another account's Project memory.

## Step-by-step setup

1. **Export and fill the repo.** Export the Project with cswap. In a new repository put the Project's files at the top, its instructions as `CLAUDE.md`, the exported `Memory/` folder as `docs/memory/` with a `MEMORY.md` index, and the transcripts under `docs/history/`.
2. **Add the coordination files.** `docs/agents/PROTOCOL.md` (the claim rules in section 3), `docs/agents/STATE.md` (written by the coordinator), and a `CLAUDE.md` rule to read both before any work.
3. **Protect main.** Require a PR, a green CI check, and branches up to date before merging. On a private repo this needs a paid GitHub plan (section 4).
4. **Install the Claude GitHub App** on the repository. Every Project thread needs it on each repo it clones.
5. **Set up Linear.** Make a team with the states Todo, Claimed, In review and Done, and a label for each Claude account. Add the Linear connector to every Claude account (Settings, Connectors).
6. **Make the main Project.** On your main account, a new Project with this repository as its only resource, and instructions that point at `docs/agents/PROTOCOL.md` and `docs/memory/`.
7. **Make the coordinator routine** on the same account. Triggers: GitHub pull request events on this repo, an API trigger, and an hourly schedule. Its prompt: read `STATE.md`, Linear and the open PRs; split new requests into issues; release claims with no commit for 24 hours; flag two PRs touching the same files; rewrite `STATE.md`; tidy `docs/memory/`.
8. **Add the GitHub Action.** On every push to main it comments on out-of-date PRs, then fires the coordinator routine through its API trigger. The routine's token is stored as a repository secret.
9. **Add the other accounts one at a time.** Each signs in itself, makes its own Project on the same repo with the same instructions, and adds the Linear connector. Start with two accounts and add a third only when Linear has more independent issues than two can take.

## Failure modes

The research on parallel coding agents is sobering. In [CooperBench](https://www.arxiv.org/abs/2601.13295), two agents building separate features in one repo succeeded about 30% less often than one agent doing both. Free-text chat between them cut merge conflicts but did not raise success.

| Failure | What happens | How this design answers it |
| --- | --- | --- |
| Two accounts take the same issue | Duplicate work. Locks alone left 64% duplicates in [one study](https://codex.danielvaughan.com/2026/06/20/before-the-pull-request-multi-agent-coordination-codex-cli-grite-duplicate-work-prevention/); locks plus a shared record of finished work brought it to 0% (synthetic agents, not LLMs) | The branch push is the lock; merged PRs and Done issues are the shared record |
| Two PRs edit the same files | Merge conflicts or overwrites | The claim comment lists the files to be touched before any edit; a plan sent first nearly halved conflicts (29.4% vs 51.5%) in CooperBench. The coordinator flags overlap, and `docs/agents/OWNERSHIP.md` gives areas to accounts |
| A thread dies mid-task | The issue stays Claimed forever; Linear has no lease that expires | The coordinator releases a claim with no commit for 24 hours and leaves a checkpoint comment for the next taker |
| Everyone hits the same blocking bug | All agents fix it at once and overwrite each other, as in [Anthropic's C compiler run](https://www.anthropic.com/engineering/building-c-compiler) | The first account to see it files a blocker issue and claims it; the protocol says to stop and pick other work when a blocker is claimed |
| A long PR goes stale | Conflicts appear late | The Action's rebase comment, plus up-to-date-before-merge |
| Memory drifts or contradicts | Contradictory instructions may be followed arbitrarily | One fact per file, changed by PR, tidied by the coordinator |
| Too many accounts | Gains stop once agents outnumber the tasks that can run in parallel ([CAID](https://hub.openhands.dev/blog/asynchronous-software-engineering-agents)) | Start with two accounts |
| PR events are lost | GitHub events above a routine's hourly caps are dropped, not queued | The coordinator's hourly run rebuilds STATE.md from Linear, the branches and the open PRs, so a missed event is caught within the hour |
| Every account uses one GitHub user | Threads and routines act as the linked GitHub and Linear users, so work from different Claude accounts looks the same | The claim file, the Linear label and the PR description name the Claude account |
| Account enforcement | Possible bans on several accounts used from one device | Section 2: each account signs in itself, only in Anthropic's apps, at ordinary use |

## Sources

All opened on 2026-10-08. The Anthropic pages were each checked by three independent reviewers against the live page.

- [Let Claude coordinate ongoing work with Projects](https://code.claude.com/docs/en/claude-projects) (Claude Code docs)
- [Use Claude Code in the cloud](https://code.claude.com/docs/en/claude-code-on-the-web) (Claude Code docs)
- [Automate work with routines](https://code.claude.com/docs/en/routines) (Claude Code docs)
- [Remote Control](https://code.claude.com/docs/en/remote-control) (Claude Code docs)
- [Agent teams](https://code.claude.com/docs/en/agent-teams) (Claude Code docs)
- [How Claude remembers your project](https://code.claude.com/docs/en/memory) (Claude Code docs)
- [Cloud environments](https://code.claude.com/docs/en/cloud-environments) and [settings](https://code.claude.com/docs/en/settings) (Claude Code docs)
- [Legal and compliance](https://code.claude.com/docs/en/legal-and-compliance) (Claude Code docs) and the [Consumer Terms](https://www.anthropic.com/legal/consumer-terms)
- [Claude Tag overview](https://claude.com/docs/claude-tag/overview)
- [Building a C compiler with a team of parallel Claudes](https://www.anthropic.com/engineering/building-c-compiler) (Anthropic Engineering)
- [Linear MCP server](https://linear.app/docs/mcp), [Linear agents](https://linear.app/developers/agents)
- [Claude Code feature request: assign Linear issues to Claude Code](https://claudeissues.com/issue/12925-linear-integration-assign-issues-to-claude-code-to-trigger-cloud-agent-sessions)
- [CooperBench](https://www.arxiv.org/abs/2601.13295) (ICLR 2026)
- [CAID, OpenHands](https://hub.openhands.dev/blog/asynchronous-software-engineering-agents)
- [Before the pull request: duplicate-work prevention](https://codex.danielvaughan.com/2026/06/20/before-the-pull-request-multi-agent-coordination-codex-cli-grite-duplicate-work-prevention/) (summary of Sarkar, arXiv:2606.19616)
- [Why AI coding agents need work attempts, leases and checkpoints](https://dev.to/odrin/why-ai-coding-agents-need-work-attempts-leases-and-checkpoints-53k4)
- [MCP Agent Mail](https://github.com/Dicklesworthstone/mcp_agent_mail)
- [Anthropic banning multiple Claude accounts: what we know](https://metricnexus.ai/blog/anthropic-banning-multiple-claude-accounts) (third-party report, not confirmed by Anthropic)
- [About protected branches](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches) (GitHub docs)
