# {{PROJECT_NAME}}: goal and settings

This file is the project's goal and the settings every account's thin Project shares. It is the one place where the goal is written; the claude.ai Projects only point here. It changes by pull request like everything else.

## Goal

Not yet written. One paragraph: what this project makes, for whom, and what done looks like. The first session after setup writes it from the "Set up this project" issue, and the owner merges it.

## Scope

In scope: the areas this project owns, each in one line; docs/agents/OWNERSHIP.md maps them to accounts.

Out of scope, by decision: what this project does not do, each with the reason, so nobody proposes it again.

## Repositories

- {{REPO}}, this one: the shared plane for every account and every session; the default branch is {{DEFAULT_BRANCH}}.
- Other repositories this project reads or changes: none yet. Name each with what it is for and who owns it.

## Model and effort

Every account's Project uses the same model and the same effort, so the work reads the same whoever did it. Record the choice here and set it in each Project's settings when you make the Project (docs/setup/claude-project.md).

- Model: not yet chosen.
- Effort: not yet chosen.

## Worker routine

The worker routine (docs/agents/routines/worker.md) is the one part of a Project's setup that no import places: it is made in each account's Project, by hand or by the bootstrap card (.claude/skills/bootstrap), unless the line below says none.

- Worker routine: hourly

## Owners

- Repository owner: {{OWNER}}, who merges to {{DEFAULT_BRANCH}}; .github/CODEOWNERS names the same login.
- Main Claude account: the one whose Project runs the coordinator routine (docs/agents/routines/coordinator.md); its label is account:main.
- Other accounts: none yet. Each gets a label of its own (docs/setup/github.md, Labels) and a row in docs/agents/OWNERSHIP.md.
