# Session checkpoint

Written 2026-10-11 in the main account's session, for the next session
on any account. This session made installing the App the request, two
ways: the install now ends on the adoption form with the installation
filled in, so the pull request is open within about two minutes with no
server and no typing, and a scheduled sweep answers an installation that
never reaches the form, within the hour. Both are merged on sdlc-start;
the owner's one action and the two live tests are below.

## Completed work

- The install ends on the form, sdlc-start#14 (closes sdlc-start#12).
  GitHub sends whoever installs the App to its Setup URL with
  installation_id in the query string, and an issue form fills in a
  field of that name, so with the Setup URL set to the form the person
  lands on it with the Installation field filled in, chooses the kind
  and the metrics and submits. The repository field is optional: the
  form carries a name or the installation's number. With the number,
  adopt.yml signs the App's JWT (scripts/jwt.sh), mints the
  installation's token with metadata alone, lists the repositories it
  reaches and takes the one it holds once the author is read as its
  administrator; not this App's installation, several repositories and
  an author who is not an administrator get one identical answer, so a
  guessed number learns nothing; the name is masked and never passed on,
  and adopt-run.yml gets the ids. A repository given by ids is "your
  repository" in the answers on the public issue, with the links left
  out (SAID, PULLS_LINK, BRANCHES_LINK, SETTINGS_WORDS in the run's
  environment). The owner's step 9 in sdlc-start's README is the Setup
  URL with "Redirect on update".
