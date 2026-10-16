# Parity with SWE-bench

Source: the thread "Agentic workflow benchmarks" of the project symphony,
2026-10-16; no Claude Doc or artifact.

The rule, taken from coordbench's PARITY.md: flowbench measures every
measure SWE-bench measures, as close to SWE-bench's way as it can, and
differs only for a stated reason, either because the difference is better
or because the two cannot be made the same. "SWE-bench" here is three
things, and each row says which:

- the harness, the swebench package on PyPI, 5.0.2 at the time of writing
  (github.com/SWE-bench/SWE-bench), whose `swebench eval` is the one
  scorer the leaderboard accepts;
- the task repository, github.com/SWE-bench/swe-bench-tasks, which holds
  every instance's files and which `swebench dataset build` compiles into
  the parquet files the harness reads;
- the leaderboard at swebench.com, read here only from the harness's docs
  and README (the site is blocked from the session).

Status, as coordbench uses the words: same, equivalent, different, not
measured.

**1. resolved.** Status: same.
- SWE-bench: harness/grading.py: resolved when every FAIL_TO_PASS test
  passes and every PASS_TO_PASS test passes after the patch, read from the
  log eval.sh leaves, parsed by the instance's log_parser.
- flowbench: score.py writes the run's one prediction and calls
  `swebench eval` on the dataset compiled from the task repository
  (`score.py build`), then reads the summary's resolved, unresolved,
  empty-patch, error and infrastructure-failure lists and the instance's
  report and log; result.json's scoring block copies the verdict and the
  reason: unresolved, empty_patch, patch_failed when the harness could not
  apply the patch (run_instance.log says so), which is the arm's failure,
  and error or infra_failure, which are the harness's and leave the run
  out.

**2. The test lists.** Status: same.
- SWE-bench: tests.json per instance in the task repository (FAIL_TO_PASS,
  PASS_TO_PASS), the harness's test_spec built from it.
- flowbench: never read by an agent; tasks.py reads the counts for the
  strata and the report, nothing else.

**3. The prediction.** Status: same.
- SWE-bench: a JSONL line per instance: instance_id, model_name_or_path,
  model_patch.
- flowbench: prediction.jsonl per run, model_patch the workspace's change
  against the commit it started at (the base commit under the image's own
  build commit, where the harness applies a patch), new files included,
  file modes, test caches and the files the image already held untracked
  left out; model_name_or_path the arm and the model, so a scorer run
  names its arm.

**4. The image.** Status: same.
- SWE-bench: task.yaml's image, swebench/sweb.eval.x86_64.<instance> on
  Docker Hub; the harness pulls it, or builds it from the task's
  Dockerfile with `--task-repo`.
- flowbench: the same image, pulled through mirror.gcr.io where Docker
  Hub rate-limits the host and retagged under its own name so the harness
  finds it; the image id is in result.json's provenance. The harness
  scores in that same image, since flowbench never passes `--task-repo`,
  which would rebuild it. The agents' workspace is the image's /testbed
  copied out, and a container of the image runs it at /testbed for the
  repository's tests, where the harness runs them too.

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
  cause outside the benchmark is run again, at most three attempts
  (backlog.py's requeue stops there); one that ran out its time is kept;
  a harness error is left out and named.
- Why: a usage limit or the scorer's infrastructure measures the route,
  not the flow.

**7. Time and turns.** Status: different.
- SWE-bench: the harness sets no limit on the agent; the leaderboard
  reports what each entry chose.
- flowbench: a wall-clock limit per agent and per run (PLAN.md: 45 and
  120 minutes), no turn cap; an agent that runs out its time is counted
  as a timeout, apart from the arm's orchestration failures.
- Why: a subscription's window is the budget, and a flow with five stages
  must fit the same clock as one agent.

**8. Cost.** Status: equivalent.
- SWE-bench: the Verified evaluation lists an average cost per instance
  for entries that report it (eval/SWE-bench_Verified.yaml's
  swe_bench_average_cost), from API prices.
- flowbench: tokens by kind from each agent's stream-json output, each
  message counted once, and Claude Code's own cost where it reports one,
  else the tokens at Anthropic's list prices, cache reads included; an
  agent that left no stream is counted as uncounted, so its run never
  reads as a cheap one; on the session route the inherited prompt
  inflates every arm alike, and the record says which route it is.
- Why: no API is billed; the price is an estimate, marked as such, as
  coordbench's cost_source says.

**9. The tool surface.** Status: different.
- SWE-bench: each entry's own; the bash-only track gives mini-swe-agent
  bash alone.
- flowbench: Claude Code's built-in local tools with WebFetch, WebSearch
  and the Agent tool off, the login's settings and MCP servers left out,
  and each agent's tool list read back from its stream into the record;
  the arm's own commands (the gate's for symphony, once it is wired).
