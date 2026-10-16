# The arms

An arm is a flow: how the work on one issue moves through agents and
gates. Each is a folder here with a `stages.json` and its prompts, and
nothing else varies between arms: the same instance, the same image, the
same model, the same tools, the same scorer (PARITY.md in the design).

## stages.json

```json
{"name": "script",
 "description": "one sentence",
 "stages": [
   {"name": "build", "kind": "work", "prompt": "prompts/build.md", "agents": "builders", "parallel": true},
   {"name": "review", "kind": "review", "prompt": "prompts/review.md",
    "lenses": {"correctness": "...", "conventions": "...", "path": "..."}, "parallel": true,
    "writes": "{findings_file}"},
   {"name": "verify", "kind": "verify", "prompt": "prompts/verify.md", "agents": "per_finding",
    "parallel": true, "needs": "raised", "writes": "{verdict_file}"},
   {"name": "fix", "kind": "fix", "prompt": "prompts/fix.md", "needs": "confirmed", "writes": "{flow_dir}/fixed-{stage}.json"}
 ]}
```

- `name`: the stage's own name, unique in the arm and without a dash,
  since the files its agents leave are read back by splitting their
  names on the first dash; the agents are named after it
  (`review-correctness`, `verify-correctness-1`, `build-2`).
- `kind`: what the stage is for, one of work, stack, review, verify, fix,
  answer. The fake agent acts by it, and the record counts findings,
  verdicts, fixes and merges by the files those kinds leave.
- `prompt`: the prompt's file, with placeholders (below).
- `agents`: a count (default 1), `builders` (one agent per builder, each in
  a copy of the workspace of its own on the branch builder-K with a
  container of its own, when the run's option builders is above 1; a
  copy and not a git worktree, since a worktree has none of the image's
  untracked build products and its .git file names a path no container
  sees) or `per_finding` (one agent per finding the review raised). Before
  a stack stage the runner fetches every builder's branch into the
  workspace, and a builder that left its work uncommitted is the flow's
  failure.
- `lenses`: a table of lens name to lens text; one agent per lens, given
  `{lens}` and `{lens_text}`.
- `parallel`: the stage's agents run at once (up to `--parallel`).
- `needs`: `raised` skips the stage when the review raised nothing,
  `confirmed` when the verdicts confirmed nothing.
- `writes`: the file each agent must leave; one missing is an
  orchestration failure of the arm, recorded and counted, never a harness
  error. A fix or answer stage names its file after the stage
  (`{flow_dir}/fixed-{stage}.json`), so an arm that lists such a stage
  twice keeps each round's file.

## The placeholders

The runner fills these in every prompt; any other `{word}` is an error
`python3 flowbench/run.py arm <name>` reports.

| Placeholder | What it is |
| --- | --- |
| `{instance_id}`, `{repo}` | the instance |
| `{base_commit}` | the commit the workspace starts at: the instance's base commit under the one commit the image's build adds on top of it, which is what the agent's diff is read against |
| `{workspace}` | the agent's working directory: the repository at that commit (a builder's own copy for a builder) |
| `{container}` | the container that runs the same workspace at /testbed, or empty in a fake run |
| `{test_shell}` | a wrapper script that runs the command after it in the container's Python environment, from /testbed (`{test_shell} pytest -x path/to/test_x.py`); on the host in a fake run |
| `{problem_file}` | the issue's text, beside the workspace, never inside it |
| `{run_dir}`, `{flow_dir}` | the run's directory and its flow/ directory, where stages leave their files |
| `{stage}`, `{agent}` | the stage's and the agent's names |
| `{lens}`, `{lens_text}`, `{findings_file}` | a review agent's lens and where it writes |
| `{finding}`, `{finding_id}`, `{verdict_file}` | a verify agent's finding (JSON) and where it writes |
| `{findings}`, `{confirmed_findings}` | every finding raised, and those the verdicts confirmed (JSON lists) |
| `{builders}`, `{branch}` | the builders (a JSON list of each builder's number and branch, every branch fetched into the workspace before the stack stage) and a builder's own branch, empty with one builder |
| `{run_token}` | the line the agent's last message begins with, so a transcript can be found by it |
| `{options}` | the run's options (JSON) |

## The files a stage leaves

Under the run's flow/ directory:

- a review agent: `findings-<stage>-<lens>.json`, `{"lens": ..., "findings": [{"id", "file", "line", "claim", "evidence", "severity"}]}`;
- a verify agent: `verdict-<stage>-<id>.json`, `{"id", "real", "why"}`;
- a fix stage: `fixed-<stage>.json`, `{"fixed": [ids], "not_fixed": [{"id", "why"}]}`;
- the stack stage: `stack.json`, `{"merged", "conflicts", "tests", "notes"}`;
- a worker that opens a pull request: `pull-request.md`;
- an answer stage: `answers-<stage>.json`, `{"answers": [{"id", "answer", "changed"}]}`.

Every agent is told to write under the flow directory only the file its
prompt asks for and notes of its own, and never to read another agent's
files there.

The record (result.json) reads them into `flow`: findings raised, by
lens, confirmed, fixed; the merges; the review rounds and the answers;
the agents that ran out of time or turns; and `orchestration_failure`
with its reasons.

## The arms here

| Arm | The flow | Status |
| --- | --- | --- |
| solo | one agent, one stage | runs in fake mode |
| script | build (builders=K for K candidates), stack, review through three lenses, verify each finding, fix the confirmed ones | runs in fake mode |
| symphony | work (the claim branch claude/1 and the pull request's description), review through the same three lenses, answer every finding | runs in fake mode; the protocol's gate is not wired (symphony/README.md) |

The review prompt and the lens texts are the same file content in script
and symphony, and tests/test_arms.py holds them equal, so an arm's
reviewers are never told something another arm's are not.

## Adding an arm

A folder with stages.json and prompts; `python3 flowbench/run.py arm
<folder>` checks it; a fake run (`run.py run --fake`) walks it end to end
on the fixture task; the fake agent acts by each stage's kind, so a stage
of a new kind needs a deed in fake_agent.py too. An arm that needs a
framework (the design's framework-langgraph) carries it in an image layer
of its own, never in the harness, and runs each node as `claude -p` on
the login's subscription, never on an API key.
