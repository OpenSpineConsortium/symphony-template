---
name: acquisition-space-saturation
description: "The fluoroscopy plateau is where the frames sit in acquisition space, not N. Tested on our data 2026-09-25 (one-view arms, per-angle render arms); Figure 5 b-d now shows it; the claim wording the paper uses and what it does NOT claim (film vs fluoro dimensionality)"
metadata:
  node_type: memory
  type: project
  originSessionId: f1bdbd78-151f-470b-b703-dd9af9b3fecc
  modified: 2026-09-25T17:49:48.311Z
---

Greg (2026-09-24) uploaded an AI-generated review (SchwingNet/lit/acquisition_space_review_2026-09-24): detectors
plateau on fluoroscopy because routine C-arm data over-represents AP/LAT; obliques, tilts, magnifications are
unsampled holes; plot accuracy against coverage / entropy, not N. Greg (2026-09-25): "demonstrate how much they vary
in the extra dimensions of the fluoro ... visualize the learning curve for plain film and the pooled fluoro vs the
dimension separated and grouped fluoro to see if it corrects."

**What our data showed (2026-09-25, nothing retrained; tools/fig_dimension_explore.py, then Figure 5 via
tools/fig_power.py, REVISION_LOG3.md section 10):**
- Naming separated by view rises like film (lateral 93.7 -> 98.1 % by 50 persons; AP 33.8 -> 90.8 % with five, 98.1 %
  with all); the untrained view stays put (lateral-trained on AP 32 -> 55 %); both views trained costs neither.
- Same-device detection plateaus from 24 frames on both views (84 %); one-view arms of 25/50 frames land in the same
  band on their own view (83.0-86.4 %) and find 0.0-39.5 % of the other. Separating the view does NOT lift the plateau.
- Renders, 40 unseen subjects, matched N along the lateral angle: AP+LAT-pose arms 82.1 % at the trained angles vs
  52.8 % over the 16 other bins; 2N 94.2 / 64.8 %; the arc arm 80.7 / 77.1 %. More frames at the same poses fill no gap.

**The claim the paper makes:** accuracy follows where the frames sit in acquisition space, not how many there are;
frames of one cell do not transfer to another. **Not claimed:** that fluoroscopy is higher-dimensional than film. The
bank records no projection angle, distance or magnification for any film corpus (DICOM_VARIABLES.md map not built),
and film has its own non-transferring dimension, corpus (NHANES II -> CSXA 74 % at best).

**How to apply:** Figure 5 is (a) persons needed, (b) naming vs persons on film AND the C-arm per view, (c) same-device
detection vs frames with one-view arms, (d) render arms vs lateral angle; the pooled N-vs-coverage fit keeps its numbers
in Results without a panel. Interpretation goes in the text, captions stay terse. Cite nothing from the AI review;
claims go through SchwingNet/lit/CITABLE_CLAIMS.md. Caveat for panel d: the Surgio card renders thick laterals
photon-starved, so the +-90 degree bins conflate geometry with synthetic underexposure. Related:
[[six-figure-paper-plan]], [[oblique-angles-and-sweep-vision]], [[resume-2026-09-24]].
