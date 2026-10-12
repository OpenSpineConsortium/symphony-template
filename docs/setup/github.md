# Setting up the repository on GitHub

A template repository copies files only. The new repository gets none of the template's settings, branch rules, secrets, labels or issues. That is why the first push runs .github/workflows/template-init.yml, which fills the names into the files, creates the labels and opens the issue "Set up this project", and why this page exists for what only a person with the repository's settings can do. Do these once, in this order, under https://github.com/{{REPO}}/settings; or run `bash scripts/setup-repo.sh` once from a clone with the GitHub CLI signed in, which does sections 1, 2 and 5 and the variables in one go and checks section 7 (docs/setup/owner-checklist.md gathers every step, the Claude side included, and says what an organization can set once for every repository it makes).

## 1. Protect the default branch

{{DEFAULT_BRANCH}} takes only pull requests, and the template ships the whole rule as a file: under Rules, Rulesets, New ruleset, Import a ruleset, pick docs/setup/ruleset-main.json from your clone. It targets ~DEFAULT_BRANCH (whatever yours is named), requires a pull request and the check named "check" on an up-to-date branch, and blocks force pushes and deletions. Imported, you are done with this step.

Writing the same rule by hand, under Branches or Rules, for {{DEFAULT_BRANCH}} and that branch only:

- Require a pull request before merging.
- Require status checks to pass, and pick the check named "check", the job .github/workflows/ci.yml runs on every pull request. It appears in the list once the first pull request has run it; if it is not in the list yet, type the name check, which both a ruleset and a branch protection rule accept.
- Require branches to be up to date before merging, so a pull request the board called "main moved" is rebased before it lands.
- Do not allow force pushes and do not allow deletions.

The rule must target only {{DEFAULT_BRANCH}}. The board is the file STATE.md on the branch `board`, one commit that .github/workflows/board.yml force-pushes anew on every run that changed it (read it with `git fetch origin board && git show origin/board:STATE.md`); a ruleset over all branches would block that push and leave the board stale. It must leave the claim branches `claude/**` alone too, and the `released/**` they become: the board renames a released claim's branch with the workflow's token (docs/agents/PROTOCOL.md, Release), and GitHub lets only an administrator rename a branch that a ruleset or a protection rule covers. Should a ruleset cover them anyway, the board says so once on the issue whose claim it could not free, naming each ruleset in the way, with its rules and a link to it. The same holds for the branch `metrics`, which .github/workflows/metrics.yml rewrites once a day with the project's field metrics, aggregates only, beside the counts a maintainer's judge may push there (docs/setup/metrics.md), and for `symphony-protocol/sync`, which .github/workflows/protocol.yml force-pushes with each new release of the protocol. tests/test_setup_repo.py holds every ruleset the template ships, docs/setup/ruleset-*.json, to the default branch alone. Nothing of the board ever lands on {{DEFAULT_BRANCH}}, so the rules above never stand in its way, and no board commit moves the default branch under an open pull request.

GitHub offers branch protection and rulesets on a private repository only on a paid plan; on GitHub Free the repository must be public for them to apply. Without them the protocol still works, but nothing stops a push straight to {{DEFAULT_BRANCH}}. docs/setup/tiers.md lays out the whole ladder: what each plan unlocks, and the three spending profiles this template is designed for.

Under General, turn on "Automatically delete head branches", so a merged claim branch goes away on its own.

## 2. Labels

template-init created seven labels: todo (the queue), claimed, in-review, blocker, account:main (the main Claude account), and the two team mode uses, epic and blocked (docs/agents/TEAM.md); a team member's agent:<name> label is made when the lead first assigns it a task or the member first takes one. Check them under Issues, Labels. To add an account, add a label `account:<name>` there, give the account a row with the same name in docs/agents/OWNERSHIP.md, and the account puts the label on each issue it claims. Nothing else about an account is recorded anywhere.

