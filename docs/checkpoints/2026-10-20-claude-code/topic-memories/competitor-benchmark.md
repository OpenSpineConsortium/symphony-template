---
name: competitor-benchmark
description: "Competitor benchmark (TotalSegmentator, SPINEPS-CT/VERIDAH + Moller ribs, NV-Segment-CT/VISTA3D, RibSeg v2) against CTSpinoPelvic1K in the one-shot scoring space: layout on the grid, what exists, what is pending (started 2026-09-08)"
metadata:
  type: project
  originSessionId: e44eca96-f48c-494d-ba1f-7dae68bdf06d
  modified: 2026-09-08T10:23:24.734Z
---

Lives in `spinesurg-ct-nnunet/benchmark/` (branch L6_Class) and on the grid under `~/bench/<system>/{native,oneshot,score}`.
Principle: predictions stay native on disk; `to_oneshot.py` maps them BY NAME into the Dataset810
one-shot labels (`mappings/<system>.json`), then the same two scorers as our folds run
(`tools/eval_oneshot.py`, `tools/decode_sequence.py --onehot`). `collect.py` joins the summaries.
Case table: `benchmark/cases.csv` (802 records, host CT path, one-shot label, fold, subtype, L6/lumbar-rib flags).

Systems: TotalSegmentator v2 (container `~/CTSpinoPelvic1K/containers/ctspinopelvic1k-ts.sif`,
weights `~/totalseg_weights`, `run_totalsegmentator.sh`; ~60-90 s/case on H200; full 802 run
queued 2026-09-08); SPINEPS CT + VERIDAH (`run_spineps.sh`, conda env `spineps`, models
`~/spineps_models` = ct + CT_instance from release v2.0.0, ct_labeling from v1.4.0; v2 CLI flags
`--model-semantic/--model-instance/--model-labeling` still to verify against `spineps sample --help`);
NV-Segment-CT (VISTA3D lineage, `run_vista3d.sh`, env `vista3d`, clone `~/NV-Segment-CTMR`,
checkpoint via HF snapshot in `fetch_weights.sh`); RibSeg v2 (clone only; pretrained checkpoint
location not found in the README, resolve before `~/CTSpinoPelvic1K/slurm/ribseg.sh`).
The old `ctspinopelvic1k-spineps.sif` described in `CTSpinoPelvic1K/docs/SPINEPS_BENCHMARK.md` was
never pulled to the grid; the conda route replaces it.
Old v3-era scorers (`CTSpinoPelvic1K/scripts/benchmark_totalseg.py`, `benchmark_spineps.py`) use the
pre-v10 10-class / 74-75 lumbar-rib ids; do not reuse them for numbers.

State 2026-09-08 06:30: ground truth scores Dice 1.000 on every class through score.sh (scorer
verified). TotalSegmentator full run (4 shards, job 40164783) in progress. spineps env built (torch
2.6 cu124; pip needed numpy/blosc2 from conda-forge first); vista3d env built; SPINEPS models in
~/spineps_models (ct, CT_instance, ct_labeling); NV-Segment-CT checkpoint in the HF cache;
~/rib-segmentation cloned (not a pip package). Moller's rib assignment uses TPTBox
Vertebra_Instance.RIB ids (T10 49, T11 50, T12 51, L1 52, T13 53; sides Location 63/64) and cannot
assign a rib below L1. SPINEPS ribs: run_spineps_ribs.{sh,py}; composition: spineps_to_oneshot.py.

Decoder changes made for this (tools/decode_sequence.py): `--onehot` (hard-label systems); an
EROSION split for a component taller than 1.6 typical bodies of the same case (erode 2-5 mm,
seeds must be stacked half a body apart, voxels go to the nearest seed; a slice-area-profile
split failed because facet joints keep the area up at the disc); same-name fragments merge
within half a body height (not by height overlap: articular processes overlap the next body);
instances need 2 cm^3 and a fifth of the case's median instance volume (label specks were
counted as vertebrae on 0068 and COLONOG_103). So a competitor without an L6 class still gets
its COUNT scored fairly while the NAME is a miss. Test: benchmark/test_decoder.sh (run A one-hot
GT, run B with L6 renamed L5): BOTH PASS 5/5 on 0007/0068/0145/0376/1053 as of 2026-09-08 07:40
(commit a8dd3fc: split pieces are never re-merged).

Figures (benchmark/figs, copied to NextPaper/AR/figs and paper/cns2026/figs): capability_matrix.py
(fig_capabilities + tab_capabilities.tex), pipeline_figure.py, plot_training.py (from
extract_training_series.py -> benchmark/data/training_series.csv), make_figures.py (result figs per
scored system). SCHEME=fullribs (Dataset813, 42 fg classes, every rib named per side) added 2026-09-08;
prep job 40164953; folds to submit after unpack (slurm/unpack_dataset.sh) when GPUs free.

**Why:** the NeurIPS/CNS claim needs the count and the junction Dice of every public system on the
same LSTV-stratified records. **How to apply:** run order in `benchmark/README.md`; results in
`~/bench/*/score/report.txt`; `python benchmark/collect.py --bench ~/bench --out ~/bench/comparison.md`.
See [[lstv-oneshot-training-run]], [[grid-access]].
