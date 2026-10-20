---
name: ruleclass-super-detector-run
description: "/rs/rs_grp_oschome/go2432/ruleclass is the SUPER DETECTOR RUN over the 21,622-CT census (TS arm A, Moller ribs on SPINEPS+VERIDAH arm B, Dataset803 pelvis) and the base of the transitional review tree; 2026-09-27 every other grid job was cancelled for it"
metadata:
  node_type: memory
  type: project
  originSessionId: f1bdbd78-151f-470b-b703-dd9af9b3fecc
  modified: 2026-09-27T19:52:48.326Z
---

**What it is.** `/rs/rs_grp_oschome/go2432/ruleclass/` (`RS/ruleclass`) -- docs `CORPUS.md`, `tiers/TIERS.md`,
`ARM_B.md`, `arms/ts/ARM_A.md` + `STATUS.md`. The census is **21,622 CTs** (tier 1 5,094 = CTSP 802 + VerSe 374 +
TS-dataset 1,278 + COBRA 692 + every flagged person; tier 2 12,217 = every other CT with a SPINEPS harvest mask;
4,311 untiered). SPINEPS+VERIDAH masks exist for 12,630 gate-passed acquisition CTs plus the benchmarks; TS on all.
Arms: **A** = TotalSegmentator 2.18.0 `total` full-res -> `arms/ts/<collection>/`; **B** = Moller rib nnU-Net
(Zenodo 14864106, folds 0-2, via SPINEPS' wrapper, P,I,R 0.8 mm) -> `arms/moller_fast/` (corpus pass, config fast) and
`arms/moller/` (full config, 20-25x slower, Dice 0.983-0.991 vs fast); **pelvis** = Dataset803 nnU-Net (CTSP-trained)
-> `arms/pelvis/`, with `pelvis_agree` vs TS and vs CTSP v11 GT. Runs in `~/mambaforge/envs/spineps` (spineps 2.1.1,
TPTBox 0.8.2, torch 2.6.0+cu124); **the Blackwell nodes ymh3/ymh4 (sm_120) cannot run it.**

**A prior screen is already in the tiers**: 2,337 tier-1 CTs carry a registry (R13) or acquisition-screen (R20) flag
-- L6 148 + 303, T13 14 + 82 -- from a rib-free lumbar count on SPINEPS/VERIDAH with a "both in field" gate (sacrum AND
last rib-bearing vertebra with whole ribs in the CT). TS rib masks often lack the rib head, so a rib-free count on TS
ribs alone disagrees with SPINEPS. `CORPUS.md` sec. 73 table gives per-collection calls (291 L6 / 75 T13 over the 17
acquisition collections; VerSe GT id 25 L6 on 50, id 28 T13 on 6).

**Only C-ArmLSpine (149 CBCT) has paired radiographs** in the census; DeepFluoro 6, Geneva 1, SpineSAC 3 are
cadaver/phantom. Everything else is CT-only.

**Why:** Greg 2026-09-27: build a per-type / per-case review tree of transitional cases (CT + XR + registration) screened
by his new rules (rib-free lumbar count, pelvis morphology, lowest-rib/rib-above ratio, MDPA T-L AUC), Ashley screens ->
Dr Tech confirms; "prioritize over all running jobs, record then cancel all, recycle the census segmentations." Every
non-ruleclass job was cancelled (83 recorded in
`spinesurg-ct-nnunet/docs/grid_records/JOBS_RECORD_2026-09-27_1544.md` with resume instructions); ruleclass kept and
its holds released, except `armb_t1pos_full` 40481738 (fidelity pass, 400-1,700 GPU-h) left held.

**How to apply:** treat ruleclass as the segmentation source; do not re-segment what its arms already wrote. Watch for
raw SPINEPS ids (1..N) in pre-147428d harvests (`tier*.tsv` column "raw ids": 108 tier-1, 422 tier-2). See
[[u251-name-sweep-traps]] for the SHA-anchoring habit, [[label-scheme-v4-vs-ostk]], [[spineps-ids-can-be-scrambled]].
