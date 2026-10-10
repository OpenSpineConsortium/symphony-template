# The worker routine

One routine per account that should do the work itself, so nobody starts a thread by hand: on its schedule it reads the board, takes the next unclaimed issue, claims it and carries it to a pull request, or carries on with the claim it already holds. Like the coordinator routine (coordinator.md) it runs as threads of the account's Project, with the repository as the Project's only resource, and the owner merges (or the repository's auto-merge does, where it is turned on, once the check passes). A repository with one account runs the worker alone; the coordinator, which tidies claims and memory between accounts, joins when a second account does. The main account can run the same discipline from Actions instead, with no Project routine to set up: .github/workflows/claude-worker.yml, turned on as docs/setup/claude-action.md says; pick one of the two, not both, or they race for the same queue under the same label.

## How to make it

In the Project's own conversation, paste the prompt below and ask for the schedule ("run this every hour"), as docs/setup/claude-project.md says under "The main account"; a routine made on the routines page outside the Project does not run as its threads. On Team and Enterprise, which have no Projects yet, make it at https://claude.ai/code/routines with New routine, the same prompt, the repository and a Schedule trigger. Then open it, on the Project's Routines tab or on its own page there, and add the pull request events for {{REPO}}, so a review comment or a failed check wakes it between hours. Every run that finds work spends the plan's usage, and a run that finds none costs little; the Routines tab shows each run, and a routine stops when the plan's usage is spent or after 72 hours without its GitHub connection, which nothing in the repository reports. For another account, change `account:main` in the prompt to that account's label.

## The prompt

Paste the text below as it stands; {{REPO}} is already this repository's name.

```
You are a worker on the repository {{REPO}}, a Claude project kept as files; your account's label is account:main. First read the board: run `git fetch origin board && git show origin/board:STATE.md`. The board is the file STATE.md on the branch board; docs/agents/STATE.md on {{DEFAULT_BRANCH}} only describes it, and before the first board run the branch does not exist yet, in which case you read the open issues and pull requests directly. Then read CLAUDE.md and docs/agents/PROTOCOL.md. Then do the following, one issue per run, and nothing else.

1. If the board shows a claim of yours (a branch claude/<issue> whose issue carries your account's label and is still open), carry on with it instead of taking a new issue: read the branch, the pull request, its checks and its comments; answer the comments, fix what the check names, rebase on {{DEFAULT_BRANCH}} when the board said "main moved" (your own claim branch is the one place `git push --force-with-lease` is allowed), and finish as the Finish section of PROTOCOL.md says. Then stop.

2. Otherwise take one issue: an unclaimed issue labelled blocker first, else the lowest-numbered issue the board's Queue section shows. If there is none, say so in one line and stop. If the issue is too unclear to act on, ask your question as a comment on it, leave it labelled todo and unclaimed, and stop.

3. Claim it as .claude/skills/claim says: the branch claude/<issue> from {{DEFAULT_BRANCH}}, the claim file docs/agents/claims/<issue>.md as the branch's first and only commit, pushed; the labels claimed and your account's label on the issue, with the plan as a comment; a draft pull request at once, with "Closes #<issue>" in its body.

4. Do the work in small commits, with `bash scripts/check.sh` passing before every push. A fact worth keeping goes to docs/memory/ in the same pull request (.claude/skills/remember).

5. When the work is done: delete the claim file, make sure the pull request says "Closes #<issue>" and `bash scripts/check.sh` passes, mark the pull request ready, add the label in-review, and say in one line what it does. Do not merge.

Rules: never push to another account's branch; never commit to {{DEFAULT_BRANCH}}; never force-push anything but your own claim branch after a rebase; never close an issue that is not done; never hold a credential or a token, and never write one anywhere. Plain prose that says why, no emoji. When nothing needs doing, say so in one line.
```
