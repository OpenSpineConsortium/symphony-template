---
name: never-reorient-when-writing-labels
description: Loading a label via as_closest_canonical and saving with that affine silently transposes it away from its CT
metadata: 
  node_type: memory
  type: project
  originSessionId: 601aef39-3c17-45b7-9ce6-4f172acc8773
  modified: 2026-08-21T04:30:45.098Z
---

Any script that WRITES a label must load it with plain `nib.load` and save with that
file's own affine and header. Loading through `nib.as_closest_canonical()` and then
saving `nib.Nifti1Image(array, img.affine, img.header)` writes the *reoriented* array
under the *canonical* affine, which transposes the label away from its CT -- a
512x645x512 label came back 512x512x645 and ITK-SNAP refused the pair.

**Why:** label renumbering is pure id arithmetic and is orientation-independent, so the
reorientation buys nothing on the write path. If the ANALYSIS needs canonical orientation
(reasoning about which rib is above which), keep two handles: derive the id map from the
canonical view, apply it to the original array, save the original affine.

**How to apply:** grep for scripts that contain both `as_closest_canonical` and
`nib.save` -- that pair is the bug signature. `scripts/check_release_invariants.py` now
gates the whole finalize chain on label geometry matching its CT, because this failure is
invisible to every downstream step and surfaced only when a human opened a case.

Related: when a check needs a left/right or superior/inferior convention, read it with
`nib.aff2axcodes(affine)` instead of assuming -- these volumes are ('P','I','R'), so the
left-right axis is the THIRD array axis, and in RAS +x is the patient's RIGHT, not left.
Asserting the opposite made a check fail 801 of 802 cases. A check that fails almost
everything is accusing itself; verify it against cases a human already reviewed before
believing it. See [[ct-spinopelvic-release-gates]].
