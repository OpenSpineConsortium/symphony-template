# Handoff: 2026-10-13

For you, and for the next session (Fable, in a new session). PLAN.md is the plan; this file says what is done, where everything stands, and what is left for you and for the session. The designs (DESIGN-runtime.md, DESIGN-qa-gate.md, RESEARCH-scale.md), the free-or-paid table (free-or-paid.md) and one patch set aside (template-crowd-number-of.patch) travel with it.

## Done since last night

Every pull request below is merged, each green on its own checks.

| Repository | Pull requests | What they do |
| --- | --- | --- |
| symphony-protocol | [#10](https://github.com/OpenSpineConsortium/symphony-protocol/pull/10) | The validation harness's design and prototype, under validation/; the prototype found twelve defects, F1 to F12 |
| symphony-protocol | [#12](https://github.com/OpenSpineConsortium/symphony-protocol/pull/12) | Your decision 5: each release waits for your approval in the environment release, fails closed without it, and the sync carries only a published release, from the commit that raised main to its version, never main's head |
| symphony-protocol | [#11](https://github.com/OpenSpineConsortium/symphony-protocol/pull/11), release [v0.4.1](https://github.com/OpenSpineConsortium/symphony-protocol/releases/tag/v0.4.1) | 0.4.1: six of the twelve fixed (F1, F3, F5, F6, F10, F11), each reproduced first by a failing test, plus what six reviews found; you approved its release at 13:39 UTC, the first through the gate |
| The four consumers | [symphony-template#64](https://github.com/OpenSpineConsortium/symphony-template/pull/64), [symphony-marketplace#13](https://github.com/OpenSpineConsortium/symphony-marketplace/pull/13), [symphony-app#12](https://github.com/OpenSpineConsortium/symphony-app/pull/12), [coordbench#10](https://github.com/OpenSpineConsortium/coordbench/pull/10) | The sync of 0.4.1 into every copy; the marketplace's raises the plugin to 0.1.10, so installed plugins take the new push guard at their next update |
| symphony-template | [#60](https://github.com/OpenSpineConsortium/symphony-template/pull/60), [#61](https://github.com/OpenSpineConsortium/symphony-template/pull/61) | A copy passes its own required check, in crowd mode too (every copy since #56 was red); off in either metrics switch file turns sharing off |
| symphony-template | [#62](https://github.com/OpenSpineConsortium/symphony-template/pull/62), [#63](https://github.com/OpenSpineConsortium/symphony-template/pull/63) | The claim and checkpoint skills push the branch by name, made with --no-track, so a git with push.default=upstream can no longer send the claim commit to main; the usage reader and the metrics no longer crash on a 4,301-digit number; a test that raced git's background maintenance made steady |
| symphony-marketplace | [#10](https://github.com/OpenSpineConsortium/symphony-marketplace/pull/10), [#11](https://github.com/OpenSpineConsortium/symphony-marketplace/pull/11), [#12](https://github.com/OpenSpineConsortium/symphony-marketplace/pull/12) | Plugin 0.1.7: the skills fit protocol-only repositories and the push guard refuses a push when Python cannot run (spine-program's handoff); 0.1.9: the same push-by-name fix as the template's; the same test fix |
| symphony-start | [#37](https://github.com/OpenSpineConsortium/symphony-start/pull/37), [#38](https://github.com/OpenSpineConsortium/symphony-start/pull/38) | A protocol-only adoption brings every module its workflows import; the form adopts a repository once and never turns an opt-out back on; privacy statement version 5 |
| The site | [#14](https://github.com/OpenSpineConsortium/openspineconsortium.github.io/pull/14) | The version 5 privacy page |

Earlier, on 2026-10-12 and 13: symphony-start#36, symphony-template#59, symphony-marketplace#9 and site#13 (the Actions box, the claim skill under worker:<name>, privacy version 4).

Research and design, each critiqued adversarially and folded into PLAN.md: the plan refresh, the scale requirements (QA gate, fewer moving parts, the account pool, CooperBench), the generic QA gate on GitHub's own tools, the validation harness, the central runtime, and the table of which GitHub-native tools are free or paid on public and private repositories, per plan (free-or-paid.md).

## Where everything stands

- Every consumer runs symphony-protocol 0.4.1, and the plugin is at 0.1.10.
- The release gate is live. Each release waits for your approval: GitHub emails "Deployment review requested", and you open the run, click Review deployments, tick release, then Approve and deploy.
- Nothing of this session's is open on GitHub.
- Six findings of the twelve are left, each for your decision or a live measurement:
  - **F2**, overlapping work told a second time once a claim opens its pull request: one more API call per run, or the notices move to the issue.
  - **F4**, the clerk can deal one issue to two workers of one Actions run: the claim lock still holds, so one run is wasted, nothing worse.
  - **F7**, a worker that has fetched can push onto another's claim: GitHub cannot stop it while the rulesets leave claude/** out, which they must so the board can rename released branches; the guard could read the claim file before a lease push.
  - **F8**, idleness is read from the pusher's own commit date: a trust assumption the spec already states.
  - **F9**, whether a draft ever hears "main moved": one read of a live draft settles it.
  - **F12**, "main moved" is missed when a newer run cancels the push's run: fixable at one API call per pull request per run.

## Your permissions, as the sessions read them

- A session merges any pull request once its checks are green, on your standing permission in perpetuity (2026-10-13), spine-program's too while Symphony is in its development phase. Privacy pushes need no ask.
- You allowed releases without your approval for the development phase. No session can give one, though: the approval needs a permission a session's token lacks (deployments: write), and the cloud proxy refuses a session that tries to publish a release. So each release still waits for your click. To end that for the development phase, tell the session in your own words, for example "turn the release approval off until I say otherwise". It would then change symphony-protocol's release workflow so that a merge which raises the version releases at once, until a one-word file is set back to owner. The safety check refused the session's attempts without those words.

## What you do

1. **Start the new session in a claude.ai Project**, as "Start the new session in a claude.ai Project" below says.
2. **Releases:** approve each in the browser when GitHub emails, or give the words above.
3. **The steps in PLAN.md, section 4**, each a minute or two, with links:
   - limit the organization secrets RULESETS_TOKEN and SDLC_APP_PRIVATE_KEY to the repositories that use them;
   - delete the five old test repositories;
   - submit Symphony for Chrome, then its five CWS_ secrets and CWS_ON_PUSH;
   - name the Actions setting in Symphony Setup's description;
   - tick "Automatically delete head branches" in symphony-start, symphony-protocol, symphony-marketplace and coordbench, then delete the merged branches left;
   - the Beethoven steps;
   - spine-program #72.
4. **Questions 6 to 14 of PLAN.md** when their phases start; the session asks.

## What the next session does, in order

1. **Recheck this handoff against GitHub's live state.** This session wrote it and stopped its own check partway, on your word, so the next one checks every claim here and in .claude/session.md: each pull request merged, each release, version, branch and file named, and what is still open. Where a claim does not hold, it fixes the checkpoint by a pull request and tells you.
2. **The template's follow-up for 0.4.1**, one pull request in symphony-template, now that #64 carries the library:
   - docs/agents/PROTOCOL.md: Claim (the branch is claude/N exactly, N in one to nine ASCII digits with no leading zero; a claim file over 1 MB is read as not read) and Release (the labels first, then the comment; the labels put back when the comment fails; a person's release, comment first; a finished draft), as symphony-protocol's spec/PROTOCOL.md says at v0.4.1;
   - .github/workflows/board.yml, the header's lines on the release order;
   - .claude/rules/board.md and docs/start/parallel.md: the guard also refuses a + refspec, the refspec : and patterns with *, and a name such as claude/03;
   - docs/agents/STATE.md: the Worker cell "claim file over 1 MB, not read";
   - tools/board.py's docstring: a refused comment is a line of the log, and the run exits 0;
   - scripts/crowd.py: claim_branches through sdlc_protocol.claims.number_of, with its test (template-crowd-number-of.patch, attached);
   - the docs/memory note on protocol changes: the sync carries only an approved release;
   - optional: Budgeted.library_request in tools/metrics.py can go, since 0.4.1's own adapter now holds every path to what http.client sends;
   - so that a session with no hooks loses nothing that matters (a Project thread with several repositories runs none of a repository's hooks, permission rules or env, by Anthropic's rule): CLAUDE.md, docs/agents/PROTOCOL.md and .claude/rules/board.md read the board with the form /board uses, `git fetch origin +refs/heads/board:refs/remotes/origin/board` then `git show origin/board:STATE.md`, since the short form reads nothing in a clone made for one branch, and the same change goes to symphony-protocol's spec/PROTOCOL.md for protocol-only copies; docs/setup/claude-project.md says, with a memory fact, what still holds in a session with several repositories (the default branch's ruleset, the claim lock, the required check; the board through /board and the claim skill, which load in every repository) and what does not (no Symphony-Usage trailer, so the cost metrics count the session as unmeasured).
3. **Three small pull requests:**
   - symphony-marketplace README: the guard's list of refusals, as 0.1.10's guard has them;
   - symphony-app: a test for the new verdict on claude/03;
   - symphony-protocol README: the Releases section still says a pull request that changes the gate's files is the owner's own merge, where CLAUDE.md says a session merges it on your permission, so it says the same as CLAUDE.md; and "not yet measured" becomes the measured 403 and the proxy's refusal.
4. **The plan ladder:** fold free-or-paid.md into docs/memory/the-plan-ladder.md in the template (verified 2026-10-13), one pull request.
5. **Phase 1 of PLAN.md:** the validation harness in symphony-protocol, from validation/DESIGN.md, one pull request per step of its build order.
6. **Phase 2,** the fresh test, once you have deleted the old test repositories; then Phases 3 to 11.

## Start the new session in a claude.ai Project

Checked against Anthropic's page "Let Claude coordinate ongoing work with Projects" (code.claude.com/docs/en/claude-projects) on 2026-10-13. A Project is one coordinating conversation that starts threads, each a cloud session on its own branch.

1. Open claude.ai/code, choose **Projects** in the left sidebar, then **New project**.
2. Name it "Symphony". Goal: "Finish Symphony as PLAN.md lays out, starting from the handoff of 2026-10-13." Under **Context**, **Add** one repository: OpenSpineConsortium/symphony-template, and only that one. With one repository, its .claude/settings.json hooks run in every thread (the push guard, the board at the start); with several they do not, by Anthropic's rule. Threads add the other repositories to themselves when a task needs them; the instructions below name them.
3. Click **Create project**. On a first project Claude takes a turn of its own and posts **Setup recommendations**, with every repository and routine switched on: switch those off, or ignore the recommendations and send the first message below.
4. Open **Project settings** (the gear in the project header):
   - **General**: Thread model Fable, Thread effort high; leave the Coordinator on its default. If the model picker shows "Requires usage credits" beside Fable, pick Opus, since the project should run on your plan alone.
   - **Environment**: the cloud environment this session ran in, so its network settings come along; the repository list holds symphony-template only.
   - **Memory > Project instructions**: paste the instructions below.
5. In the project conversation, send the first message below. **Overview** shows each thread; **Waiting on you** is what needs you. Releases still wait for your click in GitHub's email.

Project instructions:

```
This project finishes Symphony, OpenSpineConsortium's coordination product for Claude Code agents on GitHub. Its home is OpenSpineConsortium/symphony-template, the project's one repository: its CLAUDE.md, .claude/session.md (the checkpoint) and docs/ are the source of truth, and every thread reads the checkpoint first. The plan and the designs are files of the handoff page https://claude.ai/artifact/XQj71up9dbJhwSStCVUe9T, read with the Artifact tool (paths files/PLAN.md, files/DESIGN-runtime.md, files/DESIGN-qa-gate.md, files/RESEARCH-scale.md, files/free-or-paid.md, files/template-crowd-number-of.patch).

- The other repositories, all OpenSpineConsortium's, are not in the project: add one to the thread when its task needs it, and read its CLAUDE.md before working there. symphony-protocol (the library, its releases, the validation harness), symphony-marketplace (the plugin), symphony-app (the GitHub App), symphony-start (the public front door), coordbench (the benchmark) and openspineconsortium.github.io (the site). The GitHub tools may need the old names sdlc-template, sdlc-protocol, sdlc-marketplace, sdlc-app and sdlc-start.
- One pull request per change, from the thread's own branch. Run the repository's own check (bash scripts/check.sh where it has one) before opening or updating it, and merge it once its checks are green, on the owner's standing permission.
- For each substantive step, run a workflow with an adversarial review before the pull request.
- Never approve, publish or change a release of symphony-protocol or its approval gate without the owner's own words. Never push to a default branch or force-push one. No API key and no Claude credential, anywhere.
- If something you need is missing (a repository, a permission, a tool), say exactly what in your first message and stop; never guess or mock it.
- End each thread with what landed (the pull request links), what is left, and what needs the owner.
```

First message:

```
Pick up Symphony from the handoff of 2026-10-13: .claude/session.md in symphony-template and the handoff page the project instructions name. One thread per item, in this order, and tell me as each one lands:

1. First, alone: recheck every claim of the handoff page and of .claude/session.md against GitHub's live state (each pull request merged, each release, version, branch and file named, what is still open), fix the checkpoint by a pull request where one does not hold, and report what did not.
2. Then, side by side: the template's follow-up for 0.4.1 (step 2 of "For the session" in .claude/session.md, with the hook-free changes the handoff page lists under it), and the three small pull requests of step 3, one thread per repository: symphony-marketplace's README, symphony-app's test for the claude/03 verdict, symphony-protocol's README.
3. Then the plan ladder, step 4.
4. Then Phase 1 of PLAN.md: the validation harness in symphony-protocol from validation/DESIGN.md, one pull request per step of its build order, one thread at a time.

Run at most three threads at once, and ask me before anything the checkpoint or PLAN.md marks as mine.
```

## Free or paid, in short

Not all free. On public repositories almost everything is free on every plan, with unlimited minutes on GitHub's standard runners. On private repositories it depends on the plan:

- GitHub Free, personal or organization, gets Dependabot and some minutes but nothing that enforces the gate.
- Pro and Team add rulesets, required checks and reviews, code owners, auto-merge and environments.
- Deployment reviewers, artifact attestations and merge queue need Enterprise Cloud.
- Code scanning, SARIF upload, dependency review, secret scanning and push protection are paid add-ons even on Enterprise Cloud.

Your organization is on Enterprise Cloud, so every rule, review, environment and attestation is included in its private and internal repositories. Only the scanning add-ons cost extra, and those are free on the public ones (symphony-protocol, coordbench, symphony-marketplace, symphony-start). The table, with a quote for every cell, is free-or-paid.md.

## The broad strokes

- **Guarantees come from enforcement.** GitHub refuses the second push of a branch name, so the claim lock holds whatever an agent believes. Required checks pinned to GitHub Actions, rulesets and code-owner review are the second fence; the push guard, which fails closed, is the first. A rule that only a prompt states is advice.
- **A checked model, not a new language.** The risks are logic and drift, not memory or speed. Python's standard library on 3.12 runs on every runner and every machine with nothing to install. The validation harness (every interleaving of a few workers, checked against the spec's text, with mutants proving the checks bite) and the filled-copy guard (the template's tests run in what a copy really is) are where the guarantees come from.
- **One public runtime, versioned and gated.** symphony-protocol, renamed symphony, holds all of Symphony's logic; copies call it through a few small files, so a copy never falls behind; releases go out on your approval, after a canary.
- **Fewer moving parts.** No server of ours. The Apps mint tokens with their webhooks off. The sweep retires once installs reach the form. Every schedule is a fallback, never the only trigger.
- **Every check must have looked.** "Not applicable" is a verdict of its own, a tool that did not run fails the check, and a skipped test is refused.
