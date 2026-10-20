---
name: lstv-data-landscape
description: Where transitional-vertebra (LSTV/TLTV) labels actually exist for training a 2-D flag - what is downloadable today, what needs a request, and what the one published 2-D LSTV model really did
metadata:
  type: reference
---

**The whole published 2-D LSTV literature is one paper.** Kwak, Ro, Kang, J Clin Med 2025 (PMC12610351, doi
10.3390/jcm14217671): 3,116 standing lateral lumbar films, ResNet-50, acc 76.4 / sens 85.1 / spec 61.9 / AUC 0.84;
a single orthopaedic surgeon read the same 313 test films and beat it (83.9 / 81.3 / 87.3). Its labels are TEXT
MINED from MRI report impressions (words: transitional vertebra, lumbarized, sacralized), one reader, no kappa; the
62.3% positive rate is a selection artefact (population prevalence 8.8% on full-length radiographs, 26-29% on CT),
so its specificity sits near the floor for that class balance. Its Grad-CAM attends to the T12 RIB, i.e. it partly
counts from the thoracolumbar junction. Nothing released: no supplement, no weights, no code, no deposit
("data may be shared upon reasonable request"). Contacts: kang9451@gmail.com (corresponding), jadeking0308@snu.ac.kr
(data curation), duhyunro@gmail.com. SNUH IRB 2312-028-1490. Ask for the label table or the weights + test-set ids,
not the images.

**Downloadable TODAY with a transitional label.**
- **VerSe'20** (github.com/anjany/verse, OSF t98fz, CC BY-SA 4.0; the variant table is **Loeffler et al.,
  Scientific Data 8:284, 2021**, Supplemental Table 1, CC BY 4.0 - NOT the Sekuboyina MedIA paper, and the PMC
  mirror of the supplement serves HTML, so fetch it from Springer): per-scan segment counts and Castellvi grade - lumbar 6 in **85** scans, thoracic 13 in 6, cervical ribs 18, stump
  ribs 90, Castellvi IIa 35 / IIb 25 / IIIa 14 / IIIb 28 / IV 7. Cases were found by PACS report search then graded
  in consensus by two neuroradiologists, so it is enriched, not a prevalence sample. We already hold VerSe on the
  grid (~/VerSeFusion, ~/verse_drr).
- **Moeller et al. 2025 stump-rib masks** (zenodo 14864106, CC BY 4.0; code github.com/Hendrik-code/rib-segmentation):
  manual + predicted rib masks for VerSe (323) and RibFrac (420) with the published rule stump rib = length <= 38 mm;
  133/648 subjects (20.5%) have one. This is the TLTV label source.
- **BUU-LSPINE** (services.informatics.buu.ac.th/spine): 3,600 patients / 7,200 lumbar AP+lateral JPEGs whose
  annotations are said to include LSTV; 400-pair and 2,000-pair samples on Drive, full set by Google Form; licence
  "No License Provided" + acknowledgement. The LSTV column name and positive count were NOT verified by the hunt.
  Its call is made from lumbar films alone, which is the read with 32% sensitivity and kappa 0.16-0.32 (below).
- **NHANES II**: 7,408 lateral lumbar + 9,667 cervical films, US public domain, and **no radiologic reading was ever
  released** - the largest unlabelled substrate in exactly Kwak's modality.

**Reference-standard facts that bound any single-view flag.** Hanhivaara 2024 (Acta Radiol, 100 LSTV, four blinded
readers): CT sens 76 / spec 93, kappa 0.63-0.71; MRI 54 / 88, kappa 0.24-0.56; **conventional radiography sens 32 /
spec 85 / acc 42, kappa 0.16-0.32**. Farshad-Amacker 2014: MRI kappa 0.93 detection vs AP radiograph 0.53, and
"standard AP radiographs are insufficient to detect or classify LSTV". Castellvi I (a >= 19 mm transverse process)
is 68% of all LSTV and is a CORONAL measurement, not recoverable from a lateral film. The iliolumbar ligament
arises solely from L5 in 95% of controls but only 25-38% of LSTV cases, and needs axial imaging anyway. The one
positive single-lateral result: Farshad 2013 (Bone Joint J, n=186), the difference in vertical mid-vertebral angle
between the two most caudal segments <= +10 deg detects a BONY-BRIDGED LSTV (Castellvi III/IV) at sens 94 / spec 74
on a lateral radiograph - fused types only, and it does not separate sacralised L5 from lumbarised S1.

**2-D TLTV is empty.** No published detector for T13, a lumbar rib, a hypoplastic 12th rib or rib-count numbering on
any radiograph, fluoroscopic frame or scout. Sabri 2025 (Neurosurg Focus, 3,147 full-length radiographs, 8.8%
transitional) proposes rib-anchored numbering on plain film; no model implements it.

**How to apply:** grow the flag's positive patients from VerSe + the stump-rib masks before believing any accuracy
number; never benchmark against Kwak's 76.4% on a balanced set; report wide-field and lumbar-film numbers
separately; and treat a radiograph-only LSTV label (BUU-LSPINE) as weaker than a CT-derived one.
See [[fluorocap-prototype-and-lstv-arm]], [[level-model-bank-coverage]].


**Verified 2026-09-15, and what the verification changed.** The VerSe table reproduces the paper's own Table 2
exactly. Extracted and merged into `~/lstv_sources/TRANSITIONAL_LABELS.csv` (4,245 rows; also on the grid at
`~/lstv_flag/sources/`). Positives available for a transitional flag, beyond the 33 in CTSpinoPelvic1K:
**VerSe +130 LSTV and +97 TLTV (CT), BUU-LSPINE +144 LSTV (radiographs)** = 274 distinct LSTV-positive and 102
TLTV-positive cases. Three cautions that came out of the check:
- **Castellvi I shares a cell with grade 0** in the VerSe table (181 subjects) and 35 subjects carry no grade, so
  its LSTV count is a FLOOR and the negatives are contaminated with type I, which is about two thirds of all
  transitional anatomy. This depresses any specificity measured against it, as a property of the labels.
- **The Moeller stump-rib masks add no new subjects** (all are VerSe subjects the table already rates) and the
  mask-derived flag has only 65.7% sensitivity against the radiologist reading, so prefer the table. RibFrac ships
  no vertebra masks, so no level can be assigned there.
- **BUU-LSPINE is "No License Provided"** plus an EULA requiring acknowledgement and forbidding re-identification:
  record it as not open, keep it out of training, and never redistribute its images or crops.
See also [[versefusion-t13-flag-wrong]] - the VerSeFusion manifest's T13 flag was found wrong during this work.
