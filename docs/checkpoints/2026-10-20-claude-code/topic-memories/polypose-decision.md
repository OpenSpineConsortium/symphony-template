---
name: polypose-decision
description: "Greg 2026-09-23 06:50 -- morphology augmentation = PolyPose (NeurIPS 2025, MIT) used generatively to vary lordosis/kyphosis within Panjabi segmental ROM + LSTV/TLTV-specific published ranges; a fused/sacralised junction gets ZERO motion; rare-class synthetic:real:normal at the literature ratio; seeded, manifested, env-pinned, self-failing invariant checks; 3-D deformation strips + sampling chart in Figure 2"
metadata: 
  node_type: memory
  type: project
  originSessionId: f1bdbd78-151f-470b-b703-dd9af9b3fecc
  modified: 2026-09-23T07:33:56.521Z
---

**Decision (Greg, verbatim spirit):** "no shit you can't create an L6 -- I just want to add more or less lordosis
according to the Panjabi reference ranges, look up LSTV/TLTV-specific values and create a distribution, so the
network learns that L6/T13/sacralisation mean an EXTRA VERTEBRA at the junction, not a geometry (a paper showed
~0.7 AUC from 2-D angles alone); use PolyPose to augment the rare classes at the literature ratio; make sure it
never adds lordosis to an L5-sacrum fusion; run the whole pipeline; data accounting / manifest / auditable /
reproducible / automatic bug detection / seeded / environment-contained; show the 3-D deformations and how the
sampling spans the Panjabi ranges in Figure 2."

**What that means in practice** (workflow `polypose-augmentation`, resume item A30 in
`spinesurg-ct-nnunet/docs/RESUME_2026-09-22_PM.md`):
- PolyPose's polyrigid fold-free field is used with per-vertebra rigid motions SAMPLED from the reference
  distributions instead of estimated by registration; it is reproduced on DeepFluoro (Dice 0.99/0.98, 0 folds)
  before use; pinned commit and env export.
- Junction rules: fused / sacralised unit = one rigid body (zero relative motion); pelvis fixed so pelvic
  incidence is invariant; per-level delta clipped to Panjabi 1991 Table 3; LSTV-specific ranges from the
  literature (`SchwingNet/results/polypose/SAMPLING_SPEC.md`).
- Every output: seed = hash(source case, variant index); manifest row with source, patient key, subtype, deltas,
  commit, env hash, sha256s, re-measured LL/TK/PI, invariant pass/fail; `polypose-check` re-validates the bank
  from disk and exits non-zero; the invariant self-test must FAIL when a fold / moved fusion / shifted pelvis is
  injected. A warped copy keeps its SOURCE PATIENT KEY.
- Ratio: variants in 25-35 % of rendered CTs, 4x real transitional oversampling, synthetic per real rare frame
  <= 10:1 ([[synthetic-real-ratio-evidence]]); run as a measured arm (with / without) since nobody has published one.
- The manuscript still says: no synthesis makes an L6; the transitional evidence rests on real cases.

Related: [[morphology-deformation-feasibility]] (why bespoke was rejected), [[flagship-program]],
[[data-directives-2026-09-23]], [[panjabi-1991-page-892]].
