---
name: thoracic-gt-fov-limited
description: "v3 thoracic vertebra GT is FOV-limited (only the lower thoracic that's in view, typically ~T8 down, NOT up to T1)"
metadata: 
  node_type: memory
  type: project
  originSessionId: b7bbe4e5-4a8a-4821-9d22-fe7e8fb39a74
---

The v3 GT thoracic column (label scheme reserves T1-T13 = ids 13-25), but **per
case only the thoracic vertebrae inside the spinopelvic field of view are
actually labelled -- usually down from about T8, not up to T1.** Many cases have
only ~3 thoracic vertebrae labelled.

**Why it matters:** projects needing T1 -- the **T1 Pelvic Angle (TPA)** and
classic **Sagittal Vertical Axis (SVA)** (C7/T1 plumb line) -- are computable only
on the subset of cases whose FOV reaches T1. Don't claim "T1 is labelled" as a
general dataset feature.

**How to apply:** when describing v3 thoracic GT, say "FOV-visible thoracic
(typically ~T8 down)", not "T1-T13". The rib numbering only emits ribs backed by a
GT thoracic vertebra, so caudal ribs whose vertebra is out of FOV are dropped by
design. Related: [[splits-origin-and-v3-resplit]].
