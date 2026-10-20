---
name: level-model-bank-coverage
description: "The deployed level model's bank (films_all2_fov96_ctx) holds only cervical and lumbar films; thoracic, sacrum, T13 and L6 had zero or near-zero crops. All-spine bank at ~/allspine_fov96_ctx."
metadata: 
  node_type: memory
  type: project
  originSessionId: e44eca96-f48c-494d-ba1f-7dae68bdf06d
  modified: 2026-09-14T21:52:10.930Z
---

Found 2026-09-14 with `tools/diag_level_model.py`. `films_all2_fov96_ctx` = CSXA cervical films + NHANES/BUU
lumbar films: C3-C7 ~4,300 crops each, L1-L5 ~3,850, but T2-T11, T13 and L6 have ZERO crops and T12 (132),
sacrum (124), C2 (189), T1 (22) almost none. The model scores 98.7% single-crop / 99.4% run on its own val and
0.0% at T10/T11 on CT renders. The corpus QC had read this as a lumbar-biased model and recommended logit
adjustment; that was wrong: re-weighting cannot fix a class with no examples.

**Fix in progress:** `~/allspine_fov96_ctx` (rung 1 only, 85,897 crops; sources films_drr, nhanes_drr, ctsp_drr,
verse_drr, physics_drr; split by patient via `--group-regex`), built by `slurm/allspine_bank.sh`; training job
40249667 (`model_rung_1_aug2.pt`); chain `~/tmp/allspine_chain.sh` runs the diagnostic and transitional test
when it lands (log `~/FluoroCap/allspine_chain.log`). Note buu_full sits in the val split there (counting-inferred
labels), so the bank's own val number is optimistic; judge on renders and FluoroCap.

**Rare anatomy:** `~/FluoroCap/rare_cases_{verse,ctsp}.txt` (56 VerSe with L6/T13, 34 CTSP with L6/LSTV);
physics renders of them at 12 poses each go to `~/physics_rare`. TotalSegmentator has no L6/T13 labels.

**Also learned:** self-training the detector on its own pseudo-labels (v6f) did not raise the box rate
(68.7% vs 69.5% on the same 2,815 panels); resolution is the lever there. See
[[fluorocap-credentials-and-resolution]], [[local-level-identity-thesis]], [[l6-sample-count-and-counting-decoder]].

**2026-09-15 results (held out).** All-spine v2 (`~/allspine_v2_fov96_ctx`, registry alias `allspine_v2_r1`): own
validation 78.8 / 95.9 / 97.2 (exact / within-1 / region); cone-beam renders 62.5 vs v1 50.0. `diag_level_model.py`
and `eval_transitional.py` now skip renders whose CT case is in the bank's TRAINING split (default; `--include-train`
restores the old behaviour): v2 scores 64.2% on 800 held-out renders (4,505 skipped); the v1 "92.7%" was on training
cases. Transitional, held out (376 renders, 2,281 skipped): normal T12 90.8 / L4 84.3 / L5 82.5 / sacrum 100; L6 spines
T12 58.1 / L4 47.2 / L5 38.9 / L6 63.0 single-crop but the caption-free decoder calls only 39.8% L6 (rare-column
penalty 2.5 too high; sweep job 40285325 `--rare-penalties 2.5 1.5 1 .5 .25 0`, output
`transitional_eval_allspine_v2_r1_sweep.md`); T13 0/16 on four spines. Human-verified labels on real fluoroscopy: still
zero (bench has no verdicts). Reality-check page: https://claude.ai/code/artifact/5dac8139-48fe-4093-9d7a-9a651a9e4cac
