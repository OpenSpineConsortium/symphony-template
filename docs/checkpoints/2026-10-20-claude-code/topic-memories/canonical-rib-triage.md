---
name: canonical-rib-triage
description: The reproducible rib review-set rule is qc_v4_ribs_and_verts.py (label-based); rib_worklist.json is regenerated from it
metadata: 
  node_type: memory
  type: project
  originSessionId: 436e5c70-681e-4f38-aab2-30dfa25af7b5
  modified: 2026-07-21T01:40:04.731Z
---

The dataset's rib review-set selection is now defined by ONE reproducible rule for publication:
**`scripts/qc_v4_ribs_and_verts.py`** -- flags a case iff it fails **rib label-mixing OR rib-spine detachment**, computed **directly from the released v4 labels** (no build-time precomputed fields). Anyone can re-run it on the release and get the identical `rib_worklist.json`.

`rib_worklist.json` (on dataset `anonymous-mlhc/CTSpinoPelvic1K` @v4) was regenerated from it = **152 cases**. The review Space seeds from this file.

**Supersedes** the original triage `scripts/qc_v4_ribs.py` (which used build-time duplicate-rib-id + numbering-gap + extrapolated-rib -- a DIFFERENT rule, not reproducible from labels alone). The original selected ~160; ~17 of those pass the new rule (already reviewed/finalized, harmless bonus coverage) and 4 new cases the old rule missed were added (69, 518, 711, CTC-1018399231).

Same scan also reports: vertebra-in-FOV-not-annotated (interior gaps + ribs-above-spine) and lumbar-rib candidates. See [[rib-qc-gates-never-block-lstv]], [[rib-approach-ts-trust]], [[thoracic-gt-fov-limited]].
