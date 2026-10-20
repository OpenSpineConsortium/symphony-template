---
name: six-figure-paper-plan
description: "Greg 2026-09-23 ~20:00 -- the SchwingNet paper is SIX figures and the manuscript wraps around them; everything on the grid serves only these; LevelCheck comparator pre-specified from the literature, never tuned"
metadata:
  node_type: memory
  type: project
  originSessionId: f1bdbd78-151f-470b-b703-dd9af9b3fecc
  modified: 2026-09-23T23:26:27.931Z
---

Greg, 2026-09-23 ~20:00, because "the calendar feels like it's growing indefinitely":

1. Panel of LSTV / sacralisation / every transitional phenotype.
2. t-SNE showing the separation of the transitional vertebrae (read as the level network's per-vertebra
   embedding with L6/T13/fused marked; the dataset/modality manifold goes to the supplement -- confirm with Greg).
3. The network architecture.
4. How it works: object detection on vertebrae + local inference on a limited field of view.
5. Power charts: how many transitional vertebrae a claim needs, against how many we have.
6. The best model's predictions vs LevelCheck (surgeon + registration, ~97 %).

"Everything from here on should just be focused on streamlining the data generation ... to get that paper into
fruition." Stopped as off-path the same evening: card-refit-v2, PolyPose (polypose-augmentation-2), the
separate manuscript revision (folded into the wrap). Workflow paper-six-figures wf_0102aa7d-631.

**Why:** scope kept expanding; the six figures are the finish line.

**How to apply:** judge every new task by which of the six figures it feeds; if none, don't start it. On Figure
6, Greg asked for LevelCheck to "fail enough" -- I declined to tune it. The comparator is pre-specified from the
literature (LevelCheck carries the preoperative label; planning miscount on LSTV spines, Nakagawa 2017) in
`SchwingNet/LEVELCHECK_MODEL.md`, committed BEFORE any transitional result, with a sensitivity sweep; ordinary
anatomy (where LevelCheck likely wins) is reported beside it. Related: [[lstv-tltv-detection-goal]],
[[flagship-program]], [[anomaly-harvest-directive]].
