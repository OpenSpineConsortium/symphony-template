---
name: xray-corner-detector-status
description: "spine-detector (grid ~/spine-detector, private GitHub OpenSpineConsortium/spine-detector): the radiograph corner-detector corpus and the detect_v1/v2 results as of 2026-09-08"
metadata:
  type: project
  originSessionId: e44eca96-f48c-494d-ba1f-7dae68bdf06d
  modified: 2026-09-08T06:04:26.354Z
---

Corpus (data/interim/manifest.parquet, rebuilt 2026-09-07): 33,943 vertebra instances on
5,401 films -- BUU-LSPINE 2000-pair subset 19,991, AASCE 8,069 (68 landmarks = 17 vertebrae
x 4 corners), NHANES 3,217, Mendeley 2,666; AP 18,061 / LAT 15,882. VinDr downloading under
its DUA (stays on the grid, never redistributed); CSXA (ScienceDB) needs a browser download;
BUU 3600 form pending; converters for VinDr/CSXA not written yet.

Detector: YOLO11m-pose, class-agnostic 4-corner boxes, imgsz 1024. Held-out eval set is
558 instances (NHANES 294, Mendeley 249, BUU 15) via `src.run_eval`.
- detect_v1: AP50 0.957, PCK@0.1 0.77.
- detect_v2 (120 ep, 2026-09-08): AP50 0.970, PCK@0.1 0.812, PCK@0.2 0.942; film 0.960/0.852,
  standing DR 0.970/0.767. Training-time val (535 films): box mAP50 0.991, pose mAP50 0.977.
  Weights: `runs/pose/runs/detect_v2/weights/best.pt` (ultralytics nests the task dir under
  --project); eval in `runs/detect_v2/eval/{metrics.json,report.txt,renders/}`.

**Why:** the radiograph arm of the NeurIPS manuscript and the real-time wrong-site X-ray
vision; Nishaan is downloading the real films that need annotation (XRSP1K DRRs need none).
**How to apply:** grid job scripts in slurm/ (`set -uo pipefail`, never `-e`: sourcing conda
returns non-zero and kills the job silently with empty logs); write scripts LF-only.
See [[grid-access]], [[lstv-oneshot-training-run]].
