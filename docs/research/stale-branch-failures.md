# Stale branches: the curse of coordination in this project's own history

Source: the thread "Stale branch failure statistics", 2026-10-20, on the
owner's ask of 20:27 UTC to collect the failure statistics of branches
going stale when another pull request lands, as the first empirical test
of the protocol, and his note of 20:28 UTC that this is the curse of
coordination. Every number below was read from GitHub's REST API at about
20:50 UTC by `python3 tools/staleness.py collect --repo <repository>`
(the site with `--default-branch master`) and reproduces with that
command; reading spends no Claude run.

## What is happening

Every default branch here but symphony-app's had a ruleset whose required
check carried "Require branches to be up to date before merging" (the
strict policy), read at 20:45 UTC: symphony-template, symphony-protocol,
symphony-start and SchwingNet true, symphony-app false, the site with no
rule at all. Under that rule each landing makes every other open pull
request un-mergeable until its branch takes the default branch in and the
check passes again on the new head. With many threads at once, finished
and green work waits behind each landing and runs its check again, and
the next landing can make it stale again before that run ends. That is
the curse of coordination in its mechanical form: the cost of a piece of
work grows with the parallel work beside it, even when nothing conflicts.

## What the history says

| repository | merged | took main in | catch-ups | stale after green | stale wall-clock | check runs | redone on catch-up heads |
|---|---|---|---|---|---|---|---|
| symphony-template (strict) | 256 | 128 (50%) | 217 | 88 (34%) | 79.3 h, median 15 min | 524 | 182 (35%), 9.4 of 23.2 runner hours |
| symphony-protocol (strict) | 57 | 24 (42%) | 40 | 6 (11%) | 43.2 h, median 53 min | 153 | 27 (18%), 6.4 runner hours |
| symphony-start (strict) | 67 | 13 (19%) | 18 | 5 (7%) | 4.6 h | 109 | 11 (10%) |
| symphony-app (not strict) | 66 | 17 (26%) | 29 | 4 (6%) | 14.3 h | 109 | 12 (11%) |
| the site (no rule, no checks) | 115 | 46 (40%) | 71 | - | - | 0 | - |
| SchwingNet (strict, two days old) | 7 | 1 | 1 | 0 | 0 | 16 | 0 |

"Took main in" is a merged pull request whose branch carries at least one
catch-up, a merge of the default branch into it (17 of the template's were
GitHub's Update branch button, the rest made in a session's clone).
"Stale after green" is one whose finished work had passed the check and
which then had to take the default branch in before it could land; its
wall-clock is from that first green to the merge.

The dose-response is the curse's signature. In symphony-template, sorted by
how many other pull requests were at work at some moment of each one's
life:

| others at work | merged | took main in | stale after green | runs redone | stale hours |
|---|---|---|---|---|---|
| 0 | 63 | 8% | 0 | 4 of 74 | 0 |
| 1-2 | 60 | 43% | 18 | 26 of 105 | 8.8 |
| 3-5 | 86 | 62% | 40 | 73 of 199 | 22.7 |
| 6-10 | 40 | 93% | 25 | 68 of 124 | 17.5 |
| 11 or more | 7 | 100% | 5 | 11 of 22 | 30.3 |

Alone, a pull request almost never had to redo anything; beside six or
more others, nearly every one did, and over half of their check runs were
the same work checked again. By day the cost rose with the number of
threads: 2026-10-18, 66 merges, had 33 pull requests go stale after green
and 58 redone runs.

## Mapped onto coordbench and MAST

- CooperBench's curse is that two agents doing the work of one do worse
  than one, at about twice the cost (docs/research/curse-of-coordination-full-run.md:
  every two-agent arm cost about twice solo per pair). Here the cost side
  shows at landing: 35% of the template's check runs and 41% of its
  runner hours were catch-up work, and 34% of its pull requests waited a
  median 15 minutes, 79 hours in all, finished and green.
- coordbench's naive-merge conflicts are the conflict side. History keeps
  no trace of whether a catch-up merge had a conflict to resolve, which is
  why the workflow now snapshots GitHub's own word on every open pull
  request (behind, dirty, mergeable false) each time the default branch
  moves.
- MAST's FM-1.3 (step repetition) is the redone check and the repeated
  catch-up; a pull request taking main in four times is one step repeated
  four times. Turning the rule off moves the risk to FM-3.2 and FM-3.3
  (incomplete and incorrect verification): a pull request is then checked
  against an older default branch, so two that pass alone may fail
  together, which the record counts as the default branch's own failed
  check runs (default_branch_checks). Before the change, symphony-template's
  last 100 such runs had 1 failure.

