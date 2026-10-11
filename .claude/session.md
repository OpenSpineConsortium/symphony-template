# Session checkpoint

Written 2026-10-11 in the main account's session, for the next session
on any account. Overnight, on the owner's word ("drive this to
completion"), this session renamed the product to Symphony in two tiers,
built Symphony for Chrome with its store package and a promo film, and
put a Symphony page on openspineconsortium.com. What only the owner can
do is listed first, in the order to do it.

## The owner's morning, in order

1. Rename the two GitHub Apps, in each App's settings page: "OpenSpine
   SDLC" to "SymphonyBoard" (slug symphonyboard) and "OpenSpine SDLC
   Setup" to "Symphony Setup" (slug symphony-setup). The owner wants no
   OpenSpine in the name; GitHub refuses an App name that matches an
   account (Symphony, Symph, Symph0ny) or another App (Symphony Dev),
   so the owner chose SymphonyBoard on 2026-10-11. Set the main App's
   description to "Symphony: pull-request-gated Claude Code agents for
   your repository. Install it, press Create on the form, merge the pull
   request." and both Apps' homepage URL to
   https://openspineconsortium.com/symphony/, as the manifests in
   symphony-app's flip say. Keep the Setup URL of both Apps on the
   form, with "Redirect on update" ticked.
2. Rename the five repositories (Settings, General): sdlc-protocol to
   symphony-protocol, sdlc-marketplace to symphony-marketplace,
   sdlc-template to symphony-template, sdlc-app to symphony-app,
   sdlc-start to symphony-start. GitHub redirects the old names, so
   nothing merged breaks; the flips below only resolve after this.
