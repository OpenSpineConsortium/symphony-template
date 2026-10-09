# Making the thin Project for an account

A claude.ai Project belongs to one account. Each account that works here makes its own Project on this same repository. The Projects are thin on purpose: a link to the repository and a few lines of instructions that say to read CLAUDE.md, nothing more. Everything else, the goal, the memory, the board, the rules, lives in the repository, so every account's Project sees the same thing and nothing is copied between them. The Project's own memory is private to its account, and it is written only when memory is turned on in the account's claude.ai settings; the template needs neither, since a fact worth keeping goes to docs/memory/ by pull request (.claude/skills/remember).

Projects are in public beta on Pro and Max plans and are reaching accounts gradually; Team and Enterprise plans do not have them yet. If Projects is missing from the sidebar at claude.ai/code, the rollout has not reached the account.

## Steps, once per account

1. Install the Claude GitHub App on the repository if docs/setup/github.md has not been done yet; every thread of the Project needs it. The installation starts from claude.ai/code: when you link the repository in step 2, Claude sends you to GitHub to install the app and pick this repository.
2. In claude.ai, make a new Project and link the repository {{REPO}}. Make the repository the Project's only resource: a thread then starts from a fresh clone of {{DEFAULT_BRANCH}}, reads CLAUDE.md and is shown the board at the start of every session.
3. Paste the pointer text below into the Project's instructions, as it stands. Or type in the Project's chat "Set this Project's instructions from docs/setup/claude-project.md in the repository": the Project's own Claude reads this page and writes them. Nothing else happens when a repository is linked; the Project's page stays as it was, because the goal, the memory and the board are read from the repository inside every thread, not copied into the Project.
4. Choose the model and effort for this project if docs/project.md does not record them yet, set them in the Project's settings (General), and record the choice in docs/project.md under "Model and effort" by pull request, so every later Project copies it from there.
5. Name the Project after the repository and the account, so an account with several Projects tells them apart.

## The pointer text

```
This Project works on {{REPO}}. Read CLAUDE.md first. The shared memory is docs/memory/ (read MEMORY.md); the board is the file STATE.md on the branch board, read with: git fetch origin board && git show origin/board:STATE.md; work is claimed as docs/agents/PROTOCOL.md says: one issue, one branch claude/<issue>, one pull request. A fact worth keeping goes to docs/memory/ by pull request, not only into this Project's memory.
```

## The main account

The account that runs the routines (the worker, docs/agents/routines/worker.md, and the coordinator (docs/agents/routines/coordinator.md) is the main account, labelled account:main on GitHub. Its routine is made inside its Project: paste the prompt into the Project's own conversation and ask for the schedule, rather than making it on the routines page, so the routine runs as threads of the Project and shows on its Routines tab. Any other account gets a label of its own (docs/setup/github.md, Labels) and a row in docs/agents/OWNERSHIP.md; its Project is made the same way.
