# Protocol fixes after 0.5.0: where they stand

Source: the thread "Protocol fixes toward 0.5.0" (item 2 of the 2026-10-15b handoff, part 2.1), checkpointed on 2026-10-16 at 19:00 UTC when the owner asked every thread to checkpoint so the work can go on from another account. This folder holds the thread's state that was not yet in git: the open work, the findings found along the way that have no pull request yet, the reviews' reports, the workers' draft commit messages and the probe scripts. The pull requests' own "Checkpoint 2026-10-16" sections say the same for each pull request and are newer where they differ.

## What the owner asked, and where each part is

The owner's ask: the protocol fixes toward 0.5.0, in part 2.1's order, then tell the owner 0.5.0 is ready; never the release or its approval gate.

1. F8's follow-up: merged, symphony-protocol#36.
2. The stuck claim, which raised the version to 0.5.0: merged, symphony-protocol#37. The release run waits for the owner's approval at https://github.com/OpenSpineConsortium/symphony-protocol/actions/runs/38889703117: press "Review deployments", tick "release", press "Approve and deploy". No session approves it.
3. The template's follow-up for 0.5.0: done before this checkpoint; the template vendors 0.5.0 (tools/VENDORED).
4. The measurement pass, three pull requests, all merged: symphony-protocol#38 (the API calls of one board run), symphony-template#108 (claim waits in a real copy, docs/research/claim-waits-in-a-real-copy.md) with symphony-template#110 (the medians rounded by one rule), and symphony-protocol#40 (the client waits as GitHub asks on a 429 or a secondary rate limit, and makes the call again).
5. The taxonomy review's two findings: F21 merged, symphony-protocol#39 (the push guard judges a push in the clone it runs in); F22 open as draft symphony-protocol#42 (a reopened issue is freed of the labels its ended claim left).
6. Telling the owner: once F22 merges.

0.5.1 will carry what main holds since the commit that raised it to 0.5.0 (68946e6, merged as ec49498): #38, #39 and #40 now, and F22, F23, F25, F26, F24 and F27 as each merges. Raising the version to 0.5.1 is a pull request of its own once they are in; its release waits for the owner's approval as 0.5.0's does.

## Open pull requests in OpenSpineConsortium/symphony-protocol

Each is a draft, assigned to the owner, with its next steps at the top of its description.

- #42, F22, branch claude/owner-decisions-f22-reopened at 022836c: fix, harness, bookkeeping and two merges of main done; check.sh and the mutation lane were running on 022836c when the worker was stopped, so the pull request's CI is its first full check. Next: CI, an adversarial review, its fixes, a second review, ready, merge.
- #41, F23, branch claude/owner-decisions-f23-late-comment at 2529d78: the fix (bd99ad5) and its first review's fixes (a1fa9f4, green on every check) done; 0099bd1 merges main (F21 and #40); 2529d78 is a checkpoint commit of the first review's finding 3, unfinished: a rate limit's refusal read as one GitHub may have written (`wrote_nothing` false where `github.rate_limited` holds), since whether GitHub acts on a call it refuses for a rate limit is the unverified assumption C4. drafts/f23-finding-3-commit-message.txt is the worker's draft message for it. Next: finish finding 3, check.sh and the lane, a second review, ready, merge.
- #43, F25, branch claude/owner-decisions-f25-unread-command at 8271243, unfinished: the guard's reading of a command it cannot read whole and of here-document bodies. Next: merge main, finish the fix, its entry and counts, the checks, the reviews.
- #44, F26, branch claude/owner-decisions-f26-long-options at 6411668, unfinished but far along: drafts/f26-commit-message-fix.txt and drafts/f26-commit-message-harness.txt are the worker's draft messages, which say what it had built (the trace, four grammar prefixes, three mutants) and one more hole it found: GNU time's own name for its output option is --output-file, which the guard's table knew as --output. Next: merge main, finish, the checks, the reviews.

## Findings with no pull request yet

Each was reproduced on symphony-protocol main ff75657 (F24) or 4c5e3f2 (F27) and gets its own branch, trace, mutants and DESIGN.md entry.

