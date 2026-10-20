---
name: fluorocap-dataset
description: "FluoroCap = literature-mined spine fluoroscopy test set (grid ~/FluoroCap); stages, routes, manifest schema, what runs where, user's documentation requirements (started 2026-09-13)"
metadata: 
  node_type: memory
  type: project
  originSessionId: e44eca96-f48c-494d-ba1f-7dae68bdf06d
  modified: 2026-09-13T19:47:23.790Z
---

**What:** FluoroCap, a retrospective collection of published spine fluoroscopy / C-arm figures
whose captions name a vertebral level, built 2026-09-13 as the real-fluoro test set for the
level-ID pipeline. User directive: build it exhaustively, verify image integrity, and document
every image (source link, licence, public access, de-identification, terms, modality,
population, inclusion/exclusion, acquisition, preprocessing) so the set is reproducible.

**Where:** grid `~/FluoroCap/` (articles.jsonl 39,056 OA articles; captions_all/matched.jsonl;
fetched.jsonl; raw/<pmcid>/; openi/, openi_matched.jsonl (289); extra_targets.jsonl (MultiCaRe 67);
pmc18m/ + pmc18m_matched.jsonl + pmc18m_negatives.jsonl (3 random labelled sub-figures per
shard, for the modality classifier); articles_context.jsonl; panels/ + panels.jsonl;
panel_preds.jsonl; manifest.csv / figures.csv / articles.csv / stats.json / ids.json;
PROTOCOL.md; releases/FluoroCap_v*/ with SHA256SUMS + LOCK.json). Logs `log_*.txt`.
Code: `spinesurg-ct-nnunet/tools/fluorocap*.py`, `slurm/fluorocap_run_rest.sh` (orchestrator:
waits for captions -> retry-errors (JATS fallback) -> fetch -> context -> wait pmc18m -> sbatch
panels (CPU) -> sbatch classify (GPU) -> manifest), `docs/FLUOROCAP_PROTOCOL.md` (public, no
commercial language). Regulatory framing lives only in the gitignored COMMERCIALIZATION.md sec. 10.

**Routes:** Europe PMC query (fluoro  and  spine  and  OPEN_ACCESS) -> BioC captions (FIG passages
with `file`) -> figure blobs scraped from `https://pmc.ncbi.nlm.nih.gov/articles/PMC<id>/`
(`cdn.ncbi.nlm.nih.gov/pmc/blobs/...`, browser UA); BioC misses ~13% (recent PMC13* ids) ->
Europe PMC `fullTextXML` JATS fallback. Open-i (84 queries, paged to `total`), MultiCaRe
(Zenodo 10079370 csv), Open-PMC-18M (HF, 4,014 x ~60 MB tars, ~0.4 shard/s on login node).

**Rules:** LEVEL_RE excludes T1/T2-weighted; pmc18m keep requires x-ray modality label or
fluoro/radiograph word in the sub-caption and no MRI/CT word. Manifest inclusion codes
I1-I4, exclusion E1-E7, use_class from the article licence string (commercial_use_permitted,
derivatives_permitted), image_id FLUO-###### stable via ids.json, caption label vs pending
two-reader + adjudication reference, prespecified subgroups (primary / limited FOV / no anchor /
single / transitional / hardware / oblique / degenerative) filled from reader labels.

**Gotchas:** `pkill -f fluorocap_x` inside an ssh one-liner kills the ssh shell itself (exit
255) -- use `[f]luorocap` bracket pattern or a launcher script with setsid; network stages
only on the login node; heredoc `\b` becomes a backspace byte (see [[bash-heredoc-backslashes]]).

