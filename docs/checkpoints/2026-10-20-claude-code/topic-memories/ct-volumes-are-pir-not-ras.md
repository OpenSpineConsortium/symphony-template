---
name: ct-volumes-are-pir-not-ras
description: "CTSpinoPelvic1K volumes are ('P','I','R') on disk -- never assume axis 1 is anterior or axis 2 is superior"
metadata: 
  node_type: memory
  type: project
  originSessionId: 601aef39-3c17-45b7-9ce6-4f172acc8773
  modified: 2026-08-21T17:31:15.733Z
---

The label and CT volumes in this release are **('P','I','R')** in their own storage
order: array axis 0 runs POSTERIOR, axis 1 runs INFERIOR, axis 2 runs RIGHT. Nothing here
is RAS on disk.

Four separate bugs in one session came from assuming otherwise, and they all looked
different from each other:

1. A renumbering pass loaded with `as_closest_canonical` and saved under the canonical
   affine, transposing a label away from its CT. See
   [[never-reorient-when-writing-labels]].
2. A sidedness check read `affine[0,:3]` for the left-right axis and asserted left is +x.
   Both halves wrong; it failed 801 of 802 cases.
3. Viewer camera vectors assumed a patient frame, so every named radiographic view looked
   at the opposite face.
4. An opportunistic-HU script used plain `nib.load` and then cut the vertebral body along
   axis 1 as if it were anterior. The ROI came out an arbitrary slab full of cortex and
   read L1 at 264 HU where the cohort should sit near 155.

**The rule that prevents all four:** decide by reading, never by assuming.

- ANALYSIS (deriving numbers, meshes, figures) -- `nib.as_closest_canonical()` is correct
  and safe. Do it, and then anterior/superior mean what you think.
- WRITING a label back -- never canonicalise. Load plain, apply the change, save the
  original affine.
- A CHECK that needs an anatomical direction -- `nib.aff2axcodes(affine)` tells you which
  way each array axis grows. Never hardcode.

Diagnostic tell: a self-check whose SLOPE against a published relationship reproduces
while its ABSOLUTE value is far off usually means the region is geometrically wrong but
still inside the right structure -- that is what localised bug 4.
