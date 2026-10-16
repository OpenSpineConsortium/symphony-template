# flowbench: the workflow as a plug-in

Source: the thread "Agentic workflow benchmarks" of the project symphony,
2026-10-15 and 2026-10-16, from the owner's two attached documents; no
Claude Doc or artifact. Written 2026-10-16 for item 6 of the owner's handoff message of 2026-10-15
23:35 UTC: "More sophisticate agentic workflow development: see attached
docs for naive approach we are competing against (script debugging and
agent orchestration package) once again with real benchmarking in the
symphony protocol environment, essentially i want to build similar repos
like coordbench but for other LLM performance domains, and include other
software engineering benchmarks SWE-bench ect". This file is the design;
PLAN.md beside it is the draft pre-registration of the first run, PARITY.md
sets SWE-bench's measures beside flowbench's, scaffold/ is the harness in
the state that becomes the new repository's first commit, and README.md is
the thread's handoff with the owner's decisions and clicks.

## In one paragraph

coordbench measures how the way agents are wired together changes what
they get done, on CooperBench's task pairs. flowbench measures the next
thing up: how the way work flows through agents and gates changes what
gets done, on SWE-bench's issues. It keeps the task, the agent and the
scoring fixed (a SWE-bench Verified instance, Claude Code, SWE-bench's own
evaluation in SWE-bench's own image) and makes the flow a plug-in (an
arm): one agent alone; the owner's own map-reduce script (build in
worktrees, stack, review through several lenses, verify each finding, fix);
the same stages run by an orchestration framework; and Symphony, where the
flow is the repository's own pull-request lifecycle, with no script at all.
Two flows are then compared on the same issues, at the same budget, by the
same verdict, and the number that comes out is what Symphony may claim.

## What the two documents are

The owner attached two documents. They are the competitor, read as such.

1. "Script Debugging Orchestration" is a chat in which the owner pasted a
   Workflow script of Claude Code's own (the `meta`, `agent`, `parallel`,
   `phase` API) and asked what it was. The script is four phases: Build,
   three agents in parallel git worktrees, each on one planned fix with a
   plan and an adversarial check of the plan to read first; Stack, one
   agent that merges the three branches, resolves conflicts "keeping both
   intents", runs the suites and builds two dependent features on top;
   Review, four agents over the combined diff, each with one lens, each
   returning structured findings; Fix, one verifier per finding told to
   refute it and to default to "not real", then one agent that fixes the
   confirmed findings. The script failed to parse on a quoting error in
   line 77 before any agent ran, which is where the chat began, and the
   chat's answer called the design novel on four counts: worktree
   isolation, a stacking agent, multi-lens review and a "hallucination
   firewall" (the verify step), citing a guide, a Reddit thread, a pattern
   site and a vendor blog as the literature.
2. "Agent Orchestration Package Search" is a generated report that reads
   the same script block by block and recommends migrating it to packages:
   LangGraph.js (a stateful graph with checkpointing, retries and the Send
   API for fan-out) in place of `parallel()`; Temporal.io (durable
   execution, sagas with compensating transactions) around the merge;
   OpenHands' agent server or the STORM architecture (a shared workspace
   with optimistic concurrency control on writes) in place of worktrees
   and the merge step; and Zod schemas with a bounded self-healing loop in
   place of the verify step. It names CAID, the pattern the script
   implements, and quotes two numbers: CAID's gains over one agent (26.7
   points on PaperBench, 14.3 on Commit0) and STORM's over the worktree
   baseline on Commit0-Lite (82.5% against 63.8% macro pass rate).

What is true of both: neither measures the script. The first calls it
novel from its shape; the second calls it fragile from its shape, and its
remedies are each a dependency, a server, or an API key. The two papers
behind the numbers are real (CAID is arXiv 2603.21489, Geng and Neubig,
2026-03-23; STORM is arXiv 2605.20563, Liu and others, 2026-05-21), their
results are self-reported on benchmarks other than SWE-bench (PaperBench
and Commit0, paper reproduction and library-from-scratch, both
parallelizable by construction), with models other than Claude Code, and
neither was reached from this session (arxiv.org is blocked; both were read
through search summaries, see Sources). Nothing in either document says
what the script's four phases buy on an issue a single agent could fix, or
what they cost; and that is the question a benchmark answers.

