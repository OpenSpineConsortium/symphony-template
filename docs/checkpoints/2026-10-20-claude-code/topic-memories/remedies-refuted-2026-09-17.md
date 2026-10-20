---
name: remedies-refuted-2026-09-17
description: "Tested 2026-09-17 and refuted -- pretrain-on-DRR-then-finetune, film-noise randomisation, anchored-only and CReST pseudolabel admission; the v5 pseudolabels are what cost anomalous accuracy"
metadata: 
  node_type: memory
  type: project
  originSessionId: e44eca96-f48c-494d-ba1f-7dae68bdf06d
  modified: 2026-09-18T02:16:50.764Z
---

Measured against the v2 baseline (interior windows, real film: 91.8% ordinary, 66.0% anomalous), all on the
same recipe and the same held-out set:

| arm | ordinary | anomalous |
|---|---|---|
| v2 baseline | 91.8 | 66.0 |
| film-noise randomisation (v2fm, 40 ep) | 91.7 | 59.6 |
| pretrain on renders then fine-tune on real (SyntheX recipe) | 89.1 | 40.4 |
| renders + real mixed, 8 ep | 88.2 | 36.2 |
| anchored-only pseudolabel admission | 88.4 | 36.2 |

**The v5 component ablation answers "why the bigger bank lost":** v5 entire 91.2 / 52.8; minus pseudolabels
89.7 / **71.9**; minus oblique 90.0 / 58.4; minus extra real sources 88.7 / 69.7; minus all three 85.3 / 38.2.
The decoder-named pseudolabels buy 1.5 points of ordinary accuracy and cost 19 points of anomalous accuracy.
They are 30% of the bank and were named by a decoder whose prior is the ordinary alphabet.

The synthetic-fraction sweep is the one positive: holding real film fixed and raising the render fraction
from 0 to 0.5 moved anomalous 34.0 -> 53.2 while ordinary fell 2 points. Renders buy variant anatomy, not the
film domain -- so mix them in, do not pretrain on them.

**How to apply:** train the deployed encoder without the pseudolabels; do not spend more time on domain
randomisation or on pretrain-then-finetune. The lever that worked is [[sweep-map-replaces-registration]];
the lever still untested is the student review of the pseudolabels.
Product ranking: `r18_ce_v3` is best on ordinary interior windows (93.6%, cervical 99.6%, anomalous 78.7% on
12 films). See [[feasibility-claims-measured]].
