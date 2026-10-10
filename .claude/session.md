# Session checkpoint

Written 2026-10-10 at the end of the main account's session, for the next
session on any account. This session finished the three reviews the last
one left in .claude/handoff.md, fixed every finding that stood, opened the
four pull requests the last checkpoint named and merged them in its order.
The handoff file is gone with the docs pull request.

## Completed work

- Start-here documentation, merged as sdlc-template#24 from the branch
  claude/magical-shannon-ak167f (which took claude/festive-edison-al7xu2's
  commits and went on from them): docs/start/ with its two reviews
  finished. The second review's 49 findings were each re-verified by an
  agent per page and checked by a second agent per page; all 49 held, two
  in part, and each is fixed in its page. The pages outside docs/start that
  name the same things (coordinator.md, worker.md, OWNERSHIP.md, github.md,
  owner-checklist.md) carry the same corrections, and scripts/setup-repo.sh
  tells an old gh apart from a plan limit. 312 tests on 3.12.
- Field metrics, template side, merged as sdlc-template#25 from the branch
  field-metrics: tools/metrics.py (collect, judge, push), metrics.yml,
  docs/setup/metrics.md, the switch file, a memory fact, and template_init
  emptying a copy's checkpoint block. The review's 29 findings: 3 refuted
  by the earlier verifiers, 23 fixed, 3 left with a sentence on the page
  (the version format, which the collector accepts; thread replies counted
  as reviews; dismissed changes-requests not counted). The blocking four:
  the three tests that failed in every copy are template-only; the run is
  at 03:43 UTC, before the collector's 04:17 read, and on a merge that
  changes the switch; a branch metrics the project had before is never
  replaced; the crowd checkpoint skill no longer fails a test. A run stops
  short of a reserve of 300 requests for the board; check runs are read on
  every commit made in the window with every attempt. 385 tests on 3.12,
  and the suite passes in an initialised copy with sharing off.
  docs/start/links.md names the workflow, the branch and SDLC_METRICS.
- Field metrics, collector, merged as sdlc-app#3 from that repository's
  branch claude/festive-edison-al7xu2: scripts/collect.py and collect.yml
  (reviewed earlier, 9 findings fixed), plus this session's changes: the
  salt is derived from the App's private key (HMAC-SHA256 of the PEM under
  the label sdlc-metrics-salt, HKDF's extract step) with SDLC_METRICS_SALT
  as an optional override, so the owner sets no third secret; forks and
  archived repositories are skipped unread and counted; the README's
  advice to set the App's key at the organization with --visibility all is
  corrected, and its GitHub Free sentence about auto-merge too. 127 tests.
- Private adoption, merged as sdlc-start#1 from that repository's branch
  claude/festive-edison-al7xu2: the form, adopt.yml, scripts/adopt.py,
  refuse.sh and the tests, with the review's 31 findings fixed: the target
  checkout's ref is qualified (a bare name made actions/checkout fetch and
  print every branch and tag whose name starts with it); the App's tokens
  come in an order that tells a stranger nothing about a repository they
  name (account-only token with metadata read, silenced lookups, then the
  repository-scoped write token); a broken App is told from an uninstalled
  one and ends the run red with the issue open; git's messages, the pull
  request's number and the template's release line stay out of the log;
  mode existing takes the protocol's page from sdlc-protocol's
  spec/PROTOCOL.md at the commit tools/VENDORED names (apply's
  --protocol-spec), brings a workflow and its script together or not at
  all, never writes a file the repository ignores, and adds CLAUDE.md's
  import only when the page landed; mode new opens the "Set up this
  project" issue. 99 tests on 3.12; the real-template tests pass against
  the template's main.

## Current state

- Everything above is merged. No pull request of this session is open
  apart from the one carrying this checkpoint.
- sdlc-start is live. The owner made the label adopt, the ruleset
  "Protect the default branch" on its main, made the App public with the
  permission Workflows: Read and write accepted on the organization's
  installation, and confirmed SDLC_APP_ID and SDLC_APP_PRIVATE_KEY there.
  The first live request (sdlc-start#3, mode existing, sharing off, into
  the old copy OpenSpineConsortium/sdlc-template-test) was answered in 28
  seconds with the pull request sdlc-template-test#14: 20 files added,
  .claude/settings.json merged, 4 kept; its public log names no file,
  branch or number of the private side. That pull request is the owner's
  to close or merge. The run showed one wrong sentence for a repository
  that already had the board's workflow, fixed in sdlc-start#4.
