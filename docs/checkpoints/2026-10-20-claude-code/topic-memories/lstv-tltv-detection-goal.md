---
name: lstv-tltv-detection-goal
description: "STANDING DETERMINATION (Greg, 2026-09-23 01:10, as he ran out of tokens) -- accurately detect LSTV/TLTV (L6, T13, sacralised L5, four-lumbar) from C-arm exposures; every running experiment serves it; resume from docs/RESUME_2026-09-22_PM.md top block"
metadata: 
  node_type: memory
  type: project
  originSessionId: f1bdbd78-151f-470b-b703-dd9af9b3fecc
  modified: 2026-09-23T04:15:55.672Z
---

Greg's last instruction before running out of tokens on 2026-09-23: *"make sure your checkpoint includes this
determination to accurately detect LSTV/TLTV."* This is the goal the rest of the work serves, and it must be
the first thing a resumed session reads.

**The determination.** Accurately detect the transitional vertebra -- lumbosacral (L6, sacralised L5, four-lumbar)
and thoracolumbar (T13) -- from C-arm exposures, because that is the case in which counting from a landmark
fails and wrong-level surgery happens. Not "flag an anomaly" (the R + C rule was withdrawn for exactly that:
it localises nothing) -- NAME THE LEVEL CORRECTLY on a transitional spine, at parity with an ordinary one.

**The architecture that serves it** ([[two-mechanisms-thesis]]): the morphology classifier gives quick, cheap
limited-field localisation (1 body 72.9 %, 5 bodies 97.0 % on real C-ArmLSpine laterals) but is blind to an extra
body (L6 44.9 %); the count from the anchor names nothing and so cannot be fooled by an extra body; coupling
them through ALPHABETS (ordinal from the sacrum x classifier posterior; the winning alphabet is the variant
call, its margin the confidence; disagreement is the stop signal) is the error-correction Greg asked for.

**What is running toward it (2026-09-23 01:10)** -- see the top block of `spinesurg-ct-nnunet/docs/
RESUME_2026-09-22_PM.md` for job ids and where each result lands:
- workflow `alphabet-coupling` -- rule-based coupler `tools/alphabet_couple.py` (+ posterior dump in
  `level_prototype.py`) evaluated on all C-ArmLSpine folds and the THREE REAL L6 PATIENTS (case42, case121,
  case136); differentiable alphabet loss in `head_mixed_length.py`, heads retrained, L6/T13 recall measured.
- workflow `rare-class-parity` -- augmented renders of every transitional CT (VerSe 50 L6 + 6 T13, CTSP 18 L6,
  SPINEPS-called TotalSegmentator candidates, the 3 CBCTs) under many poses and all six cards; v10 bank with a
  STRATIFIED patient split holding out ~40 % of transitional patients; parity test alone vs coupled.
- `tools/anomalous_inventory.py` (job 40416205) -- every transitional spine by source with split tags.
- v9 bank (VerSe by subject) -> A12 clean re-initialised C-ArmLSpine CVs + zero-shot.
- counting-from-sacrum evaluation (workflow `counting-from-sacrum`); full COBRA fetch; pooled detector.

**Rules that bind the goal:** a transitional spine in training under ANY name is not evidence; distinct poses are
augmentation, duplicates are not ([[l6-sample-count-and-counting-decoder]]); TotalSegmentator L6/T13 are
SPINEPS+VERIDAH pseudo-truth, said so; report "not at parity" plainly if that is the result.

Related: [[two-mechanisms-thesis]], [[figure-preferences-schwingnet]], [[no-unexplained-subsets-fix-not-disclose]],
[[anomaly-rule-rc22-evaluated]], [[schwingnet-manuscript]].
