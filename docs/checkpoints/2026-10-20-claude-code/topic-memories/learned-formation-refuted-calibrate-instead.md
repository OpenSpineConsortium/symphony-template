---
name: learned-formation-refuted-calibrate-instead
description: "2026-09-21 -- CT->fluoro formation CALIBRATED on DeepFluoro (physics 80.9%, +4.3 with nine device terms, ceiling 99.5%); first per-vertebra recall on REAL fluoroscopy = sacrum 76.9% over 6 specimens / 365 frames, seeds span 26 pts; 160/366 real frames stored upside down; angle regression buys nothing; kb stays 2.5; photons fitted; noise before receptor blur"
metadata: 
  node_type: memory
  type: project
  originSessionId: f1bdbd78-151f-470b-b703-dd9af9b3fecc
  modified: 2026-09-21T18:10:29.340Z
---

**The question** (Greg, 2026-09-21): learn f: (CT, seg, pose) -> real fluoro on DeepFluoro's 366 paired
frames and apply it to whole-spine CTs. **Answer: calibrate, don't learn** -- settled by the literature
and by the residual, which agree. Full record: `docs/DEEPFLUORO_FORMATION.md` (sec. 5 results, open items).

**Literature** (two verified passes; Rapuri Table 1 read DIRECTLY 2026-09-21 -- the second pass could not
fetch it and wrongly "refuted" it): Rapuri 2026 (arXiv:2606.21414, 5 specimens -> 6th, matched views):
diffusion 4.40 mm vs real 4.89 vs physics DRR 7.83 (+/-25.7) at NCC>0.60, but **25.4 vs 17.9 at NCC>0.20**;
DRRs with +/-2.5 deg view augmentation best at EVERY threshold (4.87/6.02/9.73); matched specimen DRR = real
(4.37 vs 4.38); NO hallucination statement in the paper. RealDRR (Dhont 2020) FULL TEXT + SUPPLEMENT on hand (Greg uploaded
2026-09-21, `~/.claude/uploads/.../7c18115b-*.pdf`, `7651e796-mmc1.docx`): ray tracer -> cGAN (GAN+50-L1,
full-image D), 800 pairs/2 patients -> 3rd: SSIM 0.96, template matching 1.0-1.5 mm vs DeepDRR 1.6-3.3 vs
raw 41-49; **Supplement App. B: trained on ONE patient the GAN moved landmarks 1.8-2.1 mm ("learns to
correct" CT-vs-CBCT anatomy); >=2 patients < 1 mm** -- cite THAT, not "hallucinated geometry".
**V2 RELAUNCH 2026-09-21 ~08:30** after the driver was PREEMPTED TWICE on reqp/requeue (restarts deleted
roots under running trainings, launched duplicate chains): everything v2 wiped; driver now idempotent
(LAUNCHED markers, no-requeue); per-fold photon fit (dfphot 40403408 -> photons_folds.json) -> driver
40403428 -> refine arms 40403429-34 (dependency chain). Results: `tools/deepfluoro_anchor_report.py`.
**PROPOSAL REQUESTED (Greg, morning of 09-21)**: artifact for mobile -- single-path cartoon, in-domain
counting numbers, localisation with the PHYSICALLY RENDERED instrument (draw_instrument now a chord
integral), detector boxes on real films (`fig_boxes_films.png`), red box on the map, all DeepFluoro
results as "limits of synthetic data" (one C-arm, cadavers, seed noise), then a retrospective PACS
collection of Dr Chou's fluoroscopy (5 y) with predicted performance and what can be guaranteed. Same
figures into the manuscript. Greg hated the OLD fig_physics_real.png (white-noise renders) -- deleted;
"best synthetic" for the proposal = real pelvis frame | calibrated twin | best refiner, from v2.
**DELIVERABLES ASKED 2026-09-21 late morning (order): (1) one-page TL;DR visual abstract for community
surgeons/CFOs (cost-benefit; refs on the same page; own shareable artifact); (2) AIDaS Seed Grant
proposal (call in scratchpad/attach: $10-20k, 1-yr from Jan 2027, PI must be tenure-track AIDaS member --
Greg is a resident -> faculty PI placeholder; cover 1p + narrative 3p + alignment 1p + budget 1p +
biosketches; allowable: grad support, computing, travel, storage -- NVIDIA hardware as "computing", flag
allowability; deadline Oct 16 2026); (3) IRB protocol in Vaidya's WSU eProtocol format (VAIDYAS_IRB.pdf,
sections extracted to scratchpad/vaidya_irb_sections.txt) for retrospective PACS fluoroscopy of Dr
Chien To Do, DO (DMC neurosurgeon; spelling to confirm) 5 y + path to prospective OR trial; (4) manuscript
cost/access section; (5) phantom feasibility at the WSU C-arm lab NOW (C-Arm Validation Research Plan.docx,
X-ray safety PDF, registration form in the zip; body bequest cadaver option: Barb Rosso-Norgan
brosso@med.wayne.edu 313-577-1188). Economics numbers already verified in
docs/WRONG_LEVEL_COST_EVIDENCE.md + manuscript intro; NO source for surgeon QoL/satisfaction with nav or
nav->wrong-level reduction; nav capital cost UNVERIFIED (assumption). Old board + explainer artifacts
were deleted by the user (watch ended). NEW artifacts 2026-09-21: TL;DR visual abstract
https://claude.ai/artifact/CwxKcL5qQt2Pv37u56ndst ; proposal https://claude.ai/artifact/8uhYki72Jf355qdfLM5N96
(sources: scratchpad/visual_abstract.html + va_values.json; proposal.html + proposal_values.json + build_proposal.py).
Grant/IRB final Markdown: scratchpad/grant_final.md, irb_final.md (drafted by agents from brief_facts.md, checked
and revised; page converter md2page.py); ARTIFACTS: grant https://claude.ai/artifact/UwoqsEAjFPcUJVDutVpFHx ,
IRB https://claude.ai/artifact/8sz8XUJsAdDDWZdKBCt5sc . Greg's figure asks 2026-09-21 ~13:00: Fig 2a un-cross the learned
stage (it is BUILT now), 2c add the refiner gain; Fig 3 (old whole-spine render) replace with real |
calibrated twin | refined | residual + all-frames stats (`deepfluoro_best_synthetic.py --all-stats` ->
refiner_stats.json); Fig 9 boxes thinner (done: 1 px annotation, 2 px calls offset); look for a second
paired CT/fluoro spine dataset (candidate: Ljubljana 2D/3D registration gold-standard set, Tomazevic 2004).
**FINAL NUMBERS 2026-09-21 13:00 (`tools/deepfluoro_anchor_report.py`)**: TS arm rendered with per-fold
terms+photons (v2): **64.0% pooled/6 folds/18 seeds**; same protocol with pooled terms+range (r2): 76.9%
-- a 13-pt protocol sensitivity, bigger than any intervention; edge-rule ablation v2i 65.8% (+1.8, not the
+8 two folds suggested). pairs_v2 90.0% (one collapsed seed), pairs v1 97.3%. Learned arms (4 folds, vs
none_v2 same folds ~63): rfhp 74.2, fda 72.4, rffull 71.1; on pairs renders rfhppairs 94.0, rffullpairs
91.3 (+2-4). **Pixel-level (refiner_stats.json, 366 held-out frames, display domain): calibrated median
69.3% explained, refined 68.1%, refiner better on only 21% of frames (median -2.8)** -> it sharpens AND
invents; detection gains, pixels lose. Figures regenerated: fig_formation (learned stage un-crossed,
refiner line in 2c), fig_best_synthetic (real|twin|refined|residual), fig_boxes_films (thin boxes).
**GREG'S REAL GOAL (2026-09-21 ~13:30, verbatim gist): "if the final product of my DRR->physics->smooth
filter is close enough to real OR fluoroscopy it doesn't matter if the detector on DeepFluoro fails to
detect sacrums across domains; I'm just trying to make the DRR->physics in the live-person domain a little
more fluoro-like."** -> the metric that matters is PIXEL/appearance agreement, not the sacrum arms.
**Residual by region, all 366 held-out frames, display domain (`deepfluoro_residual_regions.py`,
`residual_regions.json`, job 40405687)**: cortical-edge band (7% of field) carries 12.5% of the energy with
bias **+8.7 grey (render too dark)** -- the ONE systematic learnable error (= device unsharp mask; the rfhp
arm addressed it and gained most); flanks 33% area / 50% energy / bias +3.8 (texture + tissue position,
NOT truncation: water_cm ~ 15 cm at the field edge); enclosed soft tissue 4% area / 1.7% energy; a smooth
12-coefficient field removes only 22% of the residual energy; the refiner leaves every number where it
found it (edge +9.0, explained 68.1). **Recommendation given: fit a 2-parameter display-sharpening term on
the pairs (LOSO) instead of a GAN/attention net -- an attention loss on the "worst" regions (bowel, flanks)
targets regions whose truth is not in the CT.** Figure 3 convention (Greg's ask): calibrated | REAL |
refined, signed residual on each outer side, RdBu_r, red = render too dark, one scale per row, smoothed 2 px.
**KCL cardiac-sheath phantom set (Wang 2025 TBME, Archive.zip, 335 biplane pairs + sheath masks, Siemens
Artis Q via frame grabber)**: a static PHANTOM with a plastic spine, one trial, near-duplicate frames -- not
useful for living-abdomen appearance; only as an unpaired second-device grain/sharpening sample.
Proposal artifact mojibake fixed (build_proposal.py read the values JSON with cp1252; now UTF-8 +
<meta charset> in every page source).
**WITHDRAWN 15:20 EDT -- the 'thin-bone effect' below was a MEASUREMENT ARTIFACT: bone mask  intersect  exposed field made the collimator border a 'bone edge'; 23 px inside the field the bias is +5.8/+3.0/+0.8 grey (`--erode 23`). The real mismatch is the collimator border ring: 22.5 % of the field, 68.6 % of residual energy, real +23 grey (penumbra vs the render's hard edge). LESSON: any region mask intersected with the field boundary manufactures edges at that boundary -- always erode or report the border ring separately.** Original (wrong) entry: **EDGE BIAS IS A THIN-BONE EFFECT (2026-09-21 14:00, `tools/deepfluoro_edge_bias.py` -> `edge_bias.json`)**:
edge-band residual of the calibrated render binned by the bone path at the edge, all 366 held-out frames:
0-0.5 cm +1.3 grey; **0.5-1 cm +62; 1-1.5 cm +81; 1.5-2 cm +48**; 2-3 cm +7; 3-4 cm +8; bone interior -1.5 to -6.
Thin bone (iliac wings, sacral ala, acetabular rims) is rendered far too faint; thick bone is right. The
existing unsharp term (alpha 0.05-0.36 at sigma_u ~ 3 px, on TRANSMISSION) does not capture it, and kb is
pinned at its 2.5 bound in every fold because the fit wants more bone contrast but a global bone scale
overshoots thick bone (opening kb hurt). Partial volume cannot explain it (linear decomposition + linear ray
sum conserve the integral). Reading: the device applies a multi-scale (small-structure) enhancement on the
LOG image far stronger than a whole-field least-squares fit will ever choose. NEXT ARM: band-pass gains on
the attenuation image (sigma 1/2/4/8 px, 3 parameters) fitted LOSO, scored by held-out explained variance AND
the thin-bone edge bias -- Greg authorised "do whatever you think will improve the results on real OR".
**TWO REMEDIES TESTED 2026-09-21 14:30 (`deepfluoro_bandgain.py`, `deepfluoro_pedestal.py`, 8 frames/spec
smoke, attenuation domain, held-out)**: (1) linear 4-band enhancement (sigma 1/2/4/8 px) fitted per-frame /
pooled / edge-only: NO change in field (87.3) or edge-band variance, edge bias untouched, gains inconsistent
across folds -> REFUTED. (2) wide scatter pedestal p-<T>: monotonically WORSE (87.3 -> 67.4 at p=0.8) ->
REFUTED. (3) **display/transfer exponent a^gamma: gamma=1.4 lifts field 87.3->89.4, edge band 71.9->74.7, thick-bone
bias +8.4->+2.6, thin-bone edge bias 8.1->6.0 / 8.3->3.5 -- monotone up to the grid end; full sweep to gamma=3.0 on
all 366 frames = job 40405xxx (`pedestal.json`, marker PEDESTAL_DONE).** If gamma is stable across folds it
becomes the TENTH device term (in `forward`/`forward_noisy` and the builder), and kb should be re-fitted
with it (kb pinned at 2.5 may have been curvature, not scale). Manuscript rewrite of the detection
subsection FINALLY committed (e040d1d; the ms12 rewrite had never reached the file). Proposal v5.
**THE REAL FRAMES WERE CONVERTED WRONGLY (2026-09-21 15:10, `tools/deepfluoro_transfer.py` -> transfer.json/png)**:
the stored DeepFluoro intensity vs model attenuation is a nearly STRAIGHT, slightly concave decreasing line
(exp(-B a) fits only with B = 0.15; transmission would give B = 1; power form gamma 0.98 calibrated / 1.27
physics-only) -> the device stores a log-compressed display image and `raw_to_atten`'s -log was a log of a
log. Every calibration, photon fit, real_test frame and edge-bias number was made against that bent target;
the gamma~2 "display exponent" (+3.2 pts) was the symptom. FIX IN CODE: `deepfluoro_calibrate.CONVERSION`
("log" default for reproducibility, "linear" = (p98 - r)/(p98 - p2)), env `DF_CONVERSION=linear` for every
tool, `--conversion` on the calibration (recorded in the JSON), `real_to_atten` used by load_pair and by
anchor.write_real/evaluate; synthetic frames still -log T. NEXT: refit terms + photons + rebuild pairs roots
under linear (`anchor_pairs_lin_<spec>`, calibration_linear.json), re-measure regions/edge bias/gamma, redo Fig 3.
Datasets Greg sent 15:00: PIG (Goswami 2020 IEEE Access) = pig LOWER LIMB + IOERT applicator on an Elekta
Synergy kV imager (7 projections +/-45 deg, CT, CBCT, matrices) -- NO spine, no use; infobot (Liu 2019 Med Phys
mp.13770) = MV portal DRs vs kV bone DRRs, 208 patients head/neck/pelvis, "Lines" = contours -- megavoltage,
not fluoroscopy, no use for appearance. FluoroCap display-window stats tool: `tools/fluorocap_display_stats.py`.
**Final six-fold learned arms (report 13:40)**: none_v2 64.0; rffull 71.7; rfhp 72.2; fda 74.2; pairs_v2 90.0;
rffullpairs 92.3; rfhppairs 95.0 (pooled over folds, seeds averaged) -- manuscript/proposal to say
"eight, eight and ten points; two to five on the matched renders".
**Ljubljana 2D-3D-GS (Tomazevic 2002/2004; Greg has the zip + user guide)**: ONE cadaveric L1-L5 segment
(80-y female, some soft tissue) in a water-filled plastic tube, CT GE HiSpeed 100 kV 0.27x0.27x1 mm stored
as **uint8 per-vertebra crops (water ~ 64, max 165, no air -> HU slope unknown)**, MR, **18 X-rays on a Trixell
PIXIUM 4600 flat panel (0.143 mm, 14-bit; supplied x2 subsampled 1560^2 float at 0.286 mm, attenuation-like,
air = 0)**, phantom rotated 20 deg steps on a turntable with fixed source/detector, fiducial gold standard TRE
~ 0.2 mm; headers give detector pose (TPosition) + source position. Small, exact, a DIFFERENT detector and
no abdomen -- a device-transfer test for the terms, not an appearance target. KCL sheath set = phantom, no use.
**Learned arms launched 2026-09-21 (Greg: "try it, I don't mind hallucination")**: rffull (RealDRR recipe
on 5 training specimens' pairs -> applied to TS renders), rfhp (high-pass-only residual), fda (low-band
swap) -- `slurm/deepfluoro_refine_arm.sh`, roots `anchor_{rffull,rfhp,fda}_v2_<spec>`, dumps
`~/model_night/refiners/dump_*.png` -- LOOK before believing. AEC is a policy on content, so the window
is PARTLY predictable from the render; only the residual scatter is not. CycleGAN/ADDA: parity under strong DR (SyntheX). Closest analogue outside
X-ray: FDA (Yang & Soatto 2020) -- swap only the lowest amplitude band per image, training-free, band-
insensitive (beta 0.01-0.09); ultrasound 3x3 DC swap +3.5 Dice (Sharifzadeh 2021); N4 removal no gain.

**Measured** (all 366 pairs, `tools/deepfluoro_*`): exact geometry (0.00 px) + repo attenuation, no
detector term -> **80.9%** explained. **Nine device terms** (kb, s, sigma_s, sigma_r, alpha, sigma_u, b, c, d), PER-FRAME
linear window (a global display curve gave -498,295%): LOSO median **+4.1**; **AP->lateral +4.6** (n=68,
>=15 deg, max 36.5 deg -- no true lateral exists in DeepFluoro).

**v2 fits** (`slurm/deepfluoro_calibrate_v2.sh`, 6 min each): scatter width boxed 6-16 px -> **+4.3**,
sigma_s 15.8 px spread 0.4, ALL terms stable -> this is **`calibration_best.json`**. Scatter dropped: +4.1 but
sigma_r destabilises. **kb opened to 6 -> kb 3.0 and held-out gain FALLS to +3.5**: keep the 2.5 bound; a
physical (kVp) reparameterisation is the only remaining fix, and it is not first. **Angle regression
(Greg's request) measured: per-angle terms vs global on the same held-out frames +0.0/-0.2/-0.4 by bin ->
do not regress on angle.**

**Ceiling**: 0.3-0.5% of variance is stochastic -> **99.5%**. Per-frame quadratic surface: calibrated
**93.9%**. Only 0.4% of variance at <=2 px -> a regional denoising net has nothing to learn.

**Photons** (`deepfluoro_photons.py`): real grain = median **2,934 counts per 0.78 mm pixel**, p10-p90
788-4,767; the assumed 4,000 was the 79th percentile. **The draw belongs after scatter and BEFORE
receptor blur** (`forward_noisy`); spine_project and the builder had drawn white noise on the finished
frame. Builder now draws uniform on the fitted p10-p90.

**Bowel**: raw DRR carries 1.03-1.05x the real 8-32 px energy (measured INSIDE the field). The bowel is
right; don't add a mid-band term.

**Whole spine**: TotalSegmentator v300, `ts_clean_subjects.py` (2-pass parallel; every subject has all 117
mask files, empty when absent -- existence says nothing): 154 with C2+sacrum, **142 clean** (metal =
>=20 voxels >2500 HU; the 1800 HU rule dropped 45 for cortical bone). VerSe raw is REGIONAL.

**THE FIRST REAL-FLUORO NUMBER (2026-09-21 03:15, corrected test)**: YOLO11m on 597 calibrated synthetic
frames (48 TS subjects x 14 real poses, no DR; synthetic-val mAP50 0.91-0.97), one model per held-out
specimen, **sacrum recall pooled over all 6 specimens / 365 real frames = 76.9%** at conf 0.05 (by
specimen 47.8-96.2; 17-1882 seeds 51.4/77.5/56.8 -> **26 points from the seed alone**); anchor called 98%,
0.64 false sacra/frame, vertebra-region hit 83%. Not counting-grade. No single-seed arm difference (mild
55/31, strong 48/53, 3x subjects 48, mild 3x 59) is resolvable -- rank only with seeds averaged + folds
(`tools/deepfluoro_anchor_report.py`). **TEST TRAP FOUND BY THE DUMP: 160/366 real frames are STORED
UPSIDE DOWN (rot-180-for-up); the writer left them as stored while synthetic frames were turned up -> a
third of the test was inverted pelves; fixed in write_real, every arm re-scored with EVAL_ONLY=1
(numbers before the fix were ~40%).** **LOOK AT THE FRAMES BEFORE TRAINING** -- round 0
was garbage (aggressive DR stripes/blotches; zero-count pixels -> atten 13.8 -> white/black frames) and no
printed number showed it. Fixes: `raw_to_atten` (ONE conversion, real+synthetic: subtract own p2, 2%
floor), `window()` on the CENTRAL ROI for both writers (whole-frame windows made lateral frames white
slabs and cadaver frames dark), DR tier as an ARM (`DR=none|mild|strong`), `TAG=_r2` per round so a
rebuild never deletes a dataset a training reads. Round 2 (ROI window) = jobs 40402568-76,
`~/model_night/anchor_<dr>_r2/eval_anchor_<dr>_r2.json`. **The dump (`--dump`, drawn calls on real frames) showed WHY**: the detector finds vertebrae at the top
edge but calls the sacrum as thin boxes at the frame's top border or not at all; the GT sacrum box
(labels 4|7 = sacrum+lower sacrum) spans the whole inlet to the symphysis; and saturated WHITE regions
(cadaver soft-tissue ends, pubis) attract vertebra calls at 0.1-0.3 -- the under-penetrated oblique
synthetic frames (no AEC) taught "white slab = vertebra". **Known domain gap to state**: DeepFluoro is
cadaveric pelves with AIR around them; the synthetic set is living abdomens; the render has no AEC
(fixed spectrum -> thick lateral views under-penetrated). Photon fit under p2-subtract conversion is
UNRELIABLE (52,000; kept as `photons_p2sub_unreliable.json`); builder uses 773-4,767.
Manuscript has Methods/Results/Discussion/abstract + `fig_formation*.png` (7,088 words, builds clean, 35 pp).
See [[deepfluoro-convention]], [[drr-to-fluoro-levers]].
