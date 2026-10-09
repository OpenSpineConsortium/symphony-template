# {{PROJECT_NAME}}

This repository is a Claude project kept as files: the instructions, the goal, the shared memory and the board that Claude Code reads in every session, local or cloud, live here under version control. It came from a GitHub template that brings the folder structure, the checks and the workflows already set up, so a new project starts with the whole arrangement in place. Each Claude account makes a thin claude.ai Project that links this repository and reads CLAUDE.md, and from then on the repository is the one place every account and every session agrees on.

## Use this template

About ten minutes, in this order.

1. Press "Use this template" on the template's GitHub page, name the new repository and choose where it lives. A public repository can protect its default branch on GitHub Free; a private one needs a paid plan for that (docs/setup/github.md says more).
2. Wait for the issue "Set up this project" to appear on the new repository. The first push runs .github/workflows/template-init.yml, which fills the names into every file except the workflows, creates the labels and opens that issue; it lists what is left to do by hand, and you close it when you are done. If the issue has not appeared after a few minutes, open the repository's Actions tab. When the run failed or Actions are off, do it by hand: clone, run `GITHUB_TOKEN=$(gh auth token) python3 tools/template_init.py --repo OWNER/NAME --default-branch main --create-labels --open-issue`, commit everything it changed and push.
3. Protect the default branch and install the Claude GitHub App on the repository, as docs/setup/github.md describes. Every Claude Code thread that works here needs the app.
4. Make one thin Project per Claude account, each on this same repository, and paste the pointer text into its instructions, as docs/setup/claude-project.md describes. Projects are in public beta on Pro and Max plans and are reaching accounts gradually; Team and Enterprise plans do not have them yet.
5. Make the coordinator routine in the main account's Project, by asking for the scheduled work in the Project's own conversation, with the prompt and the triggers docs/agents/routines/coordinator.md gives.

Then open an issue with the Task form, which carries the label todo, and the first session can claim it.

For the maintainer of the template itself: mark the repository as a template (Settings, General, "Template repository") before its first push, or the init workflow runs on the template and fills its own placeholders.

## Where a Project's metadata lives

| In the Project | In this repository |
| --- | --- |
| Instructions | `CLAUDE.md` and `.claude/rules/` |
| Goal and settings | `docs/project.md` |
| Shared memory | `docs/memory/` |
| The board | the branch `board`, file `STATE.md`; `docs/agents/STATE.md` on {{DEFAULT_BRANCH}} describes it |
| Claims | the branch `claude/<issue>` and `docs/agents/claims/` |
| History | `docs/history/` (later) |
| Skills | `.claude/skills/` |
| Checks | `scripts/check.sh` |

The Project's own memory stays private to the account that made the Project; what every account should know goes to docs/memory/ by pull request.

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
