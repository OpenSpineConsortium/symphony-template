---
name: data-audit-99-gaps
description: "The 2026-09-23 audit of every dataset -- 99 gaps (28 bug, 21 unfinished, 4 budget, 15 unknown, 31 criterion) in docs/DATA_COMPLETENESS_AUDIT.md; the ones that change the science: Elekta card fitted on 40 frames from 3 cases, COBRA Varian never solved, 5,013 duplicate COBRA frames in one arm's training, case134's spot frames exist inside CBCT/, case118's \"lateral\" is a -58 deg oblique, CT 0533 truncated in the PUBLIC release, HF mirror still v10"
metadata: 
  node_type: memory
  type: project
  originSessionId: f1bdbd78-151f-470b-b703-dd9af9b3fecc
  modified: 2026-09-23T06:03:28.398Z
---

`spinesurg-ct-nnunet/docs/DATA_COMPLETENESS_AUDIT.md` (rebuilt by `tools/build_audit_doc.py` from the workflow
journal after a usage limit killed the synthesis; twelve verify/repair agents never ran -- the document says so).
Each gap carries release count, disk count, used count, a reason class and a repair plan.

**The findings to act on before any final training** (they are D-rows in `docs/RESUME_2026-09-22_PM.md`):
- **The Elekta device card was fitted on 40 frames from three cases** (A002/A004/A0xx) -- the nine-term physics
  parameterisation the whole style pipeline rests on. Refit on the full 692.
- **COBRA Varian (225 cases) cannot be exported**: `export_case` returns "Varian geometry not solved (out of
  scope)" -- the patient->RTK axis map exists only for Elekta.
- **Leak, not a shortfall:** derived banks `cobra_elekta_v2/_ap45` were globbed into one detector arm's training
  (5,013 duplicate frames) and 338 into its validation; `ready()` excludes only "smoke" and "_multi".
- **C-ArmLSpine case134's AP and lateral exist** as extension-less XA files inside `case134/CBCT/` (the builder
  walked only `C-arm/`), and **case118's exported "lateral" is an oblique at -58.1 deg** (the OBL view class landed
  in commit 0b0424d, after that build). Both rebuildable.
- **CT 0533 is a truncated gzip in the PUBLIC release** (identical bytes on HF), and the **HF mirror still serves
  v10 labels** (the withdrawn S1 carve) -- supersedes [[grid-ct-0533-truncated]], which called it a local defect.
- VerSe: 10 of 319 VerSe'20 series never downloaded; `verse_soft_drr` has the row-spacing defect on 181 of 374;
  `ctsp_drr_obl/obl2` (3,767 renders) came from the wrong tree with C1-T9 stripped.
- TotalSegmentator: SPINEPS produced no mask for 110 of 1,228 v2 CTs (72 whole spines, undiagnosed); v3 never benched.
- NHANES II: release is **17,075 entries, all but two on disk** (CDC serves those two as 0 bytes); only 543 used.
- **VinDr's 744 / 2,632 / 10,274 are three different objects** (old lateral-only films / current bank crops /
  pseudo-labelled renders) -- not three counts of one thing.
- Dataset815 (1,176 cases, the L6 set) never consumed: both prep jobs died on a missing singularity path.
- SpineSAC has no bone truth because TotalSegmentator returned empty masks on all three sawbone CTs.

Related: [[data-directives-2026-09-23]], [[flagship-program]], [[nhanes-double-inclusion]], [[drr-row-spacing-defect]].
