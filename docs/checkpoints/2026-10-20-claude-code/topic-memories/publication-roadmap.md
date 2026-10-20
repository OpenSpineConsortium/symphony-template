---
name: publication-roadmap
description: The paper-split plan for the spinopelvic ecosystem + confirmed venues/deadlines
metadata: 
  node_type: memory
  type: project
  originSessionId: 436e5c70-681e-4f38-aab2-30dfa25af7b5
  modified: 2026-07-24T04:25:22.437Z
---

**UPDATE 2026-07-24 -- CTSpinoPelvic1K descriptor now targets a DATASET ARTICLE in *Medical Physics*
(MLHC was rejected).** Remaining work to submit, in order:
1. Finish the rib + spine annotation passes (students; spine = the 113-case unified Space).
2. **Flowcharts of dataset creation** (sources -> pipeline -> QC -> review -> final).
3. **Miraziz + the other radiology resident re-read ALL Castellvi cases**; compute **inter-reader
   agreement**, with **adjudication by a senior neuroradiologist** where they disagree.
   (Castellvi grades already exist for 39 cases in `Lumbosac.csv` -- not yet merged into the manifest.)
4. **Upload the final dataset to Zenodo -> DOI.**
5. Prepare + submit the manuscript.
Supporting artifacts already built: `docs/CORRECTIONS.md` (CTSpine1K/CTPelvic1K GT errors this dataset
fixes), `build_final_dataset.py`, `apply_lumbar_rib_class.py`, `benchmark_moller.py`.

**UPDATE 2026-06-28 (user starts residency Wed 2026-07-01 -- consolidating to close the project):**
The P1/P2/P5/P6 split is collapsed into ONE BIBM wrap-up paper = everything built *on top of*
the dataset: ostk spinopelvic params (PI/SS/PT/LL) + CT->radiograph bridge (2D port + label-carrying
DRRs / XRSpinoPelvic1K) + the NiiVue viewer/metrics.json contract + post-op synthesis prototype.
Target **BIBM sec. 6.d / sec. 6.n**. Draft written at `NextPaper/bibm-spinopelvic/main.tex` (+ tools/cohort_stats.py,
README). MLHC = the descriptor only, with **v2->v4 densification folded into the camera-ready**.
Honest scope (do NOT overclaim): localizer is a framework (untrained), no AR, engine-swap is
contract-only, post-op is a prototype, SS/PT/LL on supine CT are surrogates (PI posture-invariant),
SVA/TPA out of scope, manual validation is the stated next step. Below = the original P1-P6 plan for context.

Publication plan agreed 2026-06-25 (user "really liked" this grouping):

- **P1 -- XRSpinoPelvic1K**: limited-FOV vertebra+rib localization on DRR/XR for intraoperative level ID (wrong-level-surgery wedge). Venue **BIBM**, deadline ~**2026-07-05**. The deadline paper.
- **P2 -- spinopelvic measurement on XR**: DRR->seg->ostk geometry (PI/PT/SS/LL) vs prior art (BiLUnet/SpineCurvEst) on BUU-LSPINE, CUT for domain gap. Split from P1 (different task/metric). ~SPIE-MI/Radiology:AI.
- **P3 -- CTSpinoPelvic1K dataset descriptor**: submitted to **MLHC 2026**, decisions **2026-07-03** (this is the venue -- not a future plan). The foundational dataset paper.
- **P4 -- unified multi-source CT corpus + auto-phenotyped anomaly cohort** (LSTV/TLTV/stump/scoliosis/deformity/fracture by volume). Split into 4a (resource/harmonization) + per-anomaly studies. NeurIPS D&B / MICCAI / journal. The franchise.
- **P5 -- OpenSpineToolkit (ostk)** software note -> JOSS.
- **P6 -- geometry-driven post-op alignment synthesis** (reciprocal+Lafage+cages) -> Eur Spine J / methods journal.

Grouping calls: split P1/P2 (level-ID vs angle measurement); P3 separate (descriptor != application); split P4 into resource + studies; split P5/P6. PACS demo + licensing are deployment/stance, not papers. Highest-leverage action = pull Moller rib masks/weights ([[pacs-demo-and-ostk-params]] ecosystem) -- unblocks P1 + P4 at once. See docs/DATASETS_ROADMAP.md.

**2026-09-08 redirect:** the NeurIPS 2026 D&B draft (NextPaper/AR/neurips_2026.tex) is FROZEN as a
source document only; Greg said stop drafting it. The target for the one-shot/numbered-rib CT work
is *Radiology: Artificial Intelligence* (Original Research): NextPaper/RadAI/main.tex (RSNA order,
3,000-word limit, structured abstract <= 250, CLAIM 2024 checklist in claim_checklist.md, limits in
README.md; the journal's author pages block fetches, verify in a browser). Port content from AR, do not
extend AR.
