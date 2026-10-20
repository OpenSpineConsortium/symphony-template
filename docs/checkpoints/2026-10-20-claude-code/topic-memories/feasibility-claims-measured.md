---
name: feasibility-claims-measured
description: "The FOV feasibility report tested claim by claim (2026-09-17) -- what was disproved, confirmed, ambiguous; the head/encoder pairing trap; where every number lives"
metadata: 
  node_type: memory
  type: project
  originSessionId: e44eca96-f48c-494d-ba1f-7dae68bdf06d
  modified: 2026-09-17T21:20:04.000Z
---

The Feasibility_FOV.docx report (says isolated-stack naming is "mathematically underdetermined") was tested
claim by claim on 2026-09-17. Results in `~/model_night/feasibility_claims/{v2_ce,v5_ce}/`,
`~/model_night/geometric_indices/`, `~/model_night/fov_separability/`, `~/model_night/global_signature/`,
`~/model_night/anomaly_manifest/`. Reproduce with `slurm/reproduce_feasibility.sh` -> `LEDGER.tsv`;
doc `docs/FEASIBILITY_REPRODUCE.md`.

**ADVERSARIAL AUDIT (2026-09-17, 20 agents) OVERTURNED THREE OF MY FIVE DISPROOFS -- read before quoting:**
- "State C / unanchored" was LABEL-defined: BUU labels L1-L5 (sacrum in film, unlabelled), CSXA C3-C7 (C2
  in film); the +/-1-body crop band shows the anchor. 34% of "State-C" windows = whole stack (names forced by
  count -> the K=5 100% is the counting convention, NOT anatomy); 49% end-touching. Only 16.5% INTERIOR:
  95.5% overall; lumbar 86.7% K=2 (chance 50%), 92.3% K=3 (placement forced); cervical 99.2/99.7.
  Chance "10.3%" flattered it: placement-blind prior 59.4%, run-end detector 95.5%. 11% of val films share
  a patient with train. -> `tools/eval_interior_windows.py` (pixel-defined, film-cluster bootstrap, structural
  baselines); `slurm/interior_windows.sh`.
- "Decoder fires blind" (65/65 vs 0/1,127) was a TAUTOLOGY: pseudolabel_real_films.py demotes exact names
  at/below the junction when flagging; manifest read exact tier only. Full decode: 164/191 (86%) variant
  calls CONTAIN a sacrum; variant rate 9.0% with sacrum vs 0.32% without. Most are false positives made
  where the junction was visible. Fixed in anomaly_manifest.py (reads full decode).
- NHANES is NOT all cervical: 8,840 C + 7,394 L films; lumbar films image L1-S1; detector boxes the sacrum
  on 1.8% (72/7,394) -> classifier never sees the junction -> 0 flags IS a detector failure (31-429 expected).
- Co-occurrence inflated by count-coupling (11-thoracic => LS+ by arithmetic) and 31 unknown-scored-negative
  rows: VerSe 280 fully graded OR 3.61 [2.08, 6.27]; morphology-only 3.2 [1.8, 5.8]; both junctions in
  field (n=115) 2.1 [0.9, 5.0]. Literature: Carrino 2011 13.7, Yoon 2024 1.87, Nagata 2025 8.5.
- BUU: report's structural claim (rigid five-slot keypoints on all 3,600) CONFIRMED; the sheet refutes only
  "unrecorded". Annotators counted DOWN from last rib-bearing vertebra -> in L6 spines L1-L5 names are
  RIGHT and the 6th body is labelled "S1a"; 9/15 "L6" reads are children 7-17 (unreadable). The L5-S1 gap
  AUC 0.99 = annotation schema (S1a row on sacralised = S2). v6 rationale softened accordingly.

**MEASURED interior (pixel-defined, film-cluster CI), job 40321368, `~/model_night/interior_windows/`:**
v2 ordinary lumbar 91.8% [89.4, 94.1] (455 films; K=2 89.8, K=3 93.8); anomalous 66.0% [39.6, 87.2]
(12 films, n=47); cervical 99.6%. v5 ordinary 93.5% [91.4, 95.5]; anomalous 57.3% [29.0, 78.6] (17 films).
Placement-AWARE baseline = 100% on lumbar interior (BUU names ARE the count); placement-blind 0-4%.
Stem-leak 0.0%. These supersede the label-defined numbers in every claim.

