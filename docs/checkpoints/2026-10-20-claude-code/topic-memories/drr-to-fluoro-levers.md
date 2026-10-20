---
name: drr-to-fluoro-levers
description: "The three measured levers for DRR->real-fluoroscopy transfer, what is refuted (CycleGAN/ADDA), and the honest ceiling -- verified 2026-09-20"
metadata: 
  node_type: memory
  type: reference
  originSessionId: f1bdbd78-151f-470b-b703-dd9af9b3fecc
  modified: 2026-09-21T00:18:17.565Z
---

Deep-research pass, 107 agents, adversarially verified, 2026-09-20. Settles what to build for
sim-to-real transfer of a vertebra DETECTOR and, as usefully, what not to.

**The three levers, all from matched controls evaluated on REAL images:**

1. **Simulation fidelity** -- naive DRR -> DeepDRR moves real-image landmark error 78.2 -> 34.4 -> 26.9 ->
   24.7 mm; **~68% of the gain is the polyenergetic multi-material attenuation step alone**, scatter
   and learned decomposition are the remainder. `tools/render_physics_drr.py` ALREADY does this.
   (PMID 31187399.) This is why noise realism measured at only 11.6 points here -- noise is the small
   term, and it behaved like one.
2. **Strong domain randomization** -- the lever that was unpulled. SyntheX: 6.44+/-7.05 mm with zero real
   training images vs 6.46+/-8.21 real-trained, Dice 0.86 vs 0.79 at P=2.3e-5, on 366 real cadaveric
   C-arm images. Our renderer randomized only *physically plausible* params = SyntheX's "regular DR".
   (doi:10.1038/s42256-023-00629-1 Table 1.) Implemented as `tools/strong_dr.py`.
3. **Scale** -- 1k->10k renders: 6.61->5.95 mm, SD 7.27->3.52.

**REFUTED -- do not spend grid time here:** CycleGAN 6.62+/-6.82 and ADDA 6.41+/-6.27 vs 6.44+/-7.05 for *no
adaptation*. Indistinguishable, point estimate worse, and both require real target-domain images at
training time. So "convert my DRR corpus to fluoro with a network" is measured and buys nothing.

**Two caveats the parity number cannot travel without:** the landmark difference is NOT significant
(P=0.14) -- an underpowered null; and the real-trained control is data-starved at ~310 images/fold.
SyntheX shows synthetic beats a *small* real set, not a large film corpus.

**The caveat that binds us:** every published parity figure is at HIGH confidence / LOW coverage, and
collapses at lower thresholds. On DeepFluoro synth-CT beats real-CT at NCC 0.60, ties at 0.40, LOSES
at 0.20. Counting needs recall >=0.97 (compounds to 0.74 over ten bodies), i.e. the high-coverage end.
**So report recall as a CURVE, never one threshold.** (arXiv:2606.21414.)

**The honest ceiling -- state it, don't hunt a number to beat.** No published system detects and names
vertebrae from real intraoperative fluoroscopy *content* at counting-grade recall, and no per-vertebra
recall on real fluoroscopy is published at all. LevelCheck's 100% imports identity from the same
patient's prior CT/MRI by registration. Pelphix's 99.2->71.7 is surgical-PHASE accuracy, not detection --
the old Tier 4 claim that it agreed with our 71.67% to 0.03 points was a false equivalence, now
withdrawn from `docs/FLUORO_DATASET_STRATEGY.md`. The DeepDRR/SyntheX line reports mm error only and
discards low-belief landmarks without stating the fraction.

See [[detection-is-the-binding-constraint]], [[fluorocap-pipeline-resume]].
