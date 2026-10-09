# Making the thin Project for an account

A claude.ai Project belongs to one account. Each account that works here makes its own Project on this same repository. The Projects are thin on purpose: a link to the repository and a few lines of instructions that say to read CLAUDE.md, nothing more. Everything else, the goal, the memory, the board, the rules, lives in the repository, so every account's Project sees the same thing and nothing is copied between them.

## One click: import the repository as the Project

The repository is a cswap project export. export.json at its root describes it in the format cswap (claude-swap-cloud on PyPI) imports; tools/project_export.py writes that file from the repository's own files and scripts/check.sh keeps it current. cswap's import runs in your own browser, signed in as the account, on one click, and nothing is typed to Claude; the import is cswap's own and unchanged, and the repository only carries the manifest it reads. Clone the repository, then take one of these routes:

- With cswap's Chrome extension: on claude.ai, open the side panel, press Import, and open the clone's export.json (or the clone's folder) in the Open window.
- Without the extension: `cswap project-move import` copies the import script to the clipboard; paste it into the console of a claude.ai tab (F12, Console) and choose the clone's folder when its button asks.
- Unattended: `cswap project-move auto --export <the clone> --to <the account's number in cswap list>`.

The import creates a private Project named after the repository and places into it: the description, from the Goal paragraph of docs/project.md (README.md's opening while the goal is unwritten); the instructions, the pointer text below; the memory, one entry per file under docs/memory/ at the same name, MEMORY.md and one file per fact, the way a Project keeps its memory (when memory is off in the account's claude.ai settings, the files go to carried-memory/ among the Project's files instead, and the import says so); and {{REPO}} as the Project's linked repository, which its threads clone only with GitHub connected in the account. It pauses the Project when it is done, so that its Claude starts nothing until you open it and press Resume. To set up a Project you already made, give that Project's address (claude.ai/code/project/...) instead of a name when the import asks: what the Project already holds is left as it is, and the rest is added. After the goal, the pointer text or a memory file changes, `python3 tools/project_export.py` rewrites export.json (the remember skill does it), and importing again into the same Project brings it up to date; a memory entry already there at the same path is never overwritten.

Projects are in public beta on Pro and Max plans and are reaching accounts gradually; Team and Enterprise plans do not have them yet. If Projects is missing from the sidebar at claude.ai/code, the rollout has not reached the account.

## What no import places

The worker routine (docs/agents/routines/worker.md) is made in the Project itself: no import makes a routine. Without cswap, a Project linked to the repository is set up through a thread instead: the Project's own Claude usually starts one when a repository is linked (its usual pattern, not a rule; if none comes within a few minutes, start one with any message), and that thread, reading CLAUDE.md, runs the bootstrap skill (.claude/skills/bootstrap), which has the Project's Claude offer the instructions, the memory and the worker routine as one card, applied on your tap. The steps below are the same work by hand. The Project's own memory is private to its account and takes entries only when memory is on in the account's settings; the template needs neither, since a fact worth keeping goes to docs/memory/ by pull request (.claude/skills/remember).

## By hand, once per account

1. Install the Claude GitHub App on the repository if docs/setup/github.md has not been done yet; every thread of the Project needs it. The installation starts from claude.ai/code: when you link the repository in step 2, Claude sends you to GitHub to install the app and pick this repository.
2. In claude.ai, make a new Project and link the repository {{REPO}}. Make the repository the Project's only resource: a thread then starts from a fresh clone of {{DEFAULT_BRANCH}}, reads CLAUDE.md and is shown the board at the start of every session. (The import of export.json does this step and the next two for you.)
3. Paste the pointer text below into the Project's instructions, as it stands.
4. Choose the model and effort for this project if docs/project.md does not record them yet, set them in the Project's settings (General), and record the choice in docs/project.md under "Model and effort" by pull request, so every later Project copies it from there.
5. Name the Project after the repository and the account, so an account with several Projects tells them apart.

## The pointer text

```
This Project works on {{REPO}}. Read CLAUDE.md first. The shared memory is docs/memory/ (read MEMORY.md); the board is the file STATE.md on the branch board, read with: git fetch origin board && git show origin/board:STATE.md; work is claimed as docs/agents/PROTOCOL.md says: one issue, one branch claude/<issue>, one pull request. A fact worth keeping goes to docs/memory/ by pull request, not only into this Project's memory.
```

## The main account

The account that runs the routines (the worker, docs/agents/routines/worker.md, and the coordinator (docs/agents/routines/coordinator.md) is the main account, labelled account:main on GitHub. Its routine is made inside its Project: paste the prompt into the Project's own conversation and ask for the schedule, rather than making it on the routines page, so the routine runs as threads of the Project and shows on its Routines tab. Any other account gets a label of its own (docs/setup/github.md, Labels) and a row in docs/agents/OWNERSHIP.md; its Project is made the same way.
