# Session checkpoint

Written 2026-10-12 at the end of the main account's session
session_01AMrLKnvPcvNBSchUXZbDDX, for the next session on any account.
Today: one way of working for every worker, with the coordinator in the
repository (symphony-protocol 0.4.0), and the field metrics' economics,
what the work cost and whether working in parallel pays, live in four
repositories. Nothing of this session is open.

## Completed work

- Earlier today, this session: the released-claim pair landed
  (symphony-template#48, symphony-protocol#5, v0.3.0, then v0.3.1), the
  routines read their prompt from the repository, protocol.yml brings each
  release to a copy of the template, the push guard and the shipped
  rulesets are held by code, the App's sync pull request lands by
  auto-merge, and the library's release workflow tags each new version by
  itself. The previous checkpoint's owner item 2 is done.
- One way of working (symphony-protocol#9, released as 0.4.0 and tagged
  v0.4.0; symphony-template#56). Whatever claims an issue is a worker,
  labelled worker:<name>: a person's sessions by the person's GitHub
  login (or SYMPHONY_WORKER), a routine on any account, or a worker in
  GitHub Actions. A routine or a worker in Actions is one file under
  .github/symphony/workers/, added by the "Add a worker" issue form
  (add-worker.yml opens the pull request) or by hand. workers.yml runs the
  workers in Actions in parallel, the clerk dealing the open work by area
  before any Claude session starts. The coordinator is code in the board's
  run (idle claims released with a comment that keeps their plan,
  overlapping work told once) and Claude in coordinator.yml (epics
  planned, blocked tasks settled, finished epics integrated, a weekly
  tidy). Team mode, claude-lead.yml, claude-worker.yml and their three
  variables are gone; account:, agent: and "- Account:" are still read.
  The sync landed in coordbench (#9), symphony-marketplace (#8) and
  symphony-app (#10).
- The economics (symphony-template#57). Each session puts a
  Symphony-Usage trailer on its commits (a PreToolUse hook reads the
  transcript before git commit; the session-start hook installs the
  commit-msg hook); each Claude run in Actions (workers.yml,
  coordinator.yml, claude.yml) uploads a symphony-usage-* artifact.
  metrics.yml reads them (actions: read, at most 200 new a run, carried in
  the Actions cache) and METRICS.json gains economics (tokens by kind and
  family, the estimated price at API list prices as of 2026-10-06,
  Claude's seconds, per merge) and coordination (alone against parallel,
  seven ratios over 1 where parallel did better). 524 tests, also on
  python3.12.
- The privacy statement version 3 (symphony-start#35), its page
  (openspineconsortium.github.io#12, merged on the owner's word and
  deployed) and the collector keeping the new keys (symphony-app#11), in
  that order.

## Current state

- Every repository named above is at its default branch; this branch,
  claude/upbeat-sagan-6th2hu, is level with main and this checkpoint is
  its next commit.
- The sync left its branch symphony-protocol/sync behind in coordbench
  and symphony-marketplace, which do not delete merged branches; harmless.
- Usage is recorded only by sessions started after #57 merged, and only
  in repositories that have its files. Copies of the template made before
  today get only the library, by protocol.yml's weekly pull request: the
  board's releases and the worker labels, but not workers.yml,
  coordinator.yml, the form or the usage recording.
- Not yet measured: a real run of workers.yml, coordinator.yml and
  add-worker.yml, the usage hook in a real session, an artifact read by a
  real metrics run, and the first economics line the collector keeps
  (04:17 UTC on 2026-10-13 at the earliest).

## Remaining tasks

The owner's, in order (carried from the previous checkpoint, item 2 done):

1. The plan's first decisions (the plan, "Your first decisions"), each
   as a Decision: line; nothing runs unattended before them and before
   the safety foundation's drill passes.
2. Revert the eight adoptions of 2026-10-11 (undo-symphony.sh, signed in
   as GregorySchwing), then narrow SymphonyBoard's installation there to
   "Only select repositories".
3. The Apps' logos and descriptions, if not done.
4. Submit Symphony for Chrome, then the five CWS_ secrets and
   CWS_ON_PUSH=upload.
5. Beethoven 20.0.0 to the store: the hand test's step 18, screenshots,
   the upload.
6. Delete the stray branch claude/new-skill on symphony-template, and if
   wanted the two leftover symphony-protocol/sync branches.
7. Add the topic symphony by hand on the repositories adopted before it.

For a session:

1. A live test of the new workflows on OpenSpineConsortium/sdlc-template-test:
   bring in the new files, add a worker with the form, let workers.yml
   run it once, label an issue epic, and read the artifact and the next
   METRICS.json.
2. Bring the marketplace plugin's claim skill to worker:<name> (it may
   still write account: labels); a suggested task for it could not be
   queued.
3. A way for an existing copy to take the new files, since protocol.yml
   brings the library alone.
4. Carried: a live test of /symphony:new and of the Migrate chain;
   coordbench's texts still say sdlc-protocol; symphony-marketplace#2;
   actions/create-github-app-token@v1 to v2; crowd mode on a real
   organization copy; the 42 gradeable flash pairs; judge.py against a
   real model; coordbench#6; filing the plan's issues once the owner has
   decided.

## Decisions

The durable decisions are CLAUDE.md's block, word for word; those
settled on 2026-10-12 in this session, in brief:

- Every claimant is a worker, worker:<name>; routines and workers in
  Actions are files under .github/symphony/workers/; team mode is gone.
- The coordinator is the board's run plus Claude in coordinator.yml; a
  coordinator routine only where the repository holds no Claude token.
- What the work costs is recorded as session trailers and Actions
  artifacts and written as economics and coordination, ratios over 1
  where parallel did better; privacy statement version 3 lists it.

## Constraints

The constraints are CLAUDE.md's block, word for word; those learned on
2026-10-12 in this session, in brief:

- urllib sends a redirected request every header of the first,
  Authorization included, so a GitHub download is asked without
  following the redirect and fetched with no token.
- A pushed branch in a single-branch clone has no remote-tracking ref
  until it is added to remote.origin.fetch.
- The site's build needs beethoven-extension, beethoven-vscode and
  symphony-extension checked out beside it; the site has no CI.
