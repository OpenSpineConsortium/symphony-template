---
name: fluorocap-repo-private
description: "FluoroCap code lives on branch L6_Class of spinesurg-ct-nnunet, which was switched to PRIVATE on 2026-09-14 at the user's request; keep it private"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: e44eca96-f48c-494d-ba1f-7dae68bdf06d
  modified: 2026-09-14T09:36:28.021Z
---

On 2026-09-14 the user said "THIS WORK SHOULD BE PRIVATE TO ME" about the FluoroCap / level-ID code.
The code is committed on branch `L6_Class` of `Gregory-Schwing-MD-PhD/spinesurg-ct-nnunet` (pushed
regularly, not master). I flipped that repo to private via the GitHub API using the stored git
credential (`git credential fill` piped into curl, token never printed). Before the flip it had
0 forks, 0 stars, 0 watchers and no Software Heritage archive.

`CTSpinoPelvic1K` (origin + osc) and `OpenSpineToolkit` stayed public: the dataset article cites them
and they hold no FluoroCap code.

**Why:** the user does not want the level-ID / FluoroCap work public yet (see [[commercialization-stance]]).

**How to apply:** never push FluoroCap or level-ID code to a public repo; before adding such code to
CTSpinoPelvic1K or OpenSpineToolkit, ask. Private visibility does not change the push workflow
(same HTTPS credential). If the user wants the repo public again: PATCH `{"private": false}` or the
GitHub settings page. Related: [[fluorocap-dataset]], [[push-both-github-remotes]].
