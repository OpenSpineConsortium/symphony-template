---
name: l6-sample-count-and-counting-decoder
description: "L6 pseudo-dice stayed exactly 0.000 for 27+ epochs with 12x duplication (sample-count, not gradient); a rule-based counting decoder on 4-class GT found 6/6 L6 cases at 93-97%; Dataset815 (813 + VerSeFusion) raises L6 cases 18->62"
metadata: 
  node_type: memory
  type: project
  originSessionId: e44eca96-f48c-494d-ba1f-7dae68bdf06d
  modified: 2026-09-13T02:52:26.368Z
---

Findings from 2026-09-12 on the grid (`~/spinesurg-ct-nnunet`).

- Training 40202827 (Dataset813, ResEncL, `SPINESURG_LUMB_DUP_WEIGHT=12`): L1-L5 reach
  0.80-0.86, sacrum 0.94, **L6 0.000 every epoch** -- never one correct voxel. Duplicating 18
  cases twelvefold does nothing; the class is starved of *distinct* examples.
- Quaternary baseline (`tools/make_quaternary_dataset.py`, `tools/enumerate_decoder.py`,
  `tools/split_column.py`): on ground-truth 4-class input the counting decoder found **6/6 L6
  cases** (93-97% voxel agreement) and fails on 2/3 sacralizations (over-counts) -- the
  predicted structural limit. Four bugs mattered: 3-D watershed over-splits 4-5x (vertebrae
  aren't convex -> cut at per-slice area minima); ribs never touch vertebrae (TS medial
  truncation -> nearest-body within 20 mm); anchor must be the *min* index caudal->cranial;
  one vote per rib component, not per voxel.
- Dataset815 = 802 + 374 VerSeFusion (`tools/merge_versefusion_corpus.py`), 1,176 cases,
  L6 62 (18 ctsp + 44 vf), T13 4; folds stratified phenotypexcorpus. Preprocess with
  `slurm/prep815.sh` (needs `-q primary` for singularity).
- VerSeFusion QC (bridged to v10): invariants 372/374 (verse243/247 empty after bridge -- likely
  cervical-only), rib incidence 0.9% offset, 7 misnumbered (verse631/024/088/601/606/616/642).

**How to apply:** treat "L6 = 0.000" as a data-count signal, not a trainer bug; the merged corpus
is the experiment that tests it. Related: [[lstv-oneshot-training-run]],
[[competitor-benchmark]].
