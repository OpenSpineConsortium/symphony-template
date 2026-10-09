# Setting up the repository on GitHub

A template repository copies files only. The new repository gets none of the template's settings, branch rules, secrets, labels or issues. That is why the first push runs .github/workflows/template-init.yml, which fills the names into the files, creates the labels and opens the issue "Set up this project", and why this page exists for what only a person with the repository's settings can do. Do these once, in this order, under https://github.com/{{REPO}}/settings.

## 1. Protect the default branch

{{DEFAULT_BRANCH}} takes only pull requests. Under Branches (a branch protection rule) or under Rules (a ruleset), for {{DEFAULT_BRANCH}} and that branch only:

- Require a pull request before merging.
- Require status checks to pass, and pick the check named "check", the job .github/workflows/ci.yml runs on every pull request. It appears in the list once the first pull request has run it; if it is not in the list yet, type the name check, which both a ruleset and a branch protection rule accept.
- Require branches to be up to date before merging, so a pull request the board called "main moved" is rebased before it lands.
- Do not allow force pushes and do not allow deletions.

The rule must target only {{DEFAULT_BRANCH}}. The board is the file STATE.md on the branch `board`, one commit that .github/workflows/board.yml force-pushes anew on every run that changed it (read it with `git fetch origin board && git show origin/board:STATE.md`); a ruleset over all branches would block that push and leave the board stale. Nothing of the board ever lands on {{DEFAULT_BRANCH}}, so the rules above never stand in its way, and no board commit moves the default branch under an open pull request.

GitHub offers branch protection and rulesets on a private repository only on a paid plan; on GitHub Free the repository must be public for them to apply. Without them the protocol still works, but nothing stops a push straight to {{DEFAULT_BRANCH}}.

Under General, turn on "Automatically delete head branches", so a merged claim branch goes away on its own.

## 2. Labels

template-init created five labels: todo (the queue), claimed, in-review, blocker and account:main (the main Claude account). Check them under Issues, Labels. To add an account, add a label `account:<name>` there, give the account a row with the same name in docs/agents/OWNERSHIP.md, and the account puts the label on each issue it claims. Nothing else about an account is recorded anywhere.

## 3. Install the Claude GitHub App

Install the Claude GitHub App on the repository and grant it this repository; every thread of a claude.ai Project that works here needs it. The installation starts from claude.ai/code: when you link the repository to a Project (docs/setup/claude-project.md, step 2), Claude sends you to GitHub to install the app and pick this repository. Afterwards it is listed under Integrations, GitHub Apps.

## 4. The coordinator routine and its trigger

After the main account's Project exists (docs/setup/claude-project.md), make the routine in it, by asking for the scheduled work in the Project's own conversation, as docs/agents/routines/coordinator.md describes. To let the board workflow fire it, add two repository secrets under Secrets and variables, Actions: COORDINATOR_TRIGGER_URL, the routine's API trigger address, shown on the routine's page under the Project's Routines tab, and COORDINATOR_TRIGGER_TOKEN, the bearer token shown beside it. .github/workflows/board.yml fires the trigger only when a run changed the board, never on a run that found it unchanged, so the routine's own labels and comments do not call it back in a chain. Both secrets are optional: without them the routine's hourly schedule covers the rest. The only other secret this repository ever asks for is CLAUDE_CODE_OAUTH_TOKEN, also optional, which turns on @claude in issues and pull requests (docs/setup/claude-action.md); the workflows otherwise run on GitHub's own GITHUB_TOKEN.

When the board moves and the routine no longer acts on it, look at the Project's Routines tab: a routine stops after 72 hours without its GitHub connection, and stops with a limit error when the plan's usage is spent; nothing in the repository reports either.

## 5. Secret scanning and push protection

Under Code security, turn on secret scanning and push protection. They are the first line: GitHub refuses a push that carries a token it recognises before anything else runs. The repository's own check (tools/check_docs.py, run by scripts/check.sh) looks for the shapes of common secrets in tracked text files as the second line. Neither replaces the rule: no credential, no token and no API key in this repository, ever.

## 6. Dependabot

.github/dependabot.yml asks for weekly updates of the GitHub Actions the workflows use, which are pinned to a major tag. Nothing to set; it runs once the file is on {{DEFAULT_BRANCH}}.