What Symphony says instead, from the taxonomy spec of 2026-10-15: the
flow is the repository's own lifecycle. An issue is claimed by the first
push of its branch, worked in a draft pull request, held to a required
check, reviewed, fixed, merged. There is no orchestration script to
debug, because the orchestration is GitHub's own events and a few hundred
lines of standard-library Python that the protocol's validation harness
checks; a reviewer is a worker reading a pull request; a verifier is the
check that must pass; the "stacking" is a merge on a green check. Its
guarantees are bookkeeping ones (no two workers on one issue, no lost
work, no silent overwrite), not code quality, and the spec says so. Whether
that flow resolves more issues than the script, or the same at a lower
cost, is unknown today. flowbench exists to find out, and to say so with
intervals.

## The family: benches like coordbench

One contract, written in coordbench/README.md and kept here: a harness
holds the task, the agent and the scoring fixed and makes one thing a
plug-in, so two settings of that thing can be compared on the same work;
every run is pre-registered before it starts (the list, the arms, the
settings, the analysis), rehearsed in a fake mode that spends no usage,
audited so that a run the harness spoiled is named and left out, scrubbed
of credentials before anything is published, and bundled into the
repository with its verdicts; and a parity file sets the published
benchmark's every measure beside the harness's, row by row, with the
reason for each difference.

Three things plug in, and each is a domain of its own:

| Plug-in point | What varies | The domain | The repository |
| --- | --- | --- | --- |
| The arm | how agents are wired together: alone, by messages, a shared remote, a team, a claim protocol | coordination | coordbench, on CooperBench's pairs (exists) |
| The flow | how work moves through agents and gates: one agent, a script of phases, a framework's graph, a repository's lifecycle | workflow | flowbench, on SWE-bench Verified (this design) |
| The kit | what one agent carries: hooks, skills, memory, a context compressor, a profiler, a code index, fewer tools | efficiency | the owner's item 5; its arms fit flowbench's harness as kits over the solo flow, so no third repository is needed until its task suite differs |

The driver, which agent does the work, is the fourth and is held fixed
within a run (Claude Code, one model, one version); it is varied only to
check that a result is not the harness's own.

Each domain is a repository named `<domain>bench` under
OpenSpineConsortium, public and MIT like coordbench, with no secret and no
credential in it: the Claude runs draw on the owner's subscription tokens
held as organization secrets and never on an API key, as every other
Symphony repository does. A domain's repository owns its task suite, its
scorer adapter, its arms, its pre-registered plans and its bundled results;
what the repositories share is the contract above and the shape of a run's
record, so coordbench's readers (the report, the audit, the bundle, the
scrub) are copied and adapted rather than imported, since the suites
differ in what a run is (a pair of features; one issue; one library).

Why a repository per domain rather than one benchmark repository: the
template is copied whole into every adopted repository (symphony-start's
adopt.py stages every file of the tree, docs/checkpoints included), so a
harness in the template would land in every user's project; a domain's
Actions, images, environment and results are its own; and coordbench set
the precedent when it was split out of the template's experiment/ folder.

## Task suites

The suite is what a run resolves, and each suite answers a different part
of the owner's question. Reachability is from this project's cloud
sessions, whose network policy blocks huggingface.co, arxiv.org and most
paper hosts and allows github.com, raw.githubusercontent.com, pypi.org and
Docker Hub; GitHub's runners reach everything.

