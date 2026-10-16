# flowbench

The workflow as a plug-in: a benchmark of how work on one software
issue moves through agents and gates, on SWE-bench Verified's issues,
scored by SWE-bench's own harness. Every arm fixes the same issues in the
same images with the same model and tools; what differs is the flow: one
agent alone, a script of phases (build, stack, review, verify, fix), or
the claim protocol (a claim, a pull request, a review by lenses, an
answer to every finding). The design, the pre-registration and the
parity table are in the repository this scaffold came from,
OpenSpineConsortium/symphony-template under docs/research/flowbench/,
until they move here with the scaffold.

It is a sibling of OpenSpineConsortium/coordbench, which varies how
agents coordinate on CooperBench's pairs; flowbench varies the flow on
SWE-bench's issues, with the same contract: arms, a fixed scorer, a
pre-registered order, a fake mode that spends nothing, a record per run
and an audit that leaves harness errors out and names them.

## What runs today

- `flowbench/tasks.py`: reads the task repository (a checkout of
  github.com/SWE-bench/swe-bench-tasks), the pool (Verified and Lite) and
  the nested stratified order (repository, then difficulty band, the
  strata in an order drawn from seed 0).
- `flowbench/backlog.py`: the work list of (instance, arm) items the
  lanes take under a file lock.
- `flowbench/run.py`: one (instance, arm) attempt: the image's /testbed
  copied out as the workspace, a container on it for the repository's
  tests, the arm's stages with `claude -p` per agent on the login's
  subscription (never an API key; the login's settings and MCP servers,
  the web and subagents off), the patch, the score, the record and an
  audit of every agent's stream; a preflight refuses a real run that
  lacks its dataset, docker, the harness or claude before it spends
  anything; `lane` works a backlog, pulling each image when it is first
  needed and, with `--remove-image`, removing it after the instance's
  last arm.
- `flowbench/score.py`: `build` compiles the task repository into the
  parquet files SWE-bench's harness reads; `score` runs the harness on
  the one prediction line against that dataset, in the image the agents
  worked in, one run id per attempt; never with `--task-repo`, which
  would make the harness rebuild the image first.
- `flowbench/record.py`: result.json, events.jsonl, the tokens from the
  agents' streams and their list price.
- `flowbench/report.py`: the arms side by side: Wilson intervals, a
  bootstrap over repositories, the rate over the sample beside the rate
  over the runs finished, exact McNemar on the paired instances, cost and
  time with the paired token ratio, the review table, one row per
  instance; harness errors and excluded runs left out and named.
- `flowbench/fake_agent.py`: the agent of a rehearsal.
- `flowbench/arms/`: solo, script, symphony (arms/README.md).

## Rehearse without spending anything

    python3 -m unittest discover -s tests -t .
    python3 flowbench/run.py run --logs logs --tag rehearsal --arm script --instance fake__alpha-1 \
        --task-repo tests/fixtures/tasks --fake --option builders=2
    python3 flowbench/report.py --logs logs --tag rehearsal

`--fake` fakes the whole path (no image, a small repository, the fake
agent, a fake score). `--fake-agents` keeps the real path (the image, the
container, SWE-bench's harness) and fakes only the agents, which is how a
real instance is rehearsed before any token is spent:

    git clone --filter=blob:none https://github.com/SWE-bench/swe-bench-tasks tasks
    python3 -m venv harness && harness/bin/pip install swebench==5.0.2
    export FLOWBENCH_SWEBENCH=harness/bin/swebench
    python3 flowbench/score.py build tasks -o data
    python3 flowbench/run.py run --logs logs --tag smoke --arm solo --instance astropy__astropy-12907 \
        --task-repo tasks --dataset data/SWE-bench_Verified --fake-agents

The run pulls the instance's image through mirror.gcr.io the first time
(`run.py pull` pulls a list ahead), and the score is SWE-bench's own
verdict on the fake agent's harmless edit: unresolved.

## A real run

Only with the owner's word and the count (PLAN.md's steps): the pilot is
8 instances under three arms. Then:

    python3 flowbench/tasks.py tasks order --seed 0 --sample 8 > pilot.txt
    python3 flowbench/backlog.py add backlog.jsonl --tag pilot --arms symphony,script,solo --instances @pilot.txt
    python3 flowbench/backlog.py shuffle backlog.jsonl --seed 0
    python3 flowbench/run.py lane --backlog backlog.jsonl --lane lane-1 --logs logs --task-repo tasks \
        --dataset data/SWE-bench_Verified --model claude-sonnet-5-5 --effort medium --remove-image
    python3 flowbench/report.py --logs logs --tag pilot --primary symphony --instances @pilot.txt

Two lanes at once are two `lane` processes on the same backlog. A lane
pulls an instance's image when it first needs it and, with
`--remove-image`, removes it once no item of the backlog still needs it,
since a session's disk holds a few images at once. A lane that died with
an item in hand is reset with `backlog.py reset backlog.jsonl --lane
lane-1`; `backlog.py requeue` runs the failed items again, at most three
attempts each.

## Rules

- No API key: run.py drops ANTHROPIC_API_KEY, ANTHROPIC_AUTH_TOKEN,
  ANTHROPIC_BASE_URL and the cloud-provider switches from the agents'
  environment, and the agents run on the login's own subscription.
- The task repository is never mounted, copied or named to an agent;
  tests/test_run.py holds the prompts to it, and the audit excludes a run
  whose agents' streams name it or its patches.
- The transcripts and prompts stay on the host; a bundle takes result,
  prediction, events, audit and the harness's log.
- Python 3.12 or later with its standard library, git and Docker; the
  harness in a virtualenv of its own.

`bash scripts/check.sh` runs the checks CI runs.
