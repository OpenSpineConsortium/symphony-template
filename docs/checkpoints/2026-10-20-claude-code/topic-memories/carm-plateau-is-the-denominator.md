---
name: carm-plateau-is-the-denominator
description: "2026-09-25 per-vertebra miss diagnostic on the C-ArmLSpine test split -- the same-device detection plateau (82-85 %) is the truth denominator (CBCT-cut top-edge slivers, disagreed-level and fallback boxes, four poorly registered laterals), not detector capacity or degrees of freedom; clean subset reads 96.9 %"
metadata:
  node_type: memory
  type: project
  originSessionId: f1bdbd78-151f-470b-b703-dd9af9b3fecc
  modified: 2026-09-25T18:39:17.017Z
---

Greg (2026-09-25): "what is different about C-arm frames such that they flatten around 80 % and plain films continue
to improve? Is it my pseudolabels being poor quality? Or the extra degrees of freedom?"

**Facts.** C-ArmLSpine truth boxes are NOT human: SPINEPS body instances projected through 2-D/3-D edge-registered
poses (median edge NCC 0.37 AP / 0.21 LAT), kept when >= 50 % of projected points are in the frame; names from two
automatic labellers, used where they agree. Film truth is human corners/landmarks and is scored at conf 0.05.

**Diagnostic (tools/carm_miss_diagnostic.py, results/indomain/miss_diagnostic/, REVISION_LOG3 section 11):** over the
ten plateau arms (both views, N 24-200, body rule 0.74) 30 of 287 vertebrae are missed by every arm and 208 hit by
every arm. CBCT-cut vertebrae carry 340 of 489 misses (51.5 % vs 6.7 %); near-edge 42 % vs 5.5 %; disagreed-level
boxes 55.5 % vs 12.7 %; fallback whole-vertebra boxes 100 %. On complete, agreed, SPINEPS-boxed bodies (204 of 287)
recall is 96.9 % (AP 98.7, LAT 95.8; centre rule 99.8 %). Renders: top-edge L1/T12 slivers, garbage boxes, four
laterals with the truth half a body off the bone (NCC 0.12-0.18). One real miss.

**Why it matters:** the "unexplained flat recall" in the supplement has an explanation; the 97 % counting-grade target
is met on the clean denominator; the plateau is not evidence about acquisition-space dimensionality (that shows up
only across untrained views/angles, Figure 5 b-d).

**How to apply:** when a same-device number looks capped, stratify the misses by truth attributes and RENDER them
before theorising. Truth repair without a human: drop structures with < 80 % of projected points in the frame and every
fallback box from the detection denominator, keep them as naming context; re-score, do not retrain. Paper edits are
listed in REVISION_LOG3 section 11 and await Greg's decision. Related: [[acquisition-space-saturation]],
[[detection-is-the-binding-constraint]], [[carmlspine-level-experiment]].
