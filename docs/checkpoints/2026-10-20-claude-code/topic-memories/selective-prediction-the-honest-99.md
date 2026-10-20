---
name: selective-prediction-the-honest-99
description: The 99% target is reachable as a coverage claim, not an accuracy claim - the first risk-coverage curve for vertebral level identification, with the numbers and the framework that makes it defensible
metadata:
  type: project
---

**Measured 2026-09-15 on held-out renders** (`~/selective/SELECTIVE.md`, `tools/level_selective.py` +
`level_posteriors.py`, job 40291753; allspine_v2 rung 1, split by CASE not by crop):

| target accuracy among answered | name the exact vertebra | name the region |
|---|---|---|
| 99.0% | **35.7% coverage** (2,956 answered, 95% lower bound 98.7%) | **55.7%** |
| 97.5% | 47.4% | 74.9% |
| 95.0% | 58.0% | 95.7% |
| 90.0% | 72.8% | 100% |

Full coverage: leaf 78.8%, region 93.4%. AUGRC 0.0466. Split conformal at alpha 0.01: mean set 2.56, singleton on
33.6% at **99.2%** accuracy, set collapsing to ONE REGION on **70.3% at 99.7%**. Regions are cervical / upper
thoracic / lower thoracic / upper lumbar / lower lumbar / sacral.

**Why this is the right form of the claim.** No published system reaches 99% per-level on plain radiographs; the
best whole-spine identification found is 96.5% on MRI, where the model can count from C2. The defensible claim is
"among the vertebrae it names, right 99% of the time, and it names X%" - and X is now measured. A hierarchical
answer ("lower lumbar") is clinically actionable and annotators prefer it to a flat candidate set.

**Caveats that must travel with the number.** This is RENDERS, not real film: the calibration set for a deployed
claim must be real panels, because a render-calibrated threshold is not a threshold (conformal coverage has been
measured collapsing from 0.90 to 0.07 under corruption). Class-conditional 99% needs >= 99 real calibration cases
PER CLASS (>= 2,673 at 27 classes). Certifying 99% selective accuracy one-sided at 95% confidence with zero errors
takes ~298 answered cases. And below 50% full-coverage accuracy, abstention can LOWER accuracy on the answered set
(Jones et al. ICLR 2021 Prop. 1) - our real-panel agreement is 49%, on the wrong side of that line, which is
exactly why the real-film calibration set matters.

**Unoccupied ground.** The VerSe organisers asked in 2021 for algorithms that "identify (and skip processing) a
rare case". Nobody built it. A rigorous selective-prediction treatment of vertebral level identification,
validated on real films, appears unpublished. See [[fluorocap-prototype-and-lstv-arm]], [[lstv-data-landscape]].
