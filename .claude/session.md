# Session checkpoint

Written 2026-10-10 by the main account's cloud session, in a hurry: the
owner's usage ran out while four pieces of work were in flight. This is
the full checkpoint of claude/10 and of the split into five repositories;
main's own .claude/session.md points here. A session told to "continue"
works through "Remaining tasks" in order, all of them, without stopping
between them and without asking the owner anything: the only steps that
need the owner are registering the GitHub App (task 6, stage 1) and
merging pull requests, and the session does everything up to and around
those, commits and pushes after each task, and reports once at the end.
The owner's steps are in docs/setup/owner-checklist.md.

## Completed work

- Merged to main: #3, #5, #7, #9, #15 (push guard, claim protocol in CI,
  the plan ladder, the ruleset and one-flow Claude setup, team mode).
- claude/11, pull request #12: the push guard's newline fix alone (52 lines
  over main), rebased, ready, CI green. Waits on the owner's merge.
- claude/10, draft pull request #13 (issue #10), pushed and green at the
  commit before the trace work: experiment/ (CooperBench kit, 42 of 50
  flash pairs grade here) and experiment/coordbench/ (coordination as a
  plug-in; README.md is the contract). The review's 28 findings fixed,
  a skeptic round's residue fixed, the pilot's three bugs fixed. Timings
  per phase and per tool call (tool_done with blocked_ms), timeline.py,
  the arm archetype (new_arm.py, examples/board). Owner's checklist with
  scripts/setup-repo.sh; settings as code is issue #18; research folder
  condensed. 603 tests at that commit.
- The pilot ran: pallets_click 2068 features 1 and 6 through coordbench
  with the session driver under coop and team, scored by CooperBench's
  evaluation, both pairs passed; a third coop pair passed as the demo of
  the timing breakdown (1017 s wall, 16.7 s harness, 2 ms hub, no time
  blocked, the rest the agents). Logs lived only in that session's
  container (~/cooperbench/logs) and are gone.
- Decided with the owner (see Decisions): experiment/ ships as its own
  repository; five repositories in all; the gate policy lives in the
  shared core and the "world" in adapters; coordination CI is excluded
  from agentic behaviour and optimised separately; the Claude Code plugin
  marketplace is the client-side artifact for now.
- The owner created, and this session cloned and registered, four empty
  repositories under OpenSpineConsortium: sdlc-protocol, coordbench,
  sdlc-marketplace, sdlc-app (private). A new session must add each with
  the add_repo tool before it can push to them.
- Research saved under docs/history/split-research/: GitHub settings a
  template cannot copy (github-settings-notes.md) and the Claude Code
  plugin marketplace format (marketplace-notes.md). A third fact check,
  on the GitHub App (manifest flow, create-github-app-token, check runs,
  rulesets, webhooks), was still running and its notes may be missing.

## Progress since the first checkpoint (2026-10-10, on Opus)

- Task 1 is done: the trace integration finished green (679 tests) and is
  pushed on claude/10; production tracing costs about one function call.
  One gap it noted: run.py --debug does not yet put COORD_TRACE=debug into
  the agents' containers or the session driver's wrappers.
- coordbench: `experiment/`'s history (13 commits) is pushed to the branch
  claude/split of OpenSpineConsortium/coordbench, now its default branch;
  a reshape (kit under bench/cooperbench/, tests, CI, CLAUDE.md) was
  running on that branch. The bench adapter interface and the template
  copy are later work.
- coordbench reshape done: 511 tests green on claude/split (kit under
  bench/cooperbench/, tests, docs/research.md, CI, CLAUDE.md, LICENSE).
  Left: the sdlc arm still carries its own gate (import sdlc_protocol.gate
  once 0.1.0 exists); the bench adapter interface; the template copy;
  arm text that says "this template's claim protocol".
