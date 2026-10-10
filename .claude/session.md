# Session checkpoint

Written 2026-10-10 at the end of the main account's session, for the next
session on any account. This session built the setup-only App the last
checkpoint recommended, so an adoption through the front door applies
the repository's settings in the same run, and answered the owner's
questions about running coordbench over several sessions, accounts and a
GPU grid; those became an issue in coordbench.

## Completed work

- The Setup App, merged as sdlc-app#4 and sdlc-start#6 from the branch
  claude/magical-shannon-ak167f of each. A second GitHub App, OpenSpine
  SDLC Setup (sdlc-app's manifest-setup.json: Administration write and
  Metadata read, no webhook, public), registered by
  `python3 scripts/register.py --setup --org OpenSpineConsortium` into
  .sdlc-setup-app.env. The adopter installs it on the one repository for
  the one run and uninstalls it afterwards; installing it is the consent,
  so the form has no field for it. In adopt.yml, after the push of
  sdlc/adopt, the run mints that App's token for the one repository,
  scripts/setup.py applies what scripts/setup-repo.sh applies (the
  ruleset of the template's docs/setup/ruleset-main.json, in mode
  existing without the required check; delete-on-merge and auto-merge;
  secret scanning, then push protection), revokes the token, and
  adopt.py body renders the report as the section Settings, from which
  the next steps follow. Where the mint fails, a probe on the owner's
  own installation (the Setup App on sdlc-start, metadata read) tells an
  adopter who did not install it from a broken front door; the second is
  told to the owner in the issue "Setup App of this front door is not
  working" on sdlc-start, since GitHub reports a red run only to the
  person who opened the request. A settings step that dies before its
  report, and a run that fails after the token was made, say so. The
  run's log gets one fixed line per setting; GitHub's words go to the
  report and the pull request.
- Reviewed by a five-dimension workflow (34 agents): 29 findings, all
  verified, all fixed, then a verification pass (6 agents) that found two
  partly fixed and five minor leftovers, fixed too: among them, every 3xx
  and non-JSON answer counted as done (now a redirect handler and a
  non-2xx refusal), the probe, the words for each outcome, "Only select
  repositories" in every install instruction, and the owner's alert by
  issue rather than by a red run. 139 tests in sdlc-start on 3.12, also
  against the real template; 137 in sdlc-app; actionlint clean on all
  three repositories' workflows.
- The template's start pages, links table and owner checklist say that
  the front door applies the settings with the Setup App installed (this
  pull request).
- Answered, with coordbench read in full: a cloud session has 4 CPUs,
  15 GB and about 30 GB of disk, Docker's daemon is installed and
  bench/cooperbench/setup.sh starts it; agents spend about 90 percent of
  their time waiting on the model; the ceiling is the subscription's
  usage window, not cores; run.py already has --concurrency, resume and
  pooled reports; sessions cannot reach another account's sessions, and
  Claude has no local inference. The owner's design, one orchestrator
  with claude -p workers each on one of their own accounts' tokens, and
  the grid route with a self-hosted model, are coordbench#6, opened by
  this session.
- The name: "polyphony" is free as a GitHub App name (the page 404s);
  the rename's three layers were costed in conversation (the App's name
  and slug; the repositories to polyphony-*, with GitHub's redirects; the
  user-facing identifiers, the plugin sdlc, the skills /sdlc:, the branch
  sdlc/adopt, the switch .github/sdlc-metrics, while the package
  sdlc_protocol and the SDLC_* variables may stay).

## Current state

- Everything above is merged. No pull request of this session is open
  apart from the one carrying this checkpoint.
- The Setup App is not registered yet, so every adoption pull request
  says the front door has no Setup App yet and the steps by hand stand;
  the front door is otherwise live and unchanged for adopters.
- The two test pull requests of the earlier live runs,
  sdlc-template-test#14 and sdlc-start-test#1, are still the owner's to
  merge or close.
- The auto-mode permission classifier allowed everything this session
  asked (attaching coordbench, the pull requests, the merges, the issue);
  the proxy still refuses the Actions variables and secrets API paths.

## Remaining tasks

