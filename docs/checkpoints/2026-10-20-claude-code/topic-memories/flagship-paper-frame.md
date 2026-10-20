---
name: flagship-paper-frame
description: "Greg 2026-09-23 -- the paper ships a network, not a feasibility study: SOTA detection on real fluoroscopy, DRR->fluoro transfer, released per-device formation parameters, the released corpus, released weights; payload = naming transitional levels vs surgeon+LevelCheck; new title; every superlative verified in SchwingNet/CLAIMS_LEDGER.md; pending numbers are \\PENDING macros that fail check_limits"
metadata: 
  node_type: memory
  type: project
  originSessionId: f1bdbd78-151f-470b-b703-dd9af9b3fecc
  modified: 2026-09-23T06:09:35.604Z
---

Tone and title change ordered 2026-09-23 03:00. The five contributions and the payload are written into
`docs/FLAGSHIP_PLAN.md` ("What the paper claims") and worked by workflow `paper-reframe-flagship`:

1. detection on real C-arm fluoroscopy beating the published comparators (or the sentence is rewritten);
2. synthetic-to-real transfer from DRRs (the published gap: Pelphix 99.2 % sim -> 71.7 % cadaver; our own
   renders-only detector 71.67 % on real film);
3. **release** of the per-device nine-term image-formation parameters (refit the Elekta card first -- it was fitted
   on 40 frames from three cases, [[data-audit-99-gaps]]);
4. **release** of the corpus (rendered CT + film + real fluoroscopic frames with 3-D truth, synthetically
   augmented) -- the "largest" axis established against published corpora before claiming it;
5. **release** of the weights for OR inference and retrospective analysis.

Payload: naming the level on a transitional spine at parity with or better than surgeon + LevelCheck
([[flagship-program]] G6). Tie-up figure: every phenotype (L6, T13, sacralised L5, four-lumbar, ordinary) across
every modality (CT/3-D surface, plain DRR, styled DRR, released film, real C-arm) with empty cells NAMED
(workflow `transitional-gallery`).

**Rules that bind the rewrite:** invent no number -- a pending quantity is `\PENDING{gate}{what}` and
`check_limits.py` fails while any remain; every superlative has a row in `SchwingNet/CLAIMS_LEDGER.md` naming the
comparator, its citation and the evidence file or gate; the C-ArmLSpine L6 truth is a VERIDAH morphology read, not
a count, wherever it is shown or quoted.

**Future work in the paper:** morphology interpolation / biomechanically-bounded deformation of the transitional
CTs ([[morphology-deformation-feasibility]]) and the rotational-sweep -> patient-specific 3-D preview
([[oblique-angles-and-sweep-vision]]) -- both stated as directions with the data that exists, not as claims.
