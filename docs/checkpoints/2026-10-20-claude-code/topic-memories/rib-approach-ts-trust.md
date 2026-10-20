---
name: rib-approach-ts-trust
description: "future v-next rib labelling -- trust TS per-level numbering, add only Moller's medial spine-bridge"
metadata: 
  node_type: memory
  type: project
  originSessionId: 436e5c70-681e-4f38-aab2-30dfa25af7b5
---

The planned **future** rib-labelling approach for CTSpinoPelvic1K (Greg's idea, 2026-06-29):
**keep TotalSegmentator's per-level rib numbering as-is** (TS already numbers rib_left/right_1..12
correctly), and **only add the Moller/RibSeg voxels that bridge medially to the spine** (the
costovertebral region TS under-segments), assigning each added voxel to the adjacent TS rib's
number.

**Why it's better than the current union+renumber pipeline:** the current `build_v4_ribs.py`
unions Moller  union  TS then RE-NUMBERS via overlap-vote/ts-offset/extrapolate, and that renumber
step is what breaks -- e.g. case 0231 has only T12 (id 19) labelled as a thoracic anchor, so all
6 ribs/side collapse to rib 12. Trusting TS numbering removes the renumber step entirely (kills
the 0231-class collapse, the gaps, the mis-counts) AND auto-excludes Moller bowel false-positives
(a Moller blob that doesn't bridge to a TS rib is simply never added). See [[thoracic-gt-fov-limited]].

**Status: IMPLEMENTED** (2026-06-29) in `scripts/build_v4_ribs.py` -- `number_and_overlay` now
calls `_trust_ts_graft_moller`: out = TS ribs verbatim; graft Moller voxels (nearest-TS-number,
cropped EDT) iff their union component contains a TS rib; drop Moller-only components (bowel FP);
then `_drop_same_id_strays`. **2026-07-04: `_drop_same_id_strays` extended** -- besides dropping a
tiny fraction (< max(500 vox, 10%)), it now also auto-drops a same-id piece that is FAR
(>FAR_STRAY_MM=45mm) from the main rib body AND ISOLATED (touches no other bone) AND <FAR_STRAY_MAX_VOX
(5000): a floating mislabelled blob = **bowel/vascular calcification tagged as a rib** (Greg confirmed
this on case 0150/104 -- an 832-vox calcification 113mm off rib 12; size-only rule had kept it). Nearby
/ bone-adjacent / large second pieces still surface as a dup for human review (a real broken rib to
CONNECT is never auto-deleted). This is DELETION of FP noise, safe pre-student -- NOT the post-correction
engulf ([[rib-auto-engulf-post-correction-only]]). The old renumber machinery
(`_rib_connection_qc`, `_ts_offset_assign`, `_ts_component_numbers`, `_review_flags`,
relabel_ribs import, THORACIC_TO_RIBNUM) was deleted. Validated: TS numbers 0231 as 7-12/side
(renumber had collapsed to all-12); trust-TS removes every gap across the flagged sample; a
synthetic unit test proves the graft bridges a fragmented rib into one piece and drops a bowel
blob. NEXT: re-run `slurm/ship_v4.sh` with `RESUME=0` on the grid to regenerate v4, then re-QC
(worklist should shrink hard); the graft's fragmentation-bridging only materialises there (Moller
preds are ephemeral node-scratch, can't run locally).
