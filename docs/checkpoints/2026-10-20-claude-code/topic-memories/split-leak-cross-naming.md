---
name: split-leak-cross-naming
description: "The split was drawn PER SOURCE, so one person under two names landed on both sides: NHANES (48/54 val patients) and CTSpinoPelvic1K (357 people in v6/v7, CT render vs physics render). Fixed by tools/patient_keys.py + make_context_crops --patient-json. Styled corpora are CLEAN: all five share the same 17 val subjects"
metadata:
  type: project
---

Record: `spinesurg-ct-nnunet/docs/SPLIT_LEAK_CROSS_NAMING_2026-09-22.md` (and the NHANES-specific one).

**The rule that caused it:** `make_context_crops.py` shuffled and split each `--drr` root separately. Two roots
holding one person under different names are then independent draws.
  - NHANES: `films_drr` source `nhanes` (`patient_id nhanes_00160`) vs `~/nhanes_drr` (`NH_00160_c`).
  - CTSpinoPelvic1K: `ctsp_drr` `CTSP_COLONOG_<n>` vs physics `ctsp_<release id>_<view>_p<k>`; tied only by the
    Dataset813 symlink COLONOG_<n>_0000.nii.gz -> <id>_ct.nii.gz. 371 people on both sides of v6 and v7, 357 of
    them purely from the naming.

**Clean, and checked:** the styled device corpora all record the SAME 17 validation subjects in STYLE_INFO.json,
so a synthetic frame is always on the same side as its CT and geometries are never mixed across train/test; and
`--group-regex` already keeps the several poses of one CT together (physics_drr 7,045 cases in 2,201 groups).

**How to apply:** build every future bank with `tools/patient_keys.py` -> `make_context_crops --patient-json`
(one split over people across all sources; it refuses a case it cannot key and fails if anyone is on both sides).
`tools/test_patient_keys.py` asserts the two defects collapse. The clean rebuild is
slurm/allspine_v8_{clean,bank,train}.sh. Do not quote a pooled real-film number from v2/v6/v7; per-source CSXA
and BUU-LSPINE are unaffected. Related: [[nhanes-double-inclusion]], [[rsnai-paper-endpoint]].
