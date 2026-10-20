---
name: registration-free-prior-art
description: What is actually published on naming vertebrae from intraoperative fluoroscopy (search 2026-09-22) -- per-vertebra DETECTION recall 0.96-0.98 exists (Rao EMBC 2024), naming peaks at 73.3% via preoperative-radiograph matching (VDVM), registration-free naming 88.3% only on cadaver long-length tomosynthesis
metadata:
  type: reference
---

Logged search (22 PubMed queries with counts, Europe PMC, OpenAlex, Semantic Scholar, arXiv, openFDA, web;
1,047 PMIDs screened): `spinesurg-ct-nnunet/docs/research_registration_free_search_2026-09-22.md`.

- **Do not write** "no per-vertebra recall on real fluoroscopy is published". Rao et al., EMBC 2024
  (10.1109/EMBC53108.2024.10781813, PMID 40039607): recall 0.964, and 0.982 for YOLOv5, on 578 C-arm images from
  three commercial C-arms. Class-agnostic: it names nothing. Restrict the claim to NAMING.
- **Do not write** "every method imports identity from a preoperative CT or MR". VDVM (Zhang 2023,
  10.3233/XST-230025, PMID 37393485) matches vertebrae to the patient's preoperative RADIOGRAPH: naming 73.3 % on
  31 C-arm images, detection mAP 0.87. Huang 2022 (10.1016/j.cmpb.2022.107222, PMID 36370597) names levels with no
  preoperative image at all, 88.3 % on 13 cadavers, on O-arm long-length tomosynthesis, not C-arm fluoroscopy.
- Killeen 2025 (10.1007/s11548-025-03351-y, PMID 40205315): individual vertebral levels score Dice 0.04 on real
  cadaver C-arm frames.
- No FDA 510(k) names levels from 2-D fluoroscopy content. MacLeod 2025's review sentence that AI level
  identification "has been shown to be effective using fluoroscopic images" traces to an intraoperative-CT paper.
- **Still unread and could overturn the naming claim:** Li 2016 EMBC (PMID 28268411), Li 2017 ICCSEC
  (10.1109/ICCSEC.2017.8446758), ABLSpineLevelCheck BIBM 2024 (10.1109/BIBM62325.2024.10822817) -- IEEE Xplore
  blocks scripted access; get them through the library before submitting.

Related: [[rsnai-paper-endpoint]], [[mixed-length-head-and-sota]] (no metric-comparable plain-film naming figure).
