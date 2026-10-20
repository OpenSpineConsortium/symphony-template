---
name: xr-benchmark-and-robustness-2026-09-13
description: "X-ray level-ID competitor benchmark (re-implemented paradigms on our films), physics augmentation tiers, oblique DRR expansion, recurrent head result; job ids and result paths on the grid (13 Sep 2026 afternoon)"
metadata: 
  node_type: memory
  type: project
  originSessionId: e44eca96-f48c-494d-ba1f-7dae68bdf06d
  modified: 2026-09-13T18:02:28.562Z
---

**Benchmark scope (fixed, user-agreed):** no public XR level labeller has weights (VertXNet,
BUU baseline, Neighbor 2024 whose committed code is stock CenterNet). Every competitor is a
re-implemented *mechanism* trained on our films, scored on the same 1,653 held-out films and
the same bands (1/3/5 vertebrae): level-as-class YOLO11m (tools/make_yolo_levels.py,
fov_xr_ladder.py; jobs 40215715-17), reference-and-count (VertXNet/LevelCheck rule, same
script), Multi-View sequence-loss identifier (tools/make_mv_bands.py, train_mv_idseg.py;
40215792-95), SpineCLUE-style message fusion (tools/message_fusion.py -> ~/bench/xr_fov/fusion.json),
recurrent-order BiGRU over n=1 embeddings = Huang/Uneri/Siewerdsen 2022 + Liao 2018 paradigm
(tools/recurrent_order.py -> ~/bench/xr_fov/recurrent.json), counting oracle. Neighbor 2024
CenterNet+neighbour heads still to implement. CT-crop ladder cancelled (user: only XR matters).

**Key result:** recurrent head over the n=1 model's embeddings beats the band models:
3 vert 98.7%, 5: 99.1%, 7: 99.4%, 9: 99.5% (lumbar 92-94%). This is the shipping head:
detector -> per-vertebra classifier -> BiGRU over the run. Fusion (SpineCLUE style): 98.2-98.4%.
+BUU arm: 98.9/99.4 at 3/5. SupCon: nothing. Dual-view AP-only on BUU: 90.4/94.4/95.6.
VinDr: 744 laterals pseudo-labelled (gate rejected 1,584, mostly "not contiguous").

**Robustness:** `--augment 2` (physics: oblique, magnification, exposure, polarity,
Poisson-Gaussian, blur, shutters, instruments, shading) and `--augment 3` (k=1.8, double pass,
erasing) in train_level_classifier.py; ctx_arm.sh hooks AUG/SUPCON/TAG/VIEW.
tools/make_oblique_drr.py (yaw/tilt poses, soft tissue), tools/robustness_eval.py (11 faults x
5 severities -> ~/bench/robust/*.json). Prior art: DeepDRR, SyntheX (domain randomisation),
Lunit photometric, CheXphoto/RoMIA benchmarks.
Jobs: launch_robust.sh 40215863-74 (aug2 all2, baseline robust, obl 4-pose -> all3 aug2);
launch_obnoxious.sh 40215891-900 (aug3 all2; obl2 8-pose +/-30/+/-15 -> extra4 -> all4 aug3 60 ep;
recurrent_all4; robust all4). Rib QC v4-vs-release: ~/tmp/rib_qc_stages.json (job 40215807).

**How to apply:** results land in ~/<arm>/runs/result_rung_*_aug{2,3}.json and
~/bench/{xr_fov,robust}/; fold into the report artifact and memory; the 0.99-at-3 target is
lumbar-bound -- VinDr/oblique data + recurrent head are the levers.
