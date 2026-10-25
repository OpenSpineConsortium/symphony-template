# An auto-merge armed by an App starts the default branch's workflows

The thread "Make auto-merges start main's workflows", 2026-10-24, on the owner's choice of that day to change it in beethoven-qa (SchwingNet #239). What was changed, how it was measured, and what to keep for any repository whose pull requests GitHub merges on its own.

## The fault

GitHub starts no workflow for an event that GITHUB_TOKEN caused, workflow_dispatch and repository_dispatch aside, and an auto-merge is made as whoever armed it. beethoven-qa's kit file `.github/workflows/automerge.yml` armed every ready pull request with GITHUB_TOKEN, so in SchwingNet each merge was github-actions[bot]'s: none of main's push workflows ran (the checks, the gate, the standards, the docs, the synthesis look) and the issue its "Closes #N" named stayed open (#174 and #167 on 2026-10-23, #136, #140 and #166 before).

## The change

beethoven-qa 7.0.0 (beethoven-qa#12, tagged by its release workflow) mints the SymphonyBoard App's installation token in the arm job with actions/create-github-app-token, pinned to a commit, from the variable SDLC_APP_ID and the secret SDLC_APP_PRIVATE_KEY, for the repository alone, with contents and pull requests write, and arms with it. Contents write is what the merge itself needs.

- No workflows permission. A first draft asked for workflows write, since merging a change under `.github/workflows/` needs it; the coordinator pointed out that this lets a token that starts workflows land a change to a workflow, which the owner had not approved, and it was dropped before the merge. A pull request that changes a workflow file is armed with GITHUB_TOKEN instead, read from the pull request's files when it opens.
- Every way the App cannot be used falls back to GITHUB_TOKEN, the old behaviour: no variable (a fork, or a repository without the App), a mint that fails, an unreadable file list, or an arm the App is refused. The log line names which token armed the pull request.
- A workflow file pushed after the App armed a pull request leaves the App's arm in place; GitHub then refuses the merge for want of the workflows permission and turns auto-merge off, so nothing lands.

SchwingNet took 7.0.0 with `vendor --ref v7.0.0 --kit` (SchwingNet #241), its live automerge.yml byte for byte the kit's.

## The measurement

- The App's token is made in SchwingNet: the mint step succeeds in every run after #241.
- #241, #245 and #247 each changed a workflow file, so GITHUB_TOKEN armed them, their merges started nothing on main, and #239 was closed by hand. In SchwingNet a pull request changes a workflow file often, so many merges still take the old path.
- #255, which changed only `docs/memory/`, was the first the App armed (auto_merge_enabled by symphonyboard[bot] at 22:50 UTC). It merged at 23:14 UTC as symphonyboard[bot], and its merge commit started main's push runs of Checks, gate, standards, Docs, Board and Template init, with issue runs of the Board, the Coordinator and Tidy; issue #254, which it named, was closed as completed by symphonyboard[bot]. Both halves of the fault are gone for a merge the App arms.
- In beethoven-qa itself the App armed #12, but an organization ruleset there requires one approving review, so an auto-merge waits for a review whoever arms it; #12 was merged by hand. SchwingNet's own ruleset asks for none.
- The workflow token's arm prints "auto-merge not armed: ... Resource not accessible by integration" over a pull request an earlier run already armed: the mutation's answer reads autoMergeRequest, which that token may not read. It is not a failure to arm.
- actions/create-github-app-token v3.3.0 warns that its input app-id is deprecated in favour of client-id; it still works.

## What to keep

- An automation that must start workflows acts as an App or a person, never as GITHUB_TOKEN; that includes arming auto-merge, since the merge is the arming actor's.
- Give the App's token the least it needs for the step, and keep a workflow change out of the reach of a token that starts workflows.
- Say in the log which identity acted, so a silent merge can be told from a broken one.
- Measure on a change that takes the new path: the first three merges after the change all took the old one by design, and only a docs-only pull request opened for the purpose showed the result.
