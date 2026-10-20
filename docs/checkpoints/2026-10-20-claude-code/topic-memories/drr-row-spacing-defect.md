---
name: drr-row-spacing-defect
description: "make_drr_dataset wrote the A-P voxel size as the S-I row spacing (found 2026-09-19); VerSe \"140 mm\" C2 sweeps were ~600 mm frames, CTSP off 7.5% median / >1.2x on 172 of 801; every render sweep number before sweep_v3 is on the wrong field size"
metadata: 
  node_type: memory
  type: project
  originSessionId: f1bdbd78-151f-470b-b703-dd9af9b3fecc
  modified: 2026-09-19T17:00:10.709Z
---

`tools/make_drr_dataset.py` (spinesurg-ct-nnunet) wrote `as_closest_canonical(...).get_zooms()[1]` as
`mm_per_px_row_si_col_ap[0]`. Canonical is RAS, so index 1 is the anterior-posterior spacing; the DRR
rows run superior-inferior. `sweep_map.py` reads that field as px/mm and sizes the "9-inch" (140 mm)
field from it.

**What it did.** VerSe (0.29 mm in-plane, 1.25 mm slices): every ann said 0.29 mm/px, 140 mm became
481 rows on a 214-row image, and the C2 sweep was two whole-spine frames (2.33 "exposures"), not a
9-inch sweep; 74 of 374 spines off by >1.2x, 31 by >2x. CTSP: 7.5% at the median, >1.2x on 172 of
801, max 7.3x (5 mm slices). Real films carry no header spacing (`mm_per_px` None -> pitch-based
fallback) and are unaffected. The fallback from body pitch would have been right; the wrong header
value overrode it. Classic wrong-but-plausible: stations/spine 3.01 looked fine.

**Fix (commits 2026-09-19):** `pir_spacing(header, affine)` reads spacing through the same
`ornt_transform` the voxels go through -- using the INVERSE permutation (`argsort(tr[:,0])`); indexing
`tr[i][0]` directly is the identity on PIR input and wrong on LPS, which is how the first respace
wrote 0.29 again. `--respace` rewrites existing anns in place (pixels unchanged), original kept as
`mm_per_px_before_respace`. Both `~/verse_drr` and `~/ctsp_drr` respaced; `~/ts_drr` (TotalSegmentator,
1.5 mm iso RAS) unaffected.

**Consequence:** every render number in `sweep_holdout_v2`, `sweep_protocol`, `sweep_improve` and the
render arms of `sweep_fix` is superseded by `~/model_night/sweep_v3/<holdout|protocol|improve|fix|ts>/`
(`slurm/sweep_v3.sh`, job 40384843). The manuscript (`paper/rsnai/main.tex`), `tools/make_results_table.py`
and `docs/SWEEP_PROTOCOL.md` must be moved to sweep_v3 numbers. See [[sweep-map-replaces-registration]],
[[ct-volumes-are-pir-not-ras]].
