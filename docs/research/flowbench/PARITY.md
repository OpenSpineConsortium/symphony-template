# Parity with SWE-bench

The rule, taken from coordbench's PARITY.md: flowbench measures every
measure SWE-bench measures, as close to SWE-bench's way as it can, and
differs only for a stated reason, either because the difference is better
or because the two cannot be made the same. "SWE-bench" here is three
things, and each row says which:

- the harness, the swebench package on PyPI, 5.0.2 at the time of writing
  (github.com/SWE-bench/SWE-bench), whose `swebench eval` is the one
  scorer the leaderboard accepts;
- the task repository, github.com/SWE-bench/swe-bench-tasks, which holds
  every instance's files and is what the harness reads with `--task-repo`;
- the leaderboard at swebench.com, read here only from the harness's docs
  and README (the site is blocked from the session).

Status, as coordbench uses the words: same, equivalent, different, not
measured.

**1. resolved.** Status: same.
- SWE-bench: harness/grading.py: resolved when every FAIL_TO_PASS test
  passes and every PASS_TO_PASS test passes after the patch, read from the
  log eval.sh leaves, parsed by the instance's log_parser.
- flowbench: score.py writes the run's one prediction and calls
  `swebench eval` with the task repository, then reads results.json's
  resolved_ids and the per-instance report; result.json's scoring block
  copies the verdict and the reason (unresolved, empty_patch, error).

**2. The test lists.** Status: same.
- SWE-bench: tests.json per instance in the task repository (FAIL_TO_PASS,
  PASS_TO_PASS), the harness's test_spec built from it.
- flowbench: never read by an agent; tasks.py reads the counts for the
  strata and the report, nothing else.

**3. The prediction.** Status: same.
- SWE-bench: a JSONL line per instance: instance_id, model_name_or_path,
  model_patch.
- flowbench: prediction.jsonl per run, model_patch the workspace's
  `git diff` against the base commit, model_name_or_path the arm and the
  model, so a scorer run names its arm.

**4. The image.** Status: same.
- SWE-bench: task.yaml's image, swebench/sweb.eval.x86_64.<instance> on
  Docker Hub; the harness pulls it, or builds it from the task's
  Dockerfile with `--task-repo`.
- flowbench: the same image, pulled ahead through mirror.gcr.io where
  Docker Hub rate-limits the host and retagged under its own name so the
  harness finds it; the image id is in result.json's provenance. The
  agents work in a container of that image with the repository at
  /testbed, which is where the harness runs the tests too.

**5. The instance list.** Status: different.
- SWE-bench: the leaderboard scores all 500 Verified instances.
- flowbench: a nested stratified sample of the 93 instances in both
  Verified and Lite (PLAN.md), since a flow is run three ways and the
  budget is a subscription's windows; the arms are compared with each
  other on the same instances, and the rate is never set beside the
  leaderboard's as a comparable figure.
- Why: three arms over 500 instances is 1,500 runs; the question is the
  difference between flows, which a paired sample answers.

**6. Attempts.** Status: different.
- SWE-bench: one prediction per instance per submission.
- flowbench: coordbench's Resume rule: a run an agent of which failed for a
  cause outside the benchmark is run again, at most three times; one that
  ran out its time is kept; a harness error is left out and named.
- Why: a usage limit or a lost subagent measures the route, not the flow.

**7. Time and turns.** Status: different.
- SWE-bench: the harness sets no limit on the agent; the leaderboard
  reports what each entry chose.
- flowbench: a wall-clock limit per agent (PLAN.md), no turn cap.
- Why: a subscription's window is the budget, and a flow with five stages
  must fit the same clock as one agent.

**8. Cost.** Status: equivalent.
- SWE-bench: the Verified evaluation lists an average cost per instance
  for entries that report it (eval/SWE-bench_Verified.yaml's
  swe_bench_average_cost), from API prices.
- flowbench: tokens by kind from each agent's transcript, summed once,
  priced at Anthropic's list prices, cache reads included; on the session
  route the inherited prompt inflates every arm alike, and the record says
  which route it is.
- Why: no API is billed; the price is an estimate, marked as such, as
  coordbench's cost_source says.

**9. The tool surface.** Status: different.
- SWE-bench: each entry's own; the bash-only track gives mini-swe-agent
  bash alone.
- flowbench: Claude Code's local tools, WebFetch and WebSearch off, the
  arm's own commands (the gate's for symphony).
- Why: the flow is the variable; the web is a confound and a cost.

**10. The agent.** Status: different.
- SWE-bench: each entry's scaffold and model.
- flowbench: Claude Code on a subscription token, one model, one version,
  for every arm.
- Why: the comparison is between flows on one agent.

**11. Hidden tests and the answer.** Status: same.
- SWE-bench: the test patch and the gold patch are applied by the harness
  only.
- flowbench: the workspace is the image's /testbed at the base commit; the
  task repository's checkout, which holds gold.patch and test.patch, is
  never mounted or copied into a container, and the prompts name neither.

**12. Gradeability.** Status: equivalent.
- SWE-bench: the Verified set was annotated as solvable and gradeable.
- flowbench: the survey step scores each pool instance's gold patch on the
  route before the order is drawn, as coordbench's survey mode does, since
  an image that does not pull or a test that needs the network fails
  here for the route's reasons.

**13. The scorer's version and its cache.** Status: same.
- SWE-bench: the harness caches by run_id and instance_id and will not
  re-score an instance under a used run_id.
- flowbench: the scorer's version is pinned and recorded; every attempt
  scores under a run_id of its own (tag, arm, instance, attempt).

**14. The leaderboard's figures beside ours.** Status: different, for
orientation only.
- SWE-bench: the leaderboard's Claude Code entries, when read on a runner
  that reaches the site.
- flowbench: the report prints them in a separate table, named as the
  leaderboard's, never in the arms' table.

**15. The symphony arm's gate.** Status: shape only, until the gate is
wired.
- The design: the claim protocol's required check and merge gate decide
  what the worker may push and when the pull request lands
  (sdlc_protocol.gate over its bare-git adapter, as coordbench's sdlc arm
  vendors it).
- The scaffold: the arm runs its three stages (work, review, answer) in
  order with no gate between them, so it measures the protocol's shape (a
  claim branch, a pull request, a review by lenses, an answer to every
  finding) and not its enforcement; a measured run waits for the gate
  wiring (scaffold/flowbench/arms/symphony/README.md), and the record of
  every run before it says `shape only` in its arm's description.

## Producing each measure

| Measure | Command | Calls a model |
| --- | --- | --- |
| resolved, reason | `python3 flowbench/score.py <run dir> --task-repo <checkout>` (fake: `--fake`), which `run.py run` calls at the end of every attempt | no |
| tokens, cost, time | written into result.json by `run.py run` from each agent's stream-json output (the result event's usage and Claude Code's own cost, else the list price of the tokens) and the clock | no |
| the report | `python3 flowbench/report.py --logs <logs> --tag <tag> --arms symphony,script,solo` | no |
| the audit | audit.json beside result.json, written by `run.py run`: a harness error (no image, no docker, the scorer failing, an agent ended by a usage limit) is left out of the report and named; an agent's error or a missing stage output is the arm's orchestration failure, counted | no |