3. Create the empty private repository OpenSpineConsortium/symphony-extension
   (the session's GitHub tools may not create one: 403), then push the
   extension into it. The source is in this session's container at
   /home/user/symphony-extension (four commits on main) and was sent to
   the owner as symphony-extension.bundle (the history; `git clone
   symphony-extension.bundle`, then `git remote set-url origin ...` and
   push) and as symphony-extension-source.tar.gz (the files alone).
4. Merge the six flip pull requests, in this order, re-running a red
   check first (they are red only because the new names did not exist):
   OpenSpineConsortium/sdlc-protocol#4, sdlc-marketplace#4,
   sdlc-template#34, sdlc-app#6, sdlc-start#22, then the site's
   openspineconsortium.github.io#7.
5. Submit Symphony for Chrome: docs/store/SUBMISSION.md in the extension
   repository, step by step, with the zip symphony-1.0.0-chrome.zip
   (sent to the owner; `npm ci && npm run zip` rebuilds it) and the texts
   of docs/store/LISTING.md. Do the hand test in
   docs/store/TEST_BEFORE_UPLOAD.md first: the extension's buttons were
   checked against a logged-out read of a live repository page, but
   github.com/new needs a login, so the Create button is unverified on
   the live page. The extension links the new names (the slugs
   symphonyboard and symphony-setup, the repository symphony-start), so
   steps 1 and 2 come before the upload.
6. Optional: update the five repositories' descriptions on GitHub
   (they still say OpenSpine SDLC); press Run workflow on sdlc-start's
   Sweep once to see the sweep's dispatch path, since its schedule has
   not fired by itself in seven hours.

## Completed work

- Tier one of the rename, merged: the product is Symphony in every text
  of the five repositories (sdlc-marketplace#3, sdlc-template#33,
  sdlc-protocol#3, sdlc-app#5, sdlc-start#21). What a merge could carry
  changed with it: the form's title "Adopt Symphony", the adoption
  branch symphony/adopt (sdlc/adopt still read), the switches
  .github/symphony-metrics and .github/symphony-adopt (the old names
  still read), the refusal issue's title, the plugin symphony with
  /symphony:board and /symphony:claim, the App manifests' names.
- Tier two of the rename, prepared and reviewed, unmerged: one pull
  request per repository on the branch claude/symphony-flip flips the
  repository names, the App slugs (and the bot login), the marketplace's
  name (symphony@symphony-marketplace) and the sync branch
  symphony-protocol/sync. A reviewer per repository read every hunk;
  the findings that stood were folded in (the protocol's downstream job
  names the library's clone with SDLC_PROTOCOL so a consumer never
  skips the comparison; the marketplace's tag name and vendor README;
  the App's "still open" bullet; the front door reads the bot's login
  from the token step's app-slug output). Every local check green.
- Symphony for Chrome (/home/user/symphony-extension, WXT 0.21,
  TypeScript, 51 tests): "Create Symphony repository" beside GitHub's
  own button on github.com/new, the banner "Finish setting up Symphony"
  on the repository just made (a fifteen-minute note in storage.local,
  the one permission), "Migrate to Symphony" in every repository's
  header, a popup with three links. github.com only, no request to
  anyone, no remote code; the hygiene test holds the source and the
  built package to that. The header is found by the Primer React test
  ids github.com serves today, then by the older classic markup. The
  store package: docs/store (LISTING.md, SUBMISSION.md,
  TEST_BEFORE_UPLOAD.md), icons, a promo tile, two screenshots,
  PRIVACY.md version 1, MIT LICENSE, a CI workflow with no secret.
- The promo film (promo/ in the extension repository): a Canvas page
  where every frame is a function of time, rendered frame by frame in
  headless Chromium and encoded with ffmpeg; 1920x1080, 30 fps, 23.6 s,
  H.264 and VP9. The person at twelve o'clock sends pulses to the GitHub
  mark; six Claude marks come out from behind the person and go
  counter-clockwise round the circle to the slots around the top; all
  seven draw the same arrow and pulse together; fade out; "Symphony"
  fades in; "Powered by Claude" types itself with the mark inline.
- The site (openspineconsortium.github.io#6, merged): /symphony/ in the
  Beethoven home's style with the film, the three presses and three
  cards; /symphony/privacy.html rendered from the extension's
  PRIVACY.md (TEXTS: symphony-privacy, SYMPHONY_REPO); a Symphony tab,
  footer column and sitemap entry; the home page's closing section; one
  stamp on every page. The page links the current slugs and names; #7
  flips them after the rename.

## Current state

- Merged on main: the five tier-one pull requests and the site's #6.
  Open, waiting on the owner: sdlc-protocol#4 (check green, downstream
  jobs red by the missing names), sdlc-marketplace#4, sdlc-template#34,
  sdlc-app#6 (checks red by the missing names), sdlc-start#22 (green),
  openspineconsortium.github.io#7.
- The extension is one commit on main in this container only, not on
  GitHub; the owner received the zip, the source archive and the mp4.
  The site's privacy page and product page are deployed by GitHub Pages
  from master; the session's proxy cannot open openspineconsortium.com,
  so they were checked only in the local build and a local render.
- The sweep's schedule on sdlc-start has had no run since the workflow
  landed (seven hours); its dispatch path is still unproven live.
- The claude/magical-shannon-ak167f branches are level with main in
  every repository; this checkpoint is their next commit.

## Remaining tasks

1. The owner's morning list above; then delete the claude/symphony-flip
   branches once merged, and the site's.
2. After the flips: the memory fact the-front-door-is-one-press.md and
   docs/start pages read fine; coordbench's own texts still say
   sdlc-protocol (not renamed; its downstream job passes), a pull
   request there when convenient.
3. The marketplace skills /symphony:new and /symphony:migrate
   (sdlc-marketplace#2), which do everything but the install click.
4. Carried: actions/create-github-app-token@v1 to v2; existing-repo.md
   should say the front door's existing mode replaces the by-hand way;
   crowd mode on a real organization copy; the 42 gradeable flash
   pairs; judge.py against a real model; the marketplace ruleset's
   unattributed-changes field; coordbench#6; sdlc-app stage 2 only if
   two minutes still reads as slow.

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
- The product is Symphony. The rename is in two tiers: tier one, merged,
  renames the product in prose and the identifiers a merge can carry
  (the form's title, the branch symphony/adopt, the switches
  .github/symphony-metrics and .github/symphony-adopt, the plugin
  symphony); tier two, five pull requests kept open until the owner
  renames the repositories and the Apps, flips the repository names,
  the App slugs, the marketplace's name and the sync branch. What stays:
  the package sdlc_protocol, the SDLC_* variables and secrets, the
  VENDORED record's first token sdlc-protocol, the plugin folder
  plugins/sdlc, the schema ids, the check run name sdlc/protocol, and
  the readers of the old names a repository adopted before carries.
- Symphony for Chrome links the new names, since it ships after the
  rename; the site links the current names, with a flip pull request,
  since it is live now.

## Constraints

- The cloud environment blocks cooperbench.com, arxiv.org, cursor.com,
  docs.github.com and openspineconsortium.com (the proxy refuses the
  CONNECT); GitHub's docs come from raw.githubusercontent.com.
- The cloud environment withholds CLAUDE_CODE_OAUTH_TOKEN; coordbench
  reads COORDBENCH_CLAUDE_TOKEN, each account its own.
- gh issue and gh pr are refused in cloud sessions; the proxy also
  refuses the Actions variables and secrets paths, renaming a
  repository, creating one in the organization, deleting a branch and
  the organization's installations endpoints; the GitHub tools cannot
  create a repository in the organization either (403). Both are the
  owner's.
- sdlc-template is internal to its enterprise; sdlc-start and its
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
  octolytics-dimension-user_id and user_login meta tags;
  #repository-container-header and ul.pagehead-actions are gone.
  github.com/new needs a login to read.
- The vendored record's first line, sdlc-protocol <version> <commit>,
  is rendered by vendoring.py in every copy: renaming it is a release
  that re-vendors every consumer, so the rename leaves it.
