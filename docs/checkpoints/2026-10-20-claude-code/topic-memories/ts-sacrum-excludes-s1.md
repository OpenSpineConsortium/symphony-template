---
name: ts-sacrum-excludes-s1
description: "TotalSegmentator v2's `sacrum` mask EXCLUDES S1 (separate class vertebrae_S1, disjoint); the whole sacrum is the union -- checked on all 1,228 TS subjects 2026-09-21"
metadata: 
  node_type: memory
  type: project
  originSessionId: f1bdbd78-151f-470b-b703-dd9af9b3fecc
  modified: 2026-09-21T23:56:05.298Z
---

TotalSegmentator v2 ships `sacrum` and `vertebrae_S1` as separate, disjoint masks (every one of the 1,228 subjects of
the TS dataset has both; overlap 0 voxels; S1 = 8-23 % of the union). Anything that reads `sacrum.nii.gz` alone
starts the sacrum at S2 for the body, while the sacral mask's alae still reach within 1-3 slices of S1's top, so a
projected BOX shrinks only a little (IoU 0.89-0.92 against the union) but a plate/end-plate or a centroid read from
it is wrong: the pelvic-landmark build put the S1 end plate on the posterior arch until S1 was added.

**Why:** found by the pelvic-landmark agent 2026-09-21; the anchor-detector renders (tools/deepfluoro_anchor.py) and
the C-ArmLSpine/COBRA/DeepFluoro/Geneva exports all read `sacrum` alone. Box-level effect too small to move an
IoU >= 0.5 detection match, so the manuscript's sacrum recall stands; end-plate / PI / centroid work does not.

**How to apply:** always use `sacrum` UNION `vertebrae_S1` from TotalSegmentator (add vertebrae_S1 to any
--roi_subset). CTSpinoPelvic1K v11 (sacrum=26) already includes S1 (29 was dissolved into 26). See
[[carmlspine-level-experiment]], [[label-scheme-v4-vs-ostk]].
