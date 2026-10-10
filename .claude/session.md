# Session checkpoint

Written 2026-10-10 at the end of the main account's session, for the next
session on any account. This session built three things: the start-here
documentation, field metrics, and a private way to adopt the template.
Everything is pushed to a branch, and no pull request is open yet.
The reviews that were running when the session ended are saved in
.claude/handoff.md: every finding, whether the verifiers kept it, and
the fix each one proposed. Delete that file in the pull request that
finishes the reviews.

## Completed work

- Earlier in this session, all merged: the one-push protocol sync,
  CooperBench parity in coordbench, the pilots, crowd mode and the
  checkpoint pull request sdlc-template#23. See the git history and
  coordbench's PARITY.md.
- Start-here documentation, branch claude/festive-edison-al7xu2 of
  OpenSpineConsortium/sdlc-template, commits f801d41 and c97b2f0:
  docs/start/ (README, solo, parallel, team, crowd, existing-repo,
  benchmark, protocol, prompts, links). A first review found 20 problems
  and all 20 were fixed, among them a blocker: team mode gave writers
  access to the owner's Claude token. board.yml now sends the routines
  beta header (anthropic-beta: experimental-cc-routine-2026-04-01) that
  /fire needs. Checks pass: 312 tests on 3.12.
- Field metrics, template side, branch field-metrics of sdlc-template
  (commits f66307e and 4f69996, pushed with the owner's leave):
  tools/metrics.py (collect, and the judge, which runs client side),
  .github/workflows/metrics.yml, which writes METRICS.json to the branch
  metrics, the switch file .github/sdlc-metrics, docs/setup/metrics.md,
  a memory fact, and template_init blanking the CLAUDE.md checkpoint
  block in a copy. That block holds this template's own decisions, which
  copies used to inherit.
- Field metrics, collector, branch claude/festive-edison-al7xu2 of
  OpenSpineConsortium/sdlc-app (f3d151d, f71ce66, e4ec1e5):
  scripts/collect.py and .github/workflows/collect.yml. The collector
  reads only METRICS.json and JUDGE.json at the ref metrics in every
  repository the App is installed on. It keeps only allowlisted numbers,
  stores each repository as HMAC-SHA256 of its node id, and appends to the
  branch data. Its review is finished and all 9 findings are fixed;
  116 tests pass.
- Private adoption: the new public repository
  OpenSpineConsortium/sdlc-start, branch claude/festive-edison-al7xu2
  (24ff731, on top of GitHub's initial commit). It has an issue form, a
  workflow that uses the App's tokens to open an adoption pull request in
  the adopter's repository, scripts/adopt.py (parse, apply, body,
  labels), and tests (77 pass). New mode brings the whole template filled
  in; existing mode brings the protocol only and never overwrites their
  files. LICENSE is never copied. The repository holds no file of the
  template: the copy of tools/template_init.py the builder made was
  replaced by tests/fixtures/fake_init.py before the first push, so it
  is in no published commit.

## Current state

- Nothing is merged from this part of the session; four branches wait
  (above). sdlc-app's review is done; the other three have reviews in
  .claude/handoff.md, verified in part.
- Owner settings made this session: sdlc-app has auto-merge on and the
  ruleset 24851112 "main" (no approval, the check "check" pinned to
  GitHub Actions 15368, strict off). The older ruleset 24827947 was to
  be deleted, and its field require_extra_approval_for_unattributed_changes
  set to false. Check both with
  `gh api repos/OpenSpineConsortium/sdlc-app/rulesets --jq '.[] | [.id, .name] | @tsv'`.
- sdlc-start has the variable SDLC_APP_ID (5258276) and the secret
  SDLC_APP_PRIVATE_KEY. The label adopt may not exist yet. Its workflow
  answers issues only once it is on main.
- The App's Setup URL is the adoption form, with "Redirect on update"
  on. The App is still private, and it does not have the Workflows
  permission yet.

## Remaining tasks

1. Finish the reviews in .claude/handoff.md: re-verify each finding
   marked NOT YET VERIFIED, fix the ones that stand, then run the checks
   (`bash scripts/check.sh` in each repository; Python 3.12). The
   blocking ones: the metrics side's checkpoint-block test fails in every
   copy, the crowd pin sentence, turning sharing off breaks the required
   check, the first metrics run wipes an existing metrics branch; in
   sdlc-start, the target checkout's short ref prints the adopter's branch
   names into the public log.
2. Open the pull requests and merge, in this order: the docs branch
   (sdlc-template), then field-metrics (sdlc-template), then sdlc-app,
   then sdlc-start. sdlc-start's pull request needs the template side
   merged first, because adopt.py copies metrics.yml when the template
   has it. After field-metrics merges, add links from docs/start to
   docs/setup/metrics.md and to sdlc-start.
3. The collector's salt: derive it from the App's private key, with
   SDLC_METRICS_SALT as an optional override, so the owner sets no new
   secret. Rotating the key changes every hash; the README must say so.
4. Setup with no manual steps (the owner asked for it). Give the App
   Workflows (write) now, which an adoption pull request with workflow
   files needs. Then either a second, setup-only App "OpenSpine SDLC
   Setup" holding Administration and Variables (write), which adopters
   install for one run and remove, and which applies what
   scripts/setup-repo.sh does in the same run (auto-merge, delete branch
   on merge, the ruleset, the variables); or one closing command,
   `bash scripts/setup-repo.sh`. The setup App is recommended. Never ask
   for Secrets: an adopter's Claude token is theirs, and
   `/install-github-app` in Claude Code stores it. No OAuth; it needs a
   server. Change the App's permissions once, when this lands, since
   every installation must accept each change.
5. Before strangers can use the front door: make the App public
   (https://github.com/organizations/OpenSpineConsortium/settings/apps/openspine-sdlc/advanced),
   create the label adopt on sdlc-start, and decide the license of
   adopted files (the template's LICENSE is MIT, and adopt.py does not
   copy it).
6. sdlc-protocol's README says GitHub Free keeps sdlc-app from
   auto-merging. That is wrong: the organization is on Enterprise Cloud.
   Correct it there.
7. Carried from the previous checkpoint: try crowd mode on a real
   organization copy; the 42 gradeable flash pairs; judge.py against a
   real model; the marketplace ruleset's unattributed-changes field;
   sdlc-app stage 2 (hosting the webhook); actions/create-github-app-token
   v2.

To continue on another account: connect GitHub at claude.ai/code with
access to the OpenSpineConsortium repositories, open a session on
sdlc-template, check out claude/festive-edison-al7xu2, and read this file
and .claude/handoff.md. The other branches are named above. The App's
private key stays only in the owner's .sdlc-app.env and in the
repositories' secrets.

## Decisions

Stated by the owner in conversation, this session and earlier:

- Prefer GitHub's native, free features. No API billing: Claude in CI
  runs on a subscription OAuth token, and never with ANTHROPIC_API_KEY.
- A protocol change is made in sdlc-protocol and reaches every consumer
  by its sync on one push.
- coordbench measures what CooperBench measures, differing only with a
  stated reason (PARITY.md).
- Crowdsourcing: each contributor works under their own Claude account,
  and the project never holds anyone's credential.
- Field metrics: no hosted server. Sharing is on by default, said
  plainly, with one switch off. Only aggregates are shared (counts,
  durations, rates, failure-type frequencies): never code, text, titles,
  names or repository names. A repository appears only as a salted hash.
  The failure-mode judge runs client side, on the maintainer's own
  machine and Claude account.
- "Free to use" is not "free access to the source". The template
  repository stays private. Anyone adopts it by the form in the public
  sdlc-start, which holds no file of the template; the files an adopter
  receives in their own repository are theirs to read.
- field-metrics is its own branch and pull request, apart from the docs.

## Constraints

- The cloud environment blocks cooperbench.com, arxiv.org, cursor.com,
  docs.github.com and github.com web pages. CooperBench's paper and data
  come from the GitHub repository cooperbench/website; GitHub's docs come
  from their source on raw.githubusercontent.com.
- The cloud environment withholds CLAUDE_CODE_OAUTH_TOKEN; coordbench
  reads COORDBENCH_CLAUDE_TOKEN, each account its own.
- gh issue and gh pr are refused in cloud sessions. Use the GitHub tools
  or gh api.
- sdlc-template is internal to its enterprise. sdlc-start is public, so
  nothing of the template may be committed there, and its Actions logs
  are public too.
- Workflows cannot be resumed across sessions; a review left unfinished
  is re-run from .claude/handoff.md.
- The scratchpad and the workflows' journals die with the container.
