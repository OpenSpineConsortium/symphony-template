---
name: no-unexplained-subsets-fix-not-disclose
description: "Greg 2026-09-22 -- a \"convenience subset\" of a public dataset is an error to fix (use all of it), every dataset gets described in prose not just a table, and a leaked initialisation is fixed by retraining, not disclosed"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: f1bdbd78-151f-470b-b703-dd9af9b3fecc
  modified: 2026-09-23T03:49:12.917Z
---

Greg, reading the SchwingNet Methods, 2026-09-22 ~23:40: *"wtf is up with all the subsetting of my datasets?
... I don't even see DeepFluoro? why aren't all the datasets described in the prose? you just assume they will
read the table?"* and, on the sentence disclosing that the encoder was initialised from a leaked bank:
*"obviously these errors should be fixed before the final manuscript is done."*

**Why:** the Methods said COBRA2026 was a "convenience subset (152 of 692 cases downloaded)". The truth in
`docs/DATASHEET.md` is that the fetch was cut by download budget (42 GB per 152 cases), not by any criterion;
26 Varian cases sit unused although a Varian card exists. And the C-ArmLSpine encoder was initialised from the
v7 bank, which leaks patients between its own splits; the manuscript disclosed it instead of fixing it.

**How to apply:**
- Use ALL of a public dataset unless a stated scientific criterion excludes cases; a download budget is not a
  criterion. If a subset is unavoidable, say the real reason in one plain sentence.
- Every dataset in the study gets its own prose sentence in Methods (what it is, how many, role, what was
  excluded and why) -- the table is a summary, not the description. DeepFluoro was missing from the prose.
- A leak in an initialisation or a base model is a defect to REPAIR (re-initialise from the clean bank, re-run),
  never a caveat to carry into the final manuscript.
- The same standard applies to "not quoted from" disclaimers: if a number depends on a leaked artefact, redo it.

Related: [[schwingnet-manuscript]], [[split-leak-cross-naming]], [[identity-audit-findings]],
[[rigor-audit-findings]].
