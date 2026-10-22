---
name: no-manual-steps-for-greg
description: greg's rule of 2026-10-20: never ask him to tag a release, merge a PR, run a script or set a repository setting by hand; automate it or batch it into one App install
metadata:
  type: feedback
  modified: 2026-10-20T16:59:58.821Z
---

On 2026-10-20 (SchwingNet thread) greg, angry, said: "I NEVER WANT TO NEED TO MANUALLY TAG A RELEASE, MERGE A PR, OR ANY OF THAT SHIT AGAIN", after a reply asked him to run scripts/setup-repo.sh and tag beethoven-qa v6.0.0.

**Why:** "Use this template" copies files only; GITHUB_TOKEN in a new repository cannot create rulesets or change settings, and the cloud session's proxy refuses every repository-settings write (403 on rulesets POST, gh repo edit, topics). So a hand step kept appearing per repository, which breaks his reproducibility rule ([[reproducibility-rule]]).

**How to apply:** settings come from the Symphony Setup App (Tokens and adopted repositories thread owns making that the default for every template repository); releases tag themselves by workflow on a version-bump merge (beethoven-qa .github/workflows/release.yml, PR of 2026-10-20); merges land by auto-merge or on his standing permission. The symphony-protocol release approval gate changes only on his explicit word (a decision card was posted 2026-10-20). If a hand step is truly unavoidable, batch it into one App permission acceptance, and never list per-repository clicks in a reply.

Extended 2026-10-21 19:37 UTC (greg): "make sure i never have to issue these fucking grid commands myself anymore". No grid shell pastes for greg; grid work goes through the Beethoven gate/worker route ("Beethoven grid node wait", [[grid-job-handoff-path]]), or is handed to the thread that owns the grid clone. Only exception: a one-time secret he must type himself (e.g. the PhysioNet password into ~/.netrc).
