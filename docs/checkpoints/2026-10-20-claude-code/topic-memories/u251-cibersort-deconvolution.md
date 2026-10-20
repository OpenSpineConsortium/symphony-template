---
name: u251-cibersort-deconvolution
description: U251 Neftel-state deconvolution 2026-09-26 - CIBERSORT is NOT installed anywhere (Jan run was the CIBERSORTx website; cibersort.tar.gz = its 3 upload files); re-implementation fit is weak, only MES agrees with GSVA
metadata:
  type: project
---

CIBERSORT is not installed on the grid, in any container (Docker Hub go2432/* checked layer by layer) or on the laptop. Greg's January 2026 run was the CIBERSORTx WEBSITE (account go2432@wayne.edu, job 3): inputs in `Desktop/nsurg/RAJ/cibersort/ANALYSIS/cibersortx/for_upload/`; `cibersort.tar.gz` there is only those three files (md5-identical, no code). The job log ends after "Make Signature Matrix" with no outputs; its phenotype file was a two-column cell-to-state list.

What exists now (u251 repo `ANALYSIS/cibersort/`, commits b929373, 0159aac): Neftel 2019 SS2 reference (4,873 scored adult malignant cells; the SCP393 matrix is log2(TPM/10+1), verified by per-cell sums of 1e6; states = argmax of the collapsed meta-module scores, identical to Greg's January labels), CIBERSORT-format signature matrices (Newman 2015 procedure, kappa 4.2), a CIBERSORTx single-cell reference, a leave-one-tumour-out check (pooled r 0.88; AC over-called ~9 points, MES under-called ~8) and a Python re-implementation of CIBERSORT's core.

Result: fit R only 0.19-0.26 in every tumour. MES is lower in recurrence (0.52 vs 0.39, survives dropping IL68B) and ranks the same as the September GSVA (Spearman +0.77/+0.89); AC does NOT agree with GSVA (GSVA: AC falls, p 0.007). OPC ~0 everywhere. Culture C2B reads less MES than the xenografts.

**Why:** Greg asked for CIBERSORT "on the known single cell profiles"; the answer depends on an install that does not exist.
**How to apply:** for the official number, Greg must run the CIBERSORTx website/token or download CIBERSORT.R under his account; compare against `results/fractions_nusvr_*.tsv`. The survey `SINGLE_CELL_REFERENCES.md` names GBM-CARE (GSE274546) for primary vs recurrent and GSE134470 for U251 culture vs brain. Related: [[u251-translation-fall-il68b]], [[u251-project-containment]].
