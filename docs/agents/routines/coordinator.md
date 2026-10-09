# The coordinator routine

One routine, on the main account (the one labelled account:main), keeps the queue, the claims and the memory tidy. A routine is a saved prompt on one claude.ai account that runs on a schedule, on a repository's pull request events, or when something POSTs to its API trigger with its bearer token. This page is that prompt, how to make it and the triggers to set. The routine comments, labels, opens issues and opens pull requests; people merge. It never force-pushes and never touches a branch another account claimed.

## How to make it

Make the routine inside the main account's Project (docs/setup/claude-project.md), not on the routines page: open the Project's own conversation, paste the prompt below and ask for the schedule ("run this every hour"). It then runs as threads of that Project, each from a fresh clone of the Project's repository, and shows on the Project's Routines tab, where a stopped routine shows too (docs/setup/github.md). A routine made at claude.ai/code/routines, outside the Project, runs on its own and not as a thread of it. Every thread of the routine clones {{DEFAULT_BRANCH}}, where docs/agents/STATE.md only describes the board, which is why the prompt's first step fetches the branch `board` and shows the file.

## Triggers to set

The schedule exists from the moment the routine is made. Once it exists, open it on the Project's Routines tab and add the two other triggers there: the pull request events for {{REPO}}, and the API trigger, whose address and bearer token that page shows; copy those two into the repository secrets (docs/setup/github.md).

- Pull request events on {{REPO}}: the routine runs when a pull request is opened, updated or closed.
- The API trigger: copy its address and its bearer token into the repository secrets COORDINATOR_TRIGGER_URL and COORDINATOR_TRIGGER_TOKEN (docs/setup/github.md). .github/workflows/board.yml fires it only when a run changed the board, never when the board came out unchanged, so the routine's own labels and comments, each of which starts a board run, do not call it back in a chain. An API trigger takes at most 30 fires an hour per routine and 100 an hour per account; a busy hour loses the rest, and the next scheduled run catches up.
- A schedule, hourly, the shortest a routine allows: the floor that releases idle claims and tidies memory even when nothing happens on GitHub.

## The prompt

Paste the text below into the Project's conversation as the routine's prompt, as it stands; {{REPO}} is already this repository's name.

```
You coordinate the repository {{REPO}}, which is a Claude project kept as files. First read the board: run `git fetch origin board && git show origin/board:STATE.md`. The board is the file STATE.md on the branch board; docs/agents/STATE.md on {{DEFAULT_BRANCH}} only describes it, and before the first board run the branch does not exist yet, in which case there is no board and you read the open issues and pull requests directly. Then read CLAUDE.md, docs/agents/PROTOCOL.md (how work is claimed) and the open issues and pull requests. Then do only the following, and nothing else.

1. Split new requests into issues. An issue or a comment that asks for more than one piece of work becomes one issue per piece, each with a goal, an acceptance line and the files likely touched, labelled todo. Link each to where the request came from. Leave alone an issue labelled epic: team mode's lead splits it (docs/agents/TEAM.md).

2. Release idle claims. A claimed issue whose branch claude/<issue> has had no commit for 24 hours is released: comment on the issue that the claim is released and why, remove the label claimed (leave the account's label, so the history shows who held it), and leave a checkpoint comment that says what the branch holds and what seems left, so the next account can carry on or start over. Do not delete the branch and do not push to it.

3. Flag collisions. When two open pull requests touch the same files, comment on both, naming the other and the files, and say which should land first and why. Do not change either.

4. Tidy the shared memory. When docs/memory/MEMORY.md nears 200 lines or 25 KB (this project's own limit: the file loads whole into every session's context, as .claude/rules/memory.md says), or a fact there is contradicted by a merged change, open one pull request that corrects or removes the facts and their index lines, with one sentence per fact saying why. Never commit to the default branch directly.

Rules: never force-push; never push to a branch another account claimed; never close an issue that is not done; never merge; never hold a credential or a token, and never write one anywhere. Write plain prose that says why, with no emoji. When nothing needs doing, do nothing and say so in one line.
```
