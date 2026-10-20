---
name: film-fluoro-boundary-not-transferable
description: "Measured 2026-09-22 over 37 corpora: each C-arm keeps its own region of image-statistics space (pairwise Bhattacharyya 0.005-0.675), but film vs fluoroscopy does NOT transfer to an unseen corpus (leave-one-corpus-out 71.1% vs a 71.8% majority share) -- the statistics separate the corpus, not the modality"
metadata:
  type: project
---

`tools/corpus_manifold.py` over 13,875 frames (7,311 real) from 37 corpora, jobs 40414544/45; numbers in
`/rs/rs_grp_oschome/go2432/data/or_ready/corpus_manifold/overlap.json` and in the claims ledger
(`manifold_lofo_pooled`, `manifold_lofo_chance`, `manifold_carm_pair_min/max`). Every C-arm corpus held out is
labelled FILM (C-ArmLSpine 1.4 %, COBRA Elekta 13 %, Varian 15 %, SpineSAC 38 %, DeepFluoro 46 %, Geneva 100 %);
film corpora score 74-100 %. pca12 and embed3 give the same picture (76.1 %, 74.3 %).

**Why:** it refutes "film and fluoroscopy are separable image domains" as a transferable statement, while leaving
"each device is its own domain" standing -- the two are not the same claim. A model that appears to tell the
domains apart has learned the corpora it was shown.

**How to apply:** score a detector on a device held out WHOLE, never on a held-out domain; do not quote a
film-vs-fluoro separability figure without saying the corpus was held out; the per-device Bhattacharyya overlaps
(0.005 DeepFluoro-Geneva to 0.675 Elekta-Geneva) are the defensible separability statement. Figure 1 row (d) of
the RSNA AI manuscript shows all three panels. Related: [[k-devices-one-network]], [[rsnai-paper-endpoint]],
[[sweep-physics-no-bone]].
