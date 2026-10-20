---
name: spine-data-review-and-ts-bench
description: "2026-09-19 workstreams -- TotalSegmentator bench (~/ts_drr, 1170 held-out CTs; v3 zip downloading), SPINEPS+VERIDAH over TS+VerSe (job 40384988 -> ~/bench_ts) to find L6/T13, and the PRISMA-ScR scoping review of public spine CT/X-ray datasets in spinesurg-ct-nnunet/spine_data_review/"
metadata: 
  node_type: memory
  type: project
  originSessionId: f1bdbd78-151f-470b-b703-dd9af9b3fecc
  modified: 2026-09-19T17:55:57.580Z
---

**TotalSegmentator as a held-out render bench.** `~/data/TotalSegmentator` (v2.0.1, 1228 CTs, 1.5 mm iso,
RAS) was on the grid unused; `tools/ts_to_drr.py` rendered 1170 (`~/ts_drr`; 58 skipped: no vertebra
labelled or stack gap/disorder = the v2 label mix-ups). None of its ids is in `allspine_v3_fov96_ctx`.
570 have a sacrum, 219 a C2, 44 both. Ordinary-spine truth only (no L6/T13 class). v3.0.0 (1939 CTs,
+291 paediatric, mix-ups fixed; Zenodo 22688904, 37 GB) downloads to `~/data/TotalSegmentator_v3/`;
when it lands: unzip, re-render to `~/ts_drr_v3`, diff v2 vs v3 labels on the 1228 common ids (that
diff is a check on the bench's truth), separate paediatric by `meta.csv` age. Sweep arms:
`sweep_v3/ts/*` (slurm/sweep_v3.sh tail).

**SPINEPS+VERIDAH over TS and VerSe** (`slurm/spineps_ts_verse.sh`, job 40384988, 12 shards, ->
`~/bench_ts/spineps/native/<case>_seg-vert_msk.nii.gz` + `_ctd.json`, VerSe ids, L6=25, T13=28;
cases `~/bench_ts/cases.csv`, 1228 TS + 374 VerSe). Purpose: VERIDAH is the one CT labeller that can
name L6/T13; score its variant calls on VerSe's expert truth FIRST, then read them on TS where the only
comparison is TS's ordinary-alphabet labels. Runner is `benchmark/run_spineps_cases.py`; staging under
/dev/shm (not /tmp).

**Scoping review** (user request 2026-09-19): predefined PRISMA-ScR protocol, programmatic dated
quotable searches over every FluoroCap literature route + data repositories, availability probed by
code (download / registration / DUA / request / unavailable), quality rubric (0-20), pooled statistics
(random-effects logit prevalence of L6/T13/LSTV across datasets reporting counts, I^2), manuscript on
PRISMA-ScR headings, download recipe second. Lives in `spinesurg-ct-nnunet/spine_data_review/` (self-
contained; venv `~/sdr_venv` in WSL; credentials from `~/.fluorocap/credentials.env`, never printed;
NCBI/S2/Springer keys live, Elsevier not entitled off-campus, no Kaggle token anywhere). Built by
workflow `spine-data-review-build` (run wf_04a13df2-fe8). No data in git. Next after the build: run the
searches from WSL, screen with recorded decisions, chart datasets (agents + adversarial verify), stats,
manuscript, recipe, then run the recipe on the grid (check quota first; `df` on /wsu misreports).

**CONTINUANCE (2026-09-19 17:00):** read `spinesurg-ct-nnunet/docs/CONTINUANCE_2026-09-19.md` FIRST -- it lists every running job, the four pre-search protocol amendments (ribs in scope; field-of-view tier for CT AND X-ray; projection stratification lateral/AP; storage fields + 'actions for Greg' checklist), and the order of the remaining steps. spine_data_review/ is NOT yet committed. Kaggle token in ~/.fluorocap/credentials.env (KAGGLE_API_TOKEN) and in the chat transcript -- rotate after the RSNA fetch. RibFrac kept (thoracic CT + rib-count variants), not for a sweep rib reader (oracle = nil).

**Also asked:** all CT-spine and X-ray-spine sets, with and without annotations, on the grid -- the
recipe is how that gets answered; whole-spine radiographs and thoracic images are the scarce, precious
class for frame stitching. See [[sweep-map-replaces-registration]], [[drr-row-spacing-defect]],
[[fluorocap-dataset]], [[competitor-benchmark]].