**Work program launched 2026-09-17 afternoon (all registered in pipeline_state.py, chained in
slurm/reproduce_all.sh, audited by tools/audit.sh + tests/test_feasibility_tools.py; envs in env/*.yml):**
- BUU schema correction DONE: `~/films_drr_buucorr` -- S1a->L6 on all 15 six-lumbar (per-study resize fit
  ~0.84x, residual <=1 px), L5 sacralised x129, review package `review/REVIEW_QUEUE.csv` + overlays.
- data_fixes2 job 40321788: film-noise knobs FITTED = photons (80k,800k), read_noise (0.05,0.4), blur
  (0.1,0.4), scatter (0.05,0.25) -> after: sharp 0.0068 (real 0.0078), noise 0.0073 (0.0059), SNR 136
  (164); 3/4 inside real band (`~/model_night/film_match/film_match_params.json`). First guess gave 10x
  real noise -- cancelled 40321763, bank deleted. Pseudolabel filter: TWO bugs fixed -- index-zip (0.23%)
  then number-only NHANES key colliding cervical/lumbar films (40%); matched cervical pairs agree 96%.
  Re-run as job 40321959 (pfilter) -> `~/pseudo_filtered/FILTER_SUMMARY.json`. v2fm bank building.
- explain: first two runs died in Grad-CAM (backward hook vs in-place residual add; wrapper lacks
  layer4). Fixed: forward hook + retain_grad, layer chosen by dry forward (enc.layer4.1.bn2), ablation
  JSON written BEFORE Grad-CAM. Resubmit pending.
- audit `tools/audit.sh` passes (12 tests) on the grid; `slurm/reproduce_all.sh --dry-run` = 19 stages.
- Pseudolabel agreement vs 543 human NHANES (geometric, keyed by number+view): cervical anchored 96.3%
  (n=970), lumbar anchored 89.9% (258), lumbar unanchored 100% (1,064). In manuscript + page.
- deep-research wf_78f61c94-3fe VERIFIED (105 agents): SyntheX -- physics DRR + STRONG photometric
  randomisation ~ real-data parity; generative transfer adds nothing; "DeepDRR beats naive DRR" REFUTED
  (it's the randomisation). No measured gain anywhere for SD/ControlNet/LoRA on radiographs. Synthetic
  pretrain->real finetune beats mixing (+6.5% vs +2.7%); saturation 2-10x real. CReST: class-dependent
  admission restores rare-class recall. Report: `docs/PRIOR_ART_SYNTHETIC_AND_SELF_TRAINING.md`.
- LEADS BEING TESTED (job 40322042 `slurm/leads_chain.sh` -> `~/model_night/leads/LEADS_TABLE.json`):
  A v2fm film-noise 40-ep vs v2; B renders-pretrain->real-finetune (train_level_backbone --init) vs
  s100_r100; C anchored-only vs CReST-admission banks (`tools/build_crest_bank.py`) vs v2/v5;
  D `tools/eval_windows_by_class.py` -> fig12 (level x K x spine class, interior & all).
- EXPLAIN DONE (v2 + v5): interior L3 (intact 90.0%, n=261) -- mask whole target body -2.3 pts; sup
  end-plate -0.4; inf 0; posterior -0.4; neighbour above -1.9; below 0; body-only 88.9%; end-plates-only
  90.4%; both neighbours masked 88.5%. C5 (99.7%): <=0.9. v5: L2 target -3.2, end-plates-only -4.8. ->
  identity redundant/distributed, no single ratio load-bearing. Only L3/C4/C5 (v2) had >=30 interior
  3-body windows. sklearn was MISSING in fluorogen (embedding/probes failed) -> installed 1.7.2 via
  `pip --only-binary`, env re-exported, rerun queued as 40322058 behind 40322057.
  Cartoon: `tools/render_feature_cartoon.py` -> fig13_feature_cartoon.png (in README + page v4 + Fig S6).
- QI deep-research DONE (wf_93111768-3ea, 106 agents): ONLY human exact-level naming number on
  intraop images = Manbachi 2018: 5 surgeons, 62 hard C-arm films, 69.6% unassisted -> 97.6% with
  LevelCheck (needs preop CT). LevelCheck 99.998%/100% = registration success, NOT naming. Only
  registration-free AI naming: Huang 2022 88.3% (cadaver long-film). Cina 2021 98.4% (whole lumbar,
  sacrum in frame). NO study stratifies by anomalous spine. Ammerman 2006: 15/100 wrong initial exposure.
  -> Table 5 + Results "Against surgeons and prior software" in main.tex; README sec. 6; page sec. 7b;
  `docs/PRIOR_ART_LEVEL_ID_HUMANS_AND_AI.md`.
- LEAK (v5 bank): pseudolabel split didn't group NHANES films by number across nhanes/nhanes_drr/NHANESPS
  -> 48/54 annotated NHANES val films had decoder-named TWINS in train. USER POLICY: FIX + RERUN, do NOT
  narrate in the manuscript (docs "Discarded" may note the rebuild). Fix = `subset_bank.py --drop-val-twins`
  + twin guard in build_crest_bank.py. v5c chain job 40323153 rebuilds v5 clean + all v5 results (paper's
  "v5" = v5c when done). Leak-free ablation 40323154 (v5 minus pseudo/obl/extras). Leads chain restarted
  as 40323152 (admission banks rebuilt with guard). v2/v6/v2fm/scaling/pretrain arms never had the leak.
- v5 lumbar composition: NHANESPS = 29.5% of lumbar train crops (largest source); physics_rare fell
  9.2%->3.5%, BUU 35%->15%. That is the ordinary-prior dilution mechanism.
- V6 DONE (16:57): label-defined State C real film, ALL 144 anomalous BUU studies (4,026 windows):
  CE 81.3% [80.0, 82.4], CORN 81.4%; ordinary 97.3/97.4%; per-K anomalous 68.5/63.4/78.4 (K=2/3/4),
  K=5 = whole stack. Renders: C anomalous 89.4%, B anomalous 96%. -> 20-film 87% was +6 optimistic,
  v5's 67% -14 pessimistic. In manuscript Results + Table S1 (v6 block), README, page. Interior v6 +
  failure renders: job 40323163 (`~/model_night/interior_windows/v6_{ce,corn}`).
- BENCHMARK MANDATE: user must BEAT Cina 2021 (98.4%, whole lumbar film, sacrum in frame) and directly
  benchmark VertXNet 2024, Kim 2024, Konya 2021 (weights or reimplementation on OUR films, one scorer).
  `tools/benchmark_cina.py` = per-vertebra correct-name ratio on whole lumbar lateral films + sacrum-count
  floor + `--external <dir>` slot (per-film JSON {"levels":{i:{"name","box"}}}) + interior 3/4-body rows;
  job 40323179 (`slurm/benchmark_cina.sh`) for v2/v6ce/v6corn/v5c. Table 5 (tex + README) now split
  "Needs CT" / "No CT" with published vs benchmarked columns; "in progress" cells filled by the chain.
  deep-research wf_aacb742c-222 running: code/weights/architecture/naming rule for the four methods.
- V6 INTERIOR (pixel-defined, 128 anomalous films, n=607): **49.9% [41.5, 58.9]**; ordinary 89.9%
  [87.1, 92.7] (453 films); cervical 99.4%. -> the DEFINITIVE anomalous anchor-free number; 66% on 12
  films was noise. In abstract/key points/summary/Results/Table 5/README/page (v7).
- CINA BENCHMARK (`benchmark_cina.py`): whole-film ordinary v2 99.96% [99.9,100] (520 films) = sacrum-
  count rule 99.96% -> task SATURATED on counting-labelled public films; v6 whole-film anomalous 98.06%
  (CE)/99.44% (CORN) vs count 100%. Interior 3-body: v2 92.7% ord / 53.3% anom; v6 91.1/45.1 (CE),
  91.4/44.0 (CORN); count rule 0%. Only the limited field discriminates.
- Product ranking so far (twin-free ordinary interior): r18_ce_v4 92.0% > v2 91.8% > v6 89.9% (v6 lost
  2 pts ordinary from anomalous oversampling). Anomalous columns not comparable across banks (12 vs 128
  films).
- strict_fov job 40323217 (`slurm/strict_fov.sh`, K FULL vertebrae only); leads re-run 40323218 (arm A
  now that v2fm READY; check 40323152 log for B/C); v5c: 2,089 twin crops dropped, training.
- Full-image (no-K) methods deep-research wf_c97e0a7f-752 running.
- Product: `slurm/product_select.sh` job 40323155 ranks every encoder by twin-free ordinary interior
  accuracy (BUU+CSXA) -> `~/model_night/product/PRODUCT_RANKING.json`; model cards + checkpoint publishing
  (private HF repo gregoryschwingmdphd/level-id-weights per memory rule: never public via website) TODO.
- Manuscript Results now opens with the three questions + explicit comparators (placement-blind /
  placement-aware priors; intact crop; Table 5).
- scaling sweep job 40321409 -> `~/model_night/scaling/SCALING_CURVE.json` (6 points, 8-epoch arms).
- film LoRA job 40321779 -> `~/fluorogen/lora_film_v1/` (public X-ray datasets ONLY, no FluoroCap, equal
  weight per datasetxregion, images only); apply with `slurm/film_lora_apply.sh` (--prompt-template film)
  -> `~/allspine_v2sd_fov96_ctx` after `label_preservation_gate.py`.
- explain job 40321780 -> `~/model_night/explain/explain.json` (region-occlusion ablation etc.).
- v6 chain 40321317 still training (started 14:18).
- deep-research wf_78f61c94-3fe resumed after the 3:40 pm rate limit; raw leads: SyntheX (DeepDRR +
  domain randomisation ~ real-data parity; style transfer adds nothing), arXiv 2508.16783 (pretrain-on-
  synthetic-then-finetune beats mixing; saturates ~5x real), CReST for class-imbalanced self-training.

**Still standing:** label-defined State C real film anomalous 87.2% n=572 / ordinary 97.2%; per-level L1-L5
90/88/86/86/85% (not exchangeable, but pooled domains); mechanism = +/-1 offset (83%); CT->film collapse;
report's Wigh band covers 5.1% AND the real Wigh rule (<=1.37) fires on 99.9% of ordinary films; sacral
slope AUC 0.73 for L6.

**Ambiguous:** global anomaly signature in distant vertebrae -- VerSe AUC 0.65 vs 0.53 shuffled, nothing in
physics DRRs (embeddings trained for naming, so bounds them not the thesis). 4-class FOV: 42% balanced
acc at K=1 junction-free (chance 25%), no clean threshold, data runs out past K=3.

**Product limitation to state plainly:** L6 at 44.9% in State C; cranial-anchor + anomalous 81.6%.

**Per-K on anomalous real film, no anchor (v2 / v5):** K=2 60.5/41.5, K=3 82.9/61.8, K=4 85.0/57.1,
K=5 **100.0**/85.1 (n=225/235). K=5 = whole L1-L5 stack so span is a cue; K=3-4 are span-free. No real
isolated-stack window >5 exists. Pseudolabel training (v5) loses at EVERY K on anomalous, ordinary unchanged.

**Root cause of the 87%:** 124 of BUU's 144 anomalous films were in the v2/v5 TRAIN split labelled L1-L5
(counting names, wrong for those spines). v6 = `tools/build_v6_bank.py` (all 144 -> val, anomalous CT
crops x4, ordinary byte-identical) + `slurm/v6_chain.sh` (r18_ce_v6, r18_corn_v6, mixed heads, claims).
Launched 2026-09-17 14:06 as job 40321317; ~30 h. Results -> `~/model_night/feasibility_claims/v6_*`.

**Deliverables:** manuscript `paper/rsnai/main.tex` (RSNA structure, no official LaTeX template exists;
compiles 18 pp, 0 undefined refs; build with `paper/rsnai/build.sh` after `module load texlive/2020`);
web version https://claude.ai/artifact/3DFZMHt4oAnrDVHwxdZnyf; one-command chain `slurm/reproduce_all.sh`
(dry-run passed; flags verified against argparse); figures `tools/make_feasibility_figures.py`; arms table
`~/model_night/ARMS_TABLE.json` (ResNet-18 CE/CORN 95.0-95.4% single-crop real film; DINOv3 ~80).
Branch is `L6_Class`, not master. Title: "Naming Vertebrae Without an Anchor: Registration-Free Level
Identification on Limited-Field Radiographs".

**Why:** the operating claim in the report is deterministic impossibility; a posterior system is not bound by
it, and the numbers show information is present. The mechanism claim is correct and should be cited as such.

**How to apply:** never quote pooled anchor-free (98.32%) without the anomalous split beside it. Never pair
a head with an encoder other than the one in its sidecar -- `head_r18_corn_v5_v5.pt` + `model_r18_ce.pt`
scored 0-1% with a +2 offset (looks like a finding, is a mismatch). Valid pairings: v2 bank <->
`model_r18_ce.pt` + `head_allspine_v2_fov96_ctx_mixed_kmax4_seed0.pt`; v5 bank <-> `model_r18_ce_v5.pt` +
`head_r18_ce_v5_v5.pt`. Related: [[anomaly-manifest-sources]], [[selective-prediction-the-honest-99]],
[[mixed-length-head-and-sota]].
