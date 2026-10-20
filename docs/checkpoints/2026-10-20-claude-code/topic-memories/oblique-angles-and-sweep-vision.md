---
name: oblique-angles-and-sweep-vision
description: "Greg 2026-09-23 -- detector must work at slight/any angle (table tilt, patient roll): every device pose pool gets a synthetic AP->lateral arc (physics needs no real frame there); case134's 302-frame CBCT spin is the real oblique validation; the rotational-sweep->patient-specific 3-D / digital-fiducial / AR vision is a PREVIEW paragraph only"
metadata: 
  node_type: memory
  type: project
  originSessionId: f1bdbd78-151f-470b-b703-dd9af9b3fecc
  modified: 2026-09-23T05:41:27.181Z
---

**The practical worry:** a patient is not flat on the table (tilt, Trendelenburg, roll), so the detector must find
vertebral bodies at slight and arbitrary angles, not just AP and lateral. Found 2026-09-23: `devcorpus_build.py
poses` takes each device's pool from its REAL frames, so the Surgio pool was AP/LAT only (0/90). Decision: synthesise
a continuous arc (lat -90...+90, tilt +/-15, roll +/-10) for every device -- the physics parameterisation depends on real
frames only for validating the transfer to a scanner, never for the geometry. Workflow `oblique-arc-coverage`:
`poses --arc`, pose-pool audit, recall-vs-angle on held-out renders with the existing arms, and the **case134 sweep**
(302 real XA projections of a CBCT spin from the Surgio, the only real oblique intraoperative frames) exported as
`realxray/carmlspine_sweep` (one cluster; exposure mode "cbct_spin", kept as its own row). Results under
`SchwingNet/results/arc/`.

**The vision (preview only, Greg's words paraphrased):** rotate the C-arm and take the continuous video -> the
network sees the bones exactly as they lie on the table now (no registration back to a segmentation in a different
posture); place *digital fiducials* -- learned 3-D reference points that track rotation/translation/torque of the
spine so the registration stays aligned; extend to AR/VR so MIS becomes "open" with an edge GPU, a C-arm and the
networks. Greg: *"I don't think I should do more than preview this as a future direction and just state the data
exists for exploring it."* Honest framing for the paper: this is the CBCT-navigation paradigm without the tracker;
the data that would test it (case134's spin + CBCT) exists in the release.

**How to apply:** the final corpus (A20) renders every device with the arc; report recall vs angle as a curve (render
side) and the case134 curve (real side, n = 1); one Discussion paragraph, no claims. Related:
[[data-directives-2026-09-23]], [[k-devices-one-network]], [[lstv-tltv-detection-goal]].
