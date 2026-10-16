# flowbench: research notes

Source: the thread "Agentic workflow benchmarks" of the project symphony,
item 6 of the owner's handoff of 2026-10-15, written 2026-10-15 and
2026-10-16 and kept current as the work goes on; no Claude Doc or
artifact.

The notes of the owner's item 6 ("more sophisticated agentic workflow
development ... build similar repos like coordbench but for other LLM
performance domains, and include other software engineering benchmarks,
SWE-bench etc."), kept here as the work goes on. The design is DESIGN.md,
the pre-registration PLAN.md, the parity table PARITY.md, and scaffold/
is the future repository OpenSpineConsortium/flowbench as its first
commit, runnable today in fake mode and rehearsed on a real SWE-bench
instance under all three arms.

## What was found

- The two documents the owner attached are the naive approach: a Claude
  Code Workflow script (build in parallel worktrees, stack, review through
  several lenses, verify each finding as a "hallucination firewall", fix)
  that failed to parse on its first run, and a package report that
  recommends LangGraph.js, Temporal, OpenHands and the two papers CAID and
  STORM as the remedy. Every remedy bills an LLM API, which the project's
  rules forbid, so flowbench measures the naive script itself against one
  agent alone and against the claim protocol, and leaves the framework
  arm designed, to be built only when the owner wants the report's remedy
  measured (DESIGN.md, the arms table).
