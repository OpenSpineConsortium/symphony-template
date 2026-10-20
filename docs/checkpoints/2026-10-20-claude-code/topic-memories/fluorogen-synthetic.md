---
name: fluorogen-synthetic
description: "FluoroGen = synthetic C-arm frames from labelled DRRs (SDXL + canny ControlNet + fluoroscopy LoRA), grid paths, jobs, licence choice, how to validate"
metadata: 
  node_type: memory
  type: project
  originSessionId: e44eca96-f48c-494d-ba1f-7dae68bdf06d
  modified: 2026-09-14T10:59:44.504Z
---

Started 2026-09-14 on the user's request ("synthetic generator ... stable diffusion ... 16 H200s"; gmsap
partition = 4 nodes x 4 H200).

- Design: DRR with per-vertebra labels is BOTH the init image and the ControlNet (canny) condition, so
  appearance changes and geometry does not; the fluoroscopy look is an SDXL LoRA trained on FluoroCap
  panels + video windows + 1,200 real films with templated captions ("intraoperative fluoroscopy, lateral
  view, lumbar spine, pedicle screws and rods at L4 L5, C-arm image, greyscale radiograph"). Hardware:
  crude metal templates drawn into the DRR at chosen levels (screws / screws+rod / needle / cement) before
  synthesis, instrumented levels recorded in the label json -> hardware-rich images with known levels.
- Base model SDXL 1.0 (CreativeML Open RAIL++-M, permissive) deliberately over FLUX.1-dev (non-commercial)
  and SD3.5 (revenue-capped community licence). Never state why in public text.
- Paths on the grid: env `~/mambaforge/envs/fluorogen` (clone of spinedet + diffusers 0.35.1, accelerate,
  peft); weights in `~/.cache/huggingface/hub` (login node download, `~/fluorogen/dl_weights.py`);
  diffusers example scripts in `~/fluorogen/`; training set `~/fluorogen/dataset_v1/train/{images,
  metadata.jsonl}` (tools/fluorogen_dataset.py); LoRA `~/fluorogen/lora_v1` (slurm/fluorogen_lora.sh,
  4 H200, 6000 steps, rank 32, bf16); synthetic output `~/fluorogen/synth_v1/{img,ann,preview}` in the DRR
  dir format (slurm/fluorogen_generate.sh, job array, one GPU per shard; tools/fluorogen_generate.py).
- Validation (tools/fluorogen_check.py): film detector recall of labelled boxes on synthetic vs source DRR
  (geometry kept?), panel classifier p(spine x-ray), preview montages. The metric that matters is a
  level-model arm trained with synth added and tested on real films / FluoroCap reader labels.
- DRR sources: ~/ctsp_drr (lateral, 801), ~/verse_drr (lateral, 374, low-res 221 px), ~/ctsp_drr_obl /
  verse_drr_obl (oblique), ~/films_ap_drr (real BUU AP films, counting-inferred levels), ~/films_drr (9,109
  real films), ~/nhanes_drr (543).
- Old `~/.local/bin/huggingface-cli` has no `download` command; use huggingface_hub.snapshot_download from
  the spinedet env. Related: [[fluorocap-dataset]], [[xr-benchmark-and-robustness-2026-09-13]].

**Verdicts 2026-09-15 (render-to-frame translation):** SDXL img2img over DRRs is dead at every strength: 0.45-0.65
destroyed anatomy (12,896 images, array cancelled); 0.2 leaves the DRR essentially unchanged and 0.35 already smears
end-plates and pedicles (`~/fluorogen/synth_rare_lowstrength/preview/`). Do not retry img2img; only
ControlNet-conditioned generation from the label map, if anything. CUT v1 (`~/cut_v1`) is invalid as a test of
translation: its target domain was every FluoroCap panel, including MRI slices, lightbox photographs and annotated
screenshots (the modality classifier calls only 2,991 of 18,119 panels spine radiographs at p>=0.7). CUT v2
(`~/cut_v2`, jobs 40285274/40285275) uses `cut_b_list_v2.txt` (p_xr_spine>=0.7, p_notxr<0.3) and renders with
>=2 unclipped vertebrae; judge translation on its films-only diag, not v1's.

**CUT v2 verdict (2026-09-15 11:05):** with the target restricted to classifier-verified spine panels the translations
finally look like radiographs (`~/cut_v2/preview/step_015500.png`), but the films-only model scores 12.1 -> 14.1% on
rare renders and 13.5 -> 14.8% on cone-beam renders after translation, and the render-trained all-spine model
DROPS (33.5 -> 23.7, 51.0 -> 36.6, held out). Texture is not the gap: the films-only model never saw AP views, the
renders are cone-beam AP+lateral. Translation is not a lever for level identification; registry alias
`cut_drr2fluoro_G_v2`; eval files `~/FluoroCap/cut_eval_{films,allspine}_*_v2.json`. Do not train CUT v3.