- sdlc-marketplace done: the sdlc plugin on claude/init (skills claim,
  remember, checkpoint; command board; hooks guard, check_edit,
  session-start), 32 tests, claude plugin validate --strict clean, the
  guard matching claude/11's on 38 payloads. Left: re-vendor guard.py from
  the sdlc-protocol 0.1.0 tag; a CI workflow; the template preset and the
  decision to drop the template's own three hooks (both would run twice).
- sdlc-app done on claude/init: stdlib webhook server (HMAC, 202 then a
  worker thread, one JSON log line per delivery), JWT signed with openssl,
  installation-token cache, the gate as the check run "sdlc/protocol" from
  the vendored protocol_check, scripts/register.py (manifest flow, writes
  .sdlc-app.env 0600), Dockerfile, CI, 67 tests. Run only against fakes:
  nothing is registered yet. Owner: `python3 scripts/register.py --org
  OpenSpineConsortium` from a clone, install the App, set SDLC_APP_ID and
  SDLC_APP_PRIVATE_KEY (register.py prints the gh commands). Left:
  check_suite rerequested, re-vendor from sdlc-protocol 0.1.0, the
  template's create-github-app-token step, and dropping CI's protocol step
  once sdlc/protocol is required.
- sdlc-protocol: the extraction was resumed on Opus; work in progress is on
  its branch wip/extract (its default branch for now).
- The push guard refuses any push to a branch named main, so the four new
  repositories got their first branch under another name. Owner step,
  once per repository: Settings, Branches, rename the default branch to
  main (GitHub redirects the old name).

## Current state (in flight when the session stopped)

- Trace instrumentation on claude/10: four build agents finished green
  (trace.py; hub and arm; runner and drivers; cli and bridge); the
  integrator was mid-run. The working tree was committed as it stood,
  so the suite may not be green and the README's "Adding logging"
  paragraph may be missing. First job: run the checks and finish it.
- sdlc-protocol extraction: five builders and an integrator were running
  in /home/user/sdlc-protocol; whatever existed was pushed to the branch
  wip/extract of OpenSpineConsortium/sdlc-protocol. The design is in
  "The sdlc-protocol design" below, since the workflow script died with
  the container. Parity tests against the old tools were the integrator's
  step and may be missing.
- sdlc-marketplace, sdlc-app, the coordbench split: not started; the
  facts and the plan are below.
- #13 stays a draft until the split is done; #12 waits on the owner.

## Remaining tasks

1. claude/10: `python3.12 -m unittest discover -s tests` and
   `bash scripts/check.sh`; finish the trace integration (contract below:
   trace.py levels off|prod|debug from COORD_TRACE, event/debug/span/
   debug_span, listen/unlisten, JsonLines and Memory listeners; hub and
   runner --debug; prod registers no process listener; README "Adding
   logging" paragraph in the Running section; timeline.py still reads the
   pilot format). Commit, push.
2. sdlc-protocol: finish the library to the design below on wip/extract,
   parity tests (board render byte-equal on the template's fixtures;
   guard exit codes and messages equal to claude/11's tools/guard_push.py;
   check_protocol and team on their fixtures), CI green, merge to main,
   tag 0.1.0.
3. sdlc-template: open an issue "Vendor sdlc-protocol", claim it, run
   sdlc-protocol's scripts/vendor.sh into tools/sdlc_protocol with
   tools/VENDORED, turn tools/board.py, check_protocol.py, team.py,
   guard_push.py into thin shims (or switch the workflows to
   `python3 -m sdlc_protocol board|check|team|guard` with PYTHONPATH=tools),
   add a test that the vendored copy matches VENDORED's version; keep
   check_docs, check_edit, marked_section, template_init in the template.
