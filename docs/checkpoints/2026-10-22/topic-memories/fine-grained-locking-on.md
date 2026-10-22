---
name: fine-grained-locking-on
description: greg chose (2026-10-20 21:21 UTC) symphony-protocol 0.6.0 with the native git locks and the overlap check in place of GitHub's strict up-to-date rule, off everywhere on his order; the template runs it at advise since template #315; 0.6.1 (2026-10-21) fixed the protocol check for PRs behind main; enforce waits for his word
metadata:
  type: project
  modified: 2026-10-21T00:31:55.425Z
---

Thread "Fine-grained locking on", 2026-10-20. greg's words: turn the strict "Require branches to be up to date" rule off (20:44 UTC), switch on the locking he built (symphony-protocol#45), "dependency analysis tools at the most and git hash based code checkout locks at the least" (20:54), "PRIORITIZE SAFELY TURNING THIS HORRIBLE INEFFICIENT WAY OF WORKING OFF" (21:09); he picked "0.6.0 with locks and the overlap check" on the decision card at 21:21 UTC.

Why: 127 of 255 merged template PRs needed catch-up merges under the strict rule (Stale branch failure statistics thread). The rule went false: SchwingNet ~21:08 UTC, coordbench 21:17, symphony-start 21:17, symphony-template 21:31, symphony-protocol 22:26 (#59's settings workflow on SymphonyBoard's token); symphony-app and marketplace were already off.

What landed: `locks overlap` (protocol #60, v0.6.0 at 22:14 UTC, merged by greg after he gave the protocol's ruleset a Repository-admin bypass; template sync #308 at 22:32); template #315 (23:04 UTC) wires it at advise, ci.yml job `overlap` on every PR and overlap.yml writing the check run `overlap` on every open PR when main moves; details in the repo (docs/memory/the-overlap-check.md, docs/research/overlap-check-instead-of-up-to-date.md section 5).

The catch the switch-off exposed: the protocol check took HEAD for GitHub's test merge only when its first parent was the event's base.sha, which GitHub sets at the PR's opening and leaves while main alone moves, so every PR pushed, marked ready or edited while behind main failed the required check (template #315 at 22:57 UTC). Protocol #61 (0.6.1, merged 2026-10-21 00:20 UTC, tagged 00:21) reads the test merge by its second parent, the event's head; template #317 (the sync PR) auto-merged it at 00:25 UTC; the copies take it by their protocol.yml. symphony-protocol had "Allow auto-merge" off (#61 was merged by API); the Tokens thread turned it on by protocol #62 (2026-10-21 00:31 UTC).

How to apply: enforce only on greg's word; it needs a ruleset requiring the check `overlap` and one on branch `locks` (the Tokens thread's auto-applied rulesets, never a session's write, [[ruleset-writes-refused]]), the claim skill taking locks, ci.yml's push filter leaving `locks` out, and a decision on "could not be judged" at enforce (failure today). coordbench's locks arm is untouched; its run waits for greg's number. [[native-first]]
