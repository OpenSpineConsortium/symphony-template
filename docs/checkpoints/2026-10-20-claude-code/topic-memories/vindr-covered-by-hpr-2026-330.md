---
name: vindr-covered-by-hpr-2026-330
description: "VinDr-SpineXR is covered by WSU IRB HPR 2026-330 (29 Sep 2026, supplement to 2026-269) -- never call it gated or \"outside the IRB determination\"; spine-program's stale \"pending\" lines were corrected in PR #221 (2026-10-20); only the manuscript token remains"
metadata:
  node_type: memory
  type: project
  originSessionId: 0599380b-0d32-4e19-b5be-65bdd1017566
  modified: 2026-10-21T01:59:39.015Z
---

HPR 2026-269 (2 Sep 2026) covers public datasets downloadable without an agreement; VinDr (PhysioNet credentialed DUA)
sat outside it until the HPR tool for VinDr (filled 2026-09-25) produced **HPR 2026-330, notice 29 Sep 2026**:
"Secondary Analysis of a De-Identified Radiograph Dataset (VinDr-SpineXR) Obtained Under the PhysioNet Restricted
Health Data Use Agreement -- supplement to HPR Determination 2026-269", not human participant research. Signed notice:
`Desktop\CTSpinoPelvic1K-1\2026 330 Schwing IRB Not HPR Determination 9.29.26.pdf` (carries contact details; never in a
repo). Data platform recorded it 2026-10-10 (spinesurg-ct-nnunet 65fb454).

**Stale copies, FIXED 2026-10-20:** spine-program PR #221 (issue #220, merged) corrected every handoff copy
(DATASET_USAGE, MANUSCRIPTS, README, the working notes topic1/3/4, EXTRACTS_11), OPEN_QUESTIONS row A5, 01 CLAUDE.md and
README, the 07 and 99 TODOs, one clause of the AIDaS evidence sheet, and the data platform copy: 168 lines in 65 files plus
the copy. spinesurg-ct-nnunet bf1432f fixed the two VinDr README cards (its sources.json had the number since 65fb454).
STILL STALE and untouched: spinesurg-ct-nnunet HANDOFF/DATASET_USAGE.md. A SchwingNet registry record built from the old
handoff was wrong (fixed in SchwingNet PR #27, merged 2026-10-20). The ONLY remaining placeholder is the manuscript token
PENDING{G0} in spinesurg-ct-nnunet SchwingNet/main.tex line 137, which takes "HPR 2026-330, 29 September 2026".

On the grid: complete at `/rs/rs_grp_oschome/go2432/data/vindr_spinexr/raw/vindr/1.0.0` (8,389 train + 2,077 test DICOM).
Training use: 2,632 crops in the C-ArmLSpine fold models; v8/v9 level banks left it out "for comparability" (no
criterion); implant boxes trained yolo_hw.

**Why:** Greg 2026-10-14: permission and DUAs for all data; never raise IRB scope or D1 to drop a result. Greg 2026-10-20:
"get this bulletproof and unambiguously transparent and correct so I can have no doubt I'm doing stuff correctly".

**How to apply:** treat VinDr as held and covered; cite HPR 2026-330 if a document needs the basis; when a document
says "pending", it predates 29 Sep 2026 and should be corrected, not repeated.

Related: [[schwingnet-repo-and-registry]], [[data-platform-migration-2026-10]], [[aasce-two-copies-on-ceph]].
