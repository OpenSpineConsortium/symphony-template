---
name: two-mechanisms-thesis
description: "THE PAPER'S THESIS from 2026-09-23 00:20 -- morphological classification gives quick cheap limited-FOV localisation; the iterative sweep/count from the anchor is the safety net that catches the extra-vertebra case; disagreement is the signal"
metadata: 
  node_type: memory
  type: project
  originSessionId: f1bdbd78-151f-470b-b703-dd9af9b3fecc
  modified: 2026-09-23T04:03:11.806Z
---

Greg, 2026-09-23 ~00:20, on seeing the k-in-field curve: *"if I can just do limited FOV morphological
classification the whole iterative stepwise process is essentially unnecessary except for spines with an extra
vertebra, so it serves as a second check, and since this is patients' lives at stake it offers a safety net
while the morphological classifier offers quick and cheap localization."*

**This is the framing the SchwingNet manuscript is held to.** Two mechanisms, complementary failure modes:

| | morphology classifier (level model) | count from the anchor (sweep) |
|---|---|---|
| what it reads | the body and its neighbours (320-px crop, target 96 px; BiGRU over the run) | geometry: bodies + sacrum, linked frames; names nothing |
| cost | one exposure | a sweep of overlapping exposures |
| limited FOV, real C-ArmLSpine lateral | 1 body 72.9 % (90.2 % +/-1); 3 bodies 92.9 %; 5 bodies 97.0 %; whole frame 98.2 % | undefined from one frame without the anchor; that is what the sweep is for |
| the extra vertebra (L6 / T13) | **L6 44.9 %** (feasibility-claims-measured); T13 ~0 % -- an extra body looks like its neighbours | counts it: 45/54 transitional runs exact, 36 L6 (RSNAI_CLAIMS lstv_*) |
| what limits it | morphology has no signal for an extra body | DETECTION (80.5 / 76.8 % held-out device) |

Because one reads morphology and the other reads geometry, their errors differ, so **agreement carries
information and disagreement is the stop signal**. The classifier answers first (cheap); the sweep verifies;
a disagreement flags the case. Patients' lives: the net is not optional.

**What must be measured (not asserted) to support it:** (1) agreement analysis on the same real frames where the
sacrum is detected -- classifier name vs count ordinal->name: agreement rate, accuracy given agreement, how often
the count catches a classifier error and vice versa (counting ordinals from workflow `w3stdna1e`; classifier
names from `proto/cv_fold*/det/kfull` and `proto_v9/` once A12 lands); (2) the same on the anomalous spines
(L6/T13 renders and any real transitional case), where the net has to hold.

Consequences: the level model stays central (A13 revised); Figure 3a (k-in-field) is the limited-FOV headline;
the sweep is presented as verification, not as the primary localiser; Key Points name both roles. The
27-level posterior is therefore NOT unnecessary -- it is the cheap first answer.

Related: [[figure-preferences-schwingnet]], [[no-unexplained-subsets-fix-not-disclose]],
[[feasibility-claims-measured]], [[detection-is-the-binding-constraint]], [[schwingnet-manuscript]].
