---
name: label-scheme-v4-vs-ostk
description: Two label schemes are live; ostk now DETECTS which one a volume uses via ostk.labels.labels_for() -- never import a fixed map
metadata: 
  node_type: memory
  type: project
  originSessionId: e44eca96-f48c-494d-ba1f-7dae68bdf06d
  modified: 2026-09-10T16:14:22.357Z
---

Two incompatible name->id maps are both live on disk, and mixing them **does not raise** --
it silently returns the wrong structure.

- **v10 / released dataset (VerSe-native)**: C1-C7 = 1-7, T1-T12 = 8-19, L1-L6 = 20-25,
  sacrum = 26, coccyx = 27, T13 = 28, S1 = 29, hips = 30/31, femurs = 32/33, ribs 34-59,
  lumbar ribs 60/61, hardware 62-68. Canonical in `CTSpinoPelvic1K/scripts/label_scheme.py`
  and the release's own `dataset_labels.json`.
- **legacy (the old ostk map, and the PACS demo cases)**: L1 = 1, S1 = 7, sacrum = 8,
  hips = 9/10, femurs = 11/12, T1-T13 = 13-25, ribs from 26.

**FIXED 2026-09-10 -- `ostk.labels` now detects instead of assuming.** `labels_for(volume)`
returns the map for that volume, deciding on pelvis voxel mass under each hypothesis; it
**raises** `SchemeError` when the two are close rather than guessing, and returns the
default for an empty volume (nothing to get wrong). `LABELS_V4` and `LABELS_V10` are both
exported; `lid(name, scheme=...)` survives for callers that know what they hold. Detection is
threaded through metrics, spine, cobb, drr, metrics2d, surgery and the `morph` CLI -- once
per case, not per primitive. Regression tests are in `tests/test_labels.py`.

**What it cost before the fix:** pelvic incidence was computed for the whole 802-record
release against the legacy map, so "S1" read id 7 (= C7) and "femur_left" id 11 (= T4).
Every case came back flagged `low_voxels:S1` while S1 sat there with 200,000 voxels, and it
read as a segmentation problem rather than a lookup one. Earlier the same trap hit
`xrsp/build_dataset.py` (2026-08-04) and `femoral_head_center` on v4 data (PT -15.8 deg, PI
identity out by 31.5 deg, while SS and LL looked fine).

**How to apply:** never import a fixed label map. Call `ostk.labels.labels_for(volume)` (or
`xrsp.labels.labels_for`) and pass the result into anything that takes a structure name.
Note `level_morphometry(label, affine, level_id)` takes an INT and is unaffected. See
[[splits-origin-and-v3-resplit]], [[thoracic-gt-fov-limited]], [[s1-carve-changed-spinopelvic]].