- The sweep, sdlc-start#13 (closes sdlc-start#10): installing the App
  without the form is a request too. Every ten minutes sweep.yml signs
  the App's JWT, scripts/sweep.py lists the installations and their
  repositories and writes the candidates (installation id, repository
  id, mode read from the tree) to a file, and the workflow dispatches
  adopt-run.yml per candidate with ids only. adopt-run.yml is the
  adoption itself, reusable: workflow_call from adopt.yml and
  workflow_dispatch from the sweep; the ids path resolves the name with
  a metadata-only token and masks the name, the owner's, the requester's
  login and the default branch before anything prints them. The form
  wins (a 30-minute grace on the installation's updated_at or
  created_at; repositories named on open adopt issues, read from the
  JSON gh writes, are left alone); the sweep skips offered (branch
  sdlc/adopt), adopted (PROTOCOL.md), declined (closed pull request from
  sdlc/adopt), refused (the App's open issue "OpenSpine SDLC could not
  open its pull request"), opted out (.github/sdlc-adopt says off),
  archived, no commit, no Issues, and the organization's own; an
  installation short of a write permission is passed over without a
  token; a time budget of 420 seconds under the JWT's life, incremental
  writes and a rotating start. A refusal or a failure after the push on
  that path is told in one issue of the App's in the repository, which
  the sweep reads as told until it is closed. A five-lens review (five
  reviewers, stopped before its refutation stage to save time) found
  seven defects, all fixed before the merge: among them the pending list
  was never filled, because a heredoc on the same command took the
  pipe's place as python's stdin. 215 tests in sdlc-start on 3.12, also
  against the real template; actionlint clean.
- Answered in conversation: the sweep is slower than the form by design
  and cannot match it without an event source; GitHub hosts no always-on
  compute a webhook can reach; a hosted webhook service would cost a few
  dollars a month and a host to keep, with the App's key on it; the Setup
  URL path gives the form's latency with no server, so that was built.

## Current state

- The one-press path is live and tested. sdlc-start's main is 5e20baf:
  #14 (the install ends on the form, the ids path), #15 (the form one
  button), #17 (the request job resolves by id and learns no name, after
  a two-lens review), #18 (the form down to three fields and four
  sentences; the run picks the newest unadopted repository of an
  installation). The owner had already set the Setup URL to the form.
  Live: the owner installed the App on a fresh repository, GitHub sent
  them to the form with the installation filled in (170148056), one
  press of Create, and 49 seconds later the pull request, the labels and
  the setup issue were in the repository and the issue (sdlc-start#19)
  answered and closed; the public log showed the name, the owner, the
  default branch and the login as masked words. The Setup App was not
  on that repository, so the settings were left to the by-hand steps,
  as the pull request says.
- The sweep (sdlc-start#13) is merged as the fallback; its schedule had
  not fired by 04:15 UTC (GitHub delays a new schedule), so its dispatch
  path is unproven live; the ids path it shares with the form is proven
  by #19. If the owner wants no scheduled sweep, delete sweep.yml and
  scripts/sweep.py with their tests; the rest stands.
- The template's start pages, the links table and the memory fact
  the-front-door-is-one-press.md say install, press Create, merge (this
  pull request).
- Test repositories: sdlc-setup-test#1 and sdlc-start-test#3 are open;
  sdlc-template-test#14 is open; the Setup App is still installed on
  sdlc-setup-test and is the owner's to uninstall. test-non-org may or
  may not still be in an installation of the owner's.
- This session attached Gregory-Schwing-MD-PhD/test-non-org (push access)
  and cloned it to /home/user/test-non-org; a cloud session's attached
  repositories die with the container.

## Remaining tasks

1. Watch the sweep's first scheduled run on sdlc-start (Actions tab,
   Sweep) and read its log: counts only, and one dispatch per candidate
   if any installation has an unadopted repository older than the grace.
2. The marketplace skills (sdlc-marketplace#2), /polyphony:new and
   /polyphony:migrate after the rename, which do everything but the
   install click: gh repo create, the install page opened, the form
   issue opened as the user (now with the installation prefilled from
   the install's redirect, or named), the pull request watched and merged
   on the person's word. The browser extension's buttons
   (sdlc-start#11) link to the install page and the form.
3. The Polyphony rename, which the owner put after the setup App: the
   App first (name and slug), then the repositories, then the user-facing
   identifiers; each layer its own pull requests.
4. coordbench#6, the fan-out issue: the per-agent token in drivers.py,
   equal concurrency per arm, the grid route; the pilot first in one
   session.
5. Carried: actions/create-github-app-token@v1 warns about Node 20, move
   to v2; existing-repo.md should say the front door's existing mode
   replaces the by-hand way; try crowd mode on a real organization copy;
   the 42 gradeable flash pairs; judge.py against a real model; the
   marketplace ruleset's unattributed-changes field; sdlc-app stage 2
   (the webhook server) only if two minutes still reads as slow: it
   would dispatch sweep.yml for one installation with a short grace and
   add no logic; a public copy of the template is still the owner's
   decision and may not be needed. If the owner wants no scheduled
   sweep, delete sweep.yml and scripts/sweep.py with their tests; the
   rest stands.

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
- Installing the App is the request. The install's redirect (the App's
  Setup URL) lands on the form with the installation filled in, and one
  press of Create is the request: the run picks the installation's
  newest repository with no adoption yet, reads the kind from the tree
  and shares aggregates unless a box says otherwise; the form assumes the
  person knows what they are doing. The sweep is the fallback for an
  installation that never reaches the form. A webhook, if ever hosted,
  dispatches sweep.yml for one installation with a short grace and adds
  no logic of its own.
- A repository given by ids, from the sweep or from the form, is never
  named on the public side: not in a log, a run input, a step output, a
  job summary or an issue; the run resolves and masks the name and
  answers "your repository". A guessed installation number learns
  nothing: not the App's, several repositories and not an administrator
  are one answer.

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
- A GitHub App's installation on an organization has one repository
  list: the install link, opened for another repository with "Only
  select repositories", replaces that list; a repository of the
  organization's is added under Configure. The proxy refuses the
  organization's installations endpoints and deleting a branch.
- Workflows cannot be resumed across sessions; a review left unfinished
  is re-run from its record. A workflow's agents run two at a time on
  this machine's four CPUs.
- The scratchpad and the workflows' journals die with the container.
- GitHub hosts no always-on compute a webhook can reach: Actions runs on
  repository events, a schedule or an API call with a token, and a
  webhook delivery carries none; a newly added schedule may wait a long
  time for its first run.
- The sweep never touches the organization's own repositories (--own),
  since the main App is on "All repositories" there; a repository whose
  Issues are off is left to the form.
- A heredoc on a command that is also fed by a pipe takes the pipe's
  place as stdin; in a workflow, write the data to a file and read it by
  path.
