---
name: splits-origin-and-v3-resplit
description: "5-fold splitter is patient-grouped + LSTV-stratified, origin-blind; the upcoming v3 pseudolabelled dataset needs a fresh resplit"
metadata: 
  node_type: memory
  type: project
  originSessionId: b7bbe4e5-4a8a-4821-9d22-fe7e8fb39a74
  modified: 2026-09-21T19:08:10.865Z
---

`scripts/generate_5fold_splits.py` (CTSpinoPelvic1K) splits at the
**patient_token** level (GroupKFold-style: all of a patient's records go to
one fold) and stratifies **only by the 6-way LSTV subtype**. It does NOT use
`config`/`match_type` (fused/spine_only/pelvic_native) at all -- origin is
never aggregated or used. So fold assignment is origin-blind.

**Why:** the user worried the split keyed on origin. It does not -- confirmed
by reading the splitter. This is also why the fused-only ablation is sound:
filtering to fused keeps each retained patient in its original LSTV-stratified
fold; patients with no fused record drop out wholesale (no leakage).

**How to apply:** the planned **v3 fully-pseudolabelled dataset** WILL need a
resplit -- but because it has **new LSTV cases / changed subtypes**, not because
of origin. Just re-run `generate_5fold_splits.py --hf_dir <v3 export>`;
no code change. Canonical splits live in `~/CTSpinoPelvic1K/data/hf_export/
splits_5fold.json` (schema v6); the spinesurg pipeline now prefers that over
any project-local shadow. See [[review-space-repos]].

**The shipped v11 splits (md5 860207a7..., same as v10) did NOT read the lumbar count or
L6** (found 2026-09-21): `patient_attrs` has n_lumb_max 0 for 799/802 and has_l6_any True
only for record 0500 -- which has L1-L5 and no id 25 in its label and in every manifest.
So strata = source lstv fields only; `sacr_count` never fired (strata are lumb 15 /
sacralization 15 / semi 2 / ambiguous 2 / normal 768); 0500 sits in lumb on a phantom
L6; one real L6 record sits in normal. Cause of 0500's flag unknown. The MPDA paper
(Data Format) says this. A resplit must fix the attribute read first, and it changes the
folds every trained model used.
