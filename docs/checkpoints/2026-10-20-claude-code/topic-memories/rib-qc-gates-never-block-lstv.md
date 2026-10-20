---
name: rib-qc-gates-never-block-lstv
description: On rib reviews only rib-purity checks gate; structure_integrity + rib_vertebra_match are advisory (spine is force-restored; LSTV shifts ribs)
metadata: 
  node_type: memory
  type: project
  originSessionId: 436e5c70-681e-4f38-aab2-30dfa25af7b5
---

On a **rib review** the server force-restores the radiologist spine, so the ONLY checks that may GATE a submit are the rib-purity ones the student actually controls: `rib_label_mixing` and `rib_spine_gap`. Everything touching vertebrae is **advisory**:

- `structure_integrity` -- inspects only spine/pelvis bones (ids 1-33), all force-restored to v4. Gating on it blocks students on a **pre-existing v4 pseudo defect** (a split vertebra) they cannot fix -> impossible block. Advisory on `check=="ribs"`.
- `rib_vertebra_match` -- assumes rib-N <-> T-N, which **transitional anatomy legitimately breaks**: a rib on L1 (13th-rib / LSTV, the dataset's TARGET phenotype) shifts every rib one level, so gating blocks exactly the cases we exist to keep. Now transitional-aware (reads lumbar 8-25; a lumbar-articulating rib -> LSTV note + flag for re-read, not "misnumbered") AND advisory.
- `rib_numbering` -- already advisory (an FOV-clipped rib reads as 2 pieces).

Also: the server reject reason lists **only genuine gating failures** -- advisory "X" lines are downgraded to "note:" in `check_label` so students don't chase warnings that never blocked them.

**Why:** two students ([student 1], [student 6]) hit ALL-CHECKS-PASS-but-submit-fails because the submit gate validated the force-restored spine / transitional rib shift -- anatomy, not their error. See [[lstv-reread-queue]], [[thoracic-gt-fov-limited]], [[rib-approach-ts-trust]].