**Licence gate (user's second advice memo, implemented):** tiers A (PD/CC0/CC BY) B (permission on
file) C (NC) D (ND) E (unknown/SA/other -> REVIEW queue `license_review_queue.csv`);
`commercial_training_eligible` TRUE/FALSE/REVIEW; `license_overrides.csv` + `human_qc.csv` merged;
freeze writes Dataset A (research, all tiers) and B (clean, eligible only) -- headline numbers
from B only. Never say "publicly accessible = usable". HPR attachment in gitignored
`CTSpinoPelvic1K-1/proposals/FluoroCap_HPR_attachment.md`; regulatory framing only in
COMMERCIALIZATION.md sec. 10/10a.

**Routes 6-10 and lessons (evening 2026-09-13):** OpenAlex (11 languages) + PyMuPDF figure/caption
extraction from OA PDFs; Openverse (works, tiny); Wikimedia Commons (33); Reddit Atom feeds
(`search.rss` works, JSON is blocked; very rate-limited, run from WSL at 8 s/request); YouTube +
Bilibili via yt-dlp (grid glibc 2.17 cannot run deno/node -> run on WSL with `js_runtimes node`,
format `bv*[height<=480]`; subtitles fetched separately so a 429 does not kill the download;
auto-subtitle level mentions time-aligned to frames; dhash dedupe; three query-shard workers;
launcher scripts must not contain the process name they pkill). PMC serves a reCAPTCHA page to
the grid IP above ~1 req/s and the fetch marked 900 figures "not on page"; fetch now detects the
captcha, retries, normalises file names (`figkey`), and runs from WSL (0 captchas) with the
orchestrator waiting for `~/FluoroCap/WSL_MERGED`. DuckDuckGo/Bing/Reddit-JSON block scripts
from both hosts. pip on the grid cannot build wheels (/tmp full, old glibc): use
`mamba install -n spineps -c conda-forge pymupdf`. Panel classifier can be trained early
(`fluorocap_classify.py`, negatives from pmc18m) and score any dir (`--score-dir`, `--weights`).
Reader tool: `fluorocap_annotate.py` (static HTML, anchor click + contiguity, export JSON).
Validation montages: `validate_sources.py` -- PMC/Open-i/pmc18m are good; raw video frames are
mostly talking heads until the classifier gates them.

**Classifier lesson (2026-09-13 night):** a films-only positive class rejected 95% of real C-arm
figures (collimation, dark frames, hardware). v2 = films + caption-verified pmc18m/Open-i fluoro
positives + circular-collimation augmentation: held-out 91.7%, accepts ~36% of pmc18m/openi at
0.5 and the rejects still hold some dark fluoro, so the manifest gate E5 is 0.3 and the readers
decide. Video frames: 2.6% accepted at 0.5 (35k frames); C-arm often picture-in-picture -> 
`fluorocap_video_crop.py` searches 13 windows per frame with the classifier. Rib QC v4-vs-release
table done and in CTSpinoPelvic1K-1/results/rib_qc_v4_vs_release/.

**v0.1 frozen 2026-09-14 02:35 UTC** (`~/FluoroCap/releases/FluoroCap_v0.1_{A,B}`, records in
spinesurg-ct-nnunet/benchmark/data/fluorocap_v0.1): 4,979 figures / 2,205 articles / 10,281 panels;
A = 2,531 included panels, B = 991 licence-clean, 148 in the review queue; fluoroscopy 1,436,
radiograph 637; 1,560 with hardware. First pipeline run on the panels (all2 model + detect_v3):
detector finds nothing in 20%, caption-consistent 19% overall (38-46% when >=5 vertebrae found)
-> real-fluoro gap is the next problem; readers' pages at ~/FluoroCap/annotate (64 pages x 40).
Video route: 730 videos, 67k frames, `fluorocap_video_crop.py` window search running on WSL.

