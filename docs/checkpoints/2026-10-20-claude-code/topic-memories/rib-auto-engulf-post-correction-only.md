---
name: rib-auto-engulf-post-correction-only
description: "Rib halo/speckle auto-engulf cleanup must run ONLY after student correction, never on pre-student pseudolabels"
metadata: 
  node_type: memory
  type: project
  originSessionId: 436e5c70-681e-4f38-aab2-30dfa25af7b5
---

Rib masks have **halo / drift mislabels**: within one physical rib, the interior (or the medial
portion incident on the vertebra) is the correct rib class, but surface speckles and the
lateral/anterior tail flip to a WRONG rib class. The desired cleanup is an **auto-engulf**: the
dominant/correct rib class absorbs (engulfs) the minority wrong-class voxels within that rib.

**HARD CONSTRAINT (Greg, emphatic 2026-07-04): NEVER run the auto-engulf BEFORE student
annotation correction.** The pseudolabel can be the WRONG class exactly at the vertebra-incident
(medial/head) portion of the rib; a majority-vote engulf on the raw pseudolabel would cement that
error and spread the wrong class. Students must fix the medial/head class first; the engulf is a
**post-correction finalization** step only.

**Where it goes:** the post-adjudication finalization -- `scripts/review/reduce_to_v5.py` (the fuse
step), NOT `scripts/build_v4_ribs.py` (confirmed 2026-07-04 that the pre-student v4 build does NO
engulf/majority cleanup -- keep it that way). See [[rib-approach-ts-trust]], [[splits-origin-and-v3-resplit]].

**Related FOV rule** (same conversation): many lower ribs enter the scan only antero-laterally with
their thoracic vertebra OUT of the FOV, so the rib-anchor QC test skips a rib unless its T-N vertebra
has >= MIN_VERT_VOX (1000) voxels -- a stray ~14-voxel speckle of T11 must not anchor (or falsely
flag) a correct rib. See [[thoracic-gt-fov-limited]].
