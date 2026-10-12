# {{PROJECT_NAME}}: goal and settings

This file is the project's goal and the settings every account's thin Project shares. It is the one place where the goal is written: CLAUDE.md imports this file into every session, and the claude.ai Projects carry no copy of it. It changes by pull request like everything else.

## Goal

Not yet written. One paragraph: what this project makes, for whom, and what done looks like. The owner writes it, or asks a session to, when ticking the "Set up this project" issue's box for this file, and merges it by pull request.

## Scope

In scope: the areas this project owns, each in one line; docs/agents/OWNERSHIP.md maps them to accounts.

Out of scope, by decision: what this project does not do, each with the reason, so nobody proposes it again.

- A settings-as-code app (github/safe-settings, or the Repository Settings App reading .github/settings.yml), decided no on 2026-10-11 (issue #18): it is a dependency with admin rights on every repository it covers, and a server of our own in one case, for settings that Symphony Setup applies for one run from the front door, scripts/setup-repo.sh from a clone, and organization rulesets, secrets and variables for what an organization makes.

## Repositories

- {{REPO}}, this one: the shared plane for every account and every session; the default branch is {{DEFAULT_BRANCH}}.
- Other repositories this project reads or uses, four, each owned by the OpenSpineConsortium organization, whose owners merge to its default branch:
  - OpenSpineConsortium/symphony-protocol, public: the claim protocol as a Python library with no dependencies (the board, the protocol check, team mode's clerk, the push guard's rules and the merge gate). It is vendored here under tools/sdlc_protocol, with tools/VENDORED recording the release, its commit and the sha256 of every copied file, and scripts/check.sh fails when the copy differs from that record, or, on CI, which clones the library, from the library's files at that commit. A change to the rules is made there, never here: once it merges there, its sync workflow opens the pull request `symphony-protocol/sync` in OpenSpineConsortium/symphony-template with the new copy, and the template's check decides. A repository made from the template is not on the sync's list; its own .github/workflows/protocol.yml brings each new release in instead, weekly, as a pull request from a branch of the same name, or as an issue linking that pull request where GitHub Actions may not open one. By hand it is `python3 <symphony-protocol>/scripts/vendor.py <this repository> --consumer OpenSpineConsortium/symphony-template` and a pull request. Its ecosystem.json is the one list of which repository takes which modules, and its ECOSYSTEM.md, generated from that list, maps all five repositories.
  - OpenSpineConsortium/coordbench, public: the playground and benchmark that compares ways of coordinating Claude Code agents on CooperBench's tasks, this protocol among them; its sdlc arm runs on the library's merge gate, vendored under coordbench/vendor. It began as experiment/ on OpenSpineConsortium/symphony-template's branch claude/10.
  - OpenSpineConsortium/symphony-marketplace, public: the Claude Code plugin marketplace with one plugin, symphony, which brings the skills, /board and the hooks to a repository not made from this template. .claude/settings.json names the marketplace and enables nothing, since this repository wires the same hooks itself.
  - OpenSpineConsortium/symphony-app, private: the GitHub App SymphonyBoard (slug symphonyboard). Its installation token lets template-init's first commit start the Checks and the Board, which a push with GITHUB_TOKEN cannot, and the symphony-protocol sync opens its pull requests in every consumer with it; its webhook server, where it is run, posts the protocol check as a check run of its own, sdlc/protocol.

## Model and effort

Every account's Project uses the same model and the same effort, so the work reads the same whoever did it. Record the choice here and set it in each Project's settings when you make the Project (docs/setup/claude-project.md).

- Model: not yet chosen.
- Effort: not yet chosen.

## Crowd mode

- Crowd mode: off. To open the project to volunteers who each work on their own Claude account, the owner runs `python3 scripts/crowd.py setup` (docs/setup/crowdsourcing.md), whose pull request turns this line on with the decisions that come with it; from then on the required check holds the repository to them.

## Owners

- Repository owner: {{OWNER}}, who merges to {{DEFAULT_BRANCH}}; .github/CODEOWNERS names {{CODE_OWNER}}, the owner's own login, or in an organization's copy the person who made the copy, because GitHub asks a user or a team for review and never an organization (docs/setup/github.md, section 7).
- Main Claude account: the first account, whose Project runs the worker routine (docs/agents/routines/worker.md) and, once a second account joins, the coordinator (docs/agents/routines/coordinator.md); its label is account:main.
- Other accounts: none yet. Each gets a label of its own (docs/setup/github.md, Labels) and a row in docs/agents/OWNERSHIP.md.
