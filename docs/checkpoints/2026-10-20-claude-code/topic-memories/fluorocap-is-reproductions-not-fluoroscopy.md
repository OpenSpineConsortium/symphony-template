---
name: fluorocap-is-reproductions-not-fluoroscopy
description: "72.8% of FluoroCap panels have zero pixel residual; annotate ~200 as a TEST set, not as training data"
metadata: 
  node_type: memory
  type: project
  originSessionId: f1bdbd78-151f-470b-b703-dd9af9b3fecc
  modified: 2026-09-20T20:28:51.300Z
---

Measured 2026-09-20 with the project's own grain statistic over the corpus: **72.8 % of FluoroCap panels
have `noise_mad` exactly 0.000** -- no pixel-to-pixel residual; the press resampled the grain out. What
survives is quantised to 1-3 integer grey levels. Median short side 368 px; only 48 % reach 380.

**This qualifies the renderer's validation.** The histogram (0.187) and noise-spectrum (0.862 raw /
0.986 matched) rows are scored against 27 panels that sit at median 459 px with `noise_mad` 1.483 on
every one -- the top half by resolution  intersect  top quarter by grain, about **9 % of the corpus**. The renderer
was validated against FluoroCap's top decile, not against FluoroCap. The four literature-target rows
(photons, scatter, r(1), generator pinning) are unaffected and stand.

Also true and bounding: **no model in this project distinguishes fluoroscopy from a plain radiograph**
(`fluoroscopy_probability` is a verbatim copy of `p_xray_spine`); `human_qc_status` is `pending` on all
21,603 rows; contamination is 22.6 % of *vertebrae* not panels (montages carry 9.58 labels each vs
4.27); and there is no patient key, so no leakage-free split.

**Annotate ~200 panels as a TEST set, not training data.** Training yield is ~850-1,600 instances clean,
~8-11k relaxed, against the 143,721 that trained a detector already at 0.9914 on real film. But this
project has *no labelled real fluoroscopy anywhere*, so no number states what any of it achieves on a
C-arm image. Per-body recall compounds over 8-12 bodies (0.99 -> 0.92 chain-complete; 0.95 -> 0.66), so
the boundary is 0.97-0.99 and separating those needs ~110 bodies ~ 50-90 panels.

**The sweep cannot be tested on this corpus at all** -- `~/FluoroCap/youtube_video` is empty and no two
panels are one patient at a known displacement. That needs real C-arm pairs from theatre.

See [[detection-is-the-binding-constraint]].
