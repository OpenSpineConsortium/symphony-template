---
name: stc-does-not-transfer
description: "Star Temporal Classification does not transfer to vertebra naming, and the reason is structural: it marginalises over an alignment we already know. Penalty sweep and blank-class fix both refuted."
metadata: 
  node_type: memory
  type: project
  originSessionId: e44eca96-f48c-494d-ba1f-7dae68bdf06d
  modified: 2026-09-16T11:02:00.024Z
---

**RESULT: the star loss loses to plain cross-entropy everywhere on this task. Do not revisit it without a new
argument.** Measured on allspine_v2, k=3, held out, 2026-09-16. Three arms, identical embeddings, architecture,
schedule and seed, differing only in the loss and in which names were withheld:

| regime | ce_full | ce_kept | stc | stc, transitional stratum |
|---|---|---|---|---|
| withhold T13/L6 only (0.6% of names) | 87.26 | 86.79 | 86.7 | **22-24** vs ce_kept **39.8** |
| withhold 50% at random | 87.27 | 86.83 | 77.9 | 40.2 vs 47.2 |
| withhold 70% at random | 87.2 | 86.86 | **44.6** | 38.6 vs 46.6 |

**Two candidate explanations were tested and BOTH REFUTED.**
1. Wildcard penalty. Swept 0.5, 2, 5, 12 -- a 24-fold range. Transitional accuracy moved 22.2 -> 23.4, about
   one point. Not the hyperparameter.
2. No blank symbol in the alphabet. The star's score is the relative complement log(1-p(y)), so without a
   neutral class the model must assert a WRONG vertebra name to satisfy a wildcard; speech has blank, a 27-name
   alphabet does not. Added a 28th never-a-target class. Transitional went 22.3 and 24.3 -- unchanged. Refuted.

**THE ACTUAL REASON, and it is structural.** Connectionist temporal classification and its star variant exist
because in speech the ALIGNMENT IS UNKNOWN: many frames map to one token and the loss must marginalise over
every monotonic assignment. Here the alignment is KNOWN exactly -- the detector says which box each name belongs
to. Feeding that to an alignment-marginalising loss throws the alignment away: with U names and N>U positions
the lattice lets the names slide across the run, and the gradient is smeared over assignments we already knew
the answer to. That is why the damage vastly exceeds the 0.6% of positions actually withheld: the star graph
rescores the WHOLE run, not just the unnamed member.

**What to use instead.** A withheld name here is a per-position missing label at a KNOWN position, not an
unaligned transcript. The right treatments are (a) simply ignore it, which is the `ce_kept` arm and already
works, or (b) a candidate-set / partial-label loss at that known position. This agrees with the partial-label
pass: the consistent PLL losses operate per position and assume the truth lies in the candidate set, and
flagging an out-of-template spine must be a separate mechanism, which it is.

Code kept for the record: `tools/stc_head.py` (self-test passes, reduces to cross-entropy exactly under full
supervision, 3.6e-15), `tools/train_stc_head.py`, `slurm/stc_arm.sh`. Results in `~/model_night/stc/`.
Related: [[recurrent-head-restored-2026-09-16]], [[mixed-length-head-and-sota]].