**Late 2026-09-13/14:** detector-sensitivity runs (conf 0.4/0.2/0.1) recorded in
benchmark/data/fluorocap_v0.1/infer_comparison.md -- lowering conf inflates the loose set metric
by adding boxes (contiguous-and-consistent 4.9% -> 1.3%); the film detector does not transfer to
C-arm frames. Video route: 905-query set (`fluorocap_video_queries.py`) on 4 WSL workers, frames
rsynced to grid `~/FluoroCap/youtube` (exclude `_*` temp dirs), GPU window search job
`fluoro_vcrop` writes `video_panels/` + `video_panels.jsonl`; manifest reads video_panels and
reddit as tier-E routes. OpenAlex PDFs: 724 so far, pdf_figs kept 41 (real captures, low yield).
WSL launcher rule: never put a process name that a script pkills on the invoking command line.

**Window search lesson:** the v2 classifier on sub-windows of video frames accepts grey faces and
dark corners at p 0.5-0.8 -> v3 adds 6,000 random video frames + random windows as class-0 hard
negatives (`--neg-dir youtube:6000`); rerun `fluorocap_video_crop.py` with `--min-p 0.8` after v3.
Weights kept: panel_classifier_v1_filmsonly.pt, _v2.pt; reports classifier_report_v1/_v2.json.

**Why fluoro fails (2026-09-14, night):** detector scale gap -- trained on full films (vertebra 3-10%
of height), fails on collimated close-ups (1-3 vertebrae fill the frame); synthetic faults, inversion,
crop, projection do NOT explain it; overlays in ~/FluoroCap/validate/preds_*_lateral.png. Fix in
progress: `spine-detector/scripts/make_zoom_dataset.py` -> data/yolo_v4z (22k zoomed windows) ->
`detect_v5z` fine-tune (job 40233036). 99% target: cervical met (99.0-99.8 @3 vert), lumbar 86-96
on only 82 NHANES held-out films/level (cannot resolve 1%); needs lumbar test data (readers) and
training data. Video window search: classifier alone passes junk at 0.8 -> detector-gated version
(`--detector`) to run after detect_v5z. Report: docs/FLUOROCAP_MORNING_2026-09-14.md.

**Second failure (2026-09-14 02:00):** with detect_v5z boxes, the level model calls 50% of lumbar
fluoro cervical and never thoracic (majority-class fallback under domain shift; scale is normalised
away). Remedy started: `fluorocap_region_classifier.py` (caption regions, article-grouped folds)
+ `fluorocap_infer.py --region-prior`. Jobs: region 40233137; infer aug2/aug3 with v5z 40233135/6;
robustness suites 40233124-131; strict video window search 40233134 (min-p 0.6, det-conf 0.7, >=2
boxes); ConvNeXt arm 40233106 (ctx_arm.sh now passes ARCH); tgt128 arm 40233132.

**Working gates (2026-09-14 03:00):** video window search = classifier p>=0.6 on the window AND
detect_v5z >=2 boxes at conf>=0.7 -> clean C-arm panels. Robustness: aug2 rung 2 = ship candidate
(98.8% clean; over-exposure 78 vs 19, magnify 98 vs 66, shutter 95 vs 23); aug3 costs 2-10 points
clean. aug2/aug3 do NOT fix the fluoro region confusion (anatomy-appearance shift, not corruption).
tgt128 bank: no gain. ConvNeXt arm at lr 3e-4 collapses (18% at ep 5) -- needs its own lr.

**04:00:** strict video gate keeps 113/51k frames (too strict), medium gate (p>=0.5, det 0.55, >=2 boxes,
`--out-tag _med`) ~1/110 frames. ConvNeXt arm collapses (cancelled). all4 aug3 arms ~88% @ep35.
Region classifier v2 (pretrained): 63% out of fold -> region prior NOT used. detect_v5z at ep 25
mAP50-95 0.854 (plateau); FluoroCap infer with epoch-25 detector + aug2 rung1 = tag v5z25_aug2r1.

**Next:** reader study (annotate pages), fine-tune the detector on reader boxes from FluoroCap A,
retrain the level model with FluoroCap A caption-verified panels, freeze v1.0 after readers. Related: [[xr-benchmark-and-robustness-2026-09-13]].

## 2026-09-14 afternoon additions (hardware constraints, orientation, new routes)

