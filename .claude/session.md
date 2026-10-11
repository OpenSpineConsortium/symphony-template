# Session checkpoint

Written 2026-10-11, night, in the main account's session, for the next
session on any account. The day's earlier work (the rename to Symphony,
the release kit, one repository per press, Migrate carrying its
repository, both Apps on the form, the Apps' privacy statement, the
topic symphony, the chained installs, the form's defaults) is merged;
the night's work was the site's new home page with Beethoven as its own
tab, the way in from Claude Code (/symphony:new and
docs/start/claude-code.md), and the relaxation of Beethoven's
one-installation rule (three pull requests, left for the owner to
merge). What only the owner can do is listed first.

## The owner's list, in order

1. Revert the eight adoptions of 2026-10-11: symphony-start issue #23
   (installation 170355452, "Merge the pull request for me" ticked, no
   repository named) adopted and merged Symphony into eight repositories
   of GregorySchwing's before run 38165412998 was cancelled. The merged
   pull requests are listed at
   https://github.com/pulls?q=is%3Apr+author%3Aapp%2Fsymphonyboard+is%3Amerged;
   the script undo-symphony.sh given in chat reverts each (ruleset,
   revert, opt-out file, labels, branches, issues), signed in as
   GregorySchwing; this session has no access to that account's
   repositories. Then narrow SymphonyBoard's installation on
   GregorySchwing to "Only select repositories".
2. Upload the Apps' logos and set their descriptions, if not done: on
   each App's settings page
   (https://github.com/organizations/OpenSpineConsortium/settings/apps/symphonyboard
   and .../symphony-setup), Display information, Logo: the PNGs the site
   hosts, https://openspineconsortium.com/symphony/symphonyboard-logo.png
   and https://openspineconsortium.com/symphony/symphony-setup-logo.png;
   the descriptions with the Markdown links given in chat, each linking
   https://openspineconsortium.com/symphony/apps-privacy.html.
