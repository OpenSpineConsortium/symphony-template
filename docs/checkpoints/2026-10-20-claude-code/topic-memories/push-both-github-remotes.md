---
name: push-both-github-remotes
description: "CTSpinoPelvic1K repo has two GitHub remotes (origin = Gregory-Schwing-MD-PhD, osc = OpenSpineConsortium); push master to both every time"
metadata: 
  node_type: memory
  type: project
  originSessionId: e44eca96-f48c-494d-ba1f-7dae68bdf06d
  modified: 2026-09-07T17:14:22.561Z
---

The CTSpinoPelvic1K repository lives at two GitHub URLs: `origin` (github.com/Gregory-Schwing-MD-PhD/CTSpinoPelvic1K, the working remote) and `osc` (github.com/OpenSpineConsortium/CTSpinoPelvic1K, the URL the manuscript's Data Availability cites). The grid checkout pulls from origin.

**Why:** The paper and the website point readers at the OpenSpineConsortium copy, so it must never lag the working remote. On 2026-09-07 it was found a few commits behind.

**How to apply:** after every commit on master run `git push origin master && git push osc master` (via WSL, see [[wsl-for-network]]). Related: [[commit-directly-to-master]], [[zenodo-deposit]].
