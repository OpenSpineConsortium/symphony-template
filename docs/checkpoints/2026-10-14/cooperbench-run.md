# CooperBench run with Symphony workers: checkpoint, 2026-10-14 01:40 UTC

Thread: "CooperBench run with Symphony workers". The owner asked (2026-10-13
23:04) to start CooperBench benchmarking with the workers automatically,
working, and reporting every statistic needed to compare against the
CooperBench paper and its follow-ups. The run lives in
OpenSpineConsortium/coordbench's own GitHub Actions.

## Landed (merged, CI green)

- coordbench#11 (merge 0de6a70): the kit runs on any Docker host
  (COORDBENCH_CLAUDE_BIN stand-in, Claude Code pinned 2.1.296, proxy CA
  optional, COORDBENCH_SKIP_GRADEABLE) and run.py scrubs the agents' token
  from every file a pair leaves (scrub_pair, scrub_hub; CredentialKept fails
  a pair it cannot clean).
- coordbench#12 (merge a581d02, on the owner's "push it its green" at 01:10):
  .github/workflows/bench.yml with modes fake, survey and real; plan, survey,
  run, run-real and report jobs; bench/cooperbench/actions/ (plan.py,
  run-pair/action.yml, pair.sh, survey_task.sh, survey_report.py,
  artifacts.py, environment.py, report.sh, free_disk.sh);
  bench/cooperbench/fake_claude; PLAN.md (pre-registration), pairs.txt (43
  pairs, 17 tasks, pending the survey), METRICS.md (where each statistic of
  the paper, the blogs and the follow-ups is in the report). Its own smoke
  run, three fake pairs of pallets_click 2068 f1_f6 under solo, coop-git and
  sdlc plus the report job, passed twice on GitHub's runners.

## Not reviewed yet (review next session)

- The merged #12 had one adversarial review (35 findings, folded in commit
  c246c4b) and one CodeQL fix (873c3a7: accounts are slots 1 to 8, secrets
  SYMPHONY_CLAUDE_1..8 named one by one). Nothing after that was reviewed.
- The smoke run's report artifact was never read by a person: download
  report-smoke-pr12-38493729698-38493729698 from run 38493729698 and check
  that the Pass rates table shows 3 pairs, 0 Errors, and the sdlc pair's
  claims/merges are in metrics.json. (gh's artifact download is refused by
  the session's proxy at the blob store; use artifacts.py's redirect path or
  the Actions page.)

## Next, in order

1. Dispatch bench.yml on main in survey mode, pairs
   @bench/cooperbench/pairs.txt, tag survey-1 (no usage). Read its table and
   fix pairs.txt to the tasks that grade on a runner, in a PR.
2. Dispatch bench.yml in fake mode over the fixed list, tag fake-1 (no
   usage); expect every pair Submitted and 0 in the Errors column.
3. PR: a Coordination section in bench/cooperbench/report.py for the sdlc
   counters (claims, prs_opened, merge_attempts, merges, merge_conflicts,
   time_to_first_merge_seconds) and the team arm's metrics; METRICS.md
   names it as the one gap.
4. Once the owner's steps below are done: dispatch real on
   pallets_click_task/2068 first (the pilot), approve it, read the report,
   then the full list.

## The owner's steps before a real run (in this order)

1. coordbench Settings > Environments > New environment, named bench, with
   the owner as required reviewer:
   https://github.com/OpenSpineConsortium/coordbench/settings/environments
   The plan job refuses a real run until this exists with a reviewer.
2. One organization secret per Claude account, SYMPHONY_CLAUDE_1,
   SYMPHONY_CLAUDE_2, ... (up to 8), each the output of `claude setup-token`
   run while signed in to that account, with repository access including
   coordbench:
   https://github.com/organizations/OpenSpineConsortium/settings/secrets/actions
3. Repository variable SYMPHONY_CLAUDE_ACCOUNTS on coordbench, the slots in
   use, e.g. 1,2,3:
   https://github.com/OpenSpineConsortium/coordbench/settings/variables/actions
4. Later: remove COORDBENCH_CLAUDE_TOKEN from the claude.ai cloud
   environment, which the Actions run no longer needs.

The local clone is /home/user/coordbench at a581d02 (main). Project memory:
cooperbench-actions-benchmark.