- F24: the guard reads the quoting inside a command substitution as the quoting around it, so `out="$(git push --force origin main 2>&1)"` and `cat <(git push --force origin main)` pass guard.refused_push on main (scripts/guard-holes-probe.py shows both). The fix reads every substitution's body, `$(...)`, backquotes, `<(...)` and `>(...)`, as commands, inside double quotes too. It touches shell_parts and plain_shell, as F25 does, so it comes after F25 merges.
- F27: a label removal GitHub made but answered with a 5xx or no answer is not put back: github.release_one's first except puts back only the labels in taken_off, and take_label_off raises on anything but a 404. scripts/f23-review/label_delete_lost_main.py gives G3L on main 4c5e3f2 with the faults label-delete-lost and label-delete-unanswered added in memory. The fix puts back the label whose removal failed unless `wrote_nothing(problem)`, so it comes after F23 merges. Found by F23's first review, its finding 4 (reviews/f23-first-review.md).

## The template's follow-up for 0.5.1

Not started, on purpose. The template vendors 0.5.0 (the commit that raised it); if it vendored main now, the sync that follows the owner's approval of 0.5.0 would open a pull request taking the template back to 0.5.0. So once 0.5.0 is published, one symphony-template pull request vendors the library's main, switches tools/guard_push.py to guard.refused_push (F21's fix reaches the template's hook only then), has tools/metrics.py's Budgeted count its calls from the client's `made` (the first rate-limit review's sixth finding: the tries the client makes again are not in Budgeted's own count), and brings docs/agents/PROTOCOL.md's Release in line with F22's and F23's spec text. The durable decision in CLAUDE.md that a release puts the labels back when its comment fails has been untrue since F20; it is corrected by a line tagged Decision: in conversation for the checkpoint skill, never by hand.

## How the thread worked, for whoever takes it on

- One library worktree per branch (`git -C /home/user/symphony-protocol worktree add -b <branch> /home/user/proto-<name> origin/main`), every git command with -C and an absolute path, never a bare git stash, commits as `-c user.name=Claude -c user.email=noreply@anthropic.com` with the two trailers.
- Each pull request: `bash scripts/check.sh` and `python3.12 -m validation.mutants` green, an adversarial review, its fixes, a second review of the fixes, then ready by `gh api -X POST repos/OpenSpineConsortium/symphony-protocol/pulls/<n>/ccr/ready_for_review` (GraphQL is blocked), the check that the ready event starts waited for, a merge commit with expectedHeadSha copied from git, and main's tree compared with the head's after.
- Main is brought into a branch by a merge, never a rebase. The counts meet at each merge: the exact mutant count and bound in tests/test_validation_mutants.py, validation/README.md's account of the lane and GUARANTEES.md give the running total (134 within 150 on main 49a6192); a finding's own DESIGN.md entry keeps the count at its own fix (F20's 117, F21's 125).
- A rendered string is part of the interface: changed only on purpose, and said so in the pull request.

## The first step from a new account

Attach OpenSpineConsortium/symphony-protocol with push access, clone it, fetch the four branches above, read #42's description and run its CI's results through an adversarial review; then #41's finding 3; then #43 and #44; then F24 and F27; then, once the owner has approved 0.5.0, the template's follow-up and the raise to 0.5.1.

## Files here

- drafts/: the workers' draft commit messages for the unfinished work (F23's finding 3, F26's fix and harness).
- reviews/: F23's first adversarial review and its fix report, the rate limits' second review and first fix report, the reports the next reviews build on (F21's reviews are in symphony-protocol#39's description).
- scripts/: guard-holes-probe.py and guard-two-bodies-probe.py (F24, F25 and F26 on main, run as `python3.12 -I <script> <library checkout> <a clone on main>`), f25-probe.py, heredoc-probe.py and f25-bash/ (the F25 worker's record of which pushes bash runs, by -c and on stdin, with a git that records a push and runs nothing), f23-review/ (F23's first review's scripts, each adding its faults or mutants in memory; label_delete_lost_main.py is F27's reproduction), and probe_limited.py and probe_lines.py (the F23 worker's probes of a rate limit's refusal).
