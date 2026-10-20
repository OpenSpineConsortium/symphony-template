---
name: postop-spine-synthesis
description: Synthetic post-operative spine generation in ostk (ostk.surgery)
metadata: 
  node_type: memory
  type: project
  originSessionId: 436e5c70-681e-4f38-aab2-30dfa25af7b5
---

Goal: generate a patient's spine/CT AFTER a lordosis-restoring operation, driven by the
Greenberg Ch.73 operations + the [[pacs-demo-and-ostk-params]] `surgical_recommendation`.

Insight: every lordosing op (interbody/ALIF/LLIF, ACR, SPO, PSO) = rotate the segment
CRANIAL to the operative level by Delta  deg in the sagittal plane (pelvis fixed). They differ
only by fulcrum + tissue change (Table 73.2 Delta  ceilings; Fig 73.3 osteotomy mechanics).

**Phase 1 (DONE, 2026-06, OpenSpineToolkit main):** `ostk.surgery.simulate_correction(
label, affine, level, delta_deg)` rotates at/above-level vertebrae about the level
centroid on the LABEL volume (angle change is fulcrum-independent). Validated by
re-running `ostk.metrics` on the output: LL rises ~Delta , PI/SS/PT unchanged (pelvis fixed),
PI-LL closes ~Delta . Added `geometry.rotation_matrix` (Rodrigues). `level` = lowest mobile
vertebra (e.g. L5-S1 ALIF -> level='L5'); S1/sacrum/femurs never mobile.

**Phases 2-3 (DONE):** `bend_spine` distributed smooth bend (no kink) + `warp_ct` (bone HU
follows labels) + interbody cages; `predict_compensated_alignment` (analytic pelvic re-posture).

**Phase 4 (DONE, 2026-06-23):** biomechanically realistic post-op. `surgery.synthesize_postop`
= one composite field: lumbar lordosis (0->Delta LL, S1->L1) + **reciprocal thoracic kyphosis**
(Delta LL->Delta LL-Delta TK over L1->top-thoracic; literature Delta TK~0.34-0.58-Delta LL, used 0.5) + optional global
pelvic anteversion. `age_adjusted_targets`/`plan_realignment` = **Lafage age-adjusted goals**
(PI-LL=(age-55)/2+3, PT=(age-55)/3+20, SVA=2(age-55)+25). `place_interbody_cages` (ALIF/LLIF,
NO body resection). Split `bend_params` (world-space, derive once on COARSE seg = fast) +
`transform_world_points` + `synthesize_postop(params=...)`.

**CRITICAL gotcha:** re-measuring the resampled post-op image is UNRELIABLE -- see
[[postop-jaggedness-future]] (rough endplates -> LL fit collapses 45.7->~24). So the demo
exporter (`--postop`, `tools/export_demo_case.py`) computes post-op NUMBERS analytically
(PI invariant, LL=base+Delta LL) and carries the OVERLAY forward via `transform_world_points`
(pelvic constructions below S1 unmoved; LL rides the bend). The resampled image is DISPLAY
ONLY. Demo: case 0003, ALIF L1-S1 age 50 -> LL 45.7->55.0, PI-LL 9.8->0.5, 5 cages.

Demo CLI: `export_demo_case.py --postop --postop-age 50 --postop-technique alif --mask-bone`
(needs full-res --ct + --label; writes postop_{ct,seg}.nii.gz on the demo grid + a postop
block in metrics.json with summary/geometry/plan).

Framing for neurosurgeons: forward geometric modeling driven by published per-level angles +
Lafage age-adjusted targets + reciprocal-change literature; numbers carried analytically.
