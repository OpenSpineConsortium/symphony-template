---
name: fluorocap-prototype-and-lstv-arm
description: "The single-image level prototype (tools/level_prototype.py), the transitional-anatomy harvest arm (~/FluoroCap_lstv on WSL, --extra query + TRANS_RE gate) and the Semantic Scholar route; where each writes and what the user asked for"
metadata: 
  node_type: memory
  type: project
  originSessionId: e44eca96-f48c-494d-ba1f-7dae68bdf06d
  modified: 2026-09-15T14:43:52.448Z
---

**Prototype (2026-09-15):** `tools/level_prototype.py --image <file|dir|glob> --out <dir>` on the grid (fluorogen
env, GPU): orientation net -> film histogram match -> keypoint detector -> 96-px context crops -> all-spine level
model (registry alias `allspine_v2_r1`) with flip TTA -> anchored decode with T13/L6 columns (w_rare 1.0) -> per
vertebra: level, probability, top-3, entropy, region, abstain flag (decoded != single-crop or p < 0.5); overlay PNG +
JSON per image, `prototype_results.json`. First run (job 40285709, `~/proto_test/out/`): 24 panels, 78 vertebrae,
0.1-0.7 s/image, 55 abstained, 6 no-detection; overlays sensible on a real standing lateral film. No recurrent
head by default (`--head` optional).

**Transitional arm:** `fluorocap.py search --extra` (wrong-level / LSTV / TLTV / rib / numbering terms, Europe PMC
full text) -> `captions --mode radiograph` with the TRANS_RE gate (a caption naming the variant is kept without a
level token; scouts/topograms count as radiographs) -> fetch -> publisher refetch -> push to the grid root under
`LSTV_FIGURES_ADDED` (`captions_matched_lstv.jsonl`, rows carry `arm: lstv`). Root `~/FluoroCap_lstv` on WSL,
chain `~/lstv_chain.sh`, marker LSTV_DONE. 10:25: 6,007 articles; 669 matched figures after 1,116 read.
`fluorocap_pdf_figs.py` has the same gate and tags rows `transitional`; `source` is s2_pdf / cc_pdf / openalex_pdf.

**Semantic Scholar route:** `tools/fluorocap_s2.py` (search: 13 query families incl. lstv, tltv, wrong_level,
hardware, corpectomy; expand: citations/references of transitional seeds) -> `~/FluoroCap_s2` -> pdf_figs ->
grid under `S2_FIGURES_ADDED`; chain `~/s2_chain.sh`. Key works (429s when hammered; 1 req/s).

**Why:** the user wants a working prototype and every real LSTV/TLTV radiograph/fluoroscopy image from the
wrong-level and transitional literature at publisher resolution for training and testing; the corpus had zero
real L6/T13 labels and only 22 transitional-term figures before this arm.

**How to apply:** run the prototype on new frames with the registry-resolved models; extend the harvest by adding
terms to QUERY_EXTRA / TRANS_RE, never by relaxing the radiograph gate; human verification of the LSTV candidates
(contact sheets under `~/FluoroCap_lstv2/candidates/`) is the next gate before any of it trains a model. See
[[fluorocap-dataset]], [[level-model-bank-coverage]], [[fluorocap-credentials-and-resolution]].

**Measured 2026-09-15 afternoon.** Prototype on the 120-panel reading set (`~/lstv_eval/PROTOTYPE_EVAL.md`): abstains on
75% of vertebrae; on hard-caption panels only 13.7% of its levels are among the caption's levels (17.5% of the
non-abstained), run-exact vs the corpus decoder 27%, lumbar best (58% positional agreement), cervical worst. The
orientation net (`orientation_net.pt`, Sep 14, films+DRR) called up/down uncertain on 95/120 reading panels and
2,099/5,679 corpus panels -> retrained self-supervised on the 2,991 classifier-verified real panels + films
(job 40287130 -> `orientation_net_v2.pt`, registry `orientation_net_v2`; prototype re-run 40287131 ->
`~/lstv_eval/reading120/out_orient2`). Registration harness (`~/reg/level_harness/results.md`, DiffDRR, 40 CTSP1K
cases incl. 10 L6): capture 100 / 92 / 69% from 5-10 / 10-20 / 20-40 (deg / mm) starts, per-level 91.8%, median
centroid 0.8 mm, 3.8 s per frame, L6 cases 89% per level. Caption labels are not ground truth; 90% on real
fluoroscopy is unmeasurable until the LSTV candidates are human-verified.
**Outage note:** when the Claude session dies, WSL shuts down and every nohup chain with it; ledgers end in a
truncated line -> run `~/tmp/repair_ledgers.py` then `~/relaunch2.sh` (lstv_chain, round2b, both caption crawls,
instagram). Grid nohup waiters survive.

**Orientation v2 verdict (16:20):** self-supervised 4-way rotation retrained on 2,991 real panels reaches only 61.7% on the 120 reading panels (chance 25%); direction_known 25 -> 33 of 120. Up/down is genuinely ambiguous on tight real crops; the decoder's two-direction search, not the orientation net, has to carry it. Do not iterate the orientation net.