- The license of adopted files is MIT, in sdlc-start's LICENSE
  (sdlc-start#2); sdlc-protocol's README no longer blames GitHub Free for
  sdlc-app's unarmed auto-merge (sdlc-protocol#2).
- sdlc-app has auto-merge on and the one ruleset 24851112 "main"
  (active, requires the check "check"); the template has ruleset
  24827932.
- The auto-mode permission classifier refused creating the label adopt
  with gh api and one git command in a merge context, and the proxy
  refuses the Actions variables, secrets and rulesets API paths, so those
  settings are the owner's to make on their own machine. Attaching
  sdlc-protocol was refused once and allowed when the owner asked for it;
  the GitHub tools' pull request and merge calls were allowed throughout.

## Remaining tasks

1. A live test of mode new is still to run: a throwaway repository
   with one commit and the App installed, the form with "New repository",
   and a look at the copy's checkpoint block, the setup issue the run
   opens and the labels. Mode existing is proven (Current state).
2. Setup with no manual steps (the owner asked for it): either a second,
   setup-only App "OpenSpine SDLC Setup" holding Administration and
   Variables (write), which adopters install for one run and remove, and
   which applies what scripts/setup-repo.sh does in the same run; or one
   closing command, `bash scripts/setup-repo.sh`. The setup App was
   recommended. Never ask for Secrets: an adopter's Claude token is theirs.
   No OAuth; it needs a server. Change the App's permissions once, when
   this lands, since every installation must accept each change.
3. actions/create-github-app-token@v1 targets Node 20, which the
   runners now warn is deprecated and force onto Node 24; the carried
   item to move to v2 is worth doing soon, since the front door's run
   prints that warning every time.
4. docs/start/README.md and links.md now name the front door for anyone
   outside the enterprise; existing-repo.md still describes the by-hand
   way, which the front door's existing mode replaces for most; say so
   there once the front door is live.
5. Carried from the earlier checkpoints: try crowd mode on a real
   organization copy; the 42 gradeable flash pairs; judge.py against a
   real model; the marketplace ruleset's unattributed-changes field
   (the template's own ruleset has require_extra_approval_for_unattributed_changes
   true, and the pull requests merged all the same); sdlc-app stage 2
   (hosting the webhook); actions/create-github-app-token v2.
6. A public copy of the template, which the docs/start pages say the
   owner publishes, is still the owner's decision; with sdlc-start live it
   may not be needed.

To continue on another account: connect GitHub at claude.ai/code with
access to the OpenSpineConsortium repositories, open a session on
sdlc-template, read this file, and attach sdlc-start, sdlc-app or
sdlc-protocol as the task needs. The App's private key stays only in the
owner's .sdlc-app.env and in the repositories' secrets.

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
- The collector's salt is derived from the App's private key, with
  SDLC_METRICS_SALT as an optional override; rotating the key, or changing
  the override, gives every repository a new hash.
- The metrics workflow never replaces a branch metrics that holds files
  it did not write, never runs in a fork, runs at 03:43 UTC before the
  collector's 04:17 read, and on a merge that changes the switch.
- Mode existing of the adoption takes the protocol's page from
  sdlc-protocol's spec/PROTOCOL.md at the commit the template vendors,
  and the App's tokens are minted account-first, so a public run log says
  nothing about a repository a stranger names.
- The pull requests this project's sessions open are merged by the
  session once their check is green, as the last checkpoint asked and as
  the earlier sessions did; the repositories' rulesets require no review.
- The files an adoption brings are offered under the MIT License, the
  template's own, in sdlc-start's LICENSE with OpenSpineConsortium as the
  holder; the adoption copies no LICENSE into anyone's repository.

## Constraints

- The cloud environment blocks cooperbench.com, arxiv.org, cursor.com,
  docs.github.com and github.com web pages. CooperBench's paper and data
  come from the GitHub repository cooperbench/website; GitHub's docs come
  from their source on raw.githubusercontent.com.
- The cloud environment withholds CLAUDE_CODE_OAUTH_TOKEN; coordbench
  reads COORDBENCH_CLAUDE_TOKEN, each account its own.
- gh issue and gh pr are refused in cloud sessions. Use the GitHub tools
  or gh api; the proxy also refuses the Actions variables and secrets
  paths of the API.
- sdlc-template is internal to its enterprise. sdlc-start is public, so
  nothing of the template may be committed there, and its Actions logs
  are public too.
- The auto-mode permission classifier can refuse an outward write (a
  label through gh api, a repository attached mid-session, a git command
  near a merge); the GitHub tools' pull request and merge calls were
  allowed. A session that needs a refused action says so and leaves it
  to the owner.
- Workflows cannot be resumed across sessions; a review left unfinished
  is re-run from its record. A workflow's agents run two at a time on
  this machine's four CPUs.
- The scratchpad and the workflows' journals die with the container.