## The protocol on against off

Only 8 of symphony-template's 256 merged pull requests came from a claim
branch (claude/<issue>); the project's threads work on branches of their
own and claim no issue, so this history is the protocol switched off. The
8 claim pull requests had 1 catch-up between them, against 51% of the
rest, but they are from 2026-10-09 to 2026-10-14, when few threads ran at
once, so that is no comparison. The board's "main moved" comment, the
protocol's answer to a stale branch, reaches only claim branches, and it
was posted on none of these pull requests. A comparison worth the name
needs the same load with the protocol on: the record now keeps, for every
pull request, whether its branch was a claim, and the switch times below.

## Before and after

The owner asked at 20:44 UTC to turn the up-to-date rule off, and at 20:54
UTC to switch on his fine-grained locking. At 20:45:46 UTC the rule still
stood as listed above. The workflow records the rule's state in each
snapshot (`up_to_date_required`), since the ruleset's own history is
readable only by an administrator (403 to the session's token), so the
record dates each switch to within one merge. The rule went off, as the thread "Tokens and adopted repositories"
reported and a poll of rules/branches/main every 30 seconds confirmed:
SchwingNet at about 21:08 UTC, coordbench at 21:17:06, symphony-start at
21:17:08 and symphony-template at 21:31:55 (Settings run 39501080936);
symphony-app and symphony-marketplace had it off already, and
symphony-protocol's followed at 22:26:34 (below). The
first pull request to land under the new rule here, symphony-template
#304, was green at 21:15, called behind after #301 landed at about 21:19,
and merged at about 21:32 as it stood, with no catch-up and no second run;
this note's own pull request, #302, went stale twice before the switch
and was brought up to date twice. The fine-grained locking thread's
overlap check (docs/research/overlap-check-instead-of-up-to-date.md),
turned on by a switch file the protocol's 0.6.0 sync brings, marks the second
"after". The comparison to make once a
few days have passed is the same table split at each switch: catch-ups and
stale-after-green should fall towards symphony-app's level, and the default
branch's own failed checks are the price to watch.

## A second failure class: one cause that stops every pull request

From 22:00 UTC on 2026-10-20 tests/test_pool.py failed on every pull
request in symphony-template, since a test pinned a reset time that the
clock then passed; the thread "Fine-grained locking on" fixed it. This is
not staleness: no landing caused it and no catch-up cures it, yet it
blocks all open work at once, as a blocker issue does under the protocol.
The record shows it as failed check runs on the pull requests' own heads
and on the default branch's own runs (default_branch_checks) on the same
day, and it is kept apart from the catch-up counts, which count only runs
on catch-up heads. Separately, symphony-protocol's up-to-date rule went off
at 22:26:34 UTC (its #59, Settings run 39508115798), the last of the
seven repositories; its 0.6.0 release, which carries the overlap check,
was tagged at 22:14:33 UTC.

The overlap check went live on symphony-template's main when #315 merged
at 23:04:45 UTC, at advise. Until symphony-protocol 0.6.1 is vendored, the
library's protocol check still fails a pull request pushed, marked ready
or edited while behind main, so catch-up merges between 23:04 UTC and that
sync are the protocol check's, not the up-to-date rule's; the clean
"after" starts with the 0.6.1 sync (docs/research/overlap-check-instead-of-up-to-date.md,
section 5).

## What history can and cannot recover

Recovered: each pull request's commits with their parents (so a catch-up
is told from own work, and the landings it took in are named), forced
pushes, ready and auto-merge events, the board's comments, and every run
of the check with its head, times, attempt and conclusion. Not recovered:
whether a catch-up merge had conflicts; whether a forced push was a rebase
onto the default branch or new work (32 in the template, counted apart);
when a pull request became behind (GitHub keeps no history of
mergeable_state); and the work a session did locally to catch up that it
never pushed. The snapshot covers the first and third from now on.

## Continuous collection

.github/workflows/staleness.yml runs on every merge into the default
branch, daily as a fallback and by hand, on GITHUB_TOKEN alone. It records
the moment's snapshot, reads the newly closed pull requests (at most 100 a
run, newest first, so the first run in a repository reads on over a few
runs), and adds one ordinary commit to the branch staleness holding
STALENESS.json (one record per closed pull request and the summary),
SNAPSHOTS.jsonl and REPORT.md, the latter also on the run's summary page.
Native first: GitHub keeps the history for good, so the record is rebuilt
from it rather than counted by a server; no webhook and no Claude run.
