---
name: anomaly-rule-rc22-evaluated
description: "The R+C=22 transitional-spine rule was measured 2026-09-22 -- it is one count (N!=23), applies to 1.2% of spines, its C1 premise is false for VerSe, and it localises nothing"
metadata: 
  node_type: memory
  type: project
  originSessionId: f1bdbd78-151f-470b-b703-dd9af9b3fecc
  modified: 2026-09-22T23:00:49.423Z
---

Evaluated rather than assumed, because Greg asked for it to be evaluated as well as drawn.
`docs/ANOMALY_RULE_EVALUATION.md` + `docs/anomaly_rule_evaluation.json`, grid job 40414996.

**It has no target.** R + C = N - 1 for every choice of target, so "R + C != 22" is exactly "N != 23". The whole
content is one count over the presacral column; picking a target vertebra is decorative. Never draw it as though
the target mattered.

**It needs the whole column, so it rarely applies.** Computable (C2 in field AND reaches the lumbosacral junction
AND no hole): VerSe **14/374 (3.7 %)**, CTSpinoPelvic1K **0/801** (abdominopelvic, and Dataset813 has no cervical
class), **14/1,175 = 1.2 %** overall. Of 74 transitional spines only 4 (5.4 %) sit in a computable field.

**The C1 premise is FALSE for VerSe.** C1 is labelled in all 76 cases carrying C2. A detector that boxes C1 counts
24 on an ordinary column, so against the constant 22 the rule flags EVERY normal spine -- specificity **0.000**.
The constant belongs to the counting convention (23 excluding C1, 24 including), not to anatomy: set it from what
the detector actually puts a node on.

**Its 1.00/1.00 is circular.** With an exact count the rule and the definition of anomalous are one sentence. What
that row really establishes is the test-set size: five anomalous spines.

**It is not robust to the detector.** Holding false alarm at 5 % needs per-body miss rate <= 0.223 %; 1 % needs
<= 0.044 %. Measured chain completeness (95 % on 203 C2-anchored scans) implies ~5 % false alarm before any spurious
node, on rendered CT not real frames. Misses modelled independent; real failures cluster by region.

**Three blind spots**: it localises nothing (N=24 holds three T13 and one L6 -- indistinguishable, and that is the
lumbosacral question); transpositions pass (R+C is permutation-invariant); an extra and a missing vertebra cancel.

**Use**: a cheap sanity flag where the whole column is in view, constant set from the detector's convention,
false-alarm rate quoted beside it. Not an anomaly detector, and it does not localise.

**Method worth keeping**: a BOX GAP cannot find a missing body -- posterior elements overhang, so neighbouring
boxes always overlap and every observed gap in 387 renders was negative. Use centre-to-centre spacing, each step
against its neighbours: p99 of the ratio is 1.17, a skipped body sits near 2.0, threshold 1.6.

**Two incidental findings**: `~/verse_drr` holds 387 files for 374 spines -- **13 exact duplicate renders**,
`glgl003`...`glgl146` repeating `gl003`...`gl146` with identical boxes (a same-person-twice case, see
[[key-patients-from-metadata-not-filenames]]); and `CTSP_COLONOG_730` is named T10...L2, **L4**, L5 with an ordinary
step between L2 and L4, so either it has four lumbar bodies named as five or L3 was skipped.

Compute from the RAW VerSe masks (`VerSeFusion/data/unified`, 25=L6, 28=T13), not the render anns -- the renderer
drops silhouettes under 60 px. Cross-checks held: T13 = 6 VerSe cases (the manifest's 18 is wrong,
[[versefusion-t13-flag-wrong]]); CTSP L6 = 18, matching `slurm/l6_cases.txt`.
