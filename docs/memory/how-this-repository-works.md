The repository is the shared plane for every Claude account and every session: what lives where.

A claude.ai Project belongs to one account, and its memory is private to that account. This project therefore keeps everything that more than one account or session needs in this repository, which every account's Project links and every session clones:

- CLAUDE.md and .claude/rules/: the instructions, read by Claude Code at the start of every session, local or cloud. CLAUDE.md imports docs/project.md, docs/agents/PROTOCOL.md and docs/memory/MEMORY.md with `@` lines, so the goal, the protocol and the memory index load into every session without being asked for.
- docs/project.md: the goal, the scope, the repositories, the model and effort, the owners.
- docs/memory/: the shared memory, one fact per file, with the index in MEMORY.md.
- The board: the file STATE.md on the branch `board`, rewritten by .github/workflows/board.yml from the open issues, the `claude/<issue>` branches, the claim files and the pull requests, and never edited by hand. Read it with `git fetch origin board && git show origin/board:STATE.md`, which the session hook does at the start of every session; docs/agents/STATE.md on the default branch only describes its layout.
- docs/agents/PROTOCOL.md: how an issue is claimed (the first push of the branch `claude/<issue>`), worked in the open and finished.
- docs/agents/claims/: one file per claimed issue while it is claimed; the pull request that finishes the issue deletes it.
- docs/agents/OWNERSHIP.md: which account owns which area.
- docs/agents/routines/worker.md: the prompt of the routine each working account runs in its Project, which takes the next issue from the board and carries it to a pull request.
- docs/agents/TEAM.md: team mode, a lead that plans an epic into tasks pre-assigned to members working in parallel, run by .github/workflows/claude-lead.yml and claude-worker.yml with tools/team.py doing the clerical steps.
- docs/agents/routines/coordinator.md: the prompt of the routine the main account runs once a second account joins, which keeps the queue, the claims and the memory tidy.
- docs/history/: the longer records; today its README and the research behind the split into five repositories.
- .claude/skills/: the three procedures, claim, remember and checkpoint.
- .claude/settings.json, .claude/hooks/ and .claude/commands/: the session hook that prints the board, the push guard that refuses a push the board rules forbid (tools/guard_push.py), the edit check that runs the document checks the moment an instruction or memory file changes (tools/check_edit.py), the shared permission allowlist, and /board, which reprints the whole board mid-session.
- docs/setup/: github.md, what a person with the repository's settings does once, with ruleset-main.json, the default branch's rules as a file to import; claude-project.md, how each account makes its thin Project with blank fields; claude-action.md, how the main account turns on @claude in issues and pull requests; and tiers.md, what each GitHub and Claude plan unlocks here.
- scripts/check.sh and tools/: the checks CI runs as "check", the claim-protocol check CI adds on a claude/ pull request, the board's renderer, the hooks' push guard and edit check, the template's one-time initialiser and the marker-section helper the checkpoint skill uses.
- tools/sdlc_protocol: the claim protocol's code, vendored from OpenSpineConsortium/sdlc-protocol, which tools/board.py, check_protocol.py, team.py and guard_push.py hand their arguments to. tools/VENDORED records the release, the commit and the sha256 of every copied file, scripts/check.sh fails when the copy differs from it, and tests/test_vendored.py also holds the copy to the library's files at that commit when a clone of the library is beside this repository. A change to the rules is made in that repository, never edited in place: its sync pull request brings it to OpenSpineConsortium/sdlc-template, and a repository made from the template vendors it by hand (protocol-changes-come-from-sdlc-protocol.md).

The claude.ai Project is thin on purpose: it links the repository, its instructions, description and memory stay blank (the pointer text only for chats outside code sessions), nothing is copied into it, and nothing scripts it; a thread of a Project and a cloud session opened on the repository load the same files. Nothing in this repository holds a credential or a token, and no API key is used anywhere; when @claude is turned on, its workflow runs on the main account's subscription token, held in the repository's Actions secrets, never in a file (docs/setup/claude-action.md).

Source: the template this repository was made from, its first layer.
