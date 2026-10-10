# {{PROJECT_NAME}}

This repository is a Claude project kept as files: the instructions, the goal, the shared memory and the board that Claude Code reads in every session, local or cloud, live here under version control. It came from a GitHub template that brings the folder structure, the checks and the workflows already set up, so a new project starts with the whole arrangement in place. Each Claude account makes a thin claude.ai Project that only links this repository, with its instructions, description and memory left blank, because every session loads the goal, the protocol and the memory from the files here; from then on the repository is the one place every account and every session agrees on.

## Use this template

About ten minutes, in this order.

1. Press "Use this template" on the template's GitHub page, name the new repository and choose where it lives. A public repository can protect its default branch on GitHub Free; a private one needs a paid plan for that. docs/setup/tiers.md lays out what each GitHub and Claude plan actually unlocks here, with the three spending profiles; docs/setup/github.md has the settings themselves.
2. Wait for the issue "Set up this project" to appear on the new repository. The first push runs .github/workflows/template-init.yml, which fills the names into every file except the workflows, creates the labels and opens that issue; it lists what is left to do by hand, and you close it when you are done. If the issue has not appeared after a few minutes, open the repository's Actions tab. When the run failed or Actions are off, do it by hand: clone, run `GITHUB_TOKEN=$(gh auth token) python3 tools/template_init.py --repo OWNER/NAME --default-branch main --create-labels --open-issue`, commit everything it changed and push.
3. Two one-step moves, as docs/setup/github.md describes: import the shipped branch rules (Settings, Rules, Import a ruleset, docs/setup/ruleset-main.json), and run `/install-github-app` from Claude Code as the main account, whose one OAuth flow installs the Claude GitHub App and writes the @claude secret. Every Claude Code thread that works here needs the app.
4. Make one thin Project per Claude account, link this repository as its only resource, and leave its instructions, description and memory blank. Every Claude Code session, a thread of the Project or a cloud session opened on the repository alike, starts from a fresh clone and loads CLAUDE.md with what it imports (the goal, the protocol, the memory index), the rules, the skills and the board, so blank fields lose nothing, and a merged pull request changes what every account's sessions read at once. Only if people will also chat in the Project outside a code session, paste the pointer text from docs/setup/claude-project.md into the instructions, once: a chat has no clone, and the pointer never changes. Projects are in public beta on Pro and Max plans and are reaching accounts gradually; Team and Enterprise plans do not have them yet.
5. Make the routines in the Project, by asking for the scheduled work in the Project's own conversation: in each working account's Project the worker (docs/agents/routines/worker.md), which every hour takes the next issue from the board and carries it to a pull request, so nobody starts threads by hand (or, in its place, a team that runs from Actions: a lead that plans an epic into pre-assigned tasks and members that work them in parallel, switched on by the repository variables CLAUDE_TEAM and CLAUDE_WORKER, docs/agents/TEAM.md and docs/setup/claude-action.md); and in the main account's Project the coordinator (docs/agents/routines/coordinator.md), which tidies claims and memory, once a second account joins.

