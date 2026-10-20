---
name: u251-translation-fall-il68b
description: "U251 LITT RNA-seq: the headline 'translation' fall is ONE block of ~80 cytosolic ribosomal-protein genes (KEGG MEDICUS translation initiation = 80/80 RP, no eIFs) and its size leans on ONE primary, IL68B; say ribosomal-protein genes, not translation"
metadata:
  node_type: memory
  type: project
  originSessionId: f1bdbd78-151f-470b-b703-dd9af9b3fecc
  modified: 2026-09-26T09:48:37.717Z
---

In the U251 LITT recurrence study (u251-xenograft-murine-RNASeq-study, MBR manuscript), the translation-initiation,
elongation and ribosome gene sets fall -0.38 to -0.40 log2 in recurrence with all six tumours. **IL68B, a primary, is the
highest of the six on 80/80 initiation and 85/85 ribosome genes** (+0.67 log2 above the six-tumour mean on these genes;
genome-wide it is average, -0.006). Without IL68B the sets fall -0.10 to -0.11 against -0.03 for genes matched on abundance
and control/tumour ratio; dropping any other tumour leaves -0.37 to -0.53. Among the other five tumours the set level tracks
graft fraction (r = 0.85). Median-of-ratios fold changes of the six tumours, reproducing the DESeq2 set means to 0.003
(SLIDES/07_contamination_magnitude.py, `leave_one_out` in figures_cns/contamination_magnitude.json).

**Why:** found by the adversarial check of the CNS 2026 Abstract 418 deck; the manuscript does not report it, and the GSEA
(gene-set permutation) has NOT been re-run without IL68B, so whether translation initiation still clears q < 0.05 is unknown.

**GSEA leave-one-out RESULT (2026-09-26, 41 runs, reproduction exact):** IL68B does NOT carry the enrichment: without it
translation initiation stays q < 0.05 at 5/5 seeds. What is fragile is the FDR q itself: all six tumours, five
permutation seeds, q = 0.022/0.026/0.067/0.139/0.312; without IL67B, IL69B or IL66B q > 0.05 at every seed. Robust:
NES -1.88 to -2.02 and nominal p < 0.001 in every run. Say "nominal p < 0.001, FDR q seed-dependent (0.02-0.31)",
never "the one set that clears FDR". Files: u251 ANALYSIS/gsea_leave_one_out/ (SUMMARY.md, loo_*.tsv).

**How to apply:** any statement of the translation result (talk, manuscript, response to reviewers) must carry the
one-tumour dependence. GSEA leave-one-out SUBMITTED 2026-09-26 04:45 on the grid (u251 repo ANALYSIS/gsea_leave_one_out,
jobs 40464722 prep / 40464723 array of 41 / 40464724 collect, resubmitted 04:52 after the ~/.local singularity failed; exact nf-core GSEA 4.3.2 command, one tumour removed, filter
re-applied, seeds 1234 and 1-4). Read SUMMARY.md and reproduction.json there (exact must be true) before quoting.
Related: [[cns-abstract-418-deck]].

**Ribosomal-protein correction (2026-09-26, v4 claim check):** KEGG_MEDICUS_REFERENCE_TRANSLATION_INITIATION is 80/80
RPL/RPS/FAU/UBA52 genes with no initiation factor; the other five leading sets hold 83-85 of the same genes and the six
leading edges share 76 (union 86). So the six sets are one signal. Say "ribosomal-protein genes fall"; lower RP mRNA is
not lower translation (puromycin/polysome is the test). The ranking metric (Diff_of_Classes on counts) weights abundant
genes; on a log-scale ranking all 80 stay in the lower half (74 % in the last 6.6 %). Leave-one-out counts to quote:
15 of the 35 filtered runs at q < 0.05 (41 includes six unfiltered runs); nominal p < 0.002, not < 0.001.

