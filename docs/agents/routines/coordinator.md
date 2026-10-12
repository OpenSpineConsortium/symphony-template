# The coordinator routine

One routine, on the main account (the one labelled account:main), keeps the queue, the claims and the memory tidy. A routine is a saved prompt on one claude.ai account that runs on a schedule, on a repository's pull request events, or when something POSTs to its API trigger with its bearer token. This page is that prompt, how to make it and the triggers to set. The routine comments, labels, opens issues and opens pull requests; people merge. It never force-pushes and never touches a branch another account claimed.

## How to make it

Make the routine inside the main account's Project (docs/setup/claude-project.md), not on the routines page: open the Project's own conversation, paste the short prompt below and ask for the schedule ("run this every hour"). It then runs as threads of that Project, each from a fresh clone of the Project's repository, and shows on the Project's Routines tab, where a stopped routine shows too (docs/setup/github.md). A routine made at claude.ai/code/routines, outside the Project, runs on its own and not as a thread of it. Every thread of the routine clones {{DEFAULT_BRANCH}}, where docs/agents/STATE.md only describes the board, which is why the full prompt's first step fetches the branch `board` and shows the file.

## Triggers to set

The schedule exists from the moment the routine is made. Once it exists, open it on the Project's Routines tab and add the pull request events for {{REPO}} there. Add the third trigger, the API trigger, only while every writer of the repository is you: its address and its bearer token have to be repository secrets, which any writer's workflow can read, and each fire runs the routine on the main account's usage. docs/start/team.md, step 1, takes those secrets out before anyone else gets Write, and the hourly schedule then catches up with what the trigger would have woken early.

- Pull request events on {{REPO}}: the routine runs when a pull request is opened, updated or closed.
- The API trigger, only where every writer is you: copy its address and its bearer token into the repository secrets COORDINATOR_TRIGGER_URL and COORDINATOR_TRIGGER_TOKEN (docs/setup/github.md). .github/workflows/board.yml fires it only when a run changed the board, never when the board came out unchanged, so the routine's own labels and comments, each of which starts a board run, do not call it back in a chain. An API trigger takes at most 30 fires an hour per routine and 100 an hour per account; a busy hour loses the rest, and the next scheduled run catches up.
- A schedule, hourly, the shortest a routine allows: the floor that releases idle claims and tidies memory even when nothing happens on GitHub.

## The prompt

The routine's own prompt is the short one below, pasted into the Project's conversation once, as it stands; {{REPO}} is already this repository's name. Every run reads the full prompt, the last block on this page, from {{DEFAULT_BRANCH}}, so a change to it reaches the routine at its next run once its pull request merges, and nobody pastes it again.

```
You coordinate the repository {{REPO}}. Run `git fetch origin {{DEFAULT_BRANCH}} && git show origin/{{DEFAULT_BRANCH}}:docs/agents/routines/coordinator.md` and do what the last fenced block of that page says, exactly and nothing else. Read it again on every run, since it changes by pull request.
```

The full prompt, which every run reads from here:

```
You coordinate the repository {{REPO}}, which is a Claude project kept as files. First read the board: run `git fetch origin board && git show origin/board:STATE.md`. The board is the file STATE.md on the branch board; docs/agents/STATE.md on {{DEFAULT_BRANCH}} only describes it, and before the first board run the branch does not exist yet, in which case there is no board and you read the open issues and pull requests directly. Then read CLAUDE.md, docs/agents/PROTOCOL.md (how work is claimed) and the open issues and pull requests. Then do only the following, and nothing else.

1. Split new requests into issues. An issue or a comment that asks for more than one piece of work becomes one issue per piece, each with a goal, an acceptance line and the files likely touched, labelled todo. Link each to where the request came from. Leave alone an issue labelled epic: team mode's lead splits it (docs/agents/TEAM.md).

2. Release idle claims. Your candidates are the open issues that have a branch claude/<issue>, whatever their labels. Leave alone a claim whose issue is labelled in-review or whose pull request is marked ready, however long it waits for review. Release any other whose branch has had no commit for more than 24 hours, counted from the committer date of its head (`git log -1 --format=%cI origin/claude/<issue>`), not from a rounded age, in this order: first comment on the issue that the claim is released, why, and whose it was, with the line `<!-- sdlc-coordinator: claim-released -->` as the comment's first line, which lets the board and the metrics workflow tell a release without reading what the comment says; then remove the label claimed and the holder's account label (the comment keeps the history of who held it, and the board acts on a release only once claimed is off); then leave a checkpoint comment that says what the branch holds and what seems left, so the next account can carry on or start over. Skip a claim already released: one whose latest release comment came more than 24 hours after the branch's last commit; one released sooner than that is released again, since the board does not act on it. Do not delete, rename or push to the branch: the board renames it to released/<issue>-<short sha>, which keeps the work, frees the name for the next claim and puts the issue back in its Queue.

3. Flag collisions. When two open pull requests touch the same files, comment on both, naming the other and the files, and say which should land first and why. Do not change either.

4. Tidy the shared memory. When docs/memory/MEMORY.md nears 200 lines or 25 KB (this project's own limit: the file loads whole into every session's context, as .claude/rules/memory.md says), or a fact there is contradicted by a merged change, open one pull request that corrects or removes the facts and their index lines, with one sentence per fact saying why. Never commit to the default branch directly.

Rules: never force-push; never push to a branch another account claimed; never close an issue that is not done; never merge; never hold a credential or a token, and never write one anywhere. Write plain prose that says why, with no emoji. When nothing needs doing, do nothing and say so in one line.
```
