---
name: detection-is-the-binding-constraint
description: "Vertebra counting fails on detection, not linking -- 60 points vs 11-28 -- and renders alone cannot train the detector"
metadata: 
  node_type: memory
  type: project
  originSessionId: f1bdbd78-151f-470b-b703-dd9af9b3fecc
  modified: 2026-09-20T20:28:38.407Z
---

Measured 2026-09-20 on 801 abdominopelvic spines, same corpus/protocol/seed, changing only the box
source. Count exactness: boxes GIVEN 99.74 %, detector's boxes 39.52 % (clean render frames); under a
physics frame model 71.73 % and 21.50 %. **Detection costs ~60 points where realistic physics costs 28
at the published step and 11 at a short one.** Do not spend effort on linking before detection.

Two things that follow and were measured, not argued:

- **A detector trained on renders alone does not transfer.** `anchor_det_v1` (6,650 DRRs, zero real
  images) finds 71.67 % of bodies on real radiographs at conf 0.05, against 99.14 % for the
  film-trained detector on the same frames and 93.48 % for itself on renders -- so it is the weaker
  detector *before* domain shift and loses 22 more crossing to real anatomy. Pre-registered floor was
  0.80. It also emits 1.52 duplicate boxes per body (film detector: 0.069), a fault in its own domain.
- **Detector confidence 0.25 is miscalibrated for every image class here.** 0.05 is worth ten points on
  clean film (29.06 -> 39.52) and eighteenfold the reach under physics (255 -> 4,702 walks).

Full record, reproducible with `make physics`: `docs/HANDOFF_PHYSICS.md` in spinesurg-ct-nnunet
(branch L6_Class). See [[fluorocap-is-reproductions-not-fluoroscopy]] for why the obvious fix -- annotate
real fluoroscopy -- is a test-set play rather than a training-set one.
