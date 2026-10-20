---
name: sweep-map-replaces-registration
description: "Overlapping C-arm frames swept from the sacrum build a radiograph-only registration. Numbers that count are sweep_v3 (respaced renders, 2026-09-19): 120 held-out CTSP 2-body frame 72->95%, chains 100% under the end rule; TS bench 522 unseen CTs 98.5%; films 25; rib oracle adds nothing; detectors fail on renders, 21/25 on films"
metadata: 
  node_type: memory
  type: project
  originSessionId: f1bdbd78-151f-470b-b703-dd9af9b3fecc
  modified: 2026-09-19T20:50:23.899Z
---

`tools/sweep_map.py` (spinesurg-ct-nnunet, branch `L6_Class`) simulates the radiographer's protocol on any
labelled long image; frames link by NCC restricted to ~0.6 body of the commanded step; a panorama is
stitched; limited-field frames register onto it and take names from the chain nodes.

**Only `~/model_night/sweep_v3/<holdout|protocol|improve|fix|end|rib|ts>/` counts** (Windows mirror
`C:\Users\grego\model_night\sweep_v3`). Earlier runs are superseded: `sweep2` (trained-on spines),
`sweep_holdout_v2`/`sweep_protocol`/`sweep_improve`/`sweep_fix` (wrong row spacing, see
[[drr-row-spacing-defect]]). `tools/make_results_table.py` reads sweep_v3; CT headline arm = o2 jittered.

| held-out, 9-inch, 2-body | 2 bodies | 3 | 4 | chain |
|---|---|---|---|---|
| 120 CTSP renders (jittered) | 72.1 -> 95.2 | 86.8 -> 94.7 | 90.2 -> 94.8 | 97.5 % (3.4 exp) |
| 25 real lumbar films | 78.7 -> 93.6 | 85.7 -> 93.9 | 91.9 -> 100 | 100 % |
| 12 VerSe from C2 (1-body) | 9.5 -> 100 | 25 -> 100 | 30 -> 100 | 100 % (2.9 exp) |
| 522 TotalSegmentator, sacrum, fixed step + end rule | 51.2 -> 94.3 | 72.7 -> 95.0 | 82.7 -> 94.4 | 98.5 % (4.2 exp) |
| 203 TotalSegmentator from C2 | 18.9 -> 94.0 | 39.5 -> 96.4 | 58.8 -> 97.8 | 95.1 % (2.8 exp) |

**The end of the sweep (the finding of 2026-09-19).** Fixed step completed 95.0 % vs 97.5 % jittered on
CTSP and 91.4 % on TS; EVERY lost chain was the simulator's clamped final frame (last step 0-10 px, a
frame nobody takes, below the linker's half-body floor). `--end-rule skip` (refuse a final move < 0.5
body) or `--last-link open` (search the last link to zero step) -> **120/120** under both steps on CTSP,
98.5-98.7 % on TS. Protocol line added: "the last move is a full move or none."

**Overlap ladder (chain, respaced):** 0.5 body 81.7, 1 95.8, 1.5 91.7, **2 97.5**, 2.5 96.7, 3 90.8, 4
82.5. Field: collimated 92.4 / 9-inch 95.8 / 12-inch 99.2 at 1 body. 99 % by declining only at 3 bodies
(99.5 % on top 80 %); 4 bodies 98.3 % at 80 %.

**Improvements tried (all vs fixed step, clamp end rule):** global link solve helps only where skip links
exist (o3 90.8->91.7, o4 83.3->90.0) and costs 3 spines at o2; phase seed nil; ECC identical; hybrid
`local` identical on renders; node merge/order (opt-in) inert on films, harmful on true-box renders;
**rib oracle (perfect rib-bearing truth as a soft decoder term) gains nothing** -- costs one spine with
an absent 12th rib (false L6); rib count is variant anatomy, not an arbiter.

**Detectors:** on renders both fail before the linker (8-spine set: anchor 6/8 render-trained vs 4/8
film detector, chains 0/8; TS renders chain ~0). On the 25 films with box repair + unlabelled-body
exemption (a detected T12 above an L1-first label set is `unlabelled`, not a false positive): **21/25
chains**, 87.2/90.4/91.4 on the chain. Open: one film (00378) where the head reads every body one level
caudal and the L6 alphabet beats a correct count (margin 0.74, inside the genuine-T13 range); no tau or
local rule fixes it; only count or rib would, and the rib ceiling on renders is nil.

**Per level (CTSP o2, K3 on chain, ordinary):** L1-L4 90.5-92.7, T11/T12 95-96, L5 100. Held-out set
holds ONE L6 (named L5): L6 not claimable from the sweep. Decoder variant calls on TS: T13 2.9 %, L6 1.0 %
-- to be checked against SPINEPS/VERIDAH (see [[spine-data-review-and-ts-bench]]).

**How to apply:** report sweep_v3 only; TS arms as the large bench; state the end-rule line; the film
decoder error as open. Stages registered in `tools/pipeline_state.py` (`sweep_protocol`, `sweep_improve`,
`sweep_fix`, `ts_drr`, `sweep_v3`); rib arms `slurm/sweep_rib.sh` (not a stage). See
[[remedies-refuted-2026-09-17]], [[feasibility-claims-measured]].
