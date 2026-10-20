---
name: film-ncurve-ablation-result
description: "Film N-curve ablation (2026-09-25, jobs 40451157/58) answered: CT renders raise ordinary-level naming on plain films by 6-22 points at 5-25 persons per corpus, and the arms are level once every person is used; read in SchwingNet/results/coverage/film_ncurve/ablation/READ.md"
metadata:
  node_type: memory
  type: project
  originSessionId: f1bdbd78-151f-470b-b703-dd9af9b3fecc
  modified: 2026-09-26T04:55:16.021Z
---

The one open SchwingNet grid experiment as of 2026-09-26 is DONE and read. Question (Greg, 2026-09-25: "if renders are
my only source of rare classes they have to be included right? run this test"): do renders also raise ORDINARY-level
naming on plain films? Three arms on the reported N-curve's 48 cells: render-only init (the paper's Figure 5b),
ImageNet init on the same merged bank, and film only (no render rows). Pre-stated rule: separation outside the
patient-clustered intervals at N = 5 and 25 per corpus.

**Result:** renders help while film is scarce and stop mattering once it is not. N = 5: +21.9 / +11.1 / +18.7 points
(NHANES / BUU / CSXA) over film-only; N = 25: +12.2 / +6.0 / +6.2; every seed separated. From 100 persons the arms
overlap; with every person they are level (BUU film-only 1.6 points higher). The ImageNet-init arm sits between, so
pretraining and the render rows both contribute. 7 of 9 pre-stated cells separated, all "help".

**How to apply:** renders stay in training regardless (the only labelled L6 / T13). A proposed Discussion sentence is
in REVISION_LOG3 section 13, NOT in the tex (body at the limit); Greg decides. Reader: `tools/film_ncurve_ablation_read.py`.
Related: [[schwingnet-manuscript]], [[synthetic-real-ratio-evidence]].
