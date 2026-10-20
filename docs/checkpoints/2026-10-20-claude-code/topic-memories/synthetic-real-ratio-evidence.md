---
name: synthetic-real-ratio-evidence
description: Deep research 2026-09-23 -- no DRR paper ever swept synthetic:real; adjacent sweeps flatten at 4:1-10:1 (real 10-20% of the mix); two-stage pretrain -> full-depth fine-tune; 4x oversampling of real rare frames; variant in 25-35% of rendered CTs via CT choice; 200-500 renders/CT; 300-500 real frames/device
metadata: 
  node_type: memory
  type: reference
  originSessionId: f1bdbd78-151f-470b-b703-dd9af9b3fecc
  modified: 2026-09-23T05:01:05.063Z
---

Report: `spinesurg-ct-nnunet/reports/Synthetic real ratio X-ray detectors.md` (119 citations; notes under
`research_notes/Synthetic real ratio X-ray detectors/`). Recommendation table in its section 6.

**The finding the manuscript can state in as many words:** every physics-rendering paper (DeepDRR, SyntheX,
Pelphix, FluoroSAM, Toth, i3PosNet, Kausch, Rapuri) trains synthetic-only and tests real -- **no DRR study has swept
the synthetic-to-real ratio or the real-frame count.** The window comes from generative CXR (RoentGen, Moroianu,
Khosravi, Dushenev), one guidewire study (Tang 2026), dermatology (Sagers) and street-scene YOLO: gains flatten
at **4:1-10:1**, real at **10-20 %** of the mix, slight loss past 10:1; in pretrain-then-fine-tune the ratio stops
mattering (565k synthetic -> <10k real matched 66k real).

**Numbers to reuse:** Barr 2026 cervical-landmark curve -- synthetic prior worth 2.6-4.3x lower error at 100-400
real, gone at 600-700 (check its de novo n=700 value against the paper before quoting). Gherardini: 240 real fluoro
frames took a synthetic-pretrained segmenter Dice 0.10 -> 0.55. SyntheX: renders/CT flattened at 250-500
(20 CTs; CT count never ablated); realistic 9.05 vs naive 20.55 mm only under strong DR; CycleGAN 6.59 vs 6.29 at
scale (adds nothing). VERIDAH: 4x epoch-level oversampling of ~60-83 real anomaly CTs -> 96.3/97.2 % TEA/LEA
recall, 99.18 % scans correct, no ablation. VerSe: L6 became learnable with **85 distinct scans (~34 % of
junction-visible)**, T13 with 6 never stabilised. Dushenev: rare recall peaks at 4x while PR-AUC falls
(operating-point shift) -> **report rare recall with PR-AUC and common-class precision**. ISIC 2019: parity
rebalancing -> nevus sensitivity 0.35. CXR classifier knee ~20k images; resolution optimum 256-448 px (ResNet-18 at
1024 px is not resolution-limited; the detector is). Two-stage beat joint at 160 real; freezing layers cost up to
13.5 %.

**Absent everywhere (say so):** any DRR ratio sweep; what 10/50/100 real frames buy on a DeepDRR-class corpus;
synthesis of L6/T13 with per-class results; distinct-CT vs renders-per-CT ablation; X-ray curricula/upweighting;
fidelity x ratio; a YOLO learning curve on 1024-px radiographs.

**The experiment this project can be first to publish:** a real-frame learning curve per device (50/100/200/400)
with the transitional class scored separately, and distinct CTs varied against renders per CT.
Related: [[two-mechanisms-thesis]], [[lstv-tltv-detection-goal]], [[l6-sample-count-and-counting-decoder]].
