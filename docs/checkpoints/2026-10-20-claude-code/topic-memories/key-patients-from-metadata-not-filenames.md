---
name: key-patients-from-metadata-not-filenames
description: "Greg's correction 2026-09-22 -- resolve patient identity from DICOM/NIfTI headers, release manifests and ann metadata; the filename is the LAST resort, never the first"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: f1bdbd78-151f-470b-b703-dd9af9b3fecc
  modified: 2026-09-22T22:38:03.760Z
---

Greg, 2026-09-22, on being told three render banks "can't be keyed": *"wtf why can't you use metadata from the
niftis or the paper or some other metadata to key these?"* He was right and the framing was wrong -- nothing
could not be keyed; a regex was too narrow and the identity was sitting in the metadata unread.

**Why:** `tools/patient_keys.py` matched FILE NAMES with regexes and read only three ann fields. A bank whose
name did not match a pattern was refused as unkeyable, while its ann carried the identity outright. A person
under two names lands on both sides of a split and no score can reveal it -- it has already happened twice here
([[split-leak-cross-naming]]).

**How to apply:** resolve identity in this order, and treat the file name as the last resort:
DICOM PatientID / StudyInstanceUID -> release manifest or meta.csv row -> the ann's own `patient_id` ->
another ann field naming the source (`panel_path`, `source_case`, `source`) -> a documented crosswalk ->
the file name. Fields that were being ignored:

- `fluorocap_drr` `panel_path = panels/commons/<article-slug>__a.png` -- panels `__a`/`__b` of one figure are ONE
  patient, and an article may show one patient in several figures
- `aasce_drr` case `AASCE_sunhl-1th-<date>-<n>_<A|B>_AP` -- A and B are one patient's two films
- `anchor_drr` case `ctsp_0001_ap` -- the CTSP release id, plain; the regex demanded a `_p<k>` suffix
- `ts_drr` `age`, `gender`, `study_type`, `ts_split`, `pathology`
- `spinalai_drr` `patient_id = sim_000237` -- this one was read

And the question the metadata has to answer before any of it is trusted: CTSpinoPelvic1K comes from CT
colonography, which scans each patient prone AND supine, so a release id may not be a person. See
[[resume-2026-09-22-pm]].
