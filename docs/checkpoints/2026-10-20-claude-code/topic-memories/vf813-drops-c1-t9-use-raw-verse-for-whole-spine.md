---
name: vf813-drops-c1-t9-use-raw-verse-for-whole-spine
description: The converted VerSeFusion corpus (~/vf_813) maps VerSe C1-T9 to ignore; any whole-spine or 2-D level experiment must read the raw masks under ~/VerSeFusion/data/unified/scan-*/
metadata: 
  node_type: memory
  type: project
  originSessionId: e44eca96-f48c-494d-ba1f-7dae68bdf06d
  modified: 2026-09-13T02:51:38.732Z
---

`tools/convert_versefusion.py` deliberately maps VerSe ids 1-16 (C1-T9) and the coccyx to
`ignore`, because Dataset813's scheme starts at T10 and calling unnamed bone background would
teach a falsehood. Correct for the 3-D corpus; fatal for anything needing C2. On 2026-09-12 the
DRR context-ladder tool read `vf_813` and every cervical case came back with zero vertebrae
(`gl003` has C1-T5 raw, nothing converted).

**Why:** the ladder's top rung is C2->sacrum; VerSe is the only whole-spine source in hand.
Also: VerSe cases are not individually whole-spine -- `gl003` is C1-T5, `verse500` is T10-L5 --
so a "full" rung means "everything this scan holds", not C2->sacrum.

**How to apply:** for 2-D/DRR work use `~/VerSeFusion/data/unified/scan-<case>/*_msk.nii.gz`
with VerSe-native ids (C1-C7=1-7, T1-T12=8-19, L1-L6=20-25, sacrum 26, T13 28);
`make_drr_dataset.py --scheme verse` and `make_contours.py --scheme verse` do this. Reorient
in memory to PIR before projecting (analyse-only). Related: [[label-scheme-v4-vs-ostk]],
[[ct-volumes-are-pir-not-ras]].
