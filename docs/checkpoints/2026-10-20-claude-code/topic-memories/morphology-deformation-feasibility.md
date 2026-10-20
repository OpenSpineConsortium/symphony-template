---
name: morphology-deformation-feasibility
description: "Greg 2026-09-23 rejected a bespoke CT warp -- \"I wanted some proven validated state of the art approach from the literature, not you to just hack something together\"; morphology synthesis must be a PUBLISHED, validated method chosen from docs/MORPHOLOGY_SYNTHESIS_PRIOR_ART.md (workflow spine-synthesis-prior-art), and Greg decides before anything is built"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: f1bdbd78-151f-470b-b703-dd9af9b3fecc
  modified: 2026-09-23T06:18:37.131Z
---

**The correction.** I had started implementing my own deformation (per-vertebra rigid transforms blended into a
smooth displacement field, bounded by Panjabi ROM). Greg stopped it: he wants a **proven, validated, state-of-the-art
method from the literature**, not something assembled in-house. The workflow was stopped with nothing built.

**Why:** a homemade warp carries no external validation, and this project's recurring failure is exactly a
plausible-looking result from a step nobody else has checked. A published method comes with a validation metric, a
number, a dataset and often code -- all of which the manuscript can cite, and a reviewer can check.

**How to apply -- and this generalises beyond deformation:** when a new capability is needed (synthesis, a loss, an
augmentation, a registration), **search the literature for the validated method first**, report what each candidate
was validated against with the number, verify the top candidates against the papers themselves, and bring Greg a
recommendation. Build something bespoke only when the survey shows the field has nothing that meets the
requirement -- and say so in that sentence.

**Context that still holds:** `ostk.surgery.simulate_correction` rotates segments for labels only; its CT warp was
never built and its end plates were too rough to re-measure ([[postop-spine-synthesis]],
[[postop-jaggedness-future]]). Whatever is adopted must output a CT whose DRR still looks like a radiograph, keep
labels aligned, and let synthetic variants carry the SOURCE PATIENT KEY so a generated copy of a person cannot leak
across the split. Related: [[flagship-paper-frame]], [[flagship-program]], [[data-directives-2026-09-23]].
