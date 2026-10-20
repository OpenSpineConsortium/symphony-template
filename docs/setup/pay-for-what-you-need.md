# Pay for what you need

Symphony's base runs on GitHub Free and the cheapest paid Claude plan. Everything you pay for
after that buys one named thing, and most of it comes on by itself the day you buy it, because the
settings are already written. This page says what the base does, what each purchase adds, and
which configuration fits which kind of work. The facts behind it, with GitHub's own words and the
file each came from, are docs/research/github-plans-and-visibility.md; the per-plan table is
docs/setup/free-or-paid.md and the prices are docs/setup/tiers.md. Prices move: read GitHub's and
Anthropic's pages before a decision hangs on one.

## The base: what works on GitHub Free

The protocol itself needs nothing GitHub sells. On a free account, personal or organization,
public or private, all of this works:

- Claiming. A claim is the first push of the branch `claude/<issue>`, and GitHub refuses a second
  push of the same name on every plan, so two workers never hold one issue.
- The board, releasing idle claims, telling overlapping work, dealing work to workers, and the
  protocol check: all ordinary workflows on the repository's own GITHUB_TOKEN.
- The push guard: a hook in each Claude Code session, which refuses a push to the default branch,
  a forced push and a push to another worker's claim, whatever GitHub's plan.
- The required check `check`: it runs on every pull request and says red or green.
- @claude, the workers in Actions and the coordinator, on one Claude account's token from
  `claude setup-token` (Claude Pro or above; never an API key).
- The settings: the SymphonyBoard App writes them on the copy's first push
  (.github/workflows/settings.yml), on any plan. Where the plan does not enforce one, GitHub keeps
  it and shows it as not enforced.

## What a free private repository does not get

A private repository on GitHub Free runs everything above, on trust rather than enforcement:

| Feature | Free, public | Free, private | What you lose without it |
| --- | --- | --- | --- |
| Ruleset and required check enforced | yes | no | Nothing on GitHub stops a push to main or a merge with a red check; only the sessions' push guard does. |
| Auto-merge | yes | no | Workers set to `"lands": "auto-merge"` wait for you to merge. |
| Environments, such as token-store | yes | no | The App's token script is not fenced to the default branch (below). |
| Organization secrets | yes | no | Each private repository needs its own copy of the Claude token. |
| Actions minutes | unlimited | 2,000 a month | About 300 go to the schedules; the rest to checks and Claude runs. |
| CodeQL, dependency review, secret scanning | yes | no | The check's own secret-shape test is the only scan. |

## Does paying later switch it on by itself?

Mostly, yes, and you never have to start public to get there.

- Rulesets and the required check: the App writes the ruleset whatever the plan. On a free private
  repository GitHub saves it and marks it not enforced; on the day you move to Pro (a personal
  account) or Team (an organization), the same ruleset is in force with nothing to run. That it
  switches on is read from GitHub's settings page, which shows the ruleset waiting for the plan;
  GitHub's docs do not say it in words, so it is the one step to confirm on the first real upgrade.
- Auto-merge: the App ticks "Allow auto-merge" with the rest, so once the ruleset is enforced,
  workers' pull requests merge themselves when the check is green. Where a free private repository
  refuses that box, the same Settings run as the environment's, below, ticks it.
- Environments are the exception. GitHub will not let anyone make an environment on a free private
  repository, so the App's attempt is refused and recorded. After an upgrade, the token-store
  environment is made by the next run of the Settings workflow, which runs on any merge that changes
  the ruleset file, setup-repo.sh or the workflow itself, and by its Run workflow button. Making that
  happen with no press, on the first run after the plan changes, is open work for the Tokens and
  adopted repositories thread.
- Starting public and going private keeps environments too, but only until you go public again:
  GitHub ignores them while private and gives them back on the way back to public. It says nothing
  of an upgrade, so this route buys nothing over waiting for the Settings run.

## QA and code review

The QA gate the project decided on, a required check `qa` that reads each autonomous worker's pull
request and writes a report a person can read, is not built yet. What covers it today, and what it
costs:

- The check `check` (scripts/check.sh, the protocol check, the linters actionlint and zizmor): free
  on every plan. It catches what tests and rules can catch, not judgment.
- Claude's review: comment @claude on a pull request and claude.yml answers on the repository's own
  Claude token. It costs Claude usage, never GitHub money on a public repository, and it reviews only
  when asked; it is advice, since no rule makes its answer block a merge.
- GitHub's own scanning, free on public repositories: CodeQL code scanning, dependency review and
  secret scanning with push protection. On a private repository they need the paid add-ons GitHub
  Code Security and GitHub Secret Protection, which only Team and Enterprise can buy.
- Copilot code review needs a paid Copilot plan; GitHub offers no free automated review.

So on a public repository the check, GitHub's scanning and Claude's review on request together cover
most of what the QA gate will add; what is missing is a review that runs on every worker's pull
request by itself and blocks the merge, which is the qa check still to build.

## The token-store environment: when it matters

token-store fences one thing: the Token workflow's jobs (token.yml), which mint the SymphonyBoard
App's token to write Claude tokens into secrets. With the environment, only the default branch's copy
of that script ever holds the App's token. Without it, someone who can push a branch to the repository
could change the script on that branch and run it.

- One person, or people you trust with write access: it changes little, since anyone with write can
  already read the repository's secrets from a workflow on a branch. Not needed.
- Contributors you do not fully trust with write, or an organization pooling Claude tokens for many
  repositories: it matters; get it from a public repository or Pro or Team.
- Crowd mode keeps Claude's secrets out of the repository altogether, so it does not need it.

## Configurations by kind of work

Each line says what to pay for and nothing more. Claude Pro is the floor everywhere, since
`claude setup-token` needs a paid Claude plan.

1. A student or hobbyist, open work. GitHub Free, public repository, Claude Pro. Everything is on
   and enforced: the gate, auto-merge, environments, scanning, unlimited minutes. Pay for Claude only.
2. One researcher, private work (unpublished data, a paper in progress). GitHub Free, private
   repository, Claude Pro. Everything runs; the gate is advice and workers wait for your merge.
   Upgrade to GitHub Pro when you want the gate enforced and auto-merge; the ruleset is already there.
3. One person running several workers at once. GitHub Free public, or Pro private, with Claude Max,
   or two Claude Pro accounts in the token pool, since workers share one account's five-hour window.
   Pay for usage, not features.
4. A small lab or team, private work. A GitHub organization on Team, Claude Team seats or each person
   on their own Claude plan. Team brings the enforced gate, auto-merge, environments and one
   organization secret for the Claude token across every repository. Add GitHub Secret Protection
   when the work handles anything sensitive enough that a leaked key would matter.
5. An open-source project with outside contributors. GitHub Free organization, public repositories,
   crowd mode (docs/setup/crowdsourcing.md): each contributor works on their own Claude account, the
   repository holds no Claude secret, and the free public features enforce everything.
6. Regulated or confidential work at scale (clinical data, patent material). GitHub Team with Code
   Security and Secret Protection, or Enterprise Cloud for merge queue, deployment reviewers and
   50,000 minutes; Claude Team or Enterprise. Keep such repositories private and never public.
