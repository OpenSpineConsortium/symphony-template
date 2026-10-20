---
name: identity-audit-findings
description: "Patient identity audit 2026-09-22 -- CTSP prone/supine RULED OUT on disk (manifest carries the TCIA token), TS v2<->v3 is a 24-id renumber, THREE live leaks incl. the \"clean\" v8 bank (VerSe series!=subject), and C-ArmLSpine case!=person so the 98.22% CV needs day-grouped folds"
metadata: 
  node_type: memory
  type: project
  originSessionId: f1bdbd78-151f-470b-b703-dd9af9b3fecc
  modified: 2026-09-23T01:14:12.163Z
---

56 agents, adversarially verified (9 claims survived, 39 corrected). Spec: `spinesurg-ct-nnunet/docs/PATIENT_IDENTITY_SPEC.md`
(resolution order L0-L9, per-corpus rules, 19 aliases, unknowns, failure behaviour, test plan). Summary and
consequences in `docs/RESUME_2026-09-22_PM.md`. Read the spec before touching `tools/patient_keys.py`.

**CTSP prone/supine -- the feared case is ruled out on disk.** Zero shared (origin, spacing, direction, nz)
signatures over 1,728 acquisitions; TCIA lists 825 PatientIds and `patient_db.json` holds exactly those.
`~/data/CTSpinoPelvic1K/manifest.json` (802 rows, `volume_id -> token` = tail of DICOM PatientID) is the identity;
the symlink crosswalk was never needed. Residual: whether the 768 numeric-id and 34 `CTC-` records overlap as
humans -- one TCIA query. **Token != release id** (release 0145 = token 100).

**TS v201 <-> v300 is a RENUMBER.** v201 `s1406...s1429` are byte-identical to 24 different v300 ids and the vacated
numbers were reissued to other people, so `ts:s####` splits 24 and merges 15. Needs `tools/identity/ts_alias.json`
and a bank registry recording the RELEASE (no ann carries it; `ts_drr_v3` anns claim v201). Same-patient across
different scans is unknowable on disk.

**Three live leaks, one in the bank I called clean:**
- `allspine_v8_fov96_ctx`: VerSe SERIES keyed as subjects; `verse_demographics.csv` says 18 subjects own 37 series.
  verse401/406/407/408/416 on both sides -- **10.5 % of VerSe validation**, with overlapping labelled levels.
  **FIX SHIPPED 2026-09-22 21:20**: `patient_keys.py --verse-manifest ~/VerSeFusion/data/manifest/manifest.csv`
  (series_id->patient_id, 375->355) resolves series to subject on every route incl. `CTSP_VERSE_*` patient_ids;
  v9 chain keys 40415667 -> bank 40415668 -> train 40415669 -> a5 40415670 (`slurm/allspine_v9_*.sh`). Film
  numbers with PATIENT-clustered intervals already exist for v8 seed 0 in `SchwingNet/results/a5.json`
  (CSXA 99.8 [99.6,100.0], BUU 97.3 [96.5,98.0], NHANES 99.1 [98.2,99.8]); v9 gives all three seeds.
- `anchor_drr` own split: `implant_<rel>_v<k>` seeded separately from `ctsp_<rel>` (`make_anchor_drr.py:189`) --
  **301 of 801 CTSP people on both sides; `anchor_det_v1` trained on it** (the 93.48 % own-domain recall; the
  71.67 % real-film number is unaffected).
- `vindrps_fov96_ctx`: VinDr keyed per IMAGE not study (10,466 -> 5,000) -- **77.8 % validation leak**.

**C-ArmLSpine case != person, and the headline 98.22 % is split by case.** `PatientID` empty on 59,307/59,609;
`(0029,0016)` is operator free text keying an ACQUISITION (five cases are bare integers); 149 cases on FOUR days at
median 224 s apart. Same acquisition twice is ruled out; one patient / two acquisitions / two folds is NOT.
**Re-run the CV with folds grouped by acquisition day** and state the grouping in the paper. `case134/ori/` holds
302 frames with a real PatientID and name that a `*.dcm` walk misses -- handle, never print.

**Code consequences:** key by `(root, case)` (161 silent case-name collisions between banks); `patient_id` DEMOTED to
L6 (mendeley_N24 = a 35F and a 64M; `ctsp_drr_obl` holds 314 VerSe series as `CTSP_VERSE_*`; spinalai `sim_*` is a
nearest-neighbour index); add `films_ap_drr` (BUU AP, 3,600 people = the LA set) and `nhanes_pseudo` (`NHANESPS_*`,
third NHANES scheme, 362/364) as roots; DeepFluoro fluoro `PatientID` is WRONG (merges 18-2799/18-2800, splits
others) -- key by specimen; FluoroCap over-merges by design, **never report a patient count**.

Related: [[key-patients-from-metadata-not-filenames]], [[split-leak-cross-naming]], [[nhanes-double-inclusion]],
[[resume-2026-09-22-pm]].
