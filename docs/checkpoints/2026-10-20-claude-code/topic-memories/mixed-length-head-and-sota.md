---
name: mixed-length-head-and-sota
description: "Training the run-level head on mixed band lengths gains +3.8 points at 3 vertebrae; the random-window test clears the stereotyped-span shortcut; and no published plain-radiograph naming accuracy is metric-comparable"
metadata:
  type: project
---

**TRAIN THE RUN-LEVEL HEAD ON MIXED BAND LENGTHS, NOT ONE LENGTH PER HEAD.** `recurrent_order.py` trains a
separate net per k, each seeing windows of exactly 2k+1. `tools/head_mixed_length.py --train-mode mixed` samples
a fresh length and offset every epoch and produces ONE head. Held-out real radiographs, allspine_v2, seed 0:

| visible band | fixed-length training | mixed-length training |
|---|---|---|
| 3 vertebrae | 93.69 | **97.47** |
| 5 | 95.08 | **98.45** |
| 7 | 95.65 | **99.29** |
| 9 | 99.73 | **99.92** |
| random 2-9 | 96.65 | **99.02** |

The gain is concentrated at SHORT bands, which is the intra-operative case: +3.8 points at three vertebrae.
Whole-spine 27-class including renders: 83.63% at a band of 3, 89.25% at 9.
This implements the one transferable instruction from the length-generalization literature for a 3-to-9 range
where every length is trainable: sample all lengths, do not change the positional scheme.

**THE STEREOTYPED-SPAN SHORTCUT IS REAL BUT SMALL, AND ONLY FOR FIXED-LENGTH TRAINING.** Every BUU film shows
exactly L1-L5, so a run model could learn the collection's span instead of the anatomy. `--eval-mode random`
scores each vertebra inside a window of random length at a random offset, removing the film's endpoints as a
cue. Fixed-length training drops 99.73 -> 96.65 (3.1 points of the band-9 number was the span). Mixed-length
training drops only 99.92 -> 99.02. **Quote 99.02% as the shortcut-free real-film number.**

**STATE OF THE ART: THERE IS NO METRIC-COMPARABLE PUBLISHED NUMBER ON PLAIN RADIOGRAPHS.** Verified 2026-09-16.
- Cina 2021 (Sci Rep 11:9482) "98.4%" is a 24-element sigmoid PRESENCE vector over the whole film, a joint
  run-level decision, and on a lumbar film most neurons are correctly zero, so the denominator is permissive.
  Architecturally it compares to our run-level arm, not to a single-crop one.
- VertXNet (Sci Rep 2024) reports NO naming accuracy at all, only Dice 0.90 and Panoptic Quality. It names by
  finding C2 or S1 and counting; its own authors state it fails when neither anchor is in frame.
- BUU-LSPINE baseline reports only 5-class detection mAP (81.93 AP / 83.45 LA at IoU 0.5:0.95).
- SpineCLUE 97.9-98.7% ID-rate is 3-D CT with segmentation-mask input on VerSe19/20, not film.
- LevelCheck, the intra-operative state of the art, is NOT classification: it is 6-DOF 3D-2D registration that
  IMPORTS the level identity from a preoperatively labelled CT or MR. Its 99.998% is a <5 mm geometric success
  rate over 50,000 simulated projections from 10 CTs. **That is the system our registration-free approach is
  positioned against, and it needs a prior cross-sectional study we do not require.**
- The one verified clinical-utility result: a 5-surgeon, 62-hard-case reader study where median vertebral
  localisation error fell from 30.4% to 2.4% (p<0.01) with the aid.
- NEGATIVE and important: the mid-lumbar floor, short-run non-vertebral cues, and "what else moves accuracy"
  returned NO surviving evidence. Every candidate claim was voted down. Those are open problems.

Related: [[recurrent-head-restored-2026-09-16]], [[fluoro-panel-gap-diagnosed]].

**Correction 2026-09-22:** the real-film pool counts NHANES twice and 89 % of NHANES validation patients have their duplicate in training ([[nhanes-double-inclusion]]). Clean per-source v2 seed-0 random-window figures: CSXA 99.87 % (3,720), BUU-LSPINE 98.04 % (2,698).
