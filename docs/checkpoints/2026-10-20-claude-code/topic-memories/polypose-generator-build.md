---
name: polypose-generator-build-2026-09-23
description: "Where the PolyPose forward generator lives, how it runs on the grid, and six traps the first real CT exposed (measurement path, S1 corridor, stale ROM CSV, rigid inverse, cupy bool, FOV)"
metadata:
  node_type: memory
  type: project
  originSessionId: f1bdbd78-151f-470b-b703-dd9af9b3fecc
  modified: 2026-09-23T23:16:12.979Z
---

Generator = `tools/polypose_sample.py generate|finalize|head` + `tools/polypose_warp.py` (spinesurg-ct-nnunet, L6_Class,
commit 1f4418f, never pushed). Validation chain: `slurm/polypose_validate_submit.sh` (gen -> fin -> render -> collect),
banks under `/rs/rs_grp_oschome/go2432/data/polypose/validation/bank_{gravity,invdf1}`; report tool
`tools/polypose/validation_report.py`, results to `SchwingNet/results/polypose/VALIDATION.{json,md}`.

**Why:** Greg's 2026-09-23 decision (PolyPose within Panjabi + LSTV ranges, global compensation, fused = zero motion).

**How to apply / traps already paid for:**
- The checker's `measure()` must be the cohort path (`tools/polypose/measure_sagittal.measure_image`, canonical RAS,
  release plate fits). The old ostk-primitive path read PI 3.6 / LL -8.9 on PIR case 0874 (truth 53 / 54).
- The release S1 plate is isolated in the LOWEST LUMBAR footprint: a moved L5 tilts it ~3 deg with the sacrum fixed.
  Pairs use the SOURCE L5 as corridor (`s1_corridor_reference`).
- diffdrr `RigidTransform.inverse()` is a RIGID inverse; wrong for voxel affines (spacing, PIR). Use a true matrix
  inverse. `verify_equivalence` (PolyRigid class on a 64^3 crop) catches it: gate at 1e-3 voxel.
- cupy 13.6 cannot take a CUDA *bool* torch tensor (falls back to __array__): pass uint8.
- Grid data files can go stale silently: the ROM CSV on the grid predated commit 1facf60. sha-compare EVERY synced
  file with the committed blob (local checkout is CRLF; strip CR on the grid).
- gvohp nodes = H200 NVL 143 GB; galhp = L40S 46 GB; GPU queues are often full of other workflows' arrays -> the
  generator has a CPU path (`--device cpu`, scipy EDT/spline), ~10 min/output vs ~3 min on L40S.
- VerSe rare CTs have no pelvis (no PI) and CTSP has zero T13 labels: no real T13 source with PI exists.
- SPINEPS body masks carry VERIDAH names that disagree with release ids on transitional spines (0376): re-key by overlap.