3. Submit Symphony for Chrome (docs/store/SUBMISSION.md in
   OpenSpineConsortium/symphony-extension): the zip is the kit's release
   for the latest main (1.4.1.17 at this writing,
   https://github.com/OpenSpineConsortium/symphony-extension/releases/latest/download/symphony-chrome.zip);
   do the hand test in docs/store/TEST_BEFORE_UPLOAD.md first. Then set
   the five CWS_ secrets and CWS_ON_PUSH=upload on the extension
   repository, and every merge to main uploads itself.
4. Merge the Beethoven relaxation, after reading docs/TEXTS_V13_V14.md
   in beethoven-extension (five questions for counsel): first
   OpenSpineConsortium/beethoven-access#5, whose merge deploys both
   Worker names; then openspineconsortium.github.io#10, so the pages and
   the terms (agreement 13, privacy statement 14) say what the service
   does; beethoven-extension#10 at any time. Then the 20.0.0 store
   upload as docs/store/SUBMISSION.md says, with the hand test's step 18
   (a second Chrome profile approved, one notice e-mail) and new
   screenshots. The Beethoven repositories are the maintainer's to
   merge, so this session left them open.
5. Delete the stray branch claude/new-skill on symphony-template (a cd
   lost to the shell's reset put a commit on the wrong checkout; the
   proxy refuses deleting a branch): https://github.com/OpenSpineConsortium/symphony-template/branches.
6. Add the topic symphony by hand, under About, on the repositories
   adopted before the topic existed (GOMC, the sweep's adoptions, the
   test repositories), so the extension shows Ready for Symphony there.
7. Optional: update the repositories' descriptions on GitHub; press Run
   workflow on symphony-start's Sweep once; uninstall the Setup App from
   sdlc-setup-test.

## Completed work

- The rename, both tiers, merged everywhere. The Apps are SymphonyBoard
  (slug symphonyboard) and Symphony Setup (slug symphony-setup).
- The Chrome Web Store release kit as its own private repository,
  OpenSpineConsortium/chrome-store-release-kit, called as a reusable
  workflow at main; Symphony for Chrome releases through it on each push
  to main (1.0.0.9 to 1.4.1.17).
- The front door (symphony-start #24, #26, #28, #30): one press adopts
  one repository; the form's Repository field has the id state; both
  Apps are required on the form's two paths and the sweep adopts without
  the Setup App; the adoption sets the topic symphony; the installs are
  chained on GitHub's side by the Setup URLs; Kind and Merge are
  preselected dropdowns (Auto; merge for me) and the kinds say what they
  are. The extension 1.1.0 to 1.4.1: Migrate carries its repository
  through GitHub's install link, the note symphony.migrate chains the
  Setup App's install (picker and permissions page), Ready for Symphony
  from the topic, the popup's links through the browser's new-tab call.
- The two GitHub Apps' privacy statement, PRIVACY.md in symphony-start,
  rendered at /symphony/apps-privacy.html; the logos on the site.
- The site (openspineconsortium.github.io master 319e2ce and after): the
  root is the lab page, in the Beethoven page's style, with the message
  (people and AI coding one repository together, whoever is driving),
  the experiment (two features of one code base at the same time,
  CooperBench's "curse of coordination" moved into a real coding
  environment, coordbench measuring it), the three aims, how the lab
  works (one click and a few sign-ins) and the three products; two CSS
  animated figures, the board with main and the git graph of the two
  branches, drawn by tools/home_figures.py in a wide and a phone layout
  with their keyframes written between markers in assets/css/lab.css.
  Beethoven keeps its page and its flow animation at /beethoven/, as the
  tab between Symphony and Onboarding, with its children; the header
  opens its drawer below 900px, where seven tabs no longer fit in one
  row; the sitemap carries / again. Checked with Chromium screenshots
  at 1366, 820 and 390 pixels.
- The way in from Claude Code: the marketplace skill /symphony:new
  (symphony-marketplace#5, plugin 0.1.2) and the template's
  docs/start/claude-code.md (#45): gh makes the repository with a first
  commit, one install link preselected for the repository installs both
  Apps and lands on the form with the repository filled in, the run
  merges the pull request (the sweep as the fallback, without settings),
  /install-github-app puts the Claude GitHub App on, and claude --cloud
  opens a cloud session from the clone; a Project on claude.ai runs
  many threads on the repository, belongs to one account and cannot be
  shared, so another account joins with its own Project once it has
  Write. The documented facts behind it (claude --cloud, the
  claude.ai/code pre-fill link, Projects' limits, the routine fire
  endpoint as the only API) are in the constraints.
- Beethoven's one-installation rule relaxed, the owner's decision of
  2026-10-11, in three pull requests, all open: beethoven-access#5
  (every installation of an approved account approved at its first
  check; the seat record lists up to ten, oldest dropped and unbound; a
  notice e-mail at most once a day per account with one Withdraw link;
  other_installation never answered; an old Move link answers 410 out of
  date; other_account and update_required unchanged; 105 tests, 61
  vectors), beethoven-extension#10 (Beethoven 20.0.0, agreement version
  13 section 3(e) 'Your installations' and 10(a)/(d), privacy statement
  version 14, TERMS_VERSION 13; the store texts, the guides, the
  report's dated note and the drafting note for counsel; 763 tests) and
  openspineconsortium.github.io#10 (the four Beethoven pages, the terms
  and privacy at 13 and 14, and the admin page without its
  one-installation switch, whose route never existed, showing
  installations counted). Each branch had an adversarial review, whose
  findings were fixed before the pull request.

## Current state

- Merged on main: symphony-template #44, #45 and #46, symphony-marketplace
  #5, symphony-start #31; the site's master at the lab page, with the
  old home's anchors sent on (69075a0).
- Open, for the owner: beethoven-access#5 (CI green),
  beethoven-extension#10 (CI running at this writing),
  openspineconsortium.github.io#10 (built at license 13 and privacy 14;
  it conflicts on the stamps if master is rebuilt first, and is then
  rebuilt from master rather than resolved by hand). The site's master,
  built against the extension's main, still shows agreement 12 and
  privacy 13. Issue #18 (settings as code) is closed as not planned,
  recorded in docs/project.md (#46).
- The eight merged adoptions are not reverted (the owner's list, 1).
- The claude/magical-shannon-ak167f branch is level with main; this
  checkpoint is its next commit.

## Remaining tasks

1. The owner's list above.
2. After beethoven-access#5 merges: measure a second installation
   against the deployed Worker (approved with no reason, one notice
   e-mail with only a Withdraw link) and confirm /health on both names;
   until then the new rule is not yet measured in production.
3. Live test of /symphony:new on the owner's machine: gh repo create,
   the one link, the merge within two minutes, the Claude GitHub App,
   claude --cloud, then a Project on the repository with two threads at
   once; the sweep's path as the fallback. Nothing in a cloud session
   can run gh repo create or press the links.
4. Live test of the Migrate chain on a repository of the owner's (the
   permissions page preselected, the Setup App's page by itself, the
   form with the repository filled in, one pull request).
5. coordbench's own texts still say sdlc-protocol; a pull request there
   when convenient. The marketplace skill /symphony:migrate
   (symphony-marketplace#2) is still open.
6. Carried: actions/create-github-app-token@v1 to v2; existing-repo.md
   should say the front door's existing mode replaces the by-hand way;
   crowd mode on a real organization copy; the 42 gradeable flash
   pairs; judge.py against a real model; the marketplace ruleset's
   unattributed-changes field; coordbench#6; the App's stage 2 (the
   webhook server) only if two minutes still reads as slow.

## Decisions

The durable decisions are CLAUDE.md's block, which every session loads,
word for word; those settled on 2026-10-11, in brief:

- The Apps are SymphonyBoard and Symphony Setup, slugs symphonyboard and
  symphony-setup.
- One press adopts one repository: the one the form names, else the
  newest with no adoption yet (resolve.py LIMIT 1).
- Migrate carries its repository through GitHub's install link
  (target_id, suggested_target_id, repository_ids[], state); the form's
  Repository field has the id state.
- Both Apps are required on the form's two paths; the sweep adopts
  without the Setup App.
- The two Apps' privacy statement is symphony-start's PRIVACY.md, at
  /symphony/apps-privacy.html.
- The Chrome Web Store release kit is
  OpenSpineConsortium/chrome-store-release-kit, a reusable workflow at
  main.
- An adopted repository carries the topic symphony, and the extension
  shows Ready for Symphony there.
- The installs are chained by the Apps' Setup URLs: SymphonyBoard to
  Symphony Setup, Symphony Setup to the form.
- The form's Kind and Merge are preselected dropdowns (Auto; merge for
  me); the kinds say what they are.
- The site's root is the lab page; Beethoven is its own tab at
  /beethoven/.
- /symphony:new and docs/start/claude-code.md make a project from Claude
  Code; a Project is made on claude.ai alone.
- A Project holds one thing, the blank Symphony repository; after its
  first push people and sessions share the repository through the same
  upstream, each with their own account and Project.
- Beethoven 20.0.0: every installation of the student's own is approved;
  one installation still serves one account; agreement 13, privacy
  statement 14; the Beethoven repositories' pull requests are the
  maintainer's to merge.
- No settings-as-code app (issue #18, closed; docs/project.md, Out of
  scope).

## Constraints

The constraints are CLAUDE.md's block, word for word; those learned on
2026-10-11, in brief:

- docs.github.com, dagshub.com and openspineconsortium.com are
  unreachable; GitHub's documentation comes from github/docs on
  raw.githubusercontent.com, CooperBench's from cooperbench/website.
- A cd inside a Bash call can be lost to the shell's working-directory
  reset: every git command takes -C and an absolute path. The proxy
  refuses git push --delete, user/installations and repositories/{id}
  paths.
- The site's build reads the sibling Beethoven checkouts as checked out:
  build master against a worktree of the extension's main
  (BEETHOVEN_REPO) while a branch is checked out.
- Claude Code's documentation: claude --cloud starts a session from the
  clone's remote branch, bundling the clone when the Claude GitHub App
  is not on the repository; the claude.ai/code pre-fill link submits
  nothing; a Project is one user's, Pro and Max only, with no API or
  CLI; a routine's fire endpoint is the only HTTP way to start a cloud
  session.
- Chromium and Node's Playwright are installed (/opt/pw-browsers,
  /opt/node-tools), so a page is checked by screenshot.
