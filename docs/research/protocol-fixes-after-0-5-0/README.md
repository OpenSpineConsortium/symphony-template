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

0.5.1 will carry what main holds since the commit that raised it to 0.5.0 (68946e6, merged as ec49498): #38, #39 and #40, and F22 to F28 with the deep lane's SIGTERM test, all merged by 2026-10-18 (below), with F29 and F30 if they merge first. Raising the version to 0.5.1 is a pull request of its own; its release waits for the owner's approval as 0.5.0's does.

## Where it stands on 2026-10-18

Updated by the thread "Protocol fixes toward 0.5.1" (the 2026-10-16 handoff's part 2.1, taken on from another account). Every fix planned for 0.5.1 has merged in OpenSpineConsortium/symphony-protocol, each after its checks and at least two adversarial reviews, with main's tree compared with the head's after the merge:

- F26, #44, merged at 73619e3: the guard reads long options as getopt_long does, and the wrappers' option tables.
- F22, #42, merged at 4e1eb0b: a reopened issue is freed of the labels its ended claim left.
- F23, #41, merged at c6e8e1f: a call GitHub refused for a rate limit or a 5xx is not read as one that wrote nothing.
- F25, #43, merged at a272513: the guard's reading of a command it cannot read whole, here-document bodies cut out, and its length, depth and time limits.
- F27, #46, merged at fcbe822: a label whose removal GitHub made but answered with a 5xx or no answer is put back unless the call wrote nothing.
- F28, #47, merged at 930290e: env's words read as GNU env reads them (every word holding = after its options an assignment, a lone - ending them, -S split as env.c splits it, every mix of set and unset ${NAME} up to six names), and no helper the template's hook calls raises. Found by F26's review; three review rounds.
- The deep lane's SIGTERM test, #49, merged at fdac907: its test parts wait in short sleeps, since one long sleep slept through a SIGTERM caught just before the sleep's system call (about 1 in 1,000 runs under load); the library was right.
- F24, #48, merged at a4ff6c3: every substitution's text read as commands, in double quotes, parameter expansions, arithmetic and unquoted here-document bodies too, with quoted bodies left as text. Two review rounds; the fuzz's misses went from 1,670 of 5,599 on main to 1 of 9,557.

Mutants: 194 within the bound of 200 on main a4ff6c3.

The reviews found more, each now its own branch:

- F29, branch claude/owner-decisions-f29-words-built: words bash builds that the guard reads otherwise: ANSI-C quoting (`git push origin $'main'`), a substitution inside a word (`git pu$(true)sh origin main`), an empty expansion as the command word (`$NOPE git push origin main`), a bare `GIT_DIR=` assignment judged only in the session's clone, and lexer edge cases (a `#` after a line continuation, a substitution in a here-document's delimiter, arithmetic around a quoted nested here-document, the one miss F24's second review left).
- F30, branch claude/owner-decisions-f30-reopen-rename-back: F22's review met G1 or G11a in a search of reopened issues to depth 5, on paths where a released branch is renamed back.

What the reviews found about the template, for its follow-up below: its hook, tools/guard_push.py, calls simple_commands, push_arguments and refusal itself and never guard.refused_push, so F21's, F24's and F25's readings never reach it, and its own first test (`"push" not in command`) lets `git pu""sh origin main` through; it has no length or time limit either. With 0.5.0's library a command like `cat <(git push origin main)` passes it. Switching it to guard.refused_push, as the follow-up already says, closes all of these.

## Paused on 2026-10-18 at 06:20 UTC, for a model switch

- F30 merged as symphony-protocol#50 (c11e0d7), harness only: the model merges only what the required check passes and renames only to a free name.
- F31 is symphony-protocol#52, a draft. CI was green at 0593edc. Its first adversarial review found the check fails open when git is missing or refuses the checkout; misses a stray under a head that is itself a merge, checked out at the head; misses a claims folder made a symlink; lets a stale copy on main back in under a non-strict ruleset; and over-refuses on a head checkout, where a two-dot diff reads main's deletion as an addition. 74e5ff8 is unfinished work on these. The pull request's top comment lists each finding and the next steps.
- F29 is symphony-protocol#53, a draft. The fix at 2f32727 was green, with 206 mutants and the lane's bound raised to 250. Its first review found six misses (a line continuation inside the verb past run()'s pre-filter, coproc, a ${x:-...} default with blanks, array subscripts, $'..' in a braced default, extglob) and three over-refusals (`$B:$B` read as `:`, a word made only of expansions, `--no-verify${NOPE}`). 05dcbd8 is unfinished work on these. It merges main in only after #52 lands, so the mutant records are reconciled once.
- Each still needs its fixes finished, a second review round and a merge once green. Then comes the template follow-up below, once the owner has published 0.5.0.

## Checkpoint on 2026-10-18 at 13:10 UTC

- F31 merged as symphony-protocol#52 (4905fcc), after two adversarial reviews. The required check now reads two changes, the test merge's and the branch's own from every merge base, and fails a pull request that adds or changes a claim file other than its own issue's. It also refuses a claim folder or claim file that is not a plain file, and a claim path written in another case. It runs git with every GIT_* variable stripped, and fails closed when git cannot read the change. What it leaves: with no .git in the checkout it judges only the head's own claim file, as before F31, since the template's TheProtocolCheck tests run that way; and a two-argument caller of problems_for (symphony-app) judges no change.
- F29 is symphony-protocol#53, ready at 0d1dd26 with both review rounds answered and main merged in. check.sh passed locally; 225 mutants against a bound of 250. Its last local mutation-lane run and an over-refusal fuzz, comparing a4ff6c3 with the head over session-style commands, were stopped for this checkpoint, so they are the next session's first check. The repository has no auto-merge: merge it by hand once CI is green, with the head sha copied from git.
- Then, after the owner publishes 0.5.0: the template follow-up below, then the 0.5.1 version raise in its own pull request.

## The template's follow-up for 0.5.1

Not started, on purpose. The template vendors 0.5.0 (the commit that raised it); if it vendored main now, the sync that follows the owner's approval of 0.5.0 would open a pull request taking the template back to 0.5.0. So once 0.5.0 is published, one symphony-template pull request vendors the library's main, switches tools/guard_push.py to guard.refused_push (F21's fix reaches the template's hook only then), has tools/metrics.py's Budgeted count its calls from the client's `made` (the first rate-limit review's sixth finding: the tries the client makes again are not in Budgeted's own count), and brings docs/agents/PROTOCOL.md's Release in line with F22's and F23's spec text. The durable decision in CLAUDE.md that a release puts the labels back when its comment fails has been untrue since F20; it is corrected by a line tagged Decision: in conversation for the checkpoint skill, never by hand.

## How the thread worked, for whoever takes it on

- One library worktree per branch (`git -C /home/user/symphony-protocol worktree add -b <branch> /home/user/proto-<name> origin/main`), every git command with -C and an absolute path, never a bare git stash, commits as `-c user.name=Claude -c user.email=noreply@anthropic.com` with the two trailers.
- Each pull request: `bash scripts/check.sh` and `python3.12 -m validation.mutants` green, an adversarial review, its fixes, a second review of the fixes, then ready by `gh api -X POST repos/OpenSpineConsortium/symphony-protocol/pulls/<n>/ccr/ready_for_review` (GraphQL is blocked), the check that the ready event starts waited for, a merge commit with expectedHeadSha copied from git, and main's tree compared with the head's after.
- Main is brought into a branch by a merge, never a rebase. The counts meet at each merge: the exact mutant count and bound in tests/test_validation_mutants.py, validation/README.md's account of the lane and GUARANTEES.md give the running total (134 within 150 on main 49a6192); a finding's own DESIGN.md entry keeps the count at its own fix (F20's 117, F21's 125).
- A rendered string is part of the interface: changed only on purpose, and said so in the pull request.

## The first step from a new account

Attach OpenSpineConsortium/symphony-protocol with push access, clone it, and fetch the F29 and F30 branches; carry each through its checks, two adversarial reviews and the merge. Then, once the owner has published 0.5.0, the template's follow-up and the raise to 0.5.1.

## Files here

- drafts/: the workers' draft commit messages for the unfinished work (F23's finding 3, F26's fix and harness).
- reviews/: F23's first adversarial review and its fix report, the rate limits' second review and first fix report, the reports the next reviews build on (F21's reviews are in symphony-protocol#39's description).
- scripts/: guard-holes-probe.py and guard-two-bodies-probe.py (F24, F25 and F26 on main, run as `python3.12 -I <script> <library checkout> <a clone on main>`), f25-probe.py, heredoc-probe.py and f25-bash/ (the F25 worker's record of which pushes bash runs, by -c and on stdin, with a git that records a push and runs nothing), f23-review/ (F23's first review's scripts, each adding its faults or mutants in memory; label_delete_lost_main.py is F27's reproduction), and probe_limited.py and probe_lines.py (the F23 worker's probes of a rate limit's refusal).
