# GitHub's plans, visibility and what survives a change of either

From the thread "Control panel sign-in" of the claude.ai Project "symphony_2", 2026-10-20, on the
owner's questions of that day: what a free repository loses, whether settings made while public
come back when the owner pays, and what QA and code review cost. The source is GitHub's own
documentation as the github/docs repository holds it at main, commit 44a609d0 of 2026-10-20,
read from a clone since docs.github.com is unreachable from the cloud session; each finding names
the file it came from. docs/setup/free-or-paid.md (2026-10-13) tables the same features per plan;
nothing here contradicts it, and the three findings below it did not have are marked new.

## Enforcement on a private repository

- Rulesets: "available in public repositories with GitHub Free and GitHub Free for organizations,
  and in public and private repositories with GitHub Pro, GitHub Team, and GitHub Enterprise
  Cloud" (data/reusables/gated-features/repo-rules.md). Protected branches, code owners and
  auto-merge are gated the same way (protected-branches.md, code-owners.md, auto-merge.md in the
  same folder).
- Auto-merge is shown "only on pull requests that cannot be merged immediately", for example
  where a rule requires reviews or status checks
  (data/reusables/pull_requests/auto-merge-requires-branch-protection.md): without an enforced
  rule there is nothing for it to wait on.
- Organization secrets and variables "are not accessible by private repositories for GitHub Free"
  (data/reusables/actions/actions-secrets-variables-repository-access.md).

## What a change of visibility keeps (new)

- Environments: "If you convert a repository from public to private, any configured protection
  rules or environment secrets will be ignored, and you will not be able to configure any
  environments. If you convert your repository back to public, you will have access to any
  previously configured protection rules and environment secrets"
  (content/actions/how-tos/deploy/configure-and-manage-deployments/manage-environments.md). The
  docs say they return on going public again; they do not say whether an upgrade to Pro or Team
  brings them back.
- Rulesets and branch protection: the docs do not say whether a change to private deletes them,
  keeps them unenforced or restores them on an upgrade. "Making a repository private" says only
  that "some features won't be available" and lists stars, Dependabot custom rules, code scanning
  and forks (content/repositories/.../setting-repository-visibility.md); going private to public
  disables "All push rulesets". This project's own observation (docs/setup/free-or-paid.md,
  docs/memory/the-plan-ladder.md) is that a ruleset written on a Free private repository is saved
  and shown as not enforced on the settings page, so it is kept; that it comes into force on an
  upgrade is inferred from that page, not yet measured on a real upgrade.
- A plan downgrade: the account "will lose access to any functionality that is not included in
  the new plan" (content/billing/how-tos/manage-plan-and-licenses/downgrade-plan.md).

## Minutes

GitHub Actions "is free for self-hosted runners and for public repositories that use standard
GitHub-hosted runners" (content/billing/concepts/product-billing/github-actions.md); a private
repository draws 2,000 minutes a month on Free and on Free for organizations, 3,000 on Pro and on
Team (data/reusables/billing/actions-included-quotas.md). The template's scheduled baseline,
counted from its workflows on 2026-10-20: the board's fallback and the workers' registry each four
short runs a day, metrics one a day, protocol and coordinator one a week, drive-sync's half-hourly
run skipped at the job, at no cost, unless the variable SYMPHONY_DRIVE is on (it would be about
1,440 minutes a month on a private repository). About 300 minutes a month idle, before the check
on each pull request and the Claude runs, which take up to 90 minutes each.

## Scanning and review (new: review)

- Code scanning, CodeQL and dependency review: "Public repositories on GitHub.com", and on private
  repositories only with GitHub Code Security on Team or Enterprise
  (data/reusables/gated-features/code-scanning.md, dependency-review.md). Secret scanning "runs
  automatically for free" on public repositories (secret-scanning.md). Dependabot is on every
  repository.
- Copilot code review is "Available for all paid Copilot plans"; Copilot Free "does not include
  Copilot code review"; its runs are free minutes on public repositories, which is not a free
  review (content/copilot/concepts/agent-capabilities/agent-powered-workflows-and-operations/code-review.md).
  The docs name no free automated pull-request review.
- The template has no qa workflow yet: the QA gate is decided and not built
  (docs/research/conductor-and-agentastic.md). Its review today is Claude through
  .github/workflows/claude.yml on the repository's own Claude subscription token, asked by
  @claude on a pull request, which costs no GitHub money on a public repository.
