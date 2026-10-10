# Session checkpoint

Written 2026-10-10 at the end of a long session on the main account, for
the next session on any account. Everything below is merged to main in
its repository; nothing is open on GitHub from this session.

## Completed work

- One-push protocol sync, live. OpenSpineConsortium/sdlc-protocol#1
  (v0.2.0, tagged) with sdlc-template#19, coordbench#2,
  sdlc-marketplace#1 and sdlc-app#2. ecosystem.json in sdlc-protocol is
  the one record of who takes which modules; .github/workflows/sync.yml
  vendors main into every consumer with the OpenSpine SDLC App's token and
  opens `sdlc-protocol/sync` there; the `downstream` job runs each
  consumer's check on a library pull request before it merges; VENDORED
  records a sha256 per file and each consumer's check verifies it;
  ECOSYSTEM.md is generated. The first real sync ran after the merges and
  found every consumer up to date. The owner set auto-merge on coordbench
  and sdlc-marketplace and a ruleset on sdlc-marketplace.
- CooperBench parity in coordbench (coordbench#3): a run records what
  CooperBench's runner writes (conversation.json, trajectories,
  result.json in its key order, config.json, summary.json), the paper's
  merge cascade beside 63b9d44's verdict, a coop-nocomm arm and the
  `tool_surface=bash` option; report.py, judge.py (opt-in, model calls),
  annotate.py, export.py and compare.py; PARITY.md lists 149 rows with
  their status and reasons. The owner's other sessions then merged
  coordbench#4 (the sdlc-watch arm) and #5 (bench/cooperbench/pilot.sh,
  the Docker preflight, error kinds, `--reference-merge`).
- First real runs, claude-sonnet-5-5 on the owner's subscription: one coop
  pair, then the six-arm pilot. pallets_click 2068: solo 5/6, the coop
  arms 0/6, sdlc 2/6; every pair of that task conflicts even with the gold
  patches (dataset/gold_conflict_report.json), and 63b9d44 passes a
  conflicting pair only when agent1's patch alone passes both suites.
  pallets_jinja 1559 (clean gold merges): solo and the coop arms 4/4, team
  and sdlc 3/4. About $8 at API prices across both.
- Crowdsourcing: docs/setup/crowdsourcing.md and
  docs/history/crowdsourcing/research.md (sdlc-template#20), then crowd
  mode (sdlc-template#22): scripts/crowd.py setup, finish, invite, remove,
  audit, doctor and publish-template; tools/crowd_check.py; the variable
  CLAUDE_CROWD that stops the Claude workflows; the required check's crowd
  guard; .github/workflows/queue.yml; docs/setup/ruleset-crowd.json and
  the crowd files under docs/setup/crowd/. sdlc-template#21 (code owners
  name a person, {{CODE_OWNER}}) was merged into the crowd branch before
  it landed.

## Current state

- Every repository's main holds this work; no pull request of this
  session is open, no check-in is scheduled, no workflow runs.
- The sync is on: a merged change to sdlc-protocol's package opens
  `sdlc-protocol/sync` in each consumer. The public ones and the template
  merge themselves on a green check; sdlc-app's waits for the owner.
- coordbench main has everything for the next experiment; the task images
  are removed after each pilot, so each task needs prepare_task.sh again.

## Remaining tasks

1. Try crowd mode on a real organization copy: "Use this template" (or
   `crowd.py publish-template`, the owner's call: the template is internal
   to its enterprise), then `crowd.py setup ORG/NAME --area AREA`,
   `finish`, `invite`, `audit`, and `gh api repos/ORG/NAME/codeowners/errors`.
   Every GitHub call so far was tested against a fake.
2. The next experiment: the 42 gradeable flash pairs headless
   (bench/cooperbench/pilot.sh per task, or `run.py run --subset flash`)
   for solo, coop, coop-git, sdlc and sdlc-watch, with `--option
   tool_surface=bash` on the coop arms; then report.py and the free judge
   heuristics. One seed only so far; a second seed on pairs where the arms
   disagree is the cheapest check on noise.
3. Not exercised for real yet: judge.py against a real model, the session
   driver's transcript copy on a real subagent, the learned resolver step
   (needs a model server, COORDBENCH_RESOLVER_URL).
4. Watch the first sync pull request in sdlc-marketplace: GitHub added
   `require_extra_approval_for_unattributed_changes: true` to its ruleset,
   undocumented; if a green sync pull request does not merge itself, turn
   it off.
5. From docs/setup/crowdsourcing.md, "What is to be built": the board
   rendered by the App, a server-side check that only the claimer pushes
   to claude/N, dealing the queue across accounts, released claims going
   back to the queue.
6. Later: sdlc-app stage 2 (host the webhook server, require
   sdlc/protocol); actions/create-github-app-token@v1 runs on the
   deprecated Node 20 (v2 exists).

To continue on another account: its Claude account connects GitHub with
access to the OpenSpineConsortium repositories; a cloud environment of its
own gets COORDBENCH_CLAUDE_TOKEN from its own `claude setup-token` (never
another account's); and, under the claim protocol, it gets its own label
account:<name> and a row in docs/agents/OWNERSHIP.md. The App's private
key stays only in the owner's .sdlc-app.env.

## Decisions

Stated by the owner in conversation:

- Prefer GitHub's native, free features over workflows and paid plans,
  to save CI minutes and Claude usage. No API billing: Claude in CI runs
  on a subscription OAuth token. A claude.ai Project's own fields stay
  blank. The template serves the owner's experiment: PR-gated agents
  against a shared project.
- Five repositories: sdlc-protocol (the core, public), sdlc-template,
  coordbench (public), sdlc-marketplace (public, the Claude Code plugin),
  sdlc-app (private, the GitHub App). The gate policy lives in the core,
  the worlds in adapters.
- A protocol change is made in sdlc-protocol and reaches the others by
  its sync on one push; consumers that must answer a change merge first,
  then the library with a merge commit.
- Logging tells infrastructure inefficiency from agent inefficiency;
  coordination CI is harness cost, optimised toward zero.
- coordbench measures what CooperBench measures, as CooperBench does,
  differing only with a stated reason (PARITY.md); it reproduces
  CooperBench 63b9d44 by default. Model-judged measures are a separate
  command the owner runs on purpose; never ANTHROPIC_API_KEY.
- Crowdsourcing: each contributor works under their own Claude account;
  the project never holds anyone's credential (Anthropic's terms).
- The owner asked Claude to merge the green pull requests it opened, in
  the order the sync needs, on 2026-10-10.
- The template names the sdlc marketplace in .claude/settings.json and
  enables no plugin, so the hooks never run twice.

## Constraints

- The cloud environment's network policy blocks cooperbench.com,
  arxiv.org, cursor.com, huggingface.co, deb.debian.org and others; the
  CooperBench paper, viewer and data are read from the GitHub repository
  cooperbench/website. Docker Hub rate-limits (images from mirror.gcr.io).
- The cloud environment withholds CLAUDE_CODE_OAUTH_TOKEN from a session;
  coordbench reads COORDBENCH_CLAUDE_TOKEN instead.
- The Docker daemon can stop mid-session: check `docker info` before each
  run (run.py now does), and restart it with bench/cooperbench/setup.sh.
- A session's background command stops after two hours.
- The session's git proxy refuses tag pushes and allows two concurrent
  operations per repository.
- sdlc-template is internal to its enterprise: outsiders cannot use it as
  a template until the owner publishes a public copy.
- The scratchpad and ~/cooperbench die with the container: anything worth
  keeping goes in a repository.
