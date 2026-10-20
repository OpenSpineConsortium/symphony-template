---
name: carmlspine-level-experiment
description: "C-ArmLSpine (real intraop C-arm AP+LAT + CBCT, 148 cases) is THE project since 2026-09-21 18:20; reading traps, pose convention, pipeline and where it lives"
metadata: 
  node_type: memory
  type: project
  originSessionId: f1bdbd78-151f-470b-b703-dd9af9b3fecc
  modified: 2026-09-22T02:00:52.736Z
---

Greg, 2026-09-21: "I have actual fluoro spine data" -- run the film cropping + detector level-ID experiment on
C-ArmLSpine real OR frames at limited FOV (thoracic where it reaches). COBRA/DeepFluoro/Geneva/LUMOS are back-burner;
use them only for a fluoroscopic pelvis C-ArmLSpine lacks (it has the sacrum in AP and LAT).

**Why:** the only real intraoperative C-arm set with true laterals and a same-session CBCT (Zenodo 22768651, CC BY
4.0; PRSCS-Net, MedIA 97:103283 -- NOT the PG-Net point-cloud PDF Greg attached, which is unrelated).

**How to apply:** start at the "C-ArmLSpine is the project now" section of
`spinesurg-ct-nnunet/docs/HANDOFF_2026-09-21_PM.md`. Traps that cost time: every CBCT slice has its own series UID
(read with `tools/carmlspine_io.read_cbct`, never GDCM series grouping); no FrameOfReferenceUID anywhere; DICOM
PixelSpacing 1.0 is a placeholder (true pitch 0.150 mm: iRay Jupi1212X, 307.2 mm panel; the private "30cm" tag is
nominal); case134's frames sit inside CBCT/; case118 is AP + -58 deg oblique; a third of cases name frames by UID
(sort by PositionerPrimaryAngle); the SPINEPS runner used to harvest the RAW mask with no level names (fixed; see
[[spine-data-review-and-ts-bench]]). Pose = header geometry (SID 1140, SOD 745) + edge-only registration
(`tools/drr_register.py`; intensity NCC is biased) under one device convention. Thoracic reach ~T12/T11 only.
Related: [[mixed-length-head-and-sota]], [[detection-is-the-binding-constraint]], [[no-jobs-on-login-node]].

**Results 2026-09-21 (see the handoff section "C-ArmLSpine level results"):** zero-shot lateral whole frame 96.3 %
exact over 148 cases, AP 37.9 % (one-level cranial shift); mixed fine-tune on 28 test cases LAT/AP 94.6/95.2 whole,
87.4/86.4 at 3 vertebrae; real-only fine-tune lost laterals and forgot more. Lateral poses must be BOUNDED around the
header geometry (registration jumps half a vertebra on a periodic spine); verify pose with detector boxes
(tools/carmlspine_pose_qc.py), not with the registration score. Render calls with truth
(tools/carmlspine_render_calls.py) before believing a shift.

**Trap recorded 2026-09-22:** a detector fine-tuned on real frames of a device and scored on that device's held-out
specimen is a SAME-DEVICE number; only the device-held-out arms (rx_lodo_*) and Geneva (never trained) answer "out
of the box". The render-only (manuscript) DeepFluoro sacrum number stays 76.9 %. Adversarial program 2026-09-22:
docs/HANDOFF_2026-09-21_PM.md section "OR-readiness adversarial program"; outputs /rs/.../data/or_ready/<track>/.

