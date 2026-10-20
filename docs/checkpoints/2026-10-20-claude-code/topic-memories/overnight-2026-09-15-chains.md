---
name: overnight-2026-09-15-chains
description: "Where the 2026-09-15 overnight FluoroCap runs write their results (markers, logs, chain scripts) so the morning read-out is a file list, not a search"
metadata: 
  node_type: memory
  type: project
  originSessionId: e44eca96-f48c-494d-ba1f-7dae68bdf06d
  modified: 2026-09-15T06:02:25.878Z
---

Launched the night of 2026-09-14/15, all unattended. Frozen copies run from `~/tmp/*_run.sh` on the grid and
`~/*.sh` on WSL; never edit a running copy.

**Grid (`~/FluoroCap/`):** `MORNING_REPORT.md` is the single read-out (written by the fine-tune chain last).
Markers/logs: `hires_refresh.log` + `hires_refresh_r2.log` (HIRES_REFRESH_DONE; panels re-split on the larger
figures, QC in `qc_after_hires*.md`), `allspine_v2_chain.log` (ALLSPINE_V2_READY; bank `~/allspine_v2_fov96_ctx`
with clipped targets skipped + physics_rare; model `runs/model_rung_1_aug2.pt` symlink), `rerun_chain.log`
(RERUN_DONE; inference tag v3 with the new model, decode v2 with T13/L6 allowed, `qc_report_v3.md`),
`finetune_chain.log` (FINETUNE_CHAIN_DONE; `finetune_v3/`, inference tag v4, `qc_report_v4.md`,
`level_model_diag_finetuned.json`, `transitional_eval/transitional_eval_finetuned_v3.md`). Translation: `~/cut_v1`
(CUT training, previews in `preview/`), `~/cut_rare`, `~/cut_physics`, eval `cut_eval_*.json`, marker
`~/CUT_EVAL_DONE`. FluoroGen img2img over rare renders: `~/fluorogen/synth_rare` (array 40275187).

**WSL:** refetch round two `~/FluoroCap_wsl/log_refetch_round2.txt` (ROUND2_DONE; applies on the grid and
launches refresh r2); pathology arm `~/FluoroCap_path/` (search 158,955 articles; `log_path_fetch_chain.txt`
PATH_FETCH_DONE pushes figures + caption rows to the grid root, marker PATHOLOGY_FIGURES_ADDED); Instagram
`log_instagram.txt` + `instagram/`; YouTube Data API list `youtube_api_urls.txt` (1,404 videos) downloading via
`log_youtube_api_{0,1}.txt`.

**Why:** the user wants to wake to a high-resolution corpus with the level model re-run and the transitional
question answered; every result has a fixed path so the morning is reading, not hunting.

**How to apply:** read MORNING_REPORT.md first; if a chain died, its log names the job and the marker it was
waiting for. See [[level-model-bank-coverage]], [[fluorocap-credentials-and-resolution]].