- Captions bind devices to vertebrae: `tools/fluorocap_hardware.py` -> `~/FluoroCap/hardware_constraints.jsonl`
  (body / disc / span / near kinds; 946 of 2,815 included panels have a body-level constraint, 309 name
  hardware in two or more vertebrae). `tools/fluorocap_anchor.py` scores every contiguous run: floored model
  log-prob (P_FLOOR 0.02) + caption term (w 3) + hardware term (w 6); HARD caption containment when the
  caption's levels fit the boxes; tries both directions when the orientation is unknown.
  `fluorocap_infer.py --anchor --orient --hardware`. Best tag `v5z25_hist_r1_anchor_hw2`: 81% of scored
  panels get a caption-consistent contiguous proposal (upper bound; caption is enforced); caption-blind
  hardware-only check 22/51.
- Orientation net `~/FluoroCap/orientation_net.pt` (`tools/train_orientation.py`, 4-way rotation, 99.9% on
  films) over-calls rotation on FluoroCap: rotate only sideways calls at p>=0.9; a 180 call = direction unknown.
- Implant detector `~/FluoroCap/hardware_det_v1.pt` from VinDr "Surgical implant" boxes (mAP50 0.42 on VinDr);
  precise but low recall on fluoro (152/1,957 panels flagged). Flag rule: construct box covers >=40% of the
  vertebra box. Next: metal pseudo-labels from FluoroCap + CT hardware DRRs (11 cases, label 66 mostly).
- New routes (run from WSL, root `~/FluoroCap_wsl`): `fluorocap_datarepos.py` (Zenodo/Figshare/Dryad/OSF/
  Mendeley/DataCite), `fluorocap_commoncrawl.py` (device-company technique-guide PDFs via the CC index ->
  `pdf/cc_*.pdf` + `cc_pdfs.jsonl`; `--html` mode for practice websites), `fluorocap_caserepos.py`
  (Radiopaedia CC BY-NC-SA, Eurorad, MedPix). Manifest does not yet ingest cc_pdfs / caserepos / datarepos rows.
- Social video: yt-dlp + curl_cffi (`--impersonate chrome`) lists TikTok user pages but not tags/search;
  Instagram and X need the user's login cookies. TikTok discover pages are client-rendered (no items in HTML).
- Competitor: xvr (MIT, arXiv 2503.16309) is 2-D/3-D registration needing a preop CT; note in
  docs/PRIOR_ART_WEAK_SUPERVISION.md.

## 2026-09-14 evening: routes, checks, self-training
- New route script `tools/fluorocap_archives.py` (Wellcome API, Europeana demo key, Flickr public feeds or
  API with FLICKR_KEY, Internet Archive texts -> `pdf/ia_*.pdf` + `ia_pdfs.jsonl`); manifest ingests
  `archives_matched.jsonl` (routes archive_<site>) and IA PDFs via pdffig; panels scan includes `archives/`.
  Run on WSL root `~/FluoroCap_wsl`; rsync `archives*`, `ia_pdfs.jsonl`, `pdf/ia_*.pdf` to grid `~/FluoroCap/`.
  Dropbox / Google Drive / personal hosts have no search surface; only via Common Crawl (index down 2026-09-14).
- YouTube route on WSL keeps running (3 workers): 197k frames / 101 GB / 15,174 matched by evening; rsync
  to the grid started (`~/FluoroCap_wsl/log_rsync_youtube.txt`); then rerun the window search
  (`fluorocap_video_crop.py`) over the new frames on the grid.
- Caption-free checks `tools/fluorocap_consistency.py`: figure mates (same figure, same caption levels)
  agree on region 88% with the decoder vs 52% model-only (Jaccard>=0.5: 69% vs 31%) -- partly induced by the
  shared caption; video-neighbour check needs video panels in the manifest's included set (0 pairs now).
