# flowbench's first run, pre-registered (draft)

What bench.yml and the session route run in real mode, to be written down
before any agent runs, so the instances, the arms, the settings and the
analysis are fixed first and the numbers read afterwards. The numbers in
angle brackets are the owner's to choose (README.md says where); once the
first real run starts, a change to this file is a new benchmark under a
new tag, not an amendment of the one that ran, as coordbench's PLAN.md
rules.

## Question

Does Symphony's flow (flowbench's symphony arm: an issue claimed by the
first push of its branch, a draft pull request, a required check, a
reviewer's lenses, a fix round, a merge on green) resolve as many SWE-bench
Verified issues as the owner's map-reduce script (the script arm: build,
stack, review through three lenses, verify each finding, fix), at what cost
in tokens and time, and how does each stand to one agent alone (solo)?

## Instances

The pool is the 93 instances that are in both SWE-bench Verified and
SWE-bench Lite, read from github.com/SWE-bench/swe-bench-tasks at the
commit the harness pins (task.yaml's datasets list carries both names):
human-verified as solvable and well specified, and lite, so a pilot's
minutes go to the flow and not to the hardest repositories. The order is
nested and stratified: by repository, then by the difficulty band the
Verified annotators gave the instance, seed 0, equal allocation (flowbench's
tasks.py, `order`); the sample of size N is the first N of the order, so a
run grows by taking more of the same order, and a run cut short is still a
balanced sample. An instance whose image cannot be pulled on the route, or
whose gold patch does not grade there (the survey step, below), is left
out before the order is drawn and named in the report.

Every arm runs every instance of the sample, so the arms are compared on
the same instances.

## Arms

Three, in this order of interest: symphony, the arm under test; script,
the owner's own flow, the naive approach of the two documents; solo, one
agent alone, the leaderboard's shape and the floor the other two must
earn their cost against. The script arm runs with one builder in the first
run (`builders = 1`); K candidates in K worktrees is the first ablation
after it, not part of this run. framework-langgraph joins when it is
built, as a fourth arm under a new tag.

## Settings

- Agents: Claude Code, the version the harness pins at the first real
  dispatch; model <claude-sonnet-5-5, as coordbench's runs, unless the
  owner names another> for every agent of every arm; local tools only
  (WebFetch and WebSearch off); no turn cap; <45> minutes of wall clock
  per agent on the session route and <120> on the Actions route, the most
  its workflow allows; one seed. The reviewer's three lenses are the
  same text in script and symphony (arms/script/prompts/review.md and
  arms/symphony/prompts/review.md carry it word for word), so the flows
  differ in where the review happens, not in what it asks.
- The workspace: the instance's official image, the repository at its
  base commit at /testbed, no test patch, no gold patch; the task
  repository's checkout is never mounted, so no agent can read the hidden
  tests or the answer.
- Routes: the session route for the pilot and the steps (no token, the
  session's own subscription); the Actions route for the full run if the
  owner has set the environment `bench` and the account slots (coordbench's
  owner-todo item 3 applies unchanged).
- Resume, attempts, harness errors: coordbench's PLAN.md rules, word for
  word: a run an agent of which failed for a cause outside the benchmark
  is run again (at most three dispatches), one that ran out its time is
  kept and scored, a harness error is left out and named, and a fake
  run's tag reads fake-<tag>.
- Judging: none by a model in the run. The free counts only (findings,
  confirmations, fixes, merges, orchestration failures), read from the
  events.

## Primary outcome

resolved, SWE-bench's own verdict from its harness in its image, k/n over
every instance of the sample, each by its newest finished attempt, an
error counting as a failure. The rate on finished instances is reported
beside it.

The primary comparison is symphony against script on resolved, two-sided
at alpha 0.05 by the exact McNemar test over the instances both arms
scored; symphony against solo and script against solo are secondary. The
McNemar test takes the instances as independent trials, which instances of
one repository are not; the bootstrap intervals resample repositories for
that reason, and a significant p whose discordant instances cluster in one
repository is read with that in mind.

The primary cost comparison is tokens per instance, symphony against
script, as a paired ratio with a bootstrap interval, and tokens per
resolved instance beside it.

## Analysis, in report.py as it stands

1. The resolved rate of each arm with a 95% Wilson interval and a
   bootstrap over repositories (2,000 resamples, seed 0).
2. symphony against each other arm on the instances both scored: the
   discordant counts and an exact McNemar test; the gap in points.
3. Cost and time per instance per arm: tokens by kind, the estimated
   price, wall clock, the blocked time; the paired ratios against solo.
4. The flow tables: orchestration failures per arm; for script and
   symphony, findings raised, confirmed and fixed, and the resolved rate
   of runs with a confirmed finding against runs with none; for symphony,
   review rounds and check failures before the merge.
5. One row per instance.

## What the sample sizes can show

With the leaderboard-era rates for a Claude Code-like agent on Verified
(roughly 60 to 75% resolved) the discordant instances of two flows are
perhaps a fifth to a third of the sample. An exact McNemar test at n = 8
is never significant; at n = 32 it detects a gap of roughly 35 points or
more; at n = 93 roughly 20 points. So the pilot and the step of 32 measure
cost and time, where the differences are large, and find the instances
where the flows disagree; a gap of 10 points in resolved will not reach
significance in this run and is reported as an estimate with its interval.
A second seed on the discordant instances is the planned follow-up, not
part of this run.

## The steps, each the owner's choice

| Step | What runs | Tokens | Disk and time | Decides |
| --- | --- | --- | --- | --- |
| survey | the gold patch of each pool instance through the scorer on the route, no agent | none | one image at a time, 1 to 3 GB each, about 2 to 5 minutes per instance | which instances grade here |
| fake | every arm on <3> instances with the fake agent | none | minutes | that the path runs end to end |
| pilot | the first <8> instances of the order under the three arms, 24 runs | about one to two of the account's five-hour windows, by the curse experiment's rate (a guess until measured) | one lane, images ahead | the cost per run, the real rates to size the step |
| step | the first <32>, 96 runs | about four to eight windows | up to three lanes | cost with intervals; the discordant instances |
| full | the pool, 279 runs | about twelve to twenty windows, or the Actions route | the Actions route is sized for it | the pre-registered answer |
| second seed | the discordant instances again | by their count | | whether the disagreements hold |

No step starts without the owner's word and its number; the thread names
the count and the windows before each.

## What is not claimed

The leaderboard's numbers are not reproduced: its entries are scaffolds of
their own on API models with their own budgets, and the bash-only track
runs mini-swe-agent; flowbench's solo arm is Claude Code on a subscription
with local tools and a wall-clock limit, and sits beside them for
orientation only (PARITY.md). CAID's and STORM's numbers are on other
suites with other agents. The comparison is between flows on the same
agent, instances and day.