| Suite | Size | A task is | Where the data is | Images | From a session | Fit |
| --- | --- | --- | --- | --- | --- | --- |
| SWE-bench Verified | 500 issues, 12 repositories, Python | one repository at a commit, one issue, hidden FAIL_TO_PASS and PASS_TO_PASS tests | github.com/SWE-bench/swe-bench-tasks (every instance's problem statement, gold patch, test patch, test lists, eval.sh and image name; 2,519 instances, 500 tagged Verified, 323 Lite) | Docker Hub, swebench/sweb.eval.x86_64.<instance>, pulled through mirror.gcr.io where Docker Hub rate-limits | yes | the first suite: the issue a single agent could fix, where the flow's review, verify and fix stages either earn their cost or do not |
| SWE-bench Lite | 300 issues (323 with the dev split) | the same | the same task repository | the same | yes | the pilot pool: the 93 instances in both Verified and Lite are human-verified and well specified |
| Commit0-Lite | 16 libraries (the paper's) | a library implemented from its specification to pass a suite, many functions at once | github.com/commit-0/commit0 | its own, built | partly (the harness needs pip packages) | the parallel-work question, where CAID and STORM report their numbers; the second suite, once flowbench runs |
| CooperBench pairs | 652 tasks, 4 languages | two features on one repository, one per agent | coordbench already runs it | mirror.gcr.io | yes | coordbench's; a flow can be run on a pair, which is how the two repositories meet |
| SWE-bench Multilingual, Multimodal | 300 and 480 | as Verified, in other languages, or with images | huggingface.co only | Docker Hub | no, runners only | later, and only on the Actions route |
| Terminal-Bench, Aider polyglot | 80 and 225 tasks | a terminal task; a coding exercise | github.com (laude-institute/terminal-bench; Aider-AI/polyglot-benchmark) | own | partly | not flows: one agent, one task; they fit the kit domain, not this one |

A SWE-bench instance from the task repository is read without any
package: tasks/<instance_id>/task.yaml (repository, base commit, image,
log parser, the datasets it is in), problem_statement.md, test.patch,
tests.json (FAIL_TO_PASS and PASS_TO_PASS), gold.patch and eval.sh. The
harness's own scorer, the swebench package on PyPI (5.0.2 at the time of
writing), needs no HuggingFace dataset either: `swebench dataset build
<checkout> -o <dir>` compiles the task repository into one parquet file
per split, and `swebench eval <dir>/SWE-bench_Verified -p
prediction.jsonl --run-id <id> -i <instance>` reads the local parquet,
applies the patch in the instance's published image, runs eval.sh,
parses the log and writes logs/run_evaluation/<run_id>/<model>/<instance>/
(report.json and run_instance.log) and the summary <model>.<run_id>.json
with the resolved, unresolved, empty-patch, error and
infrastructure-failure lists. The same command given `--task-repo
<checkout>` instead rebuilds the instance's image from the task's
Dockerfile before scoring, and falls back to the published image when
that build fails, so the image scored would not be the one the agent
worked in; flowbench never passes it (the adversarial review of
2026-10-16 found this, and the first smoke test's harness log showed the
fallback). flowbench calls that scorer in a virtualenv of its own, as
coordbench calls CooperBench's, and keeps its own code to the standard
library.

## flowbench's arms

An arm is a directory: stages.json (the arm's name, its stages in order,
each with its prompt, its kind, how many agents it starts, whether they
run in parallel, what it needs from the stage before and the file it must
leave) and the prompt of every stage (scaffold/flowbench/arms/README.md
lists the keys and the placeholders). The harness, not the arm, provisions
the workspace (the image's /testbed copied out as the working directory,
and a container on the same files for the repository's tests), starts
each agent, records the events, takes the patch (`git diff` of the
workspace against the commit it started at: the instance's base commit
under the one commit the image's build adds, which is where the harness
applies a patch) and scores it. So an arm says what the agents do and in
what order, and nothing about Docker, tokens or scoring, as coordbench's
arms do.

| Arm | The flow | Agents | Needs | Status |
| --- | --- | --- | --- | --- |
| solo | one agent reads the issue and the repository and leaves a patch; the leaderboard's shape | 1 | nothing | scaffolded (prompt) |
| script | the owner's script, made for one issue: build (one builder; `--option builders=K` for K candidates, each in a copy of the workspace on a branch of its own with a container of its own, the stack stage then fetching the branches and picking by the repository's own tests), stack (merge and run the suites), review (three lenses: correctness, the repository's conventions, the issue's path end to end), verify (one refuter per finding, default not real), fix (the confirmed findings, with a test each) | 1 + K + 3 + findings + 1 | an orchestrator: the session's Workflow tool on the session route, flowbench's own stage runner (standard library, `claude -p` per stage) on the Actions route | scaffolded (stages.json and the prompts) |
| symphony | the issue becomes an issue of a repository under the claim protocol: a worker claims it (the first push of claude/<issue>), opens a draft pull request, the required check runs the repository's tests of the modules the diff touches, a reviewer worker reviews the pull request through the same three lenses as the script's and asks for changes or approves, the worker answers each thread or says why not, the merge gate merges on a green check; the patch is main's diff. The flow is the protocol's events; no orchestrator script. Decided by the protocol library (sdlc_protocol.gate over its bare-git adapter, vendored as coordbench vendors it) on the session route; by a scratch repository on GitHub with the template's workers.yml on the Actions route (symphony-github, below) | 1 worker + 1 reviewer, the worker again per review round | git_remote; the vendored library | scaffolded (prompts); the gate wiring is coordbench's sdlc arm's, to be carried over |
| symphony-github | symphony on GitHub itself: one scratch repository per instance, made from the template's protocol-only files, the issue opened by the harness, the workers in Actions on the owner's accounts, the real required check, Claude Code Review on the pull request, auto-merge; "real benchmarking in the symphony protocol environment" in the owner's words | the registry's workers | a scratch organization or a prefix, the owner's account slots, an Actions minutes budget | designed; not scaffolded, since it needs the repository and the owner's accounts first |
| framework-langgraph | the script's stages as a LangGraph.js graph (Send API fan-out, a checkpointer, retries, Zod on the findings), each node running `claude -p` on the subscription token, so the framework is measured and no API key is used | as script | Node and the packages in the arm's own image layer, never in the harness | designed; built when the owner wants the package report's remedy measured |
| caid, storm | the two papers' systems | theirs | OpenHands and an LLM API key for both; STORM's repository has no licence file | out until the owner says: both bill an API, which the project's rules forbid |

What the arms hold equal: the model, the effort (one level for every
agent, medium unless the owner names another), the agent's version, the
tool surface (Claude Code's built-in local tools, with WebFetch and
WebSearch off, as the CooperBench runs and the leaderboard's bash-only
track do, and the Agent tool off, so one agent is one process and an
arm's agent count is what its stages say), the settings (the login's own
settings, hooks and MCP servers left out: `--setting-sources project` and
`--strict-mcp-config` with an empty server list, and each agent's tools
and servers read back from its stream into the record), the time limits
(45 minutes per agent and 120 per run, no turn cap), the instance's
image, the order of the instances, and the day. What differs is the flow
alone.

## What is measured

Per (instance, arm) run, in result.json, with the audit beside it:

- Outcome: resolved, SWE-bench's own verdict (every FAIL_TO_PASS test
  passes and every PASS_TO_PASS test still passes, in the official image,
  by the official harness), and the harness's reasons when not
  (unresolved; a patch that did not apply, which is the arm's failure; an
  empty patch; the harness's own error or infrastructure failure, which
  leaves the run out). PARITY.md row 1.
