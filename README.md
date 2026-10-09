# {{PROJECT_NAME}}

This repository is a Claude project kept as files: the instructions, the goal, the shared memory and the board that Claude Code reads in every session, local or cloud, live here under version control. It came from a GitHub template that brings the folder structure, the checks and the workflows already set up, so a new project starts with the whole arrangement in place. Each Claude account links this repository to a claude.ai Project of its own, and the repository sets that Project up: its first thread composes the Project's instructions, memory and worker routine from the files here (.claude/skills/bootstrap) and the Project offers them as one card, applied on one tap, and from then on the repository is the one place every account and every session agrees on.

## Use this template

About ten minutes, in this order.

1. Press "Use this template" on the template's GitHub page, name the new repository and choose where it lives. A public repository can protect its default branch on GitHub Free; a private one needs a paid plan for that (docs/setup/github.md says more).
2. Wait for the issue "Set up this project" to appear on the new repository. The first push runs .github/workflows/template-init.yml, which fills the names into every file except the workflows, creates the labels and opens that issue; it lists what is left to do by hand, and you close it when you are done. If the issue has not appeared after a few minutes, open the repository's Actions tab. When the run failed or Actions are off, do it by hand: clone, run `GITHUB_TOKEN=$(gh auth token) python3 tools/template_init.py --repo OWNER/NAME --default-branch main --create-labels --open-issue`, commit everything it changed and push.
3. Protect the default branch and install the Claude GitHub App on the repository, as docs/setup/github.md describes. Every Claude Code thread that works here needs the app.
4. Make a claude.ai Project per Claude account and link this repository as its only resource. The Project's page shows nothing new, because the goal, the memory and the board are read from the repository inside every thread. The Project's Claude usually starts a first thread when a repository is linked (its usual pattern, not a rule; if none comes, start one with any message); that thread composes the Project's instructions, memory and worker routine from the files, as .claude/skills/bootstrap says, and the Project's chat shows one card: tap Apply, and it is set up. That tap is the one thing a person does besides linking, because a Project's settings change only with the person's word. docs/setup/claude-project.md has the same steps by hand for when that thread could not. Projects are in public beta on Pro and Max plans and are reaching accounts gradually; Team and Enterprise plans do not have them yet.
5. When a second account joins, make the coordinator routine in the main account's Project (docs/agents/routines/coordinator.md), which tidies claims and memory between accounts. The worker routine (docs/agents/routines/worker.md), which every hour takes the next issue from the board and carries it to a pull request, is made by step 4.

Then open an issue with the Task form (the repository's Issues tab, New issue, Task), which carries the label todo. The worker routine takes it at its next run, within the hour.

For the maintainer of the template itself: mark the repository as a template (Settings, General, "Template repository") before its first push, or the init workflow runs on the template and fills its own placeholders.

## Where a Project's metadata lives

| In the Project | In this repository | Placed into the Project when it is linked |
| --- | --- | --- |
| Instructions | `CLAUDE.md` and `.claude/rules/` | the pointer text of `docs/setup/claude-project.md`, as the Project's instructions |
| Goal and settings | `docs/project.md` | its Goal paragraph, as a line inside the Project's instructions (no tool writes a Project's description) |
| Shared memory | `docs/memory/` | one memory entry per file, under the same path, when memory is on in the account's settings |
| The board | the branch `board`, file `STATE.md`; `docs/agents/STATE.md` on {{DEFAULT_BRANCH}} describes it | read inside every thread |
| Claims | the branch `claude/<issue>` and `docs/agents/claims/` | read inside every thread |
| Routines | `docs/agents/routines/` | the worker routine, hourly |
| History | `docs/history/` (later) | |
| Skills | `.claude/skills/` | read inside every thread |
| Checks | `scripts/check.sh` | |

The first thread of a Project composes the right-hand column from the files and the Project applies it on one tap (.claude/skills/bootstrap); claude.ai itself copies nothing from a linked repository, and everything in the middle column is read from the repository inside every thread whether or not it was placed. The Project's own memory stays private to the account that made the Project; what every account should know goes to docs/memory/ by pull request.

cswap is the optional multi-account switcher (claude-swap-cloud on PyPI); its `checkpoint write` rewrites the same block at the end of CLAUDE.md as the checkpoint skill does, and nothing in this repository needs it.

## What comes next

This is the first layer: the repository as the shared plane, with the board, the claim protocol and the memory as plain files. Nothing below exists yet, and nothing in this layer refers to it.

- Layer 2 adds tools/materialize.py and .github/workflows/materialize.yml, which turn a cswap export or a routine's export branch into CLAUDE.md, docs/memory/ and docs/history/.
- Layer 3 adds Linear as the queue (the labels map to Linear states) and, for a repository whose owner accepts an API key there, claude-code-action; this repository stays without one.
- Layer 4 adds cswap teleport --checkpoint between accounts.

## What this never does

- Nothing here scripts claude.ai. Anthropic's consumer terms forbid automated access except through an API key or where Anthropic explicitly permits it; routines and cloud threads are Anthropic's own features, used as offered, and Claude Code reads the repository natively. The Project links the repository, and people press the buttons.
- No credential and no token is kept in the repository. The workflows run on GitHub's own token; the one optional pair of secrets is the coordinator routine's trigger, kept in the repository's settings and never in a file (docs/setup/github.md).
- No API key anywhere.
