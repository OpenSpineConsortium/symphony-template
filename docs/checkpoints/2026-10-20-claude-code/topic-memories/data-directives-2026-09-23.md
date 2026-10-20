---
name: data-directives-2026-09-23
description: "Greg's binding orders 2026-09-23 -- every dataset truncation fixed or justified in writing BEFORE any rerun; FluoroCap DROPPED from training; ALL NHANES II (~17k films), ALL VinDr, ALL COBRA (692 cases, every frame), rest of TotalSegmentator v2, SpineSAC/SpinalAI/AASCE/anchor-crop USED; Mendeley excluded (BUU duplicate); C-ArmLSpine frames-per-case checked"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: f1bdbd78-151f-470b-b703-dd9af9b3fecc
  modified: 2026-09-23T05:25:35.991Z
---

After the COBRA "40 per centre" bug, Greg found the corpus table full of unexplained shortfalls and ordered
(verbatim spirit): *"literally every instance of these stupid mistakes should be fixed or justified why they aren't
included before rerunning, except FluoroCap. I don't need that anymore."* The list lives as D1-D9 in
`spinesurg-ct-nnunet/docs/RESUME_2026-09-22_PM.md` ("GREG'S DATA DIRECTIVES"); the audit that found them is
`docs/DATA_COMPLETENESS_AUDIT.md`.

**Why:** a download budget, a truncated file, a stale list, a display bug or "enough for now" is not a scientific
criterion; a subset without a written criterion is selective reporting, and the project's recurring failure is a
plausible number from an incomplete input. FluoroCap is dropped because it is reproductions, not fluoroscopy
([[fluorocap-is-reproductions-not-fluoroscopy]]).

**How to apply:**
- Before training the final bank or any detector arm, walk D1-D9: each closed (data on disk, in the lists) or
  justified in the datasheet in one written sentence.
- FluoroCap never re-enters a training list (test only if annotated).
- "Use all" means all cases AND all frames; a per-epoch sampler over everything is allowed, a fixed subset is not.
- Mendeley-716 stays out: redistribution of BUU-LSPINE, duplicate subjects -- that is the written justification.
- Every doc count (datasheet, NUMBERS, tab_corpus, ATLAS) is re-derived from disk afterwards; no "of N" sentences.
Related: [[no-unexplained-subsets-fix-not-disclose]], [[lstv-tltv-detection-goal]], [[synthetic-real-ratio-evidence]].
