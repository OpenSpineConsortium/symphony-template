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
- docs/agents/routines/coordinator.md: the prompt of the routine the main account runs once a second account joins, which keeps the queue, the claims and the memory tidy.
- docs/history/: where longer records will go; today it holds only its README.
- .claude/skills/: the three procedures, claim, remember and checkpoint.
- docs/setup/: github.md, what a person with the repository's settings does once, and claude-project.md, how each account makes its thin Project with blank fields.
- scripts/check.sh and tools/: the checks CI runs as "check", the board's renderer, the template's one-time initialiser and the marker-section helper the checkpoint skill uses.

The claude.ai Project is thin on purpose: it links the repository, its instructions, description and memory stay blank (the pointer text only for chats outside code sessions), nothing is copied into it, and nothing scripts it; a thread of a Project and a cloud session opened on the repository load the same files. Nothing in this repository holds a credential or a token, and no API key is used anywhere.

Source: the template this repository was made from, its first layer.
