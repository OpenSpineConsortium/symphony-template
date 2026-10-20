---
name: rigor-audit-findings
description: "Adversarial rigor audit 2026-09-22 -- selective reporting in two places, the detector figure has no interval and an unjustified threshold (76.8% vs 90.6%), one CI in 54 claims, no paired tests, C3 never evaluated"
metadata: 
  node_type: memory
  type: project
  originSessionId: f1bdbd78-151f-470b-b703-dd9af9b3fecc
  modified: 2026-09-22T23:12:17.232Z
---

17 agents, adversarially verified, in answer to Greg's "look for anything that would embarrass me".
Ranked list in `spinesurg-ct-nnunet/docs/RESUME_2026-09-22_PM.md`; full output in the task file for `w1niwx23d`.
**Fix before the manuscript moves.**

1. **Selective reporting, two places.** `rescore_outline` scans 6 arms x 3 sets x 16 thresholds x 3 box
   conventions and the paper reports one cell; `corpus_manifold` computes leave-one-corpus-out in THREE feature
   spaces and the paper reports the only one falling below chance -- the one supporting the claim. Defensible
   perhaps, but not *stated*. The fix already exists and is used in one benchmark only:
   `~/model_night/ensemble/` picks on a dev half, reports on a disjoint test half, prints the dev->test drop.

2. **The detector number is threshold-dependent and interval-free.** 90.6 % vertebra / 83.9 % sacrum come from
   `or_lodo_rescore_outline.py` at conf 0.25 -- no interval, no rationale. `or_recall_curves.py` does it properly
   (case bootstrap, 2,000 resamples, records `selected_on_this_test=false`) and **the same arm at its own best-F1
   threshold reads sacrum 76.8 % [0.643, 0.821]**. A 7-point swing.

3. **One CI in 54 claims**, and it hits the boundary [0.957, 1.000] -- percentile bootstrap is wrong there, use BCa
   or Wilson.

4. **Film CIs cluster by VERTEBRA, not by patient**, and the two numbers the paper quotes (CSXA 99.87 %,
   BUU 98.04 %) have no `ci95` field at all.

5. **No paired tests anywhere**, though `docs/RSNAI_PLAN.md` mandates a CI of the difference. Four comparisons are
   on paired data and treated as unpaired: render 71.7 vs film 99.1 on the same 233 bodies; zero-shot LAT 96.3 vs
   AP 37.9 on the same cases; card vs uncalibrated physics on the same folds; pooled vs held-out on the same 56
   frames. `tools/stats_compare.py` has the machinery.

6. **Criterion C3 never evaluated as written** ("gain > 0 on every device with the CI excluding 0"). Only medians
   were promoted; per-fold gains are NEGATIVE on four folds (Cios -0.0128, Elekta -0.0010, PIXIUM -0.0412,
   -0.0203). Report the spread, not the median -- this project's own standing lesson.

7. **Selective prediction is strong and invisible.** `tools/level_selective.py` -> `~/selective/SELECTIVE.md`:
   99 % selective accuracy at 35.7 % coverage (lower bound 98.7 %), region 99 % at 55.7 %, AUGRC 0.0466. Cited
   nowhere, and computed on the LEAKED v2 bank -- re-run on clean v8. See [[selective-prediction-the-honest-99]].

8. **Abstention is live, untuned, unreported.** `level_prototype.py:355` abstains at p < 0.5, a fixed default. The
   C-arm lateral answers 83.1 % of the time at 98.4 % on what it answers; the paper quotes 98.2 % at FULL coverage
   without saying so.

Related: [[anomaly-rule-rc22-evaluated]], [[resume-2026-09-22-pm]], [[split-leak-cross-naming]].