## 3. Install the Claude GitHub App

Install the Claude GitHub App on the repository and grant it this repository; every thread of a claude.ai Project that works here needs it. One flow does this and the @claude secret together: from Claude Code signed in as the main account, run `/install-github-app` and pick this repository; the browser OAuth it opens installs the app and writes the repository secret CLAUDE_CODE_OAUTH_TOKEN (docs/setup/claude-action.md). The installation can also start from claude.ai/code: when you link the repository to a Project (docs/setup/claude-project.md, step 2), Claude sends you to GitHub to install the app and pick this repository; the secret then takes the by-hand path on docs/setup/claude-action.md. Afterwards the app is listed under Integrations, GitHub Apps.

## 4. The coordinator routine and its trigger

After the main account's Project exists (docs/setup/claude-project.md), make the routine in it, by asking for the scheduled work in the Project's own conversation, as docs/agents/routines/coordinator.md describes. To let the board workflow fire it, and only while every writer of the repository is you, add two repository secrets under Secrets and variables, Actions: COORDINATOR_TRIGGER_URL, the routine's API trigger address, shown on the routine's page under the Project's Routines tab, and COORDINATOR_TRIGGER_TOKEN, the bearer token shown beside it. .github/workflows/board.yml fires the trigger only when a run changed the board, never on a run that found it unchanged, so the routine's own labels and comments do not call it back in a chain. Both secrets are optional: without them the routine's hourly schedule covers the rest. They stay out once anyone else has Write, since any writer's workflow can read a repository secret and each fire runs the routine on the main account's usage; docs/start/team.md, step 1, takes them out before that. The only other secret this repository ever asks for is CLAUDE_CODE_OAUTH_TOKEN, also optional, which turns on @claude in issues and pull requests (docs/setup/claude-action.md); the workflows otherwise run on GitHub's own GITHUB_TOKEN.

When the board moves and the routine no longer acts on it, look at the Project's Routines tab: a routine stops after 72 hours without its GitHub connection, and stops with a limit error when the plan's usage is spent; nothing in the repository reports either.

## 5. Secret scanning and push protection

Under Code security, turn on secret scanning and push protection. They are the first line: GitHub refuses a push that carries a token it recognises before anything else runs. The repository's own check (tools/check_docs.py, run by scripts/check.sh) looks for the shapes of common secrets in tracked text files as the second line. Neither replaces the rule: no credential, no token and no API key in this repository, ever.

## 6. Dependabot

.github/dependabot.yml asks for weekly updates of the GitHub Actions the workflows use, which are pinned to a major tag. Nothing to set; it runs once the file is on {{DEFAULT_BRANCH}}.

## 7. Code owners

.github/CODEOWNERS is one line, `* @LOGIN`, which asks LOGIN to review every pull request. GitHub requests review only from a user or a team that has write access to the repository (a user may also be named by an email address on their account), never from an organization: a line that names anything else (an organization, a user without Write, a secret team or a team without Write) assigns no code owner, and the only sign is the error GitHub lists on the file's page and through its API. So template-init writes the owner's login in a personal copy and, in an organization's copy, the login of the user whose push made the copy, which is whoever pressed "Use this template". A copy made by an app has no such user; template-init then leaves the organization's name in the line and says so in its run's log.

Check it once: open .github/CODEOWNERS on GitHub, which marks a line it cannot resolve, or run `gh api repos/{{REPO}}/codeowners/errors`, which prints `{"errors":[]}` when every owner resolves; scripts/setup-repo.sh runs the same check. To fix the line, or to hand review to a team instead of one person, change it by pull request to `* @LOGIN` or, in an organization's copy, `* @{{OWNER}}/TEAM`, where the team is visible and has Write on this repository, and say so in docs/project.md under Owners and in docs/agents/OWNERSHIP.md. Review by a code owner is only asked for, not required, until a ruleset requires it; docs/setup/ruleset-main.json does not.
