---
name: fluoro-panel-gap-diagnosed
description: "Why literature fluoroscopy panels score 19.7% against 95.1% on real radiographs: domain plus structural contamination. NOT crop quality, and NOT resolution -- a paired test refuted the resolution reading"
metadata: 
  node_type: memory
  type: project
  originSessionId: e44eca96-f48c-494d-ba1f-7dae68bdf06d
  modified: 2026-09-16T05:54:51.322Z
---

Measured 2026-09-16 with `tools/panel_vs_film_stats.py`, `panel_label_audit.py`,
`panel_contamination_audit.py`, `panel_region_arbitration.py`. Outputs in `~/model_night/panel_stats/`.

**Three evaluation surfaces, one model (`model_r18_ce`, allspine_v2), and they are not comparable:**
real radiographs 95.1% (n=7,339), CT renders 65.5% (n=9,053), literature panels 19.7% agreement (n=7,065).
Real-film breakdown: CSXA 99.4, BUU 90.3, NHANES 92.7/90.6. Mid-lumbar is the real-film floor:
L3 82.9, L2 87.1, L4 89.8.

**Crop quality is NOT the explanation.** On sharpness, noise, contrast, SNR and grey-level count the
literature crops sit inside the real-film range (they are sharper than CSXA and have better SNR than BUU).

**NATIVE RESOLUTION IS NOT, AND THE CROSS-SECTIONAL NUMBER THAT SAID OTHERWISE WAS A CONFOUND.**
CORRECTED 2026-09-16 by a paired experiment. The descriptive gap is real: vertebra height in the SOURCE image is
NHANES 198-212 px, BUU 176, CSXA 162, all 0% magnified, against a literature median of 49 px with 81% magnified
to reach the 96 px target. Read cross-sectionally, agreement rises from 14.8% on panels whose vertebrae are
under 30 px to 26.1% at 70-96 px, +11.2 points, which looks like resolution causing accuracy.

It is not. Magnifying the SAME vertebra reproduces none of that rise. On 1,467 paired panels and 6,652
vertebrae, going from 36 px to 88 px (6.25x the pixels) moved exact agreement by **-0.33 points**, CI95 -0.88 to
+0.22, McNemar z 1.12; two further configurations gave -0.03 and -0.53. Against the real pre-refetch JPEG the
gain is under one point and that arm also carries compression. A positive control confirmed the harness can see
resolution at all before the null was accepted (`tools/hires_ladder_eval.py`). The association is a property of
WHICH PANELS have big vertebrae, not of the pixels.

**Resolution IS the lever for FINDING vertebrae, not naming them.** Same panels, same detector: full resolution
returns 6.4% more vertebrae, and panels where the detector found nothing fall from 60 to 39 of 397 (28
hires-only against 7 lores-only, McNemar z 3.38). So refetch to raise coverage, never to raise accuracy.
Evidence: `~/model_night/hires_track/`.

**Contamination is real but secondary: 11.5% of panels, 22.6% of scored vertebrae.** 109 panels the
corpus's own VLM blind read called MRI, CT or photograph; 289 montages where one figure panel holds two
or three separate films and the decoder ran ONE cranial-to-caudal name run across boxes from different
acquisitions. Rendering 12 panels is what exposed this; no aggregate statistic had.

**Labels are imperfect but not mostly wrong.** Not circular: only 7.8% of caption-decided labels equal
the previous network's own output. Where label and network disagree on REGION (34.5% of panels), an
independent blind read sides with the LABEL 72.7% and the network 27.3% (caption-decided, non-circular).
So the network really is failing on these images.

**Signature says domain, not counting:** only 17.5 points of disagreement is off-by-one; two thirds is
off by two or more. On real film the same model is within one level 98-100%.

**How to apply:** never quote the 19.7% as accuracy -- it is agreement with a weak label. Gate the corpus
on modality, montage and source resolution before training on it. Related: [[fluorocap-dataset]],
[[recurrent-head-restored-2026-09-16]].