Then open an issue with the Task form (the repository's Issues tab, New issue, Task), which carries the label todo. The worker routine takes it at its next run; to have it taken now, start a thread in the Project with "take the next issue from the board" (a thread clones the repository and reads the board; a plain chat in the Project knows only the pointer text of step 4).

To open the project to volunteers who each work under their own Claude Pro or Max account, docs/setup/crowdsourcing.md is the step-by-step for the owner and for each contributor, and docs/history/crowdsourcing/research.md the evidence behind every step. It starts from what Anthropic's terms allow with contributors' accounts, and it turns off the workflows that run on the owner's own subscription token, which anyone with write access could otherwise start.

For the maintainer of the template itself: mark the repository as a template (Settings, General, "Template repository") before its first push, or the init workflow runs on the template and fills its own placeholders.

## Where a Project's metadata lives

| In the Project | In this repository | How a session gets it |
| --- | --- | --- |
| Instructions | `CLAUDE.md` and `.claude/rules/` | read by Claude Code at the start of every session; the Project's instructions stay blank, or hold the pointer text for chats outside code sessions |
| Goal and settings | `docs/project.md` | imported by CLAUDE.md into every session; the Project's description stays blank |
| Shared memory | `docs/memory/` | the index imported by CLAUDE.md, a fact's file read when its line says it matters; the Project's own memory stays blank |
| The board | the branch `board`, file `STATE.md`; `docs/agents/STATE.md` on {{DEFAULT_BRANCH}} describes it | fetched and printed by the session hook, since no import reaches another branch |
| Claims | the branch `claude/<issue>` and `docs/agents/claims/` | read in the clone |
| History | `docs/history/` (later) | |
| Skills | `.claude/skills/` | read by Claude Code |
| Checks | `scripts/check.sh` | |

Nothing is copied from the repository into the Project's own fields, and nothing needs to be. Linking a repository to a Project is a pointer: it tells threads what to clone, and claude.ai reads nothing from the clone into the Project's instructions, description or memory. Claude Code, on the other hand, assembles every session's context from the clone, identically for a thread of a Project and for a cloud session opened on the repository, so the repository already enforces what a copy in the Project's fields would only approximate: one text for every account, changed by one merged pull request, with no per-account credential anywhere. A copy in the fields would go stale between syncs and differ quietly from one account to the next. The Project's own memory is at most a private cache of the account that made the Project; what every account should know goes to docs/memory/ by pull request.

## Where this repository fits

OpenSpineConsortium/sdlc-template, the template, is one of five repositories that share the claim protocol, and a repository made from it carries the same copy of the protocol's code. [ECOSYSTEM.md](https://github.com/OpenSpineConsortium/sdlc-protocol/blob/main/ECOSYSTEM.md) in sdlc-protocol maps them: what each repository is, which of the library's modules each one copies and what it uses them for, how the modules import each other, and how a change travels from a pull request there to a pull request here. It is generated from that repository's ecosystem.json, the one list of who takes what, and its check fails when the map falls behind.

## Where the protocol's code lives

The claim protocol's code is a library of its own, OpenSpineConsortium/sdlc-protocol, vendored here under tools/sdlc_protocol. tools/VENDORED records what the copy is: the release and the commit on its first line, then the sha256 of every copied file. tools/board.py, check_protocol.py, team.py and guard_push.py are shims over it, so the workflows, the hook and every copy already made keep calling the same paths.

A change to the protocol is made in sdlc-protocol, never in tools/sdlc_protocol. When it merges there, that repository's sync workflow vendors it into this one and opens the pull request from the branch `sdlc-protocol/sync`, or updates the one already open, with a body that lists the library's commits and the files that moved; this repository's own check decides, and where the repository allows auto-merge, the pull request lands once the check is green (docs/setup/owner-checklist.md, section 6). scripts/check.sh runs `python3 tools/sdlc_protocol/vendoring.py verify tools`, so a pull request that edits the copy by hand and leaves tools/VENDORED alone fails the required check, offline. One that also rewrites the file's line in VENDORED, which sits in the same tree, fails it too: CI clones sdlc-protocol and names the clone in SDLC_PROTOCOL, and tests/test_vendored.py then compares every file of the copy with the library's at the commit VENDORED names, failing when the clone has no such commit. To vendor by hand, from a clone of sdlc-protocol beside this one: `python3 <sdlc-protocol>/scripts/vendor.py <this repository>`, then land the change by pull request.

A repository made from this template takes the copy with it but is not on the sync's list, so no pull request reaches it by itself: its owner brings a new release in by hand with `python3 <sdlc-protocol>/scripts/vendor.py <the copy> --consumer OpenSpineConsortium/sdlc-template`, which copies what the template takes.

Three more repositories go with this one: OpenSpineConsortium/coordbench, the benchmark that compares ways of coordinating agents; OpenSpineConsortium/sdlc-marketplace, the Claude Code plugin that brings the skills and the hooks to a repository not made from this template; and sdlc-app, the private GitHub App whose token lets template-init's first commit start the Checks and the Board, and in whose name the sync opens its pull requests. docs/project.md says what each is for and who owns it.

cswap is the optional multi-account switcher (claude-swap-cloud on PyPI); its `checkpoint write` rewrites the same block at the end of CLAUDE.md as the checkpoint skill does, and nothing in this repository needs it.

## What comes next

This is the first layer: the repository as the shared plane, with the board, the claim protocol and the memory as plain files. Nothing below exists yet, and nothing in this layer refers to it.

- Layer 2 adds a materialize step that turns a session's checkpoint or a routine's export branch into docs/memory/ and docs/history/ by pull request; CLAUDE.md stays the loader and is never generated.
- Layer 3 adds Linear as the queue (the labels map to Linear states). claude-code-action already runs here on a subscription token (docs/setup/claude-action.md), and the repository stays without an API key.
- Layer 4 adds cswap teleport --checkpoint between accounts.

## What this never does

- Nothing here scripts claude.ai, and nothing writes into a Project's instructions, description or memory. Anthropic's consumer terms forbid automated access except through an API key or where Anthropic explicitly permits it; routines and cloud threads are Anthropic's own features, used as offered, and Claude Code reads the repository natively. The Project links the repository, and people press the buttons.
- No credential and no token is kept in the repository. The workflows run on GitHub's own token, and template-init on the sdlc App's token where the App is set up; the optional secrets are the coordinator routine's trigger pair, the main account's subscription token for @claude (docs/setup/claude-action.md) and the App's private key (docs/setup/owner-checklist.md), kept in the repository's settings and never in a file (docs/setup/github.md).
- No API key anywhere.