1. The owner's steps for the Setup App (sdlc-start's README, For the
   owner, steps 7 and 8): from a clone of sdlc-app,
   `python3 scripts/register.py --setup --org OpenSpineConsortium`; if
   GitHub gives a slug other than openspine-sdlc-setup, change the
   install link in sdlc-start's .github/ISSUE_TEMPLATE/adopt.yml, its
   README and tests/test_form.py (SETUP_APP_INSTALL); install the Setup
   App on OpenSpineConsortium/sdlc-start and only it, for the probe; then
   `gh variable set SDLC_SETUP_APP_ID --repo OpenSpineConsortium/sdlc-start --body <id>`
   and `python3 scripts/register.py --env-file .sdlc-setup-app.env --print-key | gh secret set SDLC_SETUP_APP_PRIVATE_KEY --repo OpenSpineConsortium/sdlc-start`.
2. A live test of the Setup App, once step 1 is done: a throwaway
   repository with one commit and both Apps installed, the form in mode
   new, then the pull request's section Settings against the
   repository's rules, general settings and code security pages, the
   closing comment, and the uninstall; then a request without the Setup
   App, whose pull request should say so; sdlc-start-test can serve
   again once its branch sdlc/adopt is deleted.
3. The Polyphony rename, which the owner put after the setup App: the
   App first (name and slug, 14 slug links and 56 name mentions across
   the repositories), then the repositories, then the user-facing
   identifiers; each layer its own pull requests.
4. coordbench#6, the fan-out issue: the per-agent token in
   drivers.py, equal concurrency per arm, the grid route with Podman or
   Apptainer and the gateway variables; the pilot first in one session.
5. Carried: actions/create-github-app-token@v1 warns about Node 20, move
   to v2 (inputs to check first); existing-repo.md should say the front
   door's existing mode replaces the by-hand way; try crowd mode on a
   real organization copy; the 42 gradeable flash pairs; judge.py against
   a real model; the marketplace ruleset's unattributed-changes field;
   sdlc-app stage 2 (hosting the webhook); a public copy of the template
   is still the owner's decision and may not be needed.

To continue on another account: connect GitHub at claude.ai/code with
access to the OpenSpineConsortium repositories, open a session on
sdlc-template, read this file, and attach sdlc-start, sdlc-app,
sdlc-protocol or coordbench as the task needs. The Apps' private keys
stay only in the owner's .sdlc-app.env and .sdlc-setup-app.env and in
sdlc-start's secrets.

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
- An adoption's repository settings are applied by a second, setup-only
  App, OpenSpine SDLC Setup, holding Administration and Metadata and
  nothing else, which the adopter installs on the one repository for the
  one run and uninstalls afterwards; installing it is the consent; the
  main App never holds Administration on anyone's repository.
- The owner's own several Claude accounts may be coordinated from one
  orchestrator of theirs, workers as claude -p subprocesses each with one
  account's token; the owner decided this knowing the terms-of-service
  question, and it does not change the rule for contributors'
  credentials.
- The Polyphony rename comes after the setup App: the App first, then
  the repositories, then the user-facing identifiers; the package
  sdlc_protocol and the SDLC_* variables may stay.

## Constraints

- The cloud environment blocks cooperbench.com, arxiv.org, cursor.com,
  docs.github.com and github.com web pages. CooperBench's paper and data
  come from the GitHub repository cooperbench/website; GitHub's docs come
  from their source on raw.githubusercontent.com; a release asset
  (actionlint's) downloads.
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
  near a merge); the GitHub tools' pull request, merge and issue calls
  were allowed. A session that needs a refused action says so and leaves
  it to the owner.
- A cloud session's tools reach only its own account's sessions,
  environments and routines; there is no cross-account messaging, and
  Remote Control drives a session on the owner's own computer.
- A cloud session's container has 4 CPUs, 15 GB of memory and about
  30 GB of free disk; Docker's daemon is installed and starts on demand;
  a background command stops after two hours.
- Workflows cannot be resumed across sessions; a review left unfinished
  is re-run from its record. A workflow's agents run two at a time on
  this machine's four CPUs.
- The scratchpad and the workflows' journals die with the container.
