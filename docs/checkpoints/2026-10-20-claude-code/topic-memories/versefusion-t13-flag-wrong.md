---
name: versefusion-t13-flag-wrong
description: The VerSeFusion manifest's has_T13 flag is wrong for 18 subjects - twelve have no T13 label at all and six carry an L6 instead, the signature of a label resolved against the wrong map; the masks give 6, matching the published table
metadata:
  type: project
---

**Defect (found 2026-09-15 while verifying VerSe against its published variant table).** `~/VerSeFusion`'s manifest
says `has_T13 = 18`. Reading the masks directly: **twelve of those eighteen contain no label 28 (T13) at all**, and
**six carry a large label 25 (L6) instead**. The true count is **6**, and those six match the published table
subject for subject: verse547, verse582, verse588, verse601, verse602, verse631.

**Why it happened.** Label 25 is L6 in the release scheme and T13 in another; resolving a name against the wrong
map returns a finite, plausible, wrong answer. This is the same failure the repo's CLAUDE.md records for S1
returning C7 and femur_left returning T4 - a third instance of it, in a different file.

**How to apply.** Never read `has_T13` from the VerSeFusion manifest. Take transitional and numerical variants for
VerSe from the published table (Loeffler et al., Scientific Data 8:284, 2021, Supplemental Table 1, CC BY 4.0;
extracted to `~/lstv_sources/verse_suppl/verse_suppl_table1.csv` and folded into
`~/lstv_sources/TRANSITIONAL_LABELS.csv`), and derive from masks only as a cross-check. Where table and mask
disagree on the thoracolumbar boundary (six subjects) the table applies a rib-length rule and the mask numbers
conventionally; both preserve the total. `verse707` is a genuine conflict - the table says normal, the mask carries
an L6 of 132,522 voxels - and should be re-read before it trains anything.

Related: [[label-scheme-v4-vs-ostk]], [[vf813-drops-c1-t9-use-raw-verse-for-whole-spine]], [[lstv-data-landscape]].
