# Session checkpoint

Written 2026-10-12 in the main account's session, for the next session
on any account. Today: Beethoven's relaxation merged and deployed; the
field metrics' breakdown by work setting shipped in four repositories;
and a plan for the owner's accounts working on their own, with
Beethoven brought onto Symphony, written and handed to the owner. What
only the owner can do is listed first.

## The owner's list, in order

1. The plan's first decisions (the plan, "Your first decisions"): the
   credential model (one Claude Code sign-in directory per account and
   repository, superseding CLAUDE.md's "each with one account's token"),
   the scope of Beethoven's rules against Symphony's, the workers' GitHub
   identity (a non-admin machine account), the conductor's private home
   and dedicated host, who merges where, accounts and caps, and the
   private dogfood with SDLC_METRICS=off. Say each as a Decision: line.
   Nothing runs unattended before them and before the safety
   foundation's drill passes.
2. Land the released-claim pair, another session's drafts
   (session_01AMrLKnvPcvNBSchUXZbDDX): symphony-template#48 takes main in
   by a merge (it is behind and overlaps #49 in tools/metrics.py and
   docs/setup/metrics.md), merge #48, re-run symphony-protocol#5's
   downstream jobs, merge #5 with a merge commit, tag v0.3.0.
3. Revert the eight adoptions of 2026-10-11 (symphony-start issue #23
   merged Symphony into eight repositories of GregorySchwing's): the
   script undo-symphony.sh given in chat on 2026-10-11, signed in as
   GregorySchwing; then narrow SymphonyBoard's installation there to
   "Only select repositories".
4. The Apps' logos and descriptions, if not done: Display information on
   each App's settings page, the PNGs at
   https://openspineconsortium.com/symphony/symphonyboard-logo.png and
   .../symphony-setup-logo.png, the descriptions linking
   https://openspineconsortium.com/symphony/apps-privacy.html.
5. Submit Symphony for Chrome (symphony-extension docs/store/SUBMISSION.md,
   after the hand test), then set the five CWS_ secrets and
   CWS_ON_PUSH=upload.
6. Beethoven 20.0.0 to the store: the hand test's step 18 (a second
   Chrome profile approved at its first check, exactly one notice
   e-mail), new screenshots, then the upload; the site already shows
   agreement 13 and privacy statement 14.
7. Delete the stray branch claude/new-skill on symphony-template.
8. Add the topic symphony by hand on the repositories adopted before the
   topic existed (GOMC, the sweep's adoptions, the test repositories).

## Completed work

- Beethoven's one-installation rule relaxed and live, merged on the
  owner's word on 2026-10-12: beethoven-access#5 (deployed 23:38 UTC on
  2026-10-11, both Worker names answering /health), beethoven-extension#10
  (Beethoven 20.0.0, CI green on main) and openspineconsortium.github.io#10
  (deployed). Not yet measured: a second installation against the
  deployed service, which is the store hand test's step 18.
- The field metrics break failures out by work setting, so one person's
  several parallel sessions are never pooled with several people's work:
  symphony-start#34 (the Apps' privacy statement version 2, dated
  2026-10-12, which lists every new count and what the workflow reads),
  openspineconsortium.github.io#11 (its page, deployed), symphony-app#7
  (the collector keeps the new keys) and symphony-template#49 (the counts:
  parallel, by_setting over eight settings with exposure, pairs by
  relation; JUDGE.json by setting; 421 tests). Designed by a panel of
  three, built in parallel, reviewed adversarially twice and verified;
  every definition is pinned by a test a one-rule mutation turns red.
  Live on OpenSpineConsortium/sdlc-template-test: 33 calls, people 1,
  sessions 1, five solo pull requests, while contributors says 2.
- The plan for the owner's accounts working unattended and Beethoven on
  Symphony, researched by five readers, written, checked by two critics,
  revised and checked again; handed to the owner as a file (PLAN.md,
  about 14,000 words), committed nowhere, since it names security
  weak points and its home is the private repository the plan proposes.
  In brief: a conductor of the owner's, kept in a private repository and
  run on a dedicated host, deals each account a different issue from one
  GitHub snapshot and runs headless Claude Code per account in a sandbox
  of its own; workers push as a non-admin machine account; only rules
  GitHub enforces gate merges; the conductor lands by itself only in a
  private dogfood; workers open issues only as proposed; beethoven-qa's
  standards run on Symphony code only as an advisory lane, never as a
  gate or a public plugin; Beethoven comes in through one pilot lane on
  beethoven-qa after eleven rulings (lanes, beethoven-agents' account
  layer, nothing deleted, the interface standard and others). Eighteen
  proposed issues are written out in it, not filed.
- The released-claim defect (the board never lists a released issue
  again, and nobody can push its claim branch) was handed off as a
  suggested task; another session opened symphony-protocol#5 and
  symphony-template#48 for it.

## Current state

- Every repository named above is on its default branch at the merges;
  claude/magical-shannon-ak167f is level with main, and this checkpoint
  is its next commit.
- Open: symphony-protocol#5 and symphony-template#48, drafts of another
  session (the owner's list, 2).
- CooperBench's App F codes (JUDGE.json) are still counted only when a
  maintainer runs the judge by hand, as the decision on model-judged
  measures requires.
- The plan lives only in this container's scratchpad and in the owner's
  hands; nothing of it is filed or committed.

## Remaining tasks

1. The owner's list above.
2. When the owner has decided: file the plan's issues (P1 to P8 in
   symphony-protocol, coordbench and the marketplace, with no private
   internals in their bodies; T1 to T4 in the template; M1, C1; H1 to H3
   in the private home once it exists; Q1 after the rulings), with the
   label proposed made first.
3. Carried: a live test of /symphony:new on the owner's machine; a live
   test of the Migrate chain; coordbench's texts still say sdlc-protocol;
   symphony-marketplace#2 (/symphony:migrate) is open;
   actions/create-github-app-token@v1 to v2; crowd mode on a real
   organization copy; the 42 gradeable flash pairs; judge.py against a
   real model; coordbench#6, whose credential model the plan leaves to
   the owner.

## Decisions

The durable decisions are CLAUDE.md's block, word for word; those
settled on 2026-10-12, in brief:

- The field metrics count each pull request that ended in the 30 days
  once, in one of eight work settings, with exposure, and pairs by
  relation; a person is the author's login, a session a whole line
  (Claude-Session, the link, the footer or Symphony-Session).
- The Apps' privacy statement is the exhaustive list of what the
  collector keeps; it changes, and its page is live, before the
  collector keeps a new key.
- A session merges a Beethoven pull request only on the owner's word
  for it.

## Constraints

The constraints are CLAUDE.md's block, word for word; those learned on
2026-10-12, in brief:

- The auto-mode classifier counts a merge the repository's rules leave
  to the maintainer as unrequested unless the owner's words ask for it.
- A cloud session's GITHUB_TOKEN runs tools/metrics.py collect on a
  repository the proxy reaches under its current name.
- beethoven-qa and beethoven-agents carry Claude Code hooks; a session
  doing other work reads them as files and registers no root for them.
