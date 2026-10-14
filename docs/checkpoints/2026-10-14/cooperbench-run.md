# CooperBench run with Symphony workers: checkpoint, 2026-10-14 23:40 UTC

Thread: "CooperBench" of the symphony project, carrying item 2 of the
2026-10-14d handoff, stopped when the owner's weekly usage ran out. The
owner asked (2026-10-13 23:04) to start CooperBench benchmarking with the
workers automatically, working, and reporting every statistic needed to
compare against the CooperBench paper and its follow-ups. The run lives in
OpenSpineConsortium/coordbench's own GitHub Actions. coordbench's main is
5e4860e.

## Landed (merged, CI green)

- coordbench#11 (merge 0de6a70): the kit runs on any Docker host and run.py
  scrubs the agents' token from every file a pair leaves.
- coordbench#12 (merge a581d02): .github/workflows/bench.yml with modes
  fake, survey and real, its jobs and actions, PLAN.md (the
  pre-registration), pairs.txt and METRICS.md.
- coordbench#13 (merge dd9aa2d): the protocol library named by its current
  repository, symphony-protocol.
- coordbench#14 (merge 99cd576): the Actions kit fixed from the
  after-the-fact review of #12 (the review's notes:
  docs/checkpoints/2026-10-14d/notes/coordbench-review-14.md).
- coordbench#15 (merge a5ddac2): the pair list fixed from the survey
  (bench.yml in survey mode, tag survey-1, run 38549172370): all 20 tasks
  and 50 pairs of CooperBench's flash subset grade on GitHub's runners.
- coordbench#16 (merge 5e4860e): the protocol's own counts (claims, pull
  requests, merge attempts, merges, conflicts, time to first merge) beside
  the emergent rates in the report, the gap METRICS.md named.

## In flight: coordbench#17, the read-back before upload

https://github.com/OpenSpineConsortium/coordbench/pull/17, draft, branch
claude/coordbench-scrub-layers-8d9veg, head 21f5382, every check green
(check, CodeQL, the smoke bench run). It makes the check that runs before
a pair's files are uploaded to a public artifact (`run.py scrub`, then
`unscrubbed`) open every layer by its bytes, gzip, xz, lzma, bzip2, tar,
zip, ar, git loose objects, packs and bundles, up to eight deep under one
budget, so a token packed or committed under any name is caught. It must
merge before any real run publishes artifacts.

Four rounds of fixes, each after an adversarial review: 7 findings, then
22, then 13 gaps and a dozen unpinned tests, then 28 (commit 21f5382's
message lists them). The fourth round's own review was stopped part way:
docs/checkpoints/2026-10-14e/notes/coordbench-review-17-round4.md holds
what it found. It found a verified blocker, a regression of 21f5382: a
zip -s first part that ends with a stored zip is read as that inner zip
and passes with the token inside, which 0d3279b refused. Three verified
should-fix findings: a tar header shorter than 512 bytes ends the scrub
in a traceback (struct.error from is_broken_tar), a zip64 split archive's
last part is never opened, and is_broken_tar takes a zipapp for a tar so
its members are not read. One should-fix finding is unverified (a file
with ustar at byte 257 that is not a tar is no longer refused). The claims
and tests lens did not finish.

Next on #17, in order: fix each finding with a test that fails on 21f5382;
`bash scripts/check.sh` with Python 3.12 first on PATH; an adversarial
review of the fixes; rewrite #17's description to cover all four rounds
(it describes the first two); mark it ready and merge it with a merge
commit once green, the expected head sha copied from git.

## Then, in order

1. Dispatch bench.yml on main in fake mode (Actions > Bench > Run
   workflow: mode fake, pairs @bench/cooperbench/pairs.txt, arms left at
   solo,coop,coop-git,team,sdlc, tag fake-1;
   https://github.com/OpenSpineConsortium/coordbench/actions/workflows/bench.yml).
   No usage is spent. Expect every pair Submitted and 0 in the Errors
   column of its report's Pass rates table.
2. Update this file with the fake run's result.
3. The owner's steps below, then a real dispatch on
   pallets_click_task/2068 first (the pilot), approved on its run's page
   (Review deployments, tick bench, Approve and deploy), its report read;
   then the full list, @bench/cooperbench/pairs.txt. No real run before
   the owner's steps.

## What the read-back does not open (bench/cooperbench/README.md)

A marker encoded another way (base64); a stream that starts partway
through other bytes; a zip after a git loose object or pack; a zip whose
directory zipfile cannot read (a non-UTF-8 name under the UTF-8 flag),
refused in a work tree and searched as it is in history; a v7 tar with a
broken first header; a split zip's first and middle parts in history; a
path staged and never committed in a git index of version 4. zstd, 7z,
rar, lz4, .Z and lzip are refused.

## The owner's steps before a real run (in this order)

1. coordbench Settings > Environments > New environment, named bench, with
   the owner as required reviewer (Prevent self-review left unticked,
   deployment branches limited to main):
   https://github.com/OpenSpineConsortium/coordbench/settings/environments
   The plan job refuses a real run until this exists with a reviewer.
2. One organization secret per Claude account, SYMPHONY_CLAUDE_1,
   SYMPHONY_CLAUDE_2, ... (up to 8), each the output of `claude setup-token`
   run while signed in to that account, Repository access set to Selected
   repositories with coordbench ticked:
   https://github.com/organizations/OpenSpineConsortium/settings/secrets/actions
3. Repository variable SYMPHONY_CLAUDE_ACCOUNTS on coordbench, the slots in
   use, e.g. 1,2,3 (three accounts let one dispatch hold all 50 pairs
   under five arms):
   https://github.com/OpenSpineConsortium/coordbench/settings/variables/actions
4. Later: remove COORDBENCH_CLAUDE_TOKEN from the claude.ai cloud
   environment, which the Actions run no longer needs.

## Rules the thread kept

Scrub and leak tests plant only the stand-in PLANTED in ordinary files,
never a link to /proc/self/environ or a real environment file; reviewer
prompts frame the work as a coverage audit of the project's own check.
