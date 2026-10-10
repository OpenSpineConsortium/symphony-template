# {{PROJECT_NAME}}: goal and settings

This file is the project's goal and the settings every account's thin Project shares. It is the one place where the goal is written: CLAUDE.md imports this file into every session, and the claude.ai Projects carry no copy of it. It changes by pull request like everything else.

## Goal

Not yet written. One paragraph: what this project makes, for whom, and what done looks like. The owner writes it, or asks a session to, when ticking the "Set up this project" issue's box for this file, and merges it by pull request.

## Scope

In scope: the areas this project owns, each in one line; docs/agents/OWNERSHIP.md maps them to accounts.

Out of scope, by decision: what this project does not do, each with the reason, so nobody proposes it again.

## Repositories

- {{REPO}}, this one: the shared plane for every account and every session; the default branch is {{DEFAULT_BRANCH}}.
- Other repositories this project reads or uses, four, each owned by the OpenSpineConsortium organization, whose owners merge to its default branch:
  - OpenSpineConsortium/sdlc-protocol, public: the claim protocol as a Python library with no dependencies (the board, the protocol check, team mode's clerk, the push guard's rules and the merge gate). It is vendored here under tools/sdlc_protocol, with tools/VENDORED naming the release and its commit; a change to the rules is made there and comes in by its scripts/vendor.sh and a pull request here.
  - OpenSpineConsortium/coordbench, public: the playground and benchmark that compares ways of coordinating Claude Code agents on CooperBench's tasks, this protocol among them; its sdlc arm is to run on the library's merge gate. It began as experiment/ on OpenSpineConsortium/sdlc-template's branch claude/10.
  - OpenSpineConsortium/sdlc-marketplace, public: the Claude Code plugin marketplace with one plugin, sdlc, which brings the skills, /board and the hooks to a repository not made from this template. .claude/settings.json names the marketplace and enables nothing, since this repository wires the same hooks itself.
  - OpenSpineConsortium/sdlc-app, private: the GitHub App sdlc. Its installation token lets template-init's first commit start the Checks and the Board, which a push with GITHUB_TOKEN cannot; later its webhook server runs the protocol check as a check run of its own.

## Model and effort

Every account's Project uses the same model and the same effort, so the work reads the same whoever did it. Record the choice here and set it in each Project's settings when you make the Project (docs/setup/claude-project.md).

- Model: not yet chosen.
- Effort: not yet chosen.

## Owners

- Repository owner: {{OWNER}}, who merges to {{DEFAULT_BRANCH}}; .github/CODEOWNERS names the same login.
- Main Claude account: the first account, whose Project runs the worker routine (docs/agents/routines/worker.md) and, once a second account joins, the coordinator (docs/agents/routines/coordinator.md); its label is account:main.
- Other accounts: none yet. Each gets a label of its own (docs/setup/github.md, Labels) and a row in docs/agents/OWNERSHIP.md.