- SWE-bench runs from a cloud session of this project without
  huggingface.co: the task data is the GitHub repository
  SWE-bench/swe-bench-tasks (every instance as a directory: the problem
  statement, the gold patch, the test patch, the test lists, eval.sh and
  the image's name), the harness is the PyPI package swebench (5.0.2),
  which compiles that repository into the parquet files it reads
  (`swebench dataset build`), and the images pull through mirror.gcr.io.
  Recorded as a memory fact
  (docs/memory/swe-bench-runs-from-github-and-pypi.md).
- The harness's `--task-repo` is not the way to score: given it, `swebench
  eval` rebuilds the instance's image from the task's Dockerfile before
  scoring and falls back to the published image when that build fails, so
  the image scored need not be the one the agent worked in. The
  adversarial review of 2026-10-16 found it and the first smoke test's
  harness log showed the fallback; the scorer now compiles the dataset
  once and scores from it, and the gold patch through that route scored
  resolved with no rebuild.
- An instance's image is not at the base commit: the build adds one commit
  of its own on top ("SWE-bench", file modes), and the harness applies a
  patch on that state. So the harness takes the agent's diff against the
  commit the workspace starts at, checks that it descends from the base,
  and records both (scaffold/flowbench/run.py, prepare and take_patch).
  The first smoke test found this.
- The adversarial review of the scaffold (2026-10-16) raised two blocking
  findings, eighteen to fix and eleven nits, and each is answered in the
  code or the documents: the scorer's route (above); a patch that does
  not apply is the arm's failure, not the harness's; the agents run with
  the login's settings, MCP servers, the web and subagents off, at one
  effort level, with their tools read back into the record; builders
  work in copies of the workspace, not worktrees, whose .git names a path
  no container sees; the image's own untracked files and file modes stay
  out of the patch; timeouts and turn limits are counted apart from the
  flow's failures; a run whose transcripts name the task repository is
  excluded and named; the strata are visited in an order drawn from the
  seed; the record carries the scorer's version and the task repository's
  commit; the report gives the rate over the sample and the paired token
  ratio PLAN.md calls the primary cost comparison; and a preflight
  refuses a real run that lacks its dataset, docker, the harness or a
  subscription login before any agent spends anything.
- A whole-template adoption copies docs/checkpoints and docs/research
  into the adopter's repository (symphony-start's adopt.py stages every
  file of the template but LICENSE), so these notes ship to adopters as
  they are; nothing here is secret, and the template's convention for
  what adopters receive is the owner's to set.
- The pool: 93 instances are in both SWE-bench Verified and Lite, over 19
  strata of repository and difficulty band, 63 of them with a hidden test
  the test patch adds; the first eight of the pre-registered order (seed
  0, the strata in an order drawn from the seed) are pytest-7490,
  sphinx-11445, matplotlib-24149, django-14752, scikit-learn-14894,
  astropy-12907, django-12708 and pylint-7080: eight strata, seven
  repositories.

## What runs today

- scaffold/: tasks (the pool and the order), backlog (the work list the
  lanes take), run (one attempt from the image to the record: the arm's
  stages as `claude -p` per agent, the patch, the score, result.json,
  events.jsonl, audit.json; a lane pulls each image when it is first
  needed), score (SWE-bench's harness on the compiled dataset), record
  (tokens and prices), report (Wilson, bootstrap over repositories, exact
  McNemar, the rate over the sample, the paired token ratio, the review
  table, one row per instance), fake_agent, and the three arms solo,
  script and symphony with their prompts. 114 tests;
  `bash scripts/check.sh` passes; a CI workflow runs the same.
- The rehearsals of 2026-10-16 on the real astropy__astropy-12907 image,
  each with the fake agent in place of Claude and SWE-bench's own harness
  scoring, no token spent: the first (solo) found the image's build
  commit; after the review, all three arms ran end to end (solo in 78 s,
  script with two builders in 38 s, symphony in 33 s), each scored
  unresolved, as the fake agent's harmless edit should be, with no
  harness error and no orchestration failure, the two builders' clashing
  edits recorded as a merge conflict, and every container and copy
  removed afterwards; a run given relative paths did the same. The gold
  patch through the same scorer: resolved. So the loop is closed at both
  ends.
- Not wired yet: the symphony arm's gate (the protocol library's required
  check and merge gate, as coordbench's sdlc arm vendors it), so that arm
  measures the protocol's shape only (PARITY.md row 15); symphony-github
  (the same flow on GitHub with the template's workers) and the framework
  arm are designed, not scaffolded; the session route's Workflow driver
  is designed, the host route (`claude -p`) is what runs. In this cloud
  container `claude auth status` reports a subscription login, which the
  preflight accepts; whether a `claude -p` agent started here draws on it
  is shown by the first step that spends anything, on the owner's word.

## The owner's decisions

Nothing below runs or is created without the owner's word.

1. The repository. A new public MIT repository is needed, as coordbench
   is one, since the template ships to adopters and a benchmark does not
   belong in every copy. Open
   https://github.com/organizations/OpenSpineConsortium/repositories/new,
   type `flowbench` as the name, choose Public, leave README, .gitignore
   and license unticked, press "Create repository". Then say so in the
   thread and a session attaches it and pushes scaffold/ as its first
   commit (the design documents move with it). Another name is fine; the
   folder and the package rename with it.
2. The pilot. PLAN.md's first paid step is 8 instances under three arms,
   24 runs, estimated at one to two five-hour windows of one account (a
   guess until measured; DESIGN.md, Routes), on the host route from a
   machine where claude is logged in on the owner's subscription, or on
   the session route once its driver is built. The word that starts it
   names the count and the account.
3. The framework arm. Built only if the owner wants the package report's
   remedy (LangGraph.js) measured; it needs Node in an image layer of the
   arm's own and no API key.
4. CAID and STORM stay out: both bill an LLM API. The owner can overrule.

## Next steps, in order

1. The repository created (above), the scaffold pushed, its CI green.
2. The symphony arm's gate wired from coordbench's sdlc arm; a fake run
   through it; PARITY.md row 15 closed.
3. The survey step of PLAN.md (no token): every image of the first 32
   instances pulled and the harness run on the gold patch, so a broken
   image is found before an agent meets it.
4. The pilot, on the owner's word.

## How to resume

    cd docs/research/flowbench/scaffold
    bash scripts/check.sh
    python3 flowbench/run.py run --logs /tmp/logs --tag rehearsal --arm script \
        --instance fake__alpha-1 --task-repo tests/fixtures/tasks --fake --option builders=2
    python3 flowbench/report.py --logs /tmp/logs --tag rehearsal --arms script

The real-instance rehearsal is in scaffold/README.md (the task repository
cloned, the harness in a virtualenv, the dataset compiled with
`score.py build`, `--fake-agents`).

## Log

- 2026-10-15: the two documents read; coordbench's contract read; SWE-bench
  reachability checked (huggingface.co, swebench.com, arxiv.org blocked;
  github.com, pypi.org, mirror.gcr.io open); DESIGN.md, PLAN.md and
  PARITY.md written; the scaffold started.
- 2026-10-16: the scaffold completed (runner, fake agent, three arms,
  tests); the first smoke test failed on the image's build commit and the
  runner was corrected; the second passed; the gold patch scored resolved;
  the notes moved from docs/checkpoints/2026-10-15b/flowbench/ to
  docs/research/flowbench/ on the owner's word that research notes
  accumulate in the repository.
- 2026-10-16, later: the adversarial review's findings answered (above);
  the scorer moved from `--task-repo` to the compiled dataset and checked
  on the gold patch; the real path rehearsed under all three arms; the
  design, the plan, the parity table and the memory fact corrected to
  match.
