---
name: recurrent-head-restored-2026-09-16
description: "The BiGRU run-level head was silently unreachable (hard-coded rung_0, weights never saved); restored 2026-09-16 and worth +10 points on the 27-class whole-spine bank"
metadata: 
  node_type: memory
  type: project
  originSessionId: e44eca96-f48c-494d-ba1f-7dae68bdf06d
  modified: 2026-09-16T05:54:33.025Z
---

**The 98.7 / 99.1 / 99.4% headline was never a whole-spine number, AND it was mostly not the head.**
CORRECTED 2026-09-16 after an adversarial check. Those figures are in `~/bench/xr_fov/recurrent.json`,
which was written 2026-09-13 13:28:00 -- 75 minutes BEFORE `films_all2_fov96_ctx/rung_0.npz` existed
(14:43:15). They came from **films_ann_fov96_ctx** (CSXA + NHANES only). films_all2's own head run is
the separate `recurrent_all2.json`: 98.84 / 99.13 / 99.42 / 99.38 at 3/5/7/9.

Both banks share ONE validation split: 8,422 crops, 7,900 cervical, 410 lumbar, 66 thoracic (exactly
T1 n=7 + T12 n=59), 46 sacrum, and only **14 of the 27 classes live** (the result files record
`chance: 0.0714` = 1/14). Both have ZERO training crops at C1, T2-T11, T13 and L6.

**The second, sharper non-comparability:** 78.7% is a SINGLE-CROP number and 98.7% is a RUN-LEVEL one.
The task-matched single-crop figures on the film banks are films_ann rung 0 **96.95%**, films_all2
rung 0 97.46%, films_all2 rung 1 **98.98%**. So on the cervical bank the head is worth about +0.4
points over single-crop; the 99% was essentially the single-crop model on 14 classes.

**Two defects retired the head, neither of them a decision.** `recurrent_order.py` opened `rung_0.npz`
by hard-coded name, and every bank built since 2026-09-14 has rung 1 only, so the script could not open
them. It also never saved the head weights. Both fixed 2026-09-16: `--rung`, `--save-head`, per-level
output, and `load_level_model()` instead of `build_model()` so it can read LevelNet checkpoints (the
backbone trainer prefixes keys with `enc.`).

**Same bug class found twice more in `level_prototype.py`**: hard-coded `resnet18` and a hard-coded 512
head width. The prototype could not load ANY arm from the 2026-09-15 experiment. Fixed; head now loads
by default from `~/model_night/heads/<set>/head_k<k>.pt`.

**Restored head on `allspine_v2_fov96_ctx` (27 classes, held out, n=16,392), vs 78.74% single-crop.
Here the head is worth +10.2 points, against +0.4 on the cervical bank -- the head matters where the
single-crop model is weak, which is the thoracic spine:**

| band | exact | within-1 | region | cervical | thoracic | lumbar |
|---|---|---|---|---|---|---|
| 3 | 83.4 | 97.1 | 98.1 | 95.2 | 66.7 | 82.7 |
| 5 | 86.1 | 97.8 | 98.4 | 96.6 | 70.2 | 86.0 |
| 7 | 86.2 | 98.0 | 98.6 | 97.3 | 73.3 | 84.3 |
| 9 | **89.0** | 98.0 | 98.7 | 97.8 | 75.0 | 89.1 |

Per-level at 9: C3-C7 96-99, T6-T8 62-65 (the floor), T10-T12 80-84, L1-L5 88-92, sacrum 100,
**T13 0.0 (n=14), L6 47.7 (n=132)**.

**How to apply:** always report which bank and class count a head number came from. Heads live at
`~/model_night/heads/{films_all2,allspine_v2}/head_k{1..4}.pt` with `.arch.json` sidecars.
Related: [[level-model-bank-coverage]], [[xr-benchmark-and-robustness-2026-09-13]].