**LSTV verification bench (2026-09-15 17:05):** https://claude.ai/artifact/6m2QhRnmRgsQgwqR53TonS (artifact with `db`);
built by `scratchpad/bench/build_bench_data.py` from `~/FluoroCap_lstv2/candidates/lstv_candidates.jsonl` (transitional-term,
non-animal, on disk -> 480-px thumbnails in `bench_data.js`); pass one = 165 PMC figures; v2 (17:30) adds 420 extra-source figures (OpenAlex/preprint PDF figures, Open-i, MedPix, Commons; ids `<source>__<id>__<file>`) = 585. Extra-source harvest summary: `~/FluoroCap_lstv2/HARVEST_SUMMARY.md` (698 images; Eurorad also ai-train=no, not fetched). Verdicts live in collection
`verdicts/<pmcid__file>`: type (xr | fl | scout | ctmri | notxr | animal), findings [L6, sacL5, lumbS1, T13, lumbrib,
rib12, cerv, wrong, none, unsure], quality (ok | small | split), note, pmcid, fig_id, file, ts. Read them back with the
Artifact tool `read_db` (collection "verdicts") to build the transitional train/test split. Republish with new
`bench_data.js` after pass two (LSTV_DONE_PASS2) and the extra-source harvest.

**Text corpus + counts (2026-09-15 16:45):** `tools/fluorocap_passages.py pmc|pdf` mines full-text passages on
transitional variants, numbering, ribs, wrong-level events and their risk factors -> `<root>/passages.jsonl`
(families, terms, excerpt); running on ~/FluoroCap_lstv (6,007 articles) then the S2 PDFs (lstv/tltv/wrong_level).
`tools/fluorocap_level_counts.py` -> `~/FluoroCap/LEVEL_COUNTS[_baseline].md/.json` (panels per level by evidence
and route; baseline 4,614 labelled of 5,789 decoded); the grid waiter `~/tmp/level_counts_waiter.sh` re-runs it when
the s2, lstv and r2 refreshes finish (LEVEL_COUNTS_DONE in level_counts.log). S2 refresh launched 16:30
(MARK=S2_FIGURES_ADDED TAGSUF=_s2). The user wants the model to learn from descriptions too (why wrong-level events
happen), not only images.

**Feasibility -> build (2026-09-15 17:10).** Verified deep-research report: https://claude.ai/artifact/URAmo1Fa5rGj9zssVgmZGP
(8 surviving findings). The narrow path it leaves open: a BINARY transitional flag on a single view (not a Castellvi
type, not an authoritative junction level), with abstention when the sacrum / 12th rib is out of frame. Comparator:
Kwak 2025 (PMC12610351) 3,116 lateral films, acc 76.4 / sens 85.1 / spec 61.9 / AUC 0.84, specialist 83.9.
Our ground truth for it: `data/zenodo_deposit/manifest.json` (802 records) carries adjudicated `lstv_label`
(769 normal, 17 SACRALIZATION, 14 LUMBARIZATION, 2 SEMI), `lstv_class`, `castellvi_type` (IIIb 16, IIb 6, IV 4,
IIa 4, Ib 2, IIIa 1), plus `lumbar_ribs.csv` (24) and `_lstv_phenotypes.csv` (33). 33 positive PATIENTS is the
binding limit on any CI. Build under `~/lstv_flag` on the grid (renders -> 5-fold patient-level CV -> AUC with
bootstrap CI, per view and per field of view, with the abstention rule measured). Extra-source figures pushed to the
grid corpus 17:01 (+137 pdffig, +12 open-i/medpix, +79 commons; marker LSTV2_FIGURES_ADDED, refresh _lstv2).

**Text corpus first result (18:35).** `tools/fluorocap_passages.py` has mined 11,761 passages from 3,343 of the
6,007 transitional-arm articles; `tools/fluorocap_wrong_level_report.py` counts the wrong-level ones ->
`~/FluoroCap_lstv/WRONG_LEVEL.md`. Over 1,678 wrong-level passages from 529 works the named mechanisms are:
process or communication failure 178, transitional or numerical variant 102, deformity 78, body habitus 72, prior
surgery 61, miscounting from a landmark 52, image misread 43, marker failure 35, osteopenia 27. Countermeasures:
time-out or protocol 144, navigation or computer assistance 83, count from a fixed landmark 26, intraoperative
radiograph with a marker 8, compare with the preoperative study 3, second reader 2. Region: lumbosacral 359,
thoracic 273, cervical 181. Counts are passages matching a named pattern, not reported events.