- Cost: tokens by kind (input, output, cache creation, cache read) per
  agent and for the run, summed once from each agent's transcript as
  coordbench does, and an estimated price at Anthropic's list prices; the
  output count a lower bound where Claude Code's transcript gives only
  that. The session route inflates every arm alike by the session's
  inherited prompt (about 80,000 tokens per call in the curse experiment);
  comparisons hold, absolute figures do not, and the record says which
  route it is.
- Time: the run's wall clock from provision to the patch, each agent's wall
  clock, the time spent blocked on another agent or on a gate (the
  symphony arm's check, the script's stack waiting on builders), and the
  scoring's own time apart.
- The flow's own failures: an agent that ended in error for a cause outside
  the benchmark (a usage limit, a full disk, the scorer's infrastructure)
  is a harness error and the run is left out and named, as coordbench's
  audit does; a
  failure of the flow itself (a script that did not parse, a stage whose
  output the next stage could not read, a merge the stacking agent left
  broken, a verifier that confirmed nothing because its input was cut) is
  the arm's result, scored as a failure, and counted under
  `orchestration_failures`, since it is exactly what the owner's first
  document shows and the second document predicts.
- Timeouts, turn limits and exclusions: an agent that ran out of its time
  or its turns is counted apart from the orchestration failures, and its
  run is kept and scored; a run whose agents' streams name the benchmark's
  own files (the task repository's path or name, gold.patch, test.patch)
  is excluded by the audit and named, since it went looking for the
  answer, and a hidden test's name in a stream (a FAIL_TO_PASS test the
  test patch adds) is recorded beside it without excluding the run, since
  an agent may write a test of that name on its own.
- Review precision, for the flows that review: findings raised per lens,
  findings confirmed by the verifier, findings the fix stage changed code
  for, and, read against the verdict, whether a run whose review raised a
  confirmed finding resolved more often than one whose review raised none.
  This is the first measurement of the "hallucination firewall" on real
  issues that either document would have.
- Merges, for the flows with more than one branch: candidates built,
  conflicts, the stack stage's test failures, the pull requests opened and
  the review rounds.
- The flow's development cost, recorded and not compared statistically:
  the lines of the arm's orchestration (stages.json and the prompts for
  script; the protocol library's lines for symphony; the graph's lines for
  a framework arm) and the number of edits the arm took before its first
  fake run passed, from the repository's history.

