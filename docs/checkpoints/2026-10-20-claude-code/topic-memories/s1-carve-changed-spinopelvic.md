---
name: s1-carve-changed-spinopelvic
description: "The carved S1 (id 29) was unreliable and is GONE as of v11 (2026-09-16) -- merged back into sacrum 26; what it taught about estimators reaching for the sacrum, and the checks that must be retired with it"
metadata:
  node_type: memory
  type: project
  originSessionId: e44eca96-f48c-494d-ba1f-7dae68bdf06d
  modified: 2026-09-16T13:20:29.934Z
---

**v11 retires the carved S1.** Through v10 id 29 held an S1 cut off the top of the sacrum on
an automatic S1/S2 boundary estimate. Measured on all 802 records it was unreliable: median
craniocaudal extent 57.6 mm where a real first sacral segment is near 30, only 26% in a
defensible range, and on 222 records the plane took more than half the sacrum -- sometimes
running nearly parallel to the sacral long axis and shaving the ventral cortex, so the
retained SACRUM lost its anterior wall. **Rendering one record showed this; no summary
statistic did.** `scripts/merge_s1_into_sacrum.py` folded 29 into 26; 155,093,558 voxels
returned to the sacrum on 801 of 802 records (1000 never had an S1). Nothing else moved,
verified two ways.

**The end-plate is now fitted to the whole sacrum**, isolated by the lowest lumbar body's
footprint (a slab under the sacral apex is WRONG -- the apex *is* the promontory, so such a
slab keeps the steep anterior lip and discards the plate). Release means PI 52.1 / SS 36.6 /
PT 15.5 on n=756, against Veilleux 52.1 / 36.5 / 15.6.

**The 60 deg plate gate is still live and still needed** -- it fires on **44** records (43 on
tilt, 1 on a posteriorly leaning normal), down from 239 under the carve. 802 - 44 - 2 = 756.
A table caption once said 14; that number was never checked against the CSV.

**RETIRE THE CHECKS THAT TEST A WITHDRAWN LABEL.** `select_anchor_cases.py` gated Figure 2's
case picks on whether the carve was plausible. After the withdrawal it should have been dead --
but every label tree on disk still had 29, so it went on firing, rejected 0428 as "S1 is 65%
of the sacrum", and silently swapped 0172 into panel (b) while the caption still named 0428.
A check on a withdrawn label is not inert; it is a check nobody is reading.

**What the carve taught, still true:** three estimators reached for the sacrum and switched
branch depending on whether S1 was present -- pelvic incidence (the fit latching onto the
near-vertical promontory face, normal z 0.03-0.44), L5-S1 disc height (lost 174 records
because the sampling column sat at the median of pooled voxels; fixed by using their
overlap), and the pelvic inlet. `level_gradients.csv` was and is bit-for-bit identical
across all of it: vertebrae and canal never depended on the sacrum.

**How to apply:** anything touching sacrum, the lumbosacral disc or the pelvis must be
computed from v11. Anything purely vertebral is unchanged. `case` ids are zero-padded
("0001") in the release and unpadded ("1") in old CSVs -- `zfill(4)` before diffing.
See [[scheme-bone-hardware-only]] and [[zenodo-deposit]].
