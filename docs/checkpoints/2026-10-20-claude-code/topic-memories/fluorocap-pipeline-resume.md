---
name: fluorocap-pipeline-resume
description: "How to resume the FluoroCap vertebra-level pipeline without losing work: the computed state tool, the resume doc, and the rule that a stage not in the tool will be lost"
metadata: 
  node_type: memory
  type: project
  originSessionId: e44eca96-f48c-494d-ba1f-7dae68bdf06d
  modified: 2026-09-16T07:54:45.724Z
---

**Start here, every session, before anything else:**
`spinesurg-ct-nnunet/docs/PIPELINE_RESUME.md`, then run the state tool on the grid:

```
ssh go2432@grid.wayne.edu
~/mambaforge/envs/spineps/bin/python ~/spinesurg-ct-nnunet/tools/pipeline_state.py
```

**It is COMPUTED, not written.** Every stage declares the artefact that proves it finished; status comes from
that predicate plus `squeue`. Predicates are files or `glob:<n>:<pattern>` (at least n matches), never a bare
directory, because a directory appears the moment a job starts and would report a running stage as done. It
writes `~/model_night/PIPELINE_STATE.md` and `.json`, lists the exact command for every ready stage, and
submits nothing.

**THE RULE: if you add a pipeline stage, add it to `tools/pipeline_state.py`.** A stage that exists only in a
shell history is a stage that will be lost. This tool exists because `recurrent_order.py` opened `rung_0.npz`
by a hard-coded name, every bank built after 2026-09-14 has rung 1 only, and the project's best model therefore
stopped being run for months with nobody noticing. See [[recurrent-head-restored-2026-09-16]].

`spinesurg-ct-nnunet/CLAUDE.md` now points at the resume doc as its first line.

**Companion tools that also recompute rather than record:**
- `tools/xray_dataset_usage.py` -> which X-ray datasets reach a training bank and why the rest do not, counted
  from the banks' own case arrays (`docs/XRAY_DATASET_USAGE.md`).
- `tools/pipeline_state.py` -> stage status.
Both regenerate; do not hand-edit their outputs.

**Standing conventions the resume doc spells out:** never quote an accuracy without its bank, class count and
whether a head was used; report real radiographs and CT renders separately; weak literature labels are not
ground truth; a run-level head is only valid with the encoder it was trained on and the prototype now refuses
a mismatch.