- Why: the flow is the variable; the web is a confound and a cost.

**10. The agent.** Status: different.
- SWE-bench: each entry's scaffold and model.
- flowbench: Claude Code on a subscription token, one model, one version,
  for every arm.
- Why: the comparison is between flows on one agent.

**11. Hidden tests and the answer.** Status: equivalent.
- SWE-bench: the test patch and the gold patch are applied by the harness
  only.
- flowbench: the workspace is the image's /testbed at the start commit;
  the task repository's checkout, which holds gold.patch and test.patch,
  is never mounted, copied into a container or named in a prompt. The
  agents run on the host, which holds that checkout, so the prompts keep
  them inside the workspace and the audit reads every agent's stream: a
  run that names the task repository or either patch is excluded and
  named, and a hidden test's name (a FAIL_TO_PASS test the test patch
  adds) is recorded.
- Why: a container per agent would wall the checkout off, at the cost of
  running Claude Code inside every instance's image; the audit makes a
  breach visible instead, and a run that breaches is never counted.

**12. Gradeability.** Status: equivalent.
- SWE-bench: the Verified set was annotated as solvable and gradeable.
- flowbench: the survey step scores each pool instance's gold patch on the
  route before the order is drawn, as coordbench's survey mode does, since
  an image that does not pull or a test that needs the network fails
  here for the route's reasons.

**13. The scorer's version and its cache.** Status: same.
- SWE-bench: the harness caches by run_id and instance_id and will not
  re-score an instance under a used run_id.
- flowbench: the scorer's version is pinned and recorded in result.json's
  provenance; every attempt scores under a run_id of its own (tag, arm,
  instance, attempt).

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

**16. Agents that run at once.** Status: different, by the arms' design.
- SWE-bench: one agent per instance.
- flowbench: a parallel stage's agents share one workspace and one
  container: the script's three reviewers and its verifiers, and
  symphony's reviewers, read the same checkout and may run its tests at
  once, while the builders each have a copy and a container of their own.
  The review and verify prompts tell each agent to change nothing in the
  repository and never to read another agent's files, and the record
  keeps every agent's stream, so a stage whose agents disturbed each other
  shows in its transcripts.
- Why: a reviewer reads the change under review, which is the shared
  checkout; a copy per reviewer would cost a copy of the repository per
  lens and change nothing it reads.

## Producing each measure

| Measure | Command | Calls a model |
| --- | --- | --- |
| the dataset the scorer reads | `python3 flowbench/score.py build <checkout> -o <dir>`, once per commit of the task repository | no |
| resolved, reason | `python3 flowbench/score.py score <run dir> --dataset <dir>/SWE-bench_Verified` (fake: `--fake`), which `run.py run` calls at the end of every attempt | no |
| tokens, cost, time | written into result.json by `run.py run` from each agent's stream-json output (the result event's usage and Claude Code's own cost, else the list price of the tokens) and the clock | no |
| the report | `python3 flowbench/report.py --logs <logs> --tag <tag> --arms symphony,script,solo --instances @<sample>` | no |
| the audit | audit.json beside result.json, written by `run.py run`: a harness error (no image, no docker, the scorer failing, an agent ended by a usage limit) and a run whose agents' streams name the benchmark's files are left out of the report and named; an agent's error or a missing stage output is the arm's orchestration failure, counted; a timeout or a turn limit is counted apart | no |
