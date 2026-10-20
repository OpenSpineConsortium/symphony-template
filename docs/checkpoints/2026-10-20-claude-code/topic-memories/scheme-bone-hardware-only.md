---
name: scheme-bone-hardware-only
description: "Label scheme is bone + hardware only, 0-68 with ONE hole at the retired 29 (was S1) from v11 (2026-09-16); thirteen ribs per side (34-46 L, 47-59 R; rib 13 = true rib of a T13, empty), lumbar ribs 60/61, hardware 62-68; T13 and lumbar rib are distinct phenotypes; v9 (58/59, 60-66) and v8 (74-82) ids are retired"
metadata:
  node_type: memory
  type: project
  originSessionId: e44eca96-f48c-494d-ba1f-7dae68bdf06d
  modified: 2026-09-16T13:20:08.444Z
---

CTSpinoPelvic1K label scheme (`scripts/label_scheme.py`, single source of truth), **v11**:
1-25 VerSe vertebrae (L6 = 25), 26 sacrum (entire), 27 coccyx, 28 T13 (VerSe ids, unused),
**29 retired and unused**, 30-31 hips, 32-33 femora, 34-46 rib_left_1..13,
47-59 rib_right_1..13, 60/61 lumbar ribs, 62 generic hardware, 63 cage, 64 screw/rod,
65 plate, 66 arthroplasty, 67 SI screw, 68 osteosynthesis. No sentinel. Rib 13 (46, 59) is
the true rib of a thirteenth thoracic vertebra, a phenotype DISTINCT from a lumbar rib
(rudimentary rib on a lumbar-type L1; Du Plessis 2018, Poolman 2023).

**29 IS A HOLE, NOT A FREE SLOT.** Through v10 it held an S1 carved off the top of the
sacrum. v11 dissolved it back into 26 (see [[s1-carve-changed-spinopelvic]]). It is retired
rather than renumbered because closing the gap by shifting 30-68 down one would rename the
hips, femora and all twenty-six ribs under ids that checkpoints, the benchmark, ostk and the
level tables are already keyed to. `label_scheme.verify()` asserts the id space is
`range(0, 69)` **minus 29** -- spelled out, so the check still catches a real gap.

`label_dict()` has **no `"S1"` key**: a map that still answered 29 would hand back an id no
voxel carries, and the caller would measure an empty mask and get a plausible zero. KeyError
is the right answer. **ostk still has `"S1": 29` in its v10 map and needs the same treatment**
-- its scheme detection is safe (it keys on hip/femur voxel mass, not on 29).

**Why:** Greg asked (2026-09-07) to close the 58-73 gap and drop the sentinel (v9), then to
add the thirteenth rib "consecutively after the twelfth rib in a logical place" (v10), which
shifted the right ribs by one and lumbar ribs/hardware by two. Then (2026-09-16) to promote
v11. Never claim a T13 and a lumbar rib are "the same object under two names"; he objected
strongly.

**How to apply:** anything that prints a rib, lumbar-rib or hardware id must use these
numbers, which v11 did not change. Never reissue 29. See [[zenodo-deposit]] and
[[label-scheme-v4-vs-ostk]].
