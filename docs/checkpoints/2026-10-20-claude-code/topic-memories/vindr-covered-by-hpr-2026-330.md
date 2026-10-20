---
name: vindr-covered-by-hpr-2026-330
description: "VinDr-SpineXR is covered by WSU IRB HPR 2026-330 (29 Sep 2026, supplement to 2026-269) -- never call it gated or \"outside the IRB determination\"; the spine-program handoff lines saying \"pending\" are stale"
metadata:
  node_type: memory
  type: project
  originSessionId: 0599380b-0d32-4e19-b5be-65bdd1017566
  modified: 2026-10-20T22:21:49.127Z
---

HPR 2026-269 (2 Sep 2026) covers public datasets downloadable without an agreement; VinDr (PhysioNet credentialed DUA)
sat outside it until the HPR tool for VinDr (filled 2026-09-25) produced **HPR 2026-330, notice 29 Sep 2026**:
"Secondary Analysis of a De-Identified Radiograph Dataset (VinDr-SpineXR) Obtained Under the PhysioNet Restricted
Health Data Use Agreement -- supplement to HPR Determination 2026-269", not human participant research. Signed notice:
`Desktop\CTSpinoPelvic1K-1\2026 330 Schwing IRB Not HPR Determination 9.29.26.pdf` (carries contact details; never in a
repo). Data platform recorded it 2026-10-10 (spinesurg-ct-nnunet 65fb454).

**Stale copies still saying "pending" / "outside 2026-269" (as of 2026-10-20, not fixed):** spine-program
01_carm_level_detection/docs/handoff/DATASET_USAGE.md (lines 30, 204, 223), its twin under 02_transitional_naming_truth,
01_carm_level_detection/CLAUDE.md line 144 ("the VinDr determination number is not recorded"), and
spinesurg-ct-nnunet HANDOFF/DATASET_USAGE.md. A SchwingNet record built from them was wrong (fixed in SchwingNet PR #27).

On the grid: complete at `/rs/rs_grp_oschome/go2432/data/vindr_spinexr/raw/vindr/1.0.0` (8,389 train + 2,077 test DICOM).
Training use: 2,632 crops in the C-ArmLSpine fold models; v8/v9 level banks left it out "for comparability" (no
criterion); implant boxes trained yolo_hw.

**Why:** Greg 2026-10-14: permission and DUAs for all data; never raise IRB scope or D1 to drop a result.

**How to apply:** treat VinDr as held and covered; cite HPR 2026-330 if a document needs the basis.

Related: [[schwingnet-repo-and-registry]], [[data-platform-migration-2026-10]].
