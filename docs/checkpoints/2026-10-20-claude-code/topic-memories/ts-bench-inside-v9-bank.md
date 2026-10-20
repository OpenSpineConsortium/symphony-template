---
name: ts-bench-inside-v9-bank
description: "The TotalSegmentator render bench (ts_drr) is NOT held out from the v9 level encoder; only 70 of 1,170 TS, 1 of 802 CTSP and 0 of 387 VerSe renders are unseen by it; --holdout-bank matches stems, not patient keys"
metadata:
  node_type: memory
  type: project
  originSessionId: f1bdbd78-151f-470b-b703-dd9af9b3fecc
  modified: 2026-09-26T03:50:53.488Z
---

Found 2026-09-25 (jobs 40453664 / 40454032): the eval gate refused a sweep of the TS bench with the v9 encoder
(`allspine_v9_fov96_ctx/runs/model_rung_1_aug2.pt`): 483 of its 523 sacrum-bearing spines are in v9's train (410) or
selection (73) keys, because the v9 bank took the SPINEPS harvest of TotalSegmentator. `tools/unseen_cases.py` (the
gate's keying + lineage store) lists what a checkpoint's chain never saw: for v9 that is 70 TS + 1 CTSP + 0 VerSe
renders, none reaching C1/C2. The earlier sweep_v3 arms (encoder model_r18_ce_v3, v7 bank) were properly held out on
the whole TS bench (522 + 203 spines).

**Why:** `--holdout-bank` in sweep_map.py filters by annotation stem (`TS_s0001`) while banks key patients
(`ts:s0001`), so it excluded nothing and only the patient-keyed gate caught it. "The TS bench, none in the bank" was
true of v7, not v9.

**How to apply:** any held-out number on renders for a v9-lineage model must come from `unseen_cases.py` output
(`~/model_night/sweep_v3/cns/unseen_v9.txt`, 71 cases) or a new corpus; never quote the 522/203-spine TS numbers as
v9 numbers. The CNS deck v9 draws the whole-spine sweep curve from the earlier checkpoint and labels it so; the v9
curve covers T10 to sacrum on 41 spines. See [[sweep-map-replaces-registration]], [[cns-deck-v2-2026-09-25]].
