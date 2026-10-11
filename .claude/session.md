# Session checkpoint

Written 2026-10-11, evening, in the main account's session, for the next
session on any account. The rename to Symphony is done and merged in all
five repositories, the Apps and the site; the day's later work was the
Chrome Web Store release kit as its own repository, Symphony for Chrome's
releases through it, the fix for the eight-repository adoption, the
Migrate button that carries its repository, both Apps required on the
form, and the GitHub Apps' privacy statement. What only the owner can do
is listed first.

## The owner's list, in order

1. Revert the eight adoptions of 2026-10-11: symphony-start issue #23
   (installation 170355452, "Merge the pull request for me" ticked, no
   repository named) adopted and merged Symphony into eight repositories
   of GregorySchwing's before run 38165412998 was cancelled (ids
   1391648997, 1394286173, 921196031, 1096074276, 889730726, 817893214,
   773105702, 749539564; four more were cancelled before any push). The
   merged pull requests are listed at
   https://github.com/pulls?q=is%3Apr+author%3Aapp%2Fsymphonyboard+is%3Amerged;
   revert each, or name the repositories to a session with access and it
   opens the reverts. The labels and, in a new repository, the setup
   issue stay to delete.
2. Upload the Apps' logos and set their descriptions: on each App's
   settings page (https://github.com/organizations/OpenSpineConsortium/settings/apps/symphonyboard
   and .../symphony-setup), Display information, Logo: the PNGs the site
   now hosts, https://openspineconsortium.com/symphony/symphonyboard-logo.png
   (GitHub's mark in warm white with the orange baton, the extension's
   icon ring and tile) and
   https://openspineconsortium.com/symphony/symphony-setup-logo.png (the
   gear); the SVG sources sit beside them. Add to each description the
   privacy page: https://openspineconsortium.com/symphony/apps-privacy.html.
3. Submit Symphony for Chrome 1.1.0 (docs/store/SUBMISSION.md in
   OpenSpineConsortium/symphony-extension): the zip is the release the
   kit made for the latest main
   (https://github.com/OpenSpineConsortium/symphony-extension/releases/latest/download/symphony-chrome.zip);
   do the hand test in docs/store/TEST_BEFORE_UPLOAD.md first, the
   Migrate chain above all, since no session can press it. Then set the
   five CWS_ secrets and CWS_ON_PUSH=upload on the extension repository,
   and every merge to main uploads itself.
4. Optional: update the repositories' descriptions on GitHub; press Run
   workflow on symphony-start's Sweep once; uninstall the Setup App from
   sdlc-setup-test.

## Completed work

- The rename, both tiers, merged everywhere (template #34, #36 to #39
  the checkpoints; the five flips and the site's #7). The Apps are
  SymphonyBoard (slug symphonyboard) and Symphony Setup (slug
  symphony-setup); GitHub refused Symphony, Symph, Symph0ny (accounts)
  and Symphony Dev (another App).
- The Chrome Web Store release kit moved out of claude-swap-cloud into
  OpenSpineConsortium/chrome-store-release-kit (private; Actions access
  "Accessible from repositories in the organization"): the reusable
  workflow .github/workflows/release-kit.yml and release-kit/ (package
  and store actions, tests, a fixture extension, CI green). A caller's
  push to main builds the zip, numbers it <manifest>.<commit count>,
  makes the GitHub release extension-v<version> with <name>-<version>-chrome.zip
  and <name>-chrome.zip, and uploads to the store when CWS_ON_PUSH is
  upload or publish with the five CWS_ secrets; unset, the run stays
  green and says "Not configured". claude-swap-cloud was left alone.
- Symphony for Chrome releases through the kit (.github/workflows/release.yml):
  1.0.0.9 the first, 1.0.0.10 the Symphony-orange buttons, then the
  create-button fix (ours follows GitHub's disabled state and comes back
  after a press), then 1.1.0 (below). CI's artifact step needed
  include-hidden-files for .output.
- The eight-repository adoption fixed in symphony-start#24, merged: one
  press adopts one repository (resolve.py LIMIT 1, the newest with no
  adoption yet, or the one the form names); the form's Repository field
  has the id state, so the repository the extension's button carries
  through GitHub's install link arrives filled in; both Apps are
  required on the form's two paths (the installation path keeps only a
  repository Symphony Setup reaches; the named path refuses, with the
  Setup App's install link preselected on that repository, when it is
  not installed there); the sweep adopts without it, as before.
- Symphony for Chrome 1.1.0: Migrate and the post-Create banner open
  SymphonyBoard's permissions page with target_id, suggested_target_id,
  repository_ids[] (from the page's octolytics-dimension-repository_id
  tag) and state=OWNER/NAME; a thirty-minute note symphony.migrate
  chains the Setup App's install after the Board's from the form page,
  adds the repository to the form's address when GitHub left it out,
  and, on an installation's settings page reached from Migrate (the
  Board installed already), offers the Setup App's install in a banner;
  PRIVACY.md version 2; hygiene tests hold the rest.