4. coordbench: `git subtree split -P experiment -b coordbench-split` on
   claude/10 (history kept), push to OpenSpineConsortium/coordbench main,
   then reshape: experiment/coordbench/* to the repository root as the
   package, experiment/*.sh and report.py under bench/cooperbench/ as the
   first adapter behind a small adapter interface (tasks, scoring, log
   layout) that run.py calls; the sdlc arm imports sdlc_protocol.gate and
   adapters.bare_git instead of its own Gate; docs/history research page
   moves with it; make the repository a copy of the template (CLAUDE.md,
   docs/project.md, .claude/, workflows) so it dogfoods use 1; move
   tests/test_coordbench_* and test_experiment_report.py with it; then on
   claude/10 delete experiment/ and those tests, update README.md and
   docs/memory (the MCP timeout fact moves to coordbench), and mark #13
   ready (delete docs/agents/claims/10.md in that commit).
5. sdlc-marketplace (facts in docs/history/split-research/marketplace-notes.md):
   .claude-plugin/marketplace.json (name sdlc-marketplace, owner
   OpenSpineConsortium, one plugin "sdlc" with source "./plugins/sdlc");
   plugins/sdlc/.claude-plugin/plugin.json (name sdlc, version 0.1.0);
   skills/ copied from the template's .claude/skills (claim, remember,
   checkpoint, board); commands/board.md from .claude/commands/board.md;
   hooks/hooks.json with the PreToolUse Bash guard and the Edit/Write
   check_edit, each running `python3 "${CLAUDE_PLUGIN_ROOT}/vendor/..."`
   over a vendored copy of sdlc_protocol (rules, CLAUDE.md fragments and
   permissions cannot ship in a plugin; they stay in the template). In
   the template, .claude/settings.json gets extraKnownMarketplaces
   {"sdlc-marketplace": {"source": {"source": "github", "repo":
   "OpenSpineConsortium/sdlc-marketplace"}}} and enabledPlugins
   {"sdlc@sdlc-marketplace": true}; `claude plugin validate` must pass.
6. sdlc-app, stage 1 (no hosting): the owner registers a GitHub App "sdlc"
   on the organisation (permissions Contents, Issues, Pull requests read
   and write, Checks write, Metadata read; events issues, issue_comment,
   pull_request, push, check_suite, installation; webhook off), installs
   it on the repositories, sets the variable SDLC_APP_ID and the secret
   SDLC_APP_PRIVATE_KEY; the template's workflows mint an installation
   token with actions/create-github-app-token (pinned to a major tag) and
   use it instead of GITHUB_TOKEN where a push or comment should trigger
   workflows. Stage 2: in sdlc-app a Python standard-library webhook
   receiver (HMAC X-Hub-Signature-256 check), the App manifest JSON, check
   runs on pull requests as the gate (sdlc_protocol.gate with the GitHub
   world adapter), board and release on webhooks, an installation-token
   client (RS256 JWT, PyJWT is a dependency decision: an issue first, or
   hand-rolled RS256 with the standard library is not possible, so decide),
   a Dockerfile, and a smee.io channel for local testing. Later: an MCP
   server in the App for the claude.ai directory.
7. Owner's items: merge #12; decide #18; the owner-checklist steps (one run
   of scripts/setup-repo.sh, the token, the Claude App); add
   CLAUDE_CODE_OAUTH_TOKEN to the cloud environment for the claude-cli
   driver.
8. With the token: the pilot through CooperBench's own runner and through
   coordbench's claude-cli driver on the same pair; then the five arms on
   the 42 gradable pairs; report.py and timeline.py; the write-up on
   whether the PR-gated way of working beats shared collaboration and solo.

## The sdlc-protocol design

Package sdlc_protocol, Python 3.12 standard library only.
- labels.py: LABELS from template_init, prefixes account: and agent:.
- claims.py: branch claude/<n>, claim file docs/agents/claims/<n>.md,
  claim parsing (account line, files to touch), release_due (24 h idle).
- board.py: Snapshot dataclasses with from_dict/to_dict; render(snapshot,
  default_branch) byte-identical to tools/board.py; comments_due for
  "main moved" and idle comments; no API calls.
- protocol_check.py: problems_for(pull, claim_file_exists).
- team.py: the clerk's rules (route, next_for, owners_for, seed, Snapshot)
  over an injected Client protocol.
- guard.py: plain_shell, simple_commands, push_arguments, refusal,
  branches, from claude/11's guard; run(payload, cwd) for the CLI.
- gate.py: Policy (claim_prefix, required_check, bring_main_in "rebase" for
  accounts or "merge" for team members, who_merges owner|gate|auto-merge,
  idle_after); World protocol (main_sha, branch_sha, standing clean|behind|
  conflicting|unknown, check green|red|pending|none, merge -> sha or
  MainMoved/GateFailed, now); decisions claim, can_open_pull, open_pull,
  mark_ready -> Outcome, pull_status, board_text; exit codes 1 refused,
  2 someone else's, 3 main moved, 4 gate failed; main_moved_instruction.
- adapters/bare_git.py (the sdlc arm's Gate over a bare repository),
  adapters/memory.py (tests), adapters/github.py (REST client from
  board.py and team.py, token from argument or GITHUB_TOKEN, World for a
  repository: standing from mergeable_state, check from check-runs, merge
  only when who_merges is gate).
- cli.py and __main__.py: python3 -m sdlc_protocol board|check|team|guard
  with the old tools' argument shapes.
- spec/PROTOCOL.md (generalised), tests/ with the template's tests ported,
  scripts/vendor.sh <target> (copies to <target>/tools/sdlc_protocol and
  writes tools/VENDORED), CI on python3.12.

## Decisions

Stated by the owner in conversation, recorded here and not in CLAUDE.md:

- Prefer GitHub's native settings over workflows, to save CI minutes and
  Claude usage. No API billing: Claude in CI runs on a subscription OAuth
  token. A claude.ai Project's own fields stay blank. The template serves
  the owner's experiment: PR-gated agents against a shared project.
- Deliver the prototype working; fix the bugs, demo it, generate the
  archetype, and do not improve it further without the owner's word.
- Logging tells infrastructure inefficiency from agent inefficiency, grows
  piecewise (one line to add an event or a span), has a passive production
  listener that costs one serialisation per event, and a debug mode for
  the playground that is never a default.
- experiment/ ships as its own repository (coordbench). Five repositories:
  sdlc-protocol (core, public), sdlc-template (free tier, public),
  coordbench (public, itself a template copy), sdlc-marketplace (public,
  the Claude Code plugin), sdlc-app (private, the GitHub App).
- The gate policy lives in the core; the world (GitHub, bare git, memory)
  in adapters; experimental gate variants live in coordbench as policy
  objects behind the same interface.
- Coordination CI is harness cost, excluded from agentic behaviour and
  optimised toward zero; verification CI (the project's tests) is the
  project's cost and agents do not wait on it; the simulated world
  carries the check delay as an explicit parameter.
- The Claude Code plugin marketplace is the client artifact now; a
  claude.ai directory connector (an MCP server in the App) comes with
  stage 2.
- The uploaded "Serverless Multi-Agent GitHub Architecture" document: take
  ETag, GraphQL batching, backoff with jitter, offline Ed25519 licences and
  a ruleset that forbids editing the gate workflow; reject IP protection by
  obfuscation on customer compute, file-level locks through an arbiter
  Action, heartbeat leases and a long-running coordinator Action.

## Constraints

- The cloud environment's network policy blocks deb.debian.org,
  deb.nodesource.com, huggingface.co, pypi.nvidia.com,
  openaipublic.blob.core.windows.net, docs.github.com and github.blog;
  Docker Hub rate-limits it (images from mirror.gcr.io); GitHub's docs are
  read from the github/docs source. A session's background command stops
  after two hours; the session starts dockerd itself.
- The session's git proxy allows two concurrent operations per repository;
  clone the four repositories one at a time.
- Verify with one skeptic per claim unless the owner asks for more.
- The scratchpad and ~/cooperbench die with the container: anything worth
  keeping goes in a repository.
