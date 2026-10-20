---
name: ostk-canal-closing-regression
description: "OpenSpineToolkit commit 1b7005c (2026-09-10, 2 mm ring closing before fill_holes in canal_mask) inflates posterior body height / end-plate depth by 10-17 mm on ~1 in 7 vertebrae with no gate firing; the grid ~/OpenSpineToolkit copy carries it; canal_mask min_vox=20 also lets 3 mm 'canals' through -- fix in ostk, test against the 0097 release rows"
metadata:
  node_type: memory
  type: project
  originSessionId: f1bdbd78-151f-470b-b703-dd9af9b3fecc
  modified: 2026-09-25T05:16:38.659Z
---

Found 2026-09-25 by rendering the body cut (spinesurg-ct-nnunet/SchwingNet/results/reader_e/diag/*.png): after
ostk 1b7005c, in the 2-3 axial sections just below the pedicles the ring closing bridges the laminae, a few-voxel
hole there joins the canal's 3-D component, `body_mask_by_canal` takes that section's "anterior canal edge" as the
wall (14-15 mm posterior of the true wall) and every lower section inherits it. Pedicle roots and inferior
articular processes become "body"; the inferior posterior corner lands on the articular process. On CTSP 0097:
T12 VBHp 38.4 vs 28.9, EPDl 52.0 vs 34.8; VBHa, SA, SP, IA and plate_rms unchanged, so nothing raised. The release
CSV (`morphometrics/ostk_level_morphometry.csv`, commit 90a27a7, earlier the same day) predates the closing and is
right. Second defect: `canal_mask` `min_vox = 20` voxels (6.5 mm3) admits a split instance's closed voxels as a
canal -> 16 % of chords below the 11.07 mm living floor vs 2.6 % published.

**Why:** the docstring claims the closing is "used only to find the hole"; it is not -- the extra hole sections
change which sections carry a wall. This is the project's failure mode: a plausible number from the wrong
surface, caught only by an outside reference and a render.

**How to apply:** do not trust ostk `level_morphometry` VBHp / EPD / EPWl computed after 2026-09-10 22:52 until
ostk is fixed (per-section hole area >= 18 mm2; wall only from sections whose hole reaches the canal's median
area; test = 0097 rows within 1 mm); refresh the grid `~/OpenSpineToolkit` rsync copy afterwards. Reader E
(`SchwingNet/tools/reader_e_features.py`) builds its own closed-ring column and uses ostk's body_mask only as a
recorded fallback. Related: [[paper-split-2026-09-24]], [[resume-2026-09-24]].
