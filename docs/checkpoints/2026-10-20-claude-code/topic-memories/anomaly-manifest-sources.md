---
name: anomaly-manifest-sources
description: "Where every anomalous spine lives (749 across 3 tiers), why the count was once 34/16/2, and the files that must be read -- master flag table, BUU L4L6 sheet, pseudolabel ann dirs"
metadata: 
  node_type: memory
  type: project
  originSessionId: e44eca96-f48c-494d-ba1f-7dae68bdf06d
  modified: 2026-09-17T18:55:34.407Z
---

Built 2026-09-17 by `tools/anomaly_manifest.py` -> `~/model_night/anomaly_manifest/{anomaly_manifest.csv,
spine_classes.json, summary.json}`. 749 anomalous spines: tier A certain 355 (VerSe 163, BUU 144 real film,
CTSP 48); tier B pseudolabel 211 (VinDr 209, LAT236 2 -- ALL on frames without the junction, so unconfirmable);
tier C FluoroCap captions 183. Four-class over all 1,113 CT spines: 902 ordinary / 98 LS-only / 47 TL-only /
66 both.

**Why the count was once 34/16/2:** only `~/data/CTSpinoPelvic1K/manifest.json` (802 abdominopelvic CTs,
can't see upper ribs) was read. The master is `~/lstv_flag/lstv_flag_labels_v2.csv` -- 1,113 spines, both
flags from voxels, cohort column. VerSe alone: both=64. Co-occurrence OR VerSe 4.30 [2.59, 7.14], CTSP 4.00
[1.00, 16.03]; pooled 12.8 is Simpson's paradox -- never quote it.

**Files that are easy to miss:** BUU anomaly labels are in
`~/spine-detector/data/raw/buu_full/BUU-LSPINEv1/KIOM2022_dataset_report.xlsx` sheet `L4L6` (129 L4, 15 L6)
plus `Pixel Spacing` (0.175 mm) and `Pos_AP/Pos_LA` corner keypoints -- NOT in `XRSpinoPelvic1K/.../Dataset
Report.xlsx` (that's a motion-class report). Pseudolabels are per-film JSON under `~/{vindr,nhanes,
lateral236}_pseudo/ann/` with `spine_config`, `config_posterior`, `levels`, `image_size`.
`~/model_night/anomaly_cooccurrence_labels.json` (voxel recount) processed ONE case and is worthless.

**How to apply:** `spine_classes.json` has `per_case` keyed by every id spelling the render banks use
(`0001`, `ctsp_0001`, `CTSP_COLONOG_1`, `gl279`, `CTSP_VERSE_gl279`); `eval_fov_separability.py` and
`eval_global_anomaly_signature.py` read it via `--classes`. A run started before `per_case` existed
silently fell back to the 802 manifest -- check the log line "per-case classes from:". NHANES: 8,840
cervical + 7,394 LUMBAR films (L*.tiff, image L1-S1); zero flags is a DETECTOR failure -- the body detector
boxes the sacrum on 72/7,394 (1.8%) so p_variant never moves (an earlier note here said "cervical, not
broken"; that was wrong). Tier-B `junction_in_frame` must be read from the FULL decode (pseudolabel script
demotes exact names at/below the junction when it flags -- reading the exact tier alone made 65/65 vs
0/1,127 a tautology; full decode: 86% of variant calls contain a sacrum). Related:
[[feasibility-claims-measured]], [[lstv-data-landscape]], [[versefusion-t13-flag-wrong]].
