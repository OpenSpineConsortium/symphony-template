---
name: context-ladder-2d-level-experiment
description: "The 2-D \"how much spine must be visible to name a vertebra\" experiment -- design decisions, data-source traps (BUU levels are counting-inferred), and where jobs/outputs live on the grid"
metadata: 
  node_type: memory
  type: project
  originSessionId: e44eca96-f48c-494d-ba1f-7dae68bdf06d
  modified: 2026-09-13T02:52:09.003Z
---

Started 2026-09-12 (Greg's question: at what field of view does level identification break,
down to a single vertebra; target n~4 for fluoroscopy, n=1 as the limit).

**Design that must be kept:** constant target scale (every target vertebra scaled to 22 px on a
320 px canvas), context removed by *masking* not cropping -- otherwise n=0 gets more resolution
than full-spine and the claim is inflated. Two channels: image + target-box marker (without it
the task is ill-posed above n=1). Absolute size withheld -> every number is a lower bound. One
model per rung (rungs full/8/6/4/3/2/1/0 = neighbours each side). No vertical flip, no Sequence
Loss in the ladder arm (Multi-View, arXiv 2307.12845, re-injects the counting prior).

**Data traps:** BUU-LSPINE levels are `inferred_from_position` (counting) -- circular for level
ID, excluded. NHANES II masks are keyed by level (annotated) -> the real-film test. VerSe raw
masks, not vf_813 (see [[vf813-drops-c1-t9-use-raw-verse-for-whole-spine]]).

**Where:** tools `make_drr_dataset.py`, `make_context_crops.py`, `train_level_classifier.py`
(`--arch`, `--eval-model`), `make_contours.py` + `train_contour_pointnet.py` (outline-only arm),
`make_report.py`. Grid: `~/verse_drr`, `~/ctsp_drr`, `~/nhanes_drr`, crops `~/verse_ctx`
(results in `runs/result_rung_*.json`), contours `~/contours`. Prior art: SpineCLUE
(arXiv 2401.07271) motivates arbitrary-FOV ID but never publishes the curve.
