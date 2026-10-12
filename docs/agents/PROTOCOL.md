# How work is claimed

The queue is GitHub Issues on {{REPO}}. The board is the file STATE.md on the branch `board`, rendered from the issues, the branches, the claim files and the pull requests by .github/workflows/board.yml, which rewrites that branch's one commit on every issue and pull request event, every branch made or deleted, every push to {{DEFAULT_BRANCH}}, and every six hours as a fallback; nobody edits it by hand. Read it with `git fetch origin board && git show origin/board:STATE.md`; the session hook prints it at the start of every session, and docs/agents/STATE.md on the default branch only describes its layout. A claim is the first push of a branch: GitHub refuses the second push of the same name, so two accounts can never hold the same issue. Everything below is done by the account doing the work, in the open, and the claim skill (.claude/skills/claim) is the same steps as commands.

## Labels

- todo: the queue. An issue labelled todo and shown unclaimed on the board is free to take.
- claimed: an account has pushed its branch. The account's own label goes on with it.
- in-review: the pull request is ready; the owner merges it and the merge closes the issue.
- blocker: the issue stops everyone until it is done.
- account:main: the main account, the first one, which runs the worker routine and, once a second account joins, the coordinator. One label per account; docs/setup/github.md says how to add one.

## Pick

Fetch, then read the board (`git fetch origin board && git show origin/board:STATE.md`). Take an open issue labelled todo that the Queue section shows as unclaimed and that no open blocker stands in the way of. An issue with a branch `claude/<issue>` on origin, or a file `docs/agents/claims/<issue>.md` on the default branch, is another account's, whatever its labels say.

## Claim

Push a new branch `claude/<issue number>` from the default branch whose first commit adds `docs/agents/claims/<issue number>.md`: the account, the plan, the files to touch, the issue's link, on the template in docs/agents/claims/README.md. Nothing else is in that first commit. If the push is refused because the branch exists, another account has it: delete the local branch and pick another issue.

## Announce

Add the label claimed and the account's label to the issue, taking off any other account's label an earlier claim left there, and post the plan as a comment, so the board and the people reading the issue see the same thing the branch says.

## Work in the open

Open a draft pull request at once, from the branch to the default branch, with "Closes #N" in its body. Push often: a branch with no commit for 24 hours is released (below). When the board comments "main moved" on the pull request, the default branch has moved past the branch: rebase on it and push again with `--force-with-lease`. That is the one forced push the protocol allows, and only on your own claim branch.

## Finish

The pull request deletes its claim file, says "Closes #N", passes `bash scripts/check.sh` and is marked ready; the issue gets the label in-review. The owner merges; the merge closes the issue, and the next board no longer lists the claim. Delete the branch after the merge if the repository does not do it by itself (docs/setup/github.md). An issue closed without a merge loses its branch too: .github/workflows/tidy.yml deletes `claude/<issue>` once no open pull request uses it, and with it any `released/<issue>-<sha>` a released claim left (Release).

## Blockers

An issue labelled blocker stops everyone: work it stands in the way of waits until it is done. It is claimed like any other issue, by one account, and nobody else fixes it in parallel; a second account that sees it waits, or helps on the one pull request by review.

## Release

A claim whose branch has had no commit for more than 24 hours, by the committer date of its head, is released by the coordinator routine (docs/agents/routines/coordinator.md), unless it is finished: an issue labelled in-review, or a pull request marked ready, waits for review however long it takes. The coordinator first posts a comment on the issue whose first line is `<!-- sdlc-coordinator: claim-released -->` and which says why and whose the claim was, then takes the label claimed and the holder's account label off the issue, and leaves a checkpoint comment saying what the branch holds and what seems left, so the next account can carry the work on or start over. It never pushes to the branch, deletes it or renames it. It takes its candidates from the open issues that have a branch `claude/<issue>`, whatever their labels, and skips a claim whose latest release comment came more than 24 hours after the branch's last commit, which is a claim already released; one it released sooner than that it releases again.

The board does the rest. A claim counts as released when its issue is open, labelled neither claimed nor in-review, its pull request, if any, is still a draft, and its latest release comment came more than 24 hours after the branch's last commit, with no commit since. A release comment counts when it is by the repository's owner, a member of its organization or a collaborator, or by anyone else who may write to the repository. The board then leaves the claim and its pull request off the page and lists the issue in the Queue again, and .github/workflows/board.yml renames the branch to `released/<issue>-<short sha of its head>`: the name `claude/<issue>` is free, the work stays under the new name, GitHub closes the branch's pull request with the rename, and the board says on the issue where the branch went. The next account claims the issue by the steps above, a new branch `claude/<issue>` from the default branch, and may carry the released work on in it after the claim commit, keeping its own claim file (.claude/skills/claim says how). A release comment made sooner, or by anyone else, frees nothing; a commit pushed to the branch before the rename, its holder coming back, keeps the claim; and putting the label claimed back undoes a release, before the rename or after it, when the branch is renamed back and its pull request reopened. A branch pushed again at the head a release already kept is deleted instead, since its work is already kept. Until the board has renamed the branch, a push of the name is still refused; the board renames it in the run that the label's removal starts.

## Team mode

With the repository variables CLAUDE_TEAM and CLAUDE_WORKER set, an issue labelled epic is planned by a lead into sub-issues pre-assigned to members (label agent:<name>), whom this protocol binds like any account, with two differences: members bring the default branch in by merging it, not by rebasing, so they never force-push, and they land by auto-merge on a green check rather than by the owner's hand. The board's queue leaves out an epic and its members' tasks, so no other account takes them; docs/agents/TEAM.md says how members divide the work and see each other's branches.

## Rules that hold everywhere

- One issue, one branch `claude/<issue>`, one pull request.
- Never push to another account's branch. Never force-push the default branch or any branch that is not your own claim.
- Memory rides in the same pull request as the change it came from (.claude/rules/memory.md).
- `bash scripts/check.sh` passes before a pull request is marked ready.
- CI holds a `claude/<issue>` pull request to this protocol (tools/check_protocol.py, part of the required check): the claim file is there while the pull request is a draft, gone once it is ready, the body closes its issue, and the branch lives in this repository.
