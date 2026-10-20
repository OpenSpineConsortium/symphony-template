---
name: device-sampling-audit
description: What the C-arm cards actually sample (audited 2026-09-22) -- the clip saturates and costs 95-98% of the joint distribution; the typicality gate that replaces it; Cios kVp recoverable from vendor DICOMs
metadata: 
  node_type: memory
  type: project
  originSessionId: f1bdbd78-151f-470b-b703-dd9af9b3fecc
  modified: 2026-09-22T21:49:23.583Z
---

Audited 2026-09-22 after Greg asked whether the renderer samples device distributions or just fits noise to the
existing data. Generated tables, not prose: `docs/DEVICE_PARAM_AUDIT.md` (from the cards + the header census) and
`docs/DEVICE_SPREAD_SWEEP.md` (card-only, so it reproduces from any commit).

**It does sample.** 51 of 114 (device x parameter) pairs are drawn per frame from the card's fitted Gaussian copula,
conditioned on the render's water-equivalent thickness through that device's AEC regression. 54 are held at the
fitted median (kb, sigma_s, sigma_u, b, c, d). 9 values come from DICOM headers; kVp is IN the copula for
bv_pulsera and surgio_b51_dr, and is a vendor constant (120, 125) for elekta_xvi and varian_halcyon.

**The clip was the defect.** `device_style.SPREAD = 0.2` clipped every term to its central 60 %. Two things wrong:
it is a MARGINAL fix for a JOINT problem (the draws that paired an extreme photon count with an extreme blur), and
`np.clip` SATURATES rather than truncates, so an out-of-band draw is pinned to the boundary VALUE. Measured:
a styled frame reaches **1.7-5.1 %** of its device's fitted joint distribution, and **94.9-98.3 % of styled frames
carry at least one pinned term** (3.2-4.4 of the 8-11 terms). The figure is what showed it -- the clipped kVp
histogram is stacked spikes, not a narrowed distribution. Second time rendering settled what numbers did not.

**The replacement is `SAMPLE_MODE = "typicality"`**: draw from the full copula, reject only draws whose Mahalanobis
distance in copula normal scores exceeds the card's own 99th percentile -- the statistic `device_fit.coverage`
already validates each card against on held-out frames. Marginals intact, 99 % of the joint reachable.
`tools/test_device_gate.py` asserts it. **The clip is still the default** until the A/B on real frames decides;
a sampler that reaches more of the distribution is not automatically better training data.

**Gate in normal-score space, never through the quantile table.** The copula maps scores to values through a
41-point piecewise-linear inverse CDF; where a term is discrete (four mAs settings, a C-arm at AP and LAT) that
inverse is not unique, and reading a value back into a score is biased. The first gate did that and shifted a
marginal median by 0.55 SD; the first test then measured typicality the same biased way and reported 88 % for a
gate that was at 99.8 %.

**Cios Fusion kVp is recoverable.** The card says "not recorded in this dataset" because the 366 registered
DeepFluoro frames dropped their technique tags. The same acquisitions' vendor DICOMs carry kVp on 2,654 frames
across 84 values and mA across 14. A per-frame join would recover it. They are ONE dataset in two representations --
never count them as two (see [[fluorocap-is-reproductions-not-fluoroscopy]] for the same trap).

Related: [[k-devices-one-network]], [[learned-formation-refuted-calibrate-instead]],
[[pooled-vs-lodo-device-designs]].
