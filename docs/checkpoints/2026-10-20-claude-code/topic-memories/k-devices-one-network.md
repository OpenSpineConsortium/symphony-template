---
name: k-devices-one-network
description: "Greg's direction 2026-09-22 -- treat each C-arm model as a low-dimensional domain, fit a parameter set per device, style whole-spine renders per device on the fly, train leave-one-device-out, test on the held-out device's REAL frames; the measured facts, and WHERE THE PIPELINE NOW LIVES (device_fit / device_style / devcorpus_build / devcorpus_train)"
metadata:
  node_type: memory
  type: project
  originSessionId: f1bdbd78-151f-470b-b703-dd9af9b3fecc
  modified: 2026-09-22T10:16:16.350Z
---

**The goal (Greg, 2026-09-22):** "learn to filter out inter-device noise and make a one-size-fits-all network" --
reduce the noise dimension to k = the number of C-arm models, gather every C-arm dataset of any anatomy (paired
CT + pose first), fit each device's formation parameters, build a corpus of synthetic whole spines under each
device's settings, train, and hold devices out.

**Measured facts that motivate it:** detectors fine-tuned on real frames of one device family collapse on others
(C-ArmLSpine-only: 1-2 % on COBRA/DeepFluoro; COBRA-held-out: 43 % sacrum near-AP), while the render-only detector
transfers (76.9 % DeepFluoro, 81 % COBRA near-AP). A same-device detector on COBRA learned a POSITION prior (98 %
sacrum hits on near-blank laterals; COBRA laterals are photon-starved, no bone). BUT real-frame detectors trained on
two devices DO transfer to a third on whole frames: C-ArmLSpine held out = 83.9 % sacrum, 90.6 % vertebrae under the
matched (outline) box convention (the 5.2 % in the first table was body vs outline boxes); on magnified 3-vertebra
crops only 36 % -- SCALE is a transfer lever of its own. See [[carmlspine-level-experiment]],
[[learned-formation-refuted-calibrate-instead]], [[drr-to-fluoro-levers]].

**Where the pipeline lives (spinesurg-ct-nnunet, branch L6_Class, all on the grid too):**
- `tools/device_fit.py` (+ `device_physics.py`, `slurm/device_fit.sh` CMD/DEVICE/EXTRA): pairs per device, the
  nine-term fit leave-one-group-out, term tests (+penumbra, +scatter~thickness, sigma_r fixed by physics), per-frame
  terms, Gaussian copula + AEC + coverage (quote `typicality_99`, not `joint`), physics defaults, border/penumbra,
  card `docs/devices/<device>.json` + `<device>.frames.csv` (written in the GRID repo copy -- rsync back), figures
  under `or_ready/devices/<device>/`. DEVICES: cios_fusion, surgio_b51_dr, surgio_b51_raw, elekta_xvi, bv_pulsera.
- `tools/device_style.py`: one styled frame = one copula draw through `device_fit.forward` at any pitch; `demo`
  (real | draws sheet) and `stats` (real-vs-styled distances vs a real-vs-real floor) = the unpaired-path validation.
- `tools/devcorpus_build.py` (`slurm/devcorpus.sh`): `poses` per device -> `render` once per geometry (142 TS
  whole spines, targets lumbar/sacral) -> `style` per noise device -> `lists` for design A (one geometry, all noise)
  or B (own geometries), held-out device excluded, real frames of training devices x2.
- `tools/devcorpus_train.py` (`slurm/devcorpus_train.sh` DESIGN/HELD): COCO-init YOLO11m at 1024, scored on every
  device's real test split, matched-convention re-score on C-ArmLSpine; `scores.json` under
  `~/spine-detector/runs/devcorpus/dc_<design>_held_<device>/`; marker `or_ready/devlodo/<design>_held_<dev>_DONE`.
- `tools/device_census.py` (`slurm/device_census.sh`): DICOM header + image census per device -> `docs/devices/census/`.

**Design decisions:** a device is a small DISTRIBUTION (fixed: detector, geometry, transfer curve, processing chain,
field; per exposure: kV/mA/pulse/auto-window sampled from its observed range). Render line integrals ONCE per
geometry family; style on the fly from the card -- no k copies of the geometry on disk. Mix real frames of the
training devices, upweighted. Randomise spine placement in the field or the detector learns layout. The display
stage is a small PARAMETRIC model (a learned filter lost to nine physical terms on DeepFluoro). Coverage = share of
held-out real frames whose fitted terms are typical under the sampler (Mahalanobis in copula normal scores).

**How to apply:** job ids and the state of the chain are in the handoff section "2026-09-22 07:40 EDT"; look at the
style demo sheet of the FULL card before trusting a styled corpus (the smoke card's draws sat ~10x the real-vs-real
floor); read `dc_*/scores.json` against the baselines (render-only 73 % sacrum on C-ArmLSpine; lodo real-frame
83.9 % / 90.6 %).
