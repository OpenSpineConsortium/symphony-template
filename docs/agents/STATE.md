# Board

The live board is the file STATE.md on the branch `board` of this repository (https://github.com/{{REPO}}/blob/board/STATE.md), rewritten by .github/workflows/board.yml on every issue and pull request event, every branch made or deleted, every push to {{DEFAULT_BRANCH}}, and every six hours as a fallback; this file on {{DEFAULT_BRANCH}} only describes it. Read it with `git fetch origin board && git show origin/board:STATE.md`; the session hook prints it at the start of every session.

The branch `board` holds exactly one commit, rewritten on every run that changed the board, and nothing else is ever on it. The board never lands on {{DEFAULT_BRANCH}}, so no board commit moves the default branch or puts an open pull request behind it, and the rules that protect {{DEFAULT_BRANCH}} never stand in the board's way (docs/setup/github.md). The branch does not exist until the first run: template-init's commit is pushed with GitHub's own token, which starts no workflow, so the first board comes with the first issue or pull request a person opens after setup, or at the next six-hourly fallback run, whichever is sooner; until then the session hook says the board has not been written yet. Nobody edits the board by hand, and this page changes only when the layout tools/board.py renders does.

## Layout

tools/board.py renders the board in this shape. Rows are sorted and the file carries no wall-clock value, so it changes only when the repository did; an empty section keeps its header and holds one row, "(none)".

```
# Board
As of commit <short sha> on <default branch>. Rewritten by .github/workflows/board.yml; do not edit by hand.
## Claims (open claude/<issue> branches and docs/agents/claims/<issue>.md)
| Issue | Branch | Account | PR | Files it touches |
## Open pull requests
| PR | Title | Branch | State (clean, behind, conflicting, blocked, unknown) | Last update |
## Queue (open issues labelled todo, unclaimed)
| Issue | Title | Labels |
## Blockers (open issues labelled blocker)
| Issue | Title | Labels |
## Recently merged (the last 5)
| PR | Title | Branch | Merged |
```

- Claims: every open branch `claude/<issue>` and its claim file, with the account from the claim file's `- Account:` line, the pull request when one is open, and the files that pull request changes; before there is a pull request, the `- ` lines under "## Files to touch" in the claim file. Once the finishing pull request has deleted the claim file, the account comes from the issue's account label. A branch whose issue is closed is a leftover: its row says "issue closed" and "delete the branch" until someone deletes it, which GitHub does on merge when docs/setup/github.md's setting is on.
- Open pull requests: State is how the branch stands to the default branch, in GitHub's words: clean (mergeable), behind (the default branch moved past it; the board comments "main moved" once per head commit), conflicting, blocked (a required check or review is missing) or unknown (GitHub has not computed it yet). Last update is the pull request's last change.
- Queue: the open issues labelled todo that have neither a branch `claude/<issue>` nor the label claimed.
- Blockers: the open issues labelled blocker.
- Recently merged: the five pull requests merged last, newest first, so a session sees what landed. The list depends on the repository alone, never on when the previous board was written: a merge fires two runs, and a window counted from the previous board's commit lost the merge in the second.
