# Session checkpoint

Written 2026-10-13 at the end of the main account's session
session_01SEcUB5mdFshEKgiQqdpdK2, for the next session, Fable or any
other. The handoff page, https://claude.ai/artifact/XQj71up9dbJhwSStCVUe9T, holds the plan (PLAN.md), the
handoff itself (HANDOFF.md), the designs (DESIGN-runtime.md,
DESIGN-qa-gate.md, RESEARCH-scale.md), the free-or-paid table
(free-or-paid.md) and one patch set aside
(template-crowd-number-of.patch), as files a session reads with the
Artifact tool; the owner has them too. This file says where things stand.
Its claims were rechecked against GitHub's live state on 2026-10-13 at
about 15:30 UTC by the Project thread "Recheck the handoff"; what did not
hold is corrected below and listed under "The recheck".

## Completed work

- symphony-protocol 0.4.1, released on the owner's approval on 2026-10-13
  at 13:39 UTC, the first release through the gate: six of the twelve
  defects the validation prototype found (F1, F3, F5, F6, F10, F11) and
  what six reviews found, each reproduced first by a failing test
  (symphony-protocol#11); the release gate of decision 5 (#12): a release
  waits for the owner's approval in the environment release and fails
  closed without it, and the sync carries only a published release, from
  the commit that raised main to its version; the validation harness's
  design and prototype (#10, validation/).
- The sync of 0.4.1 merged in all four consumers: symphony-template#64,
  symphony-marketplace#13 (the plugin to 0.1.10), symphony-app#12 and
  coordbench#10.
- The claim and checkpoint skills push the branch by name, made with
  `git switch -c claude/N --no-track origin/<default>`, since with
  push.default=upstream a branch that tracks main sent the claim commit
  to main (symphony-template#62, symphony-marketplace#11, plugin 0.1.9);
  #62 also bounds the usage reader's digits (usage.count_in) and keeps the
  metrics' downloads from following a redirect with the token; the skill
  tests made steady against git's background maintenance
  (symphony-template#63, symphony-marketplace#12).
- Three bugs that hit every new adoption, reproduced and fixed:
  symphony-start#37 (a protocol-only adoption brings every module its
  workflows' scripts import), symphony-template#60 and #61 (a copy, and a
  copy in crowd mode, passes its own check; tests/test_filled_copy.py
  makes copies and runs their checks).
- The plugin in protocol-only repositories (symphony-marketplace#10,
  plugin 0.1.7): every file a skill names is one every adoption has, or
  the skill says what to do without it; the push guard runs through
  scripts/guard.sh and refuses a push when Python cannot run, from
  spine-program's handoff.
- The front door adopts a repository once and never turns an opt-out back
  on, with privacy statement version 5 (symphony-start#38) and its page
  (site#14); earlier, the Actions box (symphony-start#36,
  symphony-template#59, site#13) and the claim skill under worker:<name>
  (symphony-marketplace#9).
- Research and design, each critiqued adversarially and folded into
  PLAN.md: the plan refresh, the scale requirements, the generic QA gate,
  the validation harness, the central runtime, and which GitHub-native
  tools are free or paid on public and private repositories, per plan.

## Current state

- Every consumer runs symphony-protocol 0.4.1; the plugin is 0.1.10.
- The release gate is live: each release waits for the owner's click in
  the browser (Review deployments, then Approve and deploy).
- Nothing of this session's is open on GitHub; the template's session
  branch claude/magical-shannon-ak167f is already gone, deleted on merge.
- Six findings of the validation prototype are left, each for the owner's
  decision or a live measurement: F2, F4, F7, F8, F9, F12 (PLAN.md,
  Phase 1, says what each needs).

## Remaining tasks

For the owner, in order (PLAN.md section 4 has the links):

1. Start the next session with HANDOFF.md's prompt.
2. Approve each symphony-protocol release in the browser when GitHub
   emails, or tell a session in the owner's own words to switch the
   approval off for the development phase.
3. Limit RULESETS_TOKEN and SDLC_APP_PRIVATE_KEY to the repositories that
   need them.
4. Delete the old test repositories (sdlc-template-test,
   sdlc-start-test, sdlc-setup-test, Gregory-Schwing-MD-PhD/test-non-org
   and Gregory-Schwing-MD-PhD/test).
5. Submit Symphony for Chrome, then the five CWS_ secrets and CWS_ON_PUSH.
6. Name the Actions setting in Symphony Setup's description.
7. Tick "Automatically delete head branches" in symphony-start,
   symphony-protocol, symphony-marketplace, coordbench, symphony-app and
   the site, then delete the merged branches left, the template's
   claude/festive-edison-al7xu2 among them (merged in main since
   2026-10-10).
8. Beethoven: the beethoven-qa tags v4.0.0 and v5.0.0, Beethoven 20.0.0
   to the store, beethoven-vscode#11 and #12.
9. spine-program #72.
10. Questions 6 to 14 of PLAN.md section 3, when their phases start.

For the session, in order:

1. Done: the recheck (below).
2. The template's follow-up for 0.4.1, one pull request here:
   docs/agents/PROTOCOL.md's Claim (claude/N exactly, N in one to nine
   ASCII digits with no leading zero; a claim file over 1 MB is read as
   not read) and Release (the labels first, then the comment, the labels
   put back when the comment fails; a person's release, comment first; a
   finished draft), from symphony-protocol's spec/PROTOCOL.md at v0.4.1;
   board.yml's header on the release order; .claude/rules/board.md and
   docs/start/parallel.md on the guard's refusals (a + refspec, the
   refspec : and patterns with *, a name such as claude/03);
   docs/agents/STATE.md's Worker cell "claim file over 1 MB, not read";
   tools/board.py's docstring (a refused comment is a log line, the run
   exits 0); scripts/crowd.py's claim_branches through
   sdlc_protocol.claims.number_of, with its test (the patch on the
   handoff page); the memory note on protocol changes (the sync carries
   only an approved release); and, optional, Budgeted.library_request in
   tools/metrics.py, which 0.4.1's adapter makes unneeded.
3. Three small pull requests: symphony-marketplace's README list of the
   guard's refusals; symphony-app's test for the claude/03 verdict;
   symphony-protocol's README made to agree with its CLAUDE.md (a session
   merges a pull request that changes the gate's files, on the owner's
   permission) and its "not yet measured" on the approval endpoint made
   the measured 403 and the proxy's refusal.
4. docs/memory/the-plan-ladder.md brought up to the free-or-paid table,
   verified 2026-10-13, one pull request.
5. Phase 1 of PLAN.md: the validation harness in symphony-protocol from
   validation/DESIGN.md, one pull request per step of its build order;
   its first pull request brings DESIGN.md's findings table up to date
   (see the recheck).
6. Phase 2, the fresh test, once the owner has deleted the old test
   repositories; then Phases 3 to 11.

Use a workflow for each substantive step, with an adversarial review
before each pull request, and merge each pull request once its checks are
green. Never approve, publish or change symphony-protocol's release
approval without the owner's own words.

## The recheck

Rechecked 2026-10-13 against GitHub: every pull request this file and
HANDOFF.md name is merged (symphony-protocol#10, #11, #12;
symphony-template#59 to #65; symphony-marketplace#9 to #13;
symphony-app#12; coordbench#10; symphony-start#36, #37, #38; site#13,
#14), each with every check run a success or skipped; v0.4.1 was
published at 13:39:56 UTC by release.yml's run for #11's merge, which
waited from 13:16 to 13:39; the plugin is 0.1.10 (0.1.7 at #10, 0.1.9 at
#11 and #12); privacy statement version 5 is in symphony-start and on the
site; no pull request of the project's repositories is open; the
follow-up's files, the patch (it applies to main) and the protocol
README's two lines are as step 2 and step 3 say. What did not hold, or
needs a word:

- The template's session branch was already deleted (Current state).
- Merged branches are left in symphony-app and the site too, not only
  the four repositories owner step 7 named, and in the template one
  from 2026-10-10 (owner step 7).
- symphony-protocol's validation/DESIGN.md, on main, still says the
  package does not change and lists F1, F2, F3, F5, F6, F10, F11 and F12
  as "fix in progress on claude/validation-fixes": 0.4.1 fixed six, and
  F2 and F12 were left with F4, F7, F8 and F9 (session step 5).
- The site has no CI, so its pull requests' "green on its own checks"
  means no check ran.
- Every consumer's VENDORED names 438844f, not v0.4.1's tag commit
  485d470: vendor.py records the last commit that changed
  sdlc_protocol/, and the package is the same at both.

## Decisions

The durable decisions are CLAUDE.md's block, word for word. Those settled
on 2026-10-13, in brief: the open core (the runtime, the protocol and the
plugin public, the hosted parts a paid App); one public versioned runtime
that copies call; the update route parked and fresh test repositories;
the Setup App ticks the Actions box; workers and the coordinator in
protocol-only adoptions, with a default worker and an opt-out box; the
panel as a site page and a stateless sign-in service; a QA report on
every agent's change; few moving parts; a validation harness with its
findings fixed; the account pool, then CooperBench; the owner's five
answers (only writers queue, GitHub stops a worker changing what steers
workers, a separate account for the token as advice only, ten runs a day,
each release on the owner's approval); merging any pull request on the
owner's standing permission, spine-program's too in the development phase.

## Constraints

The constraints are CLAUDE.md's block, word for word. Those learned on
2026-10-13, in brief: a cloud session can neither approve a deployment
nor publish a release, and the auto-mode check refuses a session's
attempts to change the gate without the owner's words; the Actions box
cascades from enterprise to organization to repository, and a session
cannot read or set it; /install-github-app needs gh signed in as the
right account; git does not pass GIT_CONFIG_COUNT to a local remote's
receive-pack, and git 2.55's detached maintenance races a test's cleanup;
the code scanning API answers a session 403, so CodeQL runs locally; gh
api reaches a renamed repository attached with push access; the merge
tool accepted a head sha that was not the head; int() refuses more than
4,300 digits; on the owner's Windows machine gh stalls on DNS and python3
may be the Store's stub.
