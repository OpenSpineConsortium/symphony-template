# Session checkpoint

Written 2026-10-09 by the main account's cloud session, at the end of the
session that finished the harness as a working prototype. This is the
full checkpoint of the work on claude/10; main's own .claude/session.md
points here. Read this first, then experiment/README.md and
experiment/coordbench/README.md (the plug-in contract). The owner's steps
(accounts, tokens, secrets, variables) are in docs/setup/owner-checklist.md.

## Completed work

- Merged to main, in order: #3 (push guard hook, edit check, permission
  allowlist, /board, tidy workflow, @claude on the subscription OAuth
  token), #5 (claim protocol checked in CI, opt-in Actions worker), #7
  (the plan ladder), #9 (the default branch's ruleset as a file, the
  Claude side in one OAuth flow, release-audit fixes), #15 (team mode).
- claude/11, pull request #12 (issue #11): the push guard's rewrite was
  cut back to the newline fix alone (52 lines over main, 29 tests),
  rebased on main, its claim file removed, marked ready; CI is green. It
  waits on the owner's merge.
- claude/10, draft pull request #13 (issue #10), all pushed and green:
  - experiment/: the kit that runs CooperBench's four-arm ablation in one
    cloud session with CooperBench's own runner; 42 of the 50 flash pairs
    grade here (experiment/README.md).
  - experiment/coordbench/: coordination as a plug-in; README.md is the
    contract. The review's 28 findings are fixed, each with a test; a
    verification round of five skeptics found the residue (races, exit
    codes, docstrings), fixed in the final round with the pilot's bugs.
  - Logging that tells infrastructure time from agent time: every tool
    call leaves a tool_done event with its duration and the part spent
    blocked on a peer; result.json carries per-phase timings (hub,
    provisioning per agent, agents, close, score, teardown) and Claude
    Code's duration and API duration per agent; experiment/coordbench/
    timeline.py prints the breakdown for one run directory.
  - The arm archetype: experiment/coordbench/new_arm.py writes a complete,
    loadable arm from a name and checks it in-process (--check);
    experiment/coordbench/examples/board/ is the generated example, pinned
    byte for byte by a test.
  - The owner's checklist is one command for the GitHub side
    (scripts/setup-repo.sh) plus the pages a template cannot reach;
    docs/setup/owner-checklist.md says what an organization can preship
    and on which plan; template-init's setup issue links every step,
    the Claude App install preselected. Settings as code is issue #18.
  - docs/history/experiment-research/ is condensed to its record.
- The pilot, the owner's original ask, ran: one pair (pallets_click 2068,
  features 1 and 6) through coordbench with the session driver under the
  coop and the team arms, one subagent of this session per agent, scored
  by CooperBench's own evaluation. Both pairs passed (both features' tests
  on the merged code). Logs: ~/cooperbench/logs/pilot-session-coop and
  pilot-session-team in this session's container only; result.json,
  eval.json, events.jsonl and the patches are there. A second coop pair
  ran after the final round as the demo of the timing breakdown
  it passed too, and experiment/coordbench/timeline.py on it shows where the
  1017 s went: 16.7 s of harness (provisioning under 2 s, scoring 14 s), 2 ms of
  hub handling, no time blocked on a peer (coop has no blocking tool), the
  rest the agents' own work, with idle stretches of up to 380 s between
  coordination calls. Logs: ~/cooperbench/logs/demo-session-coop, this
  session's container only..

## Current state

- #13 is a draft on purpose: the owner decides whether experiment/ (with
  coordbench) moves to a repository of its own before it merges, since
  everything on main ships in every copy of the template. Nothing else
  blocks marking it ready: `bash scripts/check.sh` is green
  (603 tests), the claim file docs/agents/claims/10.md still
  exists and goes with the ready mark.
- No agent has run through the claude-cli driver yet: that needs
  CLAUDE_CODE_OAUTH_TOKEN in the cloud environment (owner's checklist,
  section 2) and a new session. The session driver needs no token and is
  what the pilot used.
- Usage is not measured for the session driver (null in result.json, '-'
  in the report); time is, in every phase.
- The main account's weekly Claude usage resets on 2026-10-15 at 11:00 UTC.

## Remaining tasks

The owner asked that the prototype be delivered as it stands and not
improved further on a session's own initiative. What remains is the
owner's, or waits for the owner's word:

1. Merge #12. Decide the experiment/ question and tell a session to mark
   #13 ready (delete docs/agents/claims/10.md in that commit) or to move
   experiment/ out first.
2. Decide #18 (settings as code) and the owner's steps in
   docs/setup/owner-checklist.md: one run of scripts/setup-repo.sh, the
   token, the Claude GitHub App.
3. With CLAUDE_CODE_OAUTH_TOKEN in the environment and a new session: the
   pilot on pallets_click 2068 with CooperBench's own runner
   (experiment/run_arms.sh) and with coordbench's claude-cli driver for
   the same arms, to measure how much the harness itself moves the
   scores; then the five arms on the 42 gradable pairs, one task at a
   time; experiment/report.py; experiment/coordbench/timeline.py per pair
   for where the time went.
4. The write-up for the owner: does the PR-gated way of working (the sdlc
   arm) beat or trail shared collaboration (coop-git, team) and solo, at
   what usage and time.
5. Team mode live run on a repository made from the template, and the
   re-made test repository, once the owner has set the variables.

## Decisions

Stated by the owner in conversation, recorded here and not in CLAUDE.md:

- Prefer GitHub's native settings over workflows wherever they cover the
  case, to save CI minutes and Claude usage.
- No API billing: Claude in CI runs on a subscription OAuth token.
- A claude.ai Project's own fields stay blank; the repository is the one
  source of instructions, goal and memory.
- The template should serve the owner's experiment: PR-gated agents
  against a shared project, after CooperBench.
- Deliver the prototype working; fix the bugs found, demo it, generate the
  archetype, and stop improving it without the owner's word (2026-10-09).
- Logging must tell infrastructure inefficiency from agent inefficiency:
  per-phase timings and per-call durations with the blocked part apart.

Decisions taken by the session that fixed the review, each written where
it applies (experiment/coordbench/README.md): the team arm's
wait_for_message works where CooperBench's never returned a message, a
documented deviation; the messaging commands match coop_msg.py's output,
arguments and exit codes; no built-in arm sends MCP server instructions;
the solo arm ships no skill and no .mcp.json; every arm's .mcp.json sets a
330 s timeout; agents authenticate with per-agent bearer tokens.

## Constraints

- The cloud environment's network policy blocks deb.debian.org,
  deb.nodesource.com, huggingface.co, pypi.nvidia.com,
  openaipublic.blob.core.windows.net, docs.github.com and github.blog;
  Docker Hub rate-limits it, so images come from mirror.gcr.io; GitHub's
  docs are read from the github/docs source.
- A session's background command stops after two hours; Docker's daemon
  must be started by the session (experiment/setup.sh does).
- Verify fewer claims with one skeptic unless the owner asks for more:
  the full three-skeptic research run was the expensive choice.