- Detector self-training: `tools/make_fluoro_selftrain.py` + `slurm/fluoro_selftrain.sh` (job 40237288):
  detect_v5z boxes+corners (conf>=0.6, >=2 boxes, caption-region gate) on panels + video windows -> yolo_v6f,
  fine-tune detect_v6f, rerun pipeline tag v6f_anchor, consistency check. Judge on film test split + FluoroCap.
- FluoroGen LoRA job failed once on a broken bitsandbytes (uninstalled from env fluorogen); resubmitted
  40237290 on gmsap,galhp.

## 2026-09-14 night: v2 autoannotation pipeline (user: "build it in an integrated way, blow me away by tomorrow")
- Evidence stages (slurm/fluorocap_v2.sh, STAGE=...; env `fluorogen` needs PYTHONNOUSERSITE=1 because ~/.local
  has an onnxruntime built for a newer glibc): dedup (DINOv2-small, `duplicate_groups.jsonl`, cos 0.975/ham 4:
  995 groups, 2,208 images; manifest columns duplicate_group/_size), ocr (EasyOCR; ~6% of panels carry printed
  level labels; `ocr_levels_*.jsonl`), ovhw (OWLv2 thr 0.2: recall 30% on caption-named / FP 18%; gdino fires on
  everything below 0.4; `ovhw_owlv2.jsonl`), vlm (Qwen2.5-VL-7B, blind + caption reads, ~6 s/panel, needs a
  48 GB+ GPU -> galhp/gmsap; MedGemma gated; `vlm_panels_*.jsonl`, prompts in vlm_meta.json), anchor_build
  (AP+lat DRRs of CTSpinoPelvic1K with sacrum/femoral head/rib/rib12/lumbar rib/implant boxes -> ~/anchor_drr)
  + anchor_train (YOLO11m -> ~/FluoroCap/anchor_det_v1.pt) + tools/fluorocap_anchors_infer.py.
- tools/fluorocap_infer_v2.py: evidence only (ensemble of M18/M19/M21/M22 + flip TTA, per-(model,rung)
  recurrent heads trained on the matching rung bank -- v1 reused one head trained on rung-0 base embeddings for
  every model, a real bug), per-box probs/entropy -> `infer_v2_v2.jsonl`.
- tools/fluorocap_decode_v2.py: one contiguous run from all evidence (weights W: cap 3, ocr 6, hw 4, anchor 5,
  vlm 1.5, mate 1.5, floor 0.02; hard caption containment; two passes with figure-mate / video-neighbour
  region votes); outputs labels, confidence, evidence lines, decided_by, review_priority, duplicate_group.
- tools/fluorocap_pages_v2.py: reader pages ordered by priority with evidence (`~/FluoroCap/reading_v2`).
- slurm/fluorocap_v2_pipeline.sh: login-node orchestrator waiting for the stages -> decode -> consistency
  (tag dec2_v2) -> pages -> manifest v0.3. Log ~/FluoroCap/log_v2_pipeline.txt.
- New routes on WSL: tools/fluorocap_patents.py (Google Patents xhr query -> patent PDFs, tier A; works, 10/page)
  and tools/fluorocap_sitemaps.py (manufacturer sitemaps + resource pages -> technique-guide PDFs); both write
  cc_pdfs.jsonl rows so pdffig + manifest ingest them.
- Jobs running at 10:20: fluorogen_lora (40237308, LoRA at ~9%; watch b8brfwyji submits generation), fluoro_selftrain
  (40237288), v2_infer (40237337), v2_ocr (40237341 array), v2_ovhw (40237350), v2_vlm (40237356 array 0-3),
  v2_anchor_build (40237314 array) -> v2_anchor_train (40237315), YouTube rsync (~25% at 10:00), archives (451 PDFs),
  refresh orchestrator waiting for RSYNC_DONE.
- Dataset card artifact: https://claude.ai/code/artifact/f7062a95-0c41-49f9-8943-1bccefc70a19 (tools/fluorocap_report_stats.py).