Per run of the benchmark, in the report: the resolved rate per arm with a
95% Wilson interval and a bootstrap over repositories (instances of one
repository are not independent), each arm against the primary comparison
by an exact McNemar test over the instances both scored, the cost and time
per instance per arm, the review and merge tables, and one row per
instance.

## The record

A run directory per (instance, arm, attempt), under
logs/<tag>/<arm>/<instance>/attempt-<n>/:

- result.json: instance, arm, driver, route, model, effort, the agents
  (name, stage, status: success, timeout, turn_limit, usage_limit or
  error; its turns, tokens, cost and duration, and the tools and MCP
  servers its stream's init event lists), the stages in order with their
  durations, the patch's size, the scoring (resolved, reason, the
  harness's run id and failure reason), the timings (the agents' seconds
  summed and the run's wall clock), whether the run is a harness error or
  excluded, and the provenance (the image id, the base and start commits,
  the task repository's commit, flowbench's commit, the scorer's version).
- prediction.jsonl: the one line the scorer took (instance_id,
  model_name_or_path, model_patch).
- events.jsonl: every stage start and end, every agent start and end,
  and, once the symphony arm's gate is wired, every gate (a check run, a
  review posted, a merge), as coordbench's trace writes them, so a
  timeline reads where the time went.
- audit.json: the audit's verdict (harness error or not, and why;
  excluded or not, and which agent's stream named what; the network
  commands the agents ran), from the agents' streams while they are on
  disk.
- The agents' transcripts and prompts, kept on the host that ran them and
  never bundled, since they hold the run token; a bundle (not in the
  scaffold yet) takes result, prediction, events, audit and the scorer's
  log, as coordbench's bundle.py does, and keeps to docs/research's rule
  for a record that is committed: counts, seconds, tokens, verdicts and
  the patch, never a path, a command or an agent's text, so the bundle
  drops each agent's result_text, the harness's command line and every
  path from what it copies.

## Routes and what they cost

- The session route, as coordbench's bench/cooperbench/session/ runs it:
  one cloud session of this project drives the harness, the agents are its
  subagents on its own subscription, no token is stored anywhere. The
  script arm's orchestrator is the session's Workflow tool, which is the
  owner's own tool of the first document; symphony's workers are subagents
  with the gate's commands. The container holds about 30 GB of disk
  (SWE-bench's images run 1 to 3 GB each; the Django ones are the
  largest, and 231 of the 500 Verified instances are Django's), so images
  are pulled one at a time ahead of the lanes and removed after, as the
  curse experiment's image loop does. The budget is the account's
  five-hour window.
- The Actions route, as coordbench's bench.yml real mode: one job per
  (instance, arm) on a GitHub-hosted runner, the agent headless Claude
  Code on one of the owner's account slots (the organization secrets
  SYMPHONY_CLAUDE_<slot>, the variable SYMPHONY_CLAUDE_ACCOUNTS), the
  dispatch waiting in the environment `bench` for the owner's approval,
  the artifacts scrubbed and read back before upload, a fake mode that
  spends nothing and a pull-request smoke that runs one instance under
  three arms with the fake agent. The route for figures that go into a
  grant, since its agents carry no inherited prompt.