**Corpus and flag, end of 15 September.** LEVEL_COUNTS.md recomputed over five decode files (v2, v3, v3pre,
hires_allspine_v2_r2, v4): 20,700 panels decoded, 11,339 labelled (was 5,789 / 4,614 that morning). Per level:
L4 5,855, L3 5,731, L2 5,139, L5 4,597, L1 4,427, T12 2,858, T11 2,149, sacrum 1,570, **L6 338, T13 254**.
Routes: pmc figures 8,616, video 2,535, reddit 104, commons 84. Decoder placements, not verified labels.
**First transitional flag (CTSpinoPelvic1K renders only, 5-fold patient CV): near chance.** LSTV AUC 0.578 on
801 patients / 34 positives (sens 0.853 at spec 0.248; Youden 0.529 / 0.643); TLTV AUC 0.584 on 799 / 16
(0.875 / 0.261; Youden 0.438 / 0.787). Models at ~/lstv_flag/models/{lstv,tltv}_flag_v1.pt with the .flag.json
sidecar the prototype reads. Two live hypotheses for the weakness: 34 positives is underpowered, and the input is
a whole frame resized to 384 px, which shrinks the lumbosacral junction where the signal is - a junction-cropped
input from the detected sacrum and last mobile vertebra is the next experiment. The VerSe-augmented version
(34 -> 164 positives) was still training.

**Flag, full result (15 Sep, ~/lstv_flag/LSTV_FLAG_RESULTS.md).** Positive control first: predicting SEX from the
same renders gives AUC 0.95 [0.935, 0.966], so the renderer, trainer and patient-level CV all work - the
transitional task is hard or underpowered, not broken. CTSpinoPelvic1K alone (34 positives): LSTV AUC 0.577
[0.480, 0.669], CI contains 0.5. Adding VerSe (110 positives, 251 patients): within-cohort **AUC 0.725
[0.663, 0.787] junction / 0.729 lumbar** - the first intervals excluding chance. Pooled 0.847 is confounded by
cohort prevalence (4% vs 44%) and must never be quoted. **Field of view is the substantive finding:** junction
0.656 > lumbar film 0.509 > wide 0.543 (ctsp wide is 0.406, below chance), i.e. the signal is LOCAL lumbosacral
morphology and is diluted by framing wider - the opposite of Kwak 2025, whose Grad-CAM attends to the T12 rib.
**External check on real radiographs: no signal.** On 3,600 BUU lateral films, 5 of the 144 count anomalies fall
in the top 144 by score (chance 5.8), 19 in the top 500 (chance 20). The DRR-to-real gap is untouched.
**A safety bug worth remembering:** the abstention rule first required L5 or L6 in frame, so it abstained on four
sacralised Castellvi IIIb patients who have no L5 - it declined on exactly the positives it protects. It now asks
for the lowest mobile lumbar segment by position, never by name.
**Dataset defect found:** release record 1043 (token 730) is the only case with a GAP in the vertebral chain -
T6-T12, L1, L2, L4, L5, with **L3 missing**. Worth a re-read before the next release.
**TLTV note:** the rib-bearing-count clause is inoperative on abdominopelvic CT (it measures where the scanner
stopped; no case shows 12), so TLTV was defined on direct observations only: lumbar rib 16 cases, T13 rib 0.

**Scoping review statistics (15 Sep, ~/review/REVIEW_STATS.md).** The hypothesis that the prevention literature
aims away from the failing step is NOT supported: among 45 sources naming a countermeasure, naming an
anatomical/radiological mechanism gives 72.2% vs 70.4% naming a radiological countermeasure, Fisher p=1.000,
OR 1.07 [0.30, 3.84] - underpowered, a failure to detect, not evidence of absence. **The real finding is the
evaluation gap:** level-determination countermeasures (count from a landmark, marking, intraoperative radiograph,
second read) are evaluated against an OUTCOME in **0 of 15** explicit sources, against 19.0% for navigation and
38.9% for organisational controls; Fisher p=0.024 (sensitivity 10.6% vs 20.0%, p=0.002). Reported frequency spans
**4.65 orders of magnitude** (0.09 to 4,000 per 10,000, median 500) and ascertainment does NOT explain it in this
corpus (rho -0.10, p=0.73). Transitional anatomy implicated in 20.7% [14.8, 28.2] of wrong-level sources; regional
effect (lumbosacral 39.0% vs thoracic 8.7%, OR 6.37, p<0.001) only in the sensitivity stratum. Every test run twice
(explicit primary, inferred as sensitivity); the two strata DISAGREE on region and on time trend, reported not
resolved. PRISMA 2020 flow diagram at ~/review/prisma_flow.svg (both passes in every box).

**Verification benches (the measurement gate).** Two, and they are for different jobs.
1. **Level accuracy, RANDOM**: https://claude.ai/artifact/MKJXSYgzFBa5ndLK8TVsKo - 179 panels / 865 vertebrae drawn
   uniformly within route from decode_v2_v4 (tools/make_verify_bench.py, seed 20260916, grid ~/verify_bench).
   Verdicts in collection verdicts/<image_id>: marks {box index: y|n|u}, fix {index: level}, route, hard_caption.
   This is the unbiased estimate of real-panel accuracy - a set chosen by model uncertainty could not be reused
   as a test set (Farquhar et al. ICLR 2021).
2. **Transitional candidates, ENRICHED**: https://claude.ai/artifact/6m2QhRnmRgsQgwqR53TonS - 585 figures for
   finding anomalies, NOT for measuring accuracy.
Read either back with the Artifact tool read_db on collection "verdicts".
