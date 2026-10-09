# {{PROJECT_NAME}}

This repository is a Claude project kept as files: the instructions, the goal, the shared memory and the board that Claude Code reads in every session, local or cloud, live here under version control. It came from a GitHub template that brings the folder structure, the checks and the workflows already set up, so a new project starts with the whole arrangement in place. Each Claude account sets up a claude.ai Project from this repository with one click and no Claude prompt: the repository carries export.json, which describes it as a cswap project export, and cswap's import, run in the person's own browser, makes the Project with its description, its instructions, its memory and this repository linked. From then on the repository is the one place every account and every session agrees on.

## Use this template

About ten minutes, in this order.

1. Press "Use this template" on the template's GitHub page, name the new repository and choose where it lives. A public repository can protect its default branch on GitHub Free; a private one needs a paid plan for that (docs/setup/github.md says more).
2. Wait for the issue "Set up this project" to appear on the new repository. The first push runs .github/workflows/template-init.yml, which fills the names into every file except the workflows, creates the labels and opens that issue; it lists what is left to do by hand, and you close it when you are done. If the issue has not appeared after a few minutes, open the repository's Actions tab. When the run failed or Actions are off, do it by hand: clone, run `GITHUB_TOKEN=$(gh auth token) python3 tools/template_init.py --repo OWNER/NAME --default-branch main --create-labels --open-issue`, commit everything it changed and push.
3. Protect the default branch and install the Claude GitHub App on the repository, as docs/setup/github.md describes. Every Claude Code thread that works here needs the app.
4. Set up a claude.ai Project per Claude account from the repository, with cswap (claude-swap-cloud on PyPI) and no Claude prompt: clone the repository, then on claude.ai press Import in cswap's side panel and open the clone's export.json in the Open window; or paste the import script that `cswap project-move import` copies into the tab's console and choose the clone; or run `cswap project-move auto --export <the clone> --to <account>`. The import creates a private Project named after the repository, with the Goal of docs/project.md as its description, the pointer text as its instructions, one memory entry per file under docs/memory/, and this repository linked; it pauses the Project at the end, so open it and press Resume. To set up a Project you already made, give its address (claude.ai/code/project/...) as the name when the import asks. docs/setup/claude-project.md has the detail, what to do without cswap, and the same steps by hand. Projects are in public beta on Pro and Max plans and are reaching accounts gradually; Team and Enterprise plans do not have them yet.
5. Make the worker routine in the Project (docs/agents/routines/worker.md), which every hour takes the next issue from the board and carries it to a pull request: no import makes a routine, so this is the one setup step done in the Project itself. When a second account joins, make the coordinator routine in the main account's Project (docs/agents/routines/coordinator.md), which tidies claims and memory between accounts.

Then open an issue with the Task form (the repository's Issues tab, New issue, Task), which carries the label todo. The worker routine takes it at its next run, within the hour.

For the maintainer of the template itself: mark the repository as a template (Settings, General, "Template repository") before its first push, or the init workflow runs on the template and fills its own placeholders.

## Where a Project's metadata lives

| In the Project | In this repository | Placed by the import of export.json |
| --- | --- | --- |
| Instructions | `CLAUDE.md` and `.claude/rules/` | the pointer text of `docs/setup/claude-project.md` |
| Description | `docs/project.md` | its Goal paragraph |
| Memory | `docs/memory/` | one entry per file, under the same name (`carried-memory/` among the Project's files when memory is off in the account) |
| Linked repository | this repository | linked |
| The board | the branch `board`, file `STATE.md`; `docs/agents/STATE.md` on {{DEFAULT_BRANCH}} describes it | read inside every thread |
| Claims | the branch `claude/<issue>` and `docs/agents/claims/` | read inside every thread |
| Routines | `docs/agents/routines/` | not placed: a routine is made in the Project |
| History | `docs/history/` (later) | |
| Skills | `.claude/skills/` | read inside every thread |
| Checks | `scripts/check.sh` | |

tools/project_export.py writes the right-hand column into export.json, in the format cswap's import reads (the repository's own files are the export, so nothing is copied), and `bash scripts/check.sh` fails when that file is out of date with them. claude.ai itself copies nothing from a linked repository, and everything in the middle column is read from the repository inside every thread whether or not it was placed. The Project's own memory stays private to the account that made the Project; what every account should know goes to docs/memory/ by pull request.

cswap is the multi-account switcher (claude-swap-cloud on PyPI) whose import sets the Project up; its `checkpoint write` also rewrites the same block at the end of CLAUDE.md as the checkpoint skill does. Nothing in this repository needs it to work: without it, the bootstrap skill (.claude/skills/bootstrap) sets a Project up through one card in the Project's chat, and docs/setup/claude-project.md has the steps by hand.

## What comes next

This is the first layer: the repository as the shared plane, with the board, the claim protocol and the memory as plain files. Nothing below exists yet, and nothing in this layer refers to it.

- Layer 2 adds tools/materialize.py and .github/workflows/materialize.yml, which turn a cswap export or a routine's export branch into CLAUDE.md, docs/memory/ and docs/history/.
- Layer 3 adds Linear as the queue (the labels map to Linear states) and, for a repository whose owner accepts an API key there, claude-code-action; this repository stays without one.
- Layer 4 adds cswap teleport --checkpoint between accounts.

## What this never does

- Nothing here runs against claude.ai on its own. Anthropic's consumer terms forbid automated access except through an API key or where Anthropic explicitly permits it; routines and cloud threads are Anthropic's own features, used as offered, and Claude Code reads the repository natively. The one program that writes into a Project is cswap's import, which the person runs in their own browser, signed in, on one click; export.json is the data it reads, and this repository carries no code that runs there.
- No credential and no token is kept in the repository. The workflows run on GitHub's own token; the one optional pair of secrets is the coordinator routine's trigger, kept in the repository's settings and never in a file (docs/setup/github.md).
- No API key anywhere.