What a run costs is a guess until the pilot measures it, and the guess is:
one solo run on a Verified instance 1 to 4 million tokens read (nearly all
cache reads) and 5 to 20 minutes; the script arm three to five times that;
symphony two to four times. A pilot of 8 instances under three arms is 24
runs; by the curse experiment's rate of about 20 pair-runs per window on
the session route, that is one to two windows. The owner chooses every
step up, with the count and the windows named first; nothing runs on the
owner's tokens without that word.

## What is not claimed

- Not the leaderboard's numbers: the leaderboard's entries run their own
  scaffolds on API models with their own budgets; flowbench runs Claude
  Code on a subscription, with local tools only and a wall-clock limit. Its
  solo arm is set beside the leaderboard's Claude Code entries in the
  report for orientation only.
- Not CAID's or STORM's numbers: theirs are on Commit0 and PaperBench with
  other models and an API; the comparison here is between flows on the
  same agent, issues and day. When Commit0-Lite is the second suite, the
  script and symphony arms meet the parallel-work question those papers
  answer, and a caid arm is possible only with an API key the owner has
  not allowed.
- Not that review stages are useless or that they work: the pilot's
  intervals are wide (PLAN.md says what 8, 32 and 93 instances can show),
  and the first run is sized to measure cost and to find the instances
  where the flows disagree, which the second seed then re-runs.

## Sources

Read in full from this session, with the commit or version:

- coordbench at c433d48: README.md, coordbench/README.md (the contract),
  bench/cooperbench/PLAN.md (the pre-registration), PARITY.md,
  bench/cooperbench/session/README.md (the session route), bench.yml, the
  curse-of-coordination notes (trial-order.md, off-the-shelf.md's
  "Ruled out" list, which rules STORM's code, OpenHands-based systems and
  every API-keyed framework out of coordbench for the same reasons that
  hold here).
- github.com/SWE-bench/swe-bench-tasks at its head of 2026-10-16 (2,519
  tasks; the 500 Verified and 323 Lite tags read from every task.yaml) and
  github.com/SWE-bench/SWE-bench's README.md and docs/guides/evaluation.md
  (the predictions format, results.json, the v5 CLI's `--task-repo`); the
  swebench 5.0.2 wheel from PyPI (harness/utils.py and
  harness/run_evaluation.py load a task repository in place of the
  dataset when `--task-repo` is given and then rebuild the instance's
  image before scoring; cli/dataset.py's `dataset build` compiles a task
  repository into the parquet files `swebench eval` reads, and
  harness/reporting.py writes the summary's lists).
- The owner's two documents, converted with pandoc.
- docs/checkpoints/2026-10-15b/taxonomy/spec.md and manual.md (the
  taxonomy thread's findings: only the combination is unique; unsorry the
  closest rival).

Seen only in a search summary, not opened (arxiv.org, openreview.net,
openhands.dev and alphaxiv.org are blocked from this session):

- CAID: Jiayi Geng and Graham Neubig, "Effective Strategies for
  Asynchronous Software Engineering Agents", arXiv 2603.21489,
  2026-03-23; code at github.com/JiayiGeng/CAID, built on OpenHands; the
  26.7 and 14.3 point gains are the authors' own and sotaverified.org
  lists them as unverified.
- STORM: Mengyang Liu, Taozhi Chen, Zhenhua Xu, Xue Jiang and Yihong Dong,
  "Multi-agent Collaboration with State Management", arXiv 2605.20563,
  2026-05-21; Commit0-Lite 82.5% macro with Sonnet 4.6 against 63.8% for
  the worktree baseline and 66.4% for one agent, by the abstract and
  conclusion as summarised; the paper's own numbers.
