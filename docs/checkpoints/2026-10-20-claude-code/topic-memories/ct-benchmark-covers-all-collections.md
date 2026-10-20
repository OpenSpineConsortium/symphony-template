---
name: ct-benchmark-covers-all-collections
description: "The benchmark's CT axis is every collection here (5,700+ subjects), not CTSpinoPelvic1K's 802 limited-FOV records; tools/ct_inventory.py counts them"
metadata: 
  node_type: memory
  type: project
  originSessionId: f1bdbd78-151f-470b-b703-dd9af9b3fecc
  modified: 2026-09-22T21:49:48.995Z
---

Greg, 2026-09-22: CTSpinoPelvic1K is abdominopelvic and sees only the lower spine, so scoring a whole-spine
counting claim on its 802 records understates both the anatomy the method meets and the number of scans behind it.

`tools/ct_inventory.py` counts distinct SUBJECTS per render bank using `tools/patient_keys.py` -- the same keying
the split uses, so the inventory and the split cannot disagree -- and probes every CT root rather than assuming it.
Written to `docs/CT_INVENTORY.md`; `docs/BENCHMARK_PROTOCOL.md` axis 3 now names it.

Measured: ctsp_drr 801, physics_drr 3,029, ts_drr 1,170, ts_drr_v3 1,735, verse_drr 374, carm_drr 120,
physics_rare 81, spinalai_drr 44 (8,358 renders over only 44 subjects -- heavy pose multiplication, report it
separately). **Counts are NOT additive across banks**: several banks render the same collection, so a case list is
drawn on patient keys over the union.

**Unkeyed banks refuse to split, which is correct but means they cannot be pooled yet**: aasce_drr (457,
`AASCE_sunhl-1th-<date>-<n>_<A|B>_AP`), anchor_drr (7,842, `ctsp_<id>_<ap|lat>` -- CTSP patients under a THIRD
naming scheme, so a leak risk of the same family as the one already found), fluorocap_drr (2,385, `FLUO-<n>`).
anchor_drr is NOT in the v8 level bank (sources: films_drr, ctsp_drr, verse_drr, physics_drr, physics_rare), so no
leak there -- checked.

A collection with pseudolabelled truth (AASCE, SpinalAI) cannot support a claim that we beat the tool that made the
pseudolabels; those are reported as coverage and failure counts only.

Related: [[splits-origin-and-v3-resplit]], [[split-leak-cross-naming]], [[pooled-vs-lodo-device-designs]].