- The two GitHub Apps' privacy statement, PRIVACY.md in symphony-start,
  from a six-agent reading of the App's, the front door's and the
  template's code with every claim verified or corrected (six
  permissions, not five; the installation's number and a typed name on
  the public log; the dataset's git history; the sweep reads opted-out
  repositories too). The site renders it at /symphony/apps-privacy.html
  and links it from the install card, the footer and the strip; the
  install card shows the two logos; the Start steps say both Apps.

- "Ready for Symphony": an adopted repository carries the GitHub topic
  symphony, set by the adoption run through the Setup App
  (symphony-start#26) and by scripts/setup-repo.sh (#41); the extension
  (1.2.0, release 1.2.0.13) reads the About sidebar's topic link from the
  page, with no API call, and turns the header button into Ready for
  Symphony, a link to the board, with no banner. A repository adopted
  before the topic existed (the owner's GOMC, the sweep's adoptions, the
  test repositories) gets the topic by hand under About.
- The six merged adoptions of 2026-10-11 are the owner's to undo with the
  script undo-symphony.sh given in chat (revert, ruleset, labels,
  branches, opt-out file), signed in as GregorySchwing; this session has
  no access to that account's repositories. The four open test
  adoptions were closed from here.

## Current state

- Merged on main: symphony-start#24; the site's master carries the
  Apps' privacy page and the logos (f4d6497, deployed by Pages).
- Symphony for Chrome 1.1.0 is on main in OpenSpineConsortium/symphony-extension;
  the kit's release run numbers it on the push (see the Releases page).
  The store listing is not submitted yet: the owner does that by hand
  once, then the secrets make every later merge upload itself.
- The eight merged adoptions are not reverted (the owner's list, 1).
- The App's webhook is registered inactive; the privacy statement says
  what the server does from the day it is turned on.
- The claude/magical-shannon-ak167f branch is level with main; this
  checkpoint is its next commit.

## Remaining tasks

1. The owner's list above.
2. Live test of the Migrate chain on a repository of the owner's: the
   permissions page preselected, the Setup App's install page opening
   by itself from the form, the form arriving with the repository filled
   in, one pull request; and the settings-page banner when SymphonyBoard
   was installed already. Nothing in a cloud session can press it.
3. coordbench's own texts still say sdlc-protocol; a pull request there
   when convenient. The marketplace skills /symphony:new and
   /symphony:migrate (symphony-marketplace#2).
4. Carried: actions/create-github-app-token@v1 to v2; existing-repo.md
   should say the front door's existing mode replaces the by-hand way;
   crowd mode on a real organization copy; the 42 gradeable flash
   pairs; judge.py against a real model; the marketplace ruleset's
   unattributed-changes field; coordbench#6; the App's stage 2 (the
   webhook server) only if two minutes still reads as slow.

## Decisions

Stated by the owner in conversation, this session and earlier:

- Prefer GitHub's native, free features. No API billing: Claude in CI
  runs on a subscription OAuth token, never with ANTHROPIC_API_KEY.
- A protocol change is made in the library repository and reaches every
  consumer by its sync on one push.
- coordbench measures what CooperBench measures, differing only with a
  stated reason (PARITY.md).
- Crowdsourcing: each contributor works under their own Claude account,
  and the project never holds anyone's credential.
- Field metrics: no hosted server; on by default, said plainly, one
  switch off; aggregates only, a repository only as a salted hash; the
  failure-mode judge runs client side.
- "Free to use" is not "free access to the source": the template stays
  private and is adopted through the public front door, which holds no
  file of it.
- The collector's salt is derived from the App's private key, with
  SDLC_METRICS_SALT as an optional override.
- The metrics workflow runs at 03:43 UTC, before the collector's 04:17
  read, and on a merge that changes the switch; never replaces a branch
  metrics that holds other files; never runs in a fork.
- Mode existing takes the protocol page from the library's
  spec/PROTOCOL.md at the vendored commit; the App's tokens are minted
  account-first.
- The session merges the project's pull requests once their check is
  green; the rulesets require no review.
- The files an adoption brings are offered under the MIT License, in
  the front door's LICENSE; the adoption copies no LICENSE.
- The repository settings are applied by the setup-only App, installed
  for the one run; the main App never holds Administration.
- The owner's own several Claude accounts may be coordinated from one
  orchestrator of theirs; it does not change the rule for contributors'
  credentials.
- Installing the App is the request: the Setup URL lands on the form
  with the installation filled in, one press of Create is the request,
  the run reads the kind from the tree and shares aggregates unless a
  box says otherwise; the sweep is the fallback; a webhook, if ever
  hosted, dispatches sweep.yml for one installation and adds no logic.
- A repository given by ids is never named on the public side; a
  guessed installation number gets one answer whatever is wrong.
- The product is Symphony; the rename is two tiers, both merged on
  2026-10-11. What stays: the package sdlc_protocol, the SDLC_*
  variables and secrets, the VENDORED record's first token
  sdlc-protocol, the plugin folder plugins/sdlc, the schema ids, the
  check run name sdlc/protocol, and the readers of the old names.
- The Apps are SymphonyBoard and Symphony Setup, slugs symphonyboard and
  symphony-setup, with no OpenSpine in the name; the main App's homepage
  is https://openspineconsortium.com/symphony/.
- One press adopts one repository: the repository the form names, else
  the newest the installation reaches with no adoption yet (LIMIT 1);
  the person presses Create again for the next.
- The extension's Migrate button and the post-Create banner carry the
  repository through GitHub's own install link (target_id,
  suggested_target_id, repository_ids[] and state=OWNER/NAME); the
  form's Repository field has the id state so it arrives filled in; the
  extension's note symphony.migrate chains the Setup App's install after
  SymphonyBoard's and bridges an already-installed Board from its
  settings page.
- Both Apps are required on the form's two paths; the sweep adopts
  without the Setup App.
- The two GitHub Apps have one privacy statement, PRIVACY.md in
  symphony-start, rendered by the site at /symphony/apps-privacy.html
  and linked from the Apps' descriptions; the extension keeps its own.
- The Chrome Web Store release kit is its own private repository,
  OpenSpineConsortium/chrome-store-release-kit, called as a reusable
  workflow at main; any future extension of the owner's calls it.
- An adopted repository carries the GitHub topic symphony, set by the
  adoption run (Setup App) and by setup-repo.sh; the extension reads it
  from the page and shows Ready for Symphony instead of Migrate.
- The main App's logo is GitHub's mark adapted to the icon's colours
  with the orange baton, the Setup App's a gear, the ring and tile
  unchanged; the owner accepted the risk under GitHub's logo policy.

## Constraints

- The cloud environment blocks cooperbench.com, arxiv.org, cursor.com,
  docs.github.com, dagshub.com and openspineconsortium.com (DNS or the
  proxy's CONNECT); GitHub's documentation is read from the github/docs
  repository's content files on raw.githubusercontent.com, and
  github.com's HTML pages answer 403 to curl.
- GitHub's install link takes target_id (what GitHub's own buttons
  send), suggested_target_id and repository_ids[] (the OAuth-to-App
  migration guide; up to 100; omitted means all repositories) and state,
  which GitHub returns on the Setup URL after an install; an issue form
  fills the field whose id matches a query parameter.
- The cloud environment withholds CLAUDE_CODE_OAUTH_TOKEN; coordbench
  reads COORDBENCH_CLAUDE_TOKEN, each account its own.
- gh issue and gh pr are refused in cloud sessions; the proxy also
  refuses the Actions variables and secrets paths, renaming a
  repository, creating one in the organization, deleting a branch and
  the organization's installations endpoints; the GitHub tools cannot
  create a repository in the organization either (403). Both are the
  owner's. The GitHub tools take the session's scoped repository names,
  the old ones (sdlc-*), and gh api on a renamed repository redirects to
  a repositories/{id} path the proxy refuses; git pushes to the old
  names redirect fine.
- Parallel Bash calls in a cloud session share one working directory
  and a cd in one call lands another's commands elsewhere or resets the
  shell's directory: use absolute paths or git -C in every call.
- A reusable workflow in a private repository needs Actions access
  "Accessible from repositories in the organization" on that
  repository; a run that failed at workflow resolution cannot be re-run
  (403), a new push is needed.
- sdlc-template is internal to its enterprise; symphony-start and its
  Actions logs are public.
- The auto-mode permission classifier can refuse an outward write; the
  GitHub tools' pull request, merge and issue calls were allowed.
- A cloud session's tools reach only its own account's sessions.
- The container has 4 CPUs, 15 GB of memory and about 30 GB of disk; a
  background command stops after two hours; a restart of the session's
  worker keeps /home/user, the scratchpad and the finished agents'
  outputs but kills running agents and workflows.
- A GitHub App's installation on an organization has one repository
  list; the main App stays on "All repositories" there.
- GitHub hosts no always-on compute a webhook can reach; a newly added
  schedule may wait many hours for its first run.
- The sweep never touches the organization's own repositories; a
  heredoc on a command also fed by a pipe takes the pipe's place as
  stdin.
- github.com draws the repository header with Primer React (read
  logged out on 2026-10-11): the action list is
  ul[data-testid="repo-header-actions"], the Star button
  a[data-testid="star-button"], the owner's id and login in the
  octolytics-dimension-user_id and user_login meta tags, the
  repository's id and owner/name in octolytics-dimension-repository_id
  and repository_nwo; #repository-container-header and
  ul.pagehead-actions are gone. github.com/new needs a login to read.
- The vendored record's first line, sdlc-protocol <version> <commit>,
  is rendered by vendoring.py in every copy: renaming it is a release
  that re-vendors every consumer, so the rename leaves it.
- actions/upload-artifact v4 skips dotted folders unless
  include-hidden-files is true.
