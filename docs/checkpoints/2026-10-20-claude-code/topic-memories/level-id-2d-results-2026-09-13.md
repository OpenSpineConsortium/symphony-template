---
name: level-id-2d-results-2026-09-13
description: "2-D vertebra level ID on real films (13 Sep 2026): n=1 96.7% overall, cervical 97.7%, lumbar 81-85%; data is the only lever; round-2 arms (BUU+VinDr, SupCon, dual-view) launched midday"
metadata: 
  node_type: memory
  type: project
  originSessionId: e44eca96-f48c-494d-ba1f-7dae68bdf06d
  modified: 2026-09-13T16:02:48.174Z
---

Context ladder on real lateral films, held-out patients, exact level (13 Sep 2026 midday):
- Annotated films (CSXA cervical 4,963 pts + NHANES) in training, 48 px fov, 8,422 test
  crops: n=1 **96.7%**, 3 vert 98.8%, 5 vert 99.1%; within-one 99.7%. Cervical n=1 97.7%,
  **lumbar n=1 80.7%** (n=410), thoracic 86% (n=66), sacrum 91% (n=46).
- 96 px targets: lumbar n=1 **85.4%** (best lumbar); +BUU counting-inferred train-only: 82.7%.
- Size-in-mm scalars: no gain (third time). Architecture never mattered. CT-only -> film 7%.
- Previous headline "n=1 84.2%" was NHANES-only; unchanged, CSXA moved the overall number.
- Report artifact v10: https://claude.ai/code/artifact/f7fcc65c-4a2d-4481-b821-39125524f90d
  (source: session scratchpad level-context-report.html); numbers in ~/tmp/ladder_summary.json
  on the grid (tools/collect_context_curve.py --runs <arm>/runs per arm).

Bugs found: `r.view` in train_view_classifier.py was pandas' Series.view method -> every
training film "AP" -> VinDr got 0 laterals (fixed to r["view"]). "No space left on device"
was the login node's /tmp (25 GB, 100%), NOT the quota -- set TMPDIR=$HOME/tmp in every
script; heredocs die otherwise. Windows-written scripts arrive CRLF: `sed -i 's/\r$//'`
before sbatch.

Round 2 launched 13 Sep ~11:40 (grid ~/spinesurg-ct-nnunet/slurm/launch_round2.sh,
launch_dual.sh): +BUU rungs 1-2 (40215523); VinDr pipeline (40215525) -> crops -> merge ->
films_all2_fov48/96_ctx (40215537/38); SupCon 15 ep on films_ann_fov96_ctx (40215539,
results *_supcon.json); dual-view AP+LAT on BUU pairs, relative only (buu_pair_fov48_ctx,
40215544 lat / 45 ap / 46 both; --view flag, DualView class). Results: ~/<arm>/runs/.

**How to apply:** lumbar n=1 is bounded by ~380 annotated lumbar films; the next lever is
VinDr pseudo-labelled laterals as train-only. Never score BUU/VinDr; test = CSXA + NHANES.
