---
name: lstv-oneshot-training-run
description: "The one-shot LSTV arm on the grid (Dataset810, ResEnc-L 100G, 500ep LSTVOversample, five folds) for the CNS slides due end of September 2026: job ids, epoch times, where to evaluate, and the traps hit on the way"
metadata:
  node_type: memory
  type: project
  originSessionId: e44eca96-f48c-494d-ba1f-7dae68bdf06d
  modified: 2026-09-08T05:57:18.082Z
---

Launched 2026-09-07 for CNS (slides due end of September 2026). Repo `spinesurg-ct-nnunet`
branch `L6_Class` (local and grid; push there). Grid: `~/spinesurg-ct-nnunet`, data from the
v10 working copy `~/data/CTSpinoPelvic1K` (HF_EXPORT_DIR, single manifest.json + splits_5fold.json).

**Dataset810_SpineSurgLSTVOneShot**: 24 classes (T10..T13, L1..L6, sacrum, rib_left/right
pooled 1-11, rib12 and rib13 per side, lumbar_rib per side, hips, femur, ignore=23); planner
ResEnc-L at 100 GB (`nnUNetResEncUNetLPlans_100G`, patch 256x320x320, batch 2); trainer
`nnUNetTrainerWandB_500ep_LSTVOversample` with `SPINESURG_LABEL_SCHEME=oneshot` (commit
32bc088), LSTV_OVERSAMPLE_FRAC=0.5. Sampler pool = 39 cases (23 lumbosacral subtypes + 16
lumbar-rib carriers from case_to_attrs); the STARTUP line "oversample-pool size: 23" is a
stale count, the real one is the later "using 39 for oversampling" line.

**SUPERSEDED 2026-09-08 08:10**: Greg chose to retire the one-shot folds and run the NUMBERED-RIB arm
instead (SCHEME=fullribs, Dataset813_SpineSurgLSTVFullRibs, 42 fg classes: one-shot + every rib per
side; ignore 43). `slurm/switch_to_fullribs.sh` (nohup on the login node, log logs/switch_to_fullribs.log):
prep 40164963 -> unpack 40165184 -> folds 40165185-89 (fold 4 STAGE_LOCAL=1); when the unpack completes it
cancels the one-shot jobs, archives their logs to ~/archive/, deletes Dataset810 results+preprocessed
(raw kept: benchmark scoring space). Benchmark jobs were held so the folds take the freed GPUs; a watcher
releases them. Quota is 5 TB (home was 1.8 TB). Submit line: same as below with DATASET_ID=813,
DATASET_NAME=SpineSurgLSTVFullRibs, SPINESURG_LABEL_SCHEME=fullribs. Old one-shot jobs below are history.

**Live jobs (2026-09-08 02:00 EDT, one-shot, retired)**: folds 0/1 = 40163538/39 on msa3, fold 2 = 40163540 and
fold 3 = 40163541 on msa1, all STAGE_LOCAL=0 (read from NFS after the one-time unpack job
40163498). Epoch 0 took ~1660 s, later epochs 1150-1340 s (19-22 min) -> ~6.7 days per fold,
done ~14-15 September. Fold 4 = 40164146 resubmitted with STAGE_LOCAL=1 (222 GB of .npz to
/tmp, nnU-Net unpacks locally; one such fold per node fits the 1.7 TB /tmp) as the A/B test
of node-local staging; if its epochs are much faster than 19 min, that is how to run the
next arm. Pseudo-Dice at epoch 15: vertebrae 0.5-0.8, sacrum 0.86-0.90, femur 0.83-0.93;
L6, T13, rib13 and lumbar ribs still 0 (expected early).

**Submit line** (per fold): `sbatch --export=ALL,FOLD=N,DATASET_ID=810,DATASET_NAME=SpineSurgLSTVOneShot,PLANNER=nnUNetPlannerResEncL,GPU_MEMORY_TARGET_GB=100,TRAINER=nnUNetTrainerWandB_500ep_LSTVOversample,LSTV_OVERSAMPLE_FRAC=0.5,SPINESURG_LABEL_SCHEME=oneshot,STAGE_LOCAL=0 slurm/spine_train_fold.sh`.
Fold jobs self-requeue 20 min before their 48 h limit and resume from checkpoint_latest;
they export validation predictions (+ softmax .npz) at the end.

**Traps hit**: (1) prep job "FAILED" on a legacy dataset.json check after finishing (fixed
93f6275); (2) user-local singularity 4.0.2 fails on compute nodes, use the nextflow env's
3.8.6; (3) staging two folds per node to /tmp filled it; (4) scheme mismatch until the
trainer/loader learned "oneshot"; (5) a background watcher armed before a manual resubmit
later submitted five DUPLICATE folds (40164131-35, cancelled 2026-09-08 01:57) -- kill stale
watchers when you resubmit by hand.

**Mid-training evaluation**: `FOLD=N sbatch --export=ALL,FOLD=N slurm/eval_fold_checkpoint.sh`
(commit c31dbd5) predicts the fold's validation cases from checkpoint_best with
probabilities, then runs both tools; output in `fold_N/eval_checkpoint_best_<date>/`
(metrics/report.txt, decode.csv). One is queued for fold 2 with --begin=now+30h from
2026-09-08 03:45 EDT (starts ~epoch 110). imagesTr symlinks point at /data/hf_export,
the prep container's bind of ~/data/CTSpinoPelvic1K; the eval job binds the same.

**Evaluate** (any time, on checkpoint_best or the final validation export):
`tools/eval_oneshot.py` (rib-free count by transitional status, rib confusion, rare-class
emission) and `tools/decode_sequence.py` (monotone decode -> posterior over the rib-free
count and the A/B/C readings; self-test on labels 4/4). Results land in
`results/Dataset810_.../fold_N/validation`. Fill NextPaper/AR/neurips_2026.tex
sec. sec:oneshot-results (one PENDING block) and deck slides 13/14.

**Why:** Greg wants positive results on segmentation and on TLTV/LSTV anatomy for CNS; the
label-based six-lumbar readings (scripts/six_lumbar_readings.py, shift_hypothesis_test.py)
are the interim result (11 true L6, 4 lumbarized S1, 1 aplastic-rib T12, 2 both-ends).
**How to apply:** `squeue -u go2432`, fold logs in `logs/spine_train_f*`, epoch lines in
`results/.../fold_N/training_log_*.txt`. See [[grid-access]], [[scheme-bone-hardware-only]].

**2026-09-09 post-mortem.** All four Dataset810 NFS folds died (exit 1, epochs 46-60): batchgenerators
'background workers no longer alive' <- FileNotFoundError on /workspace/tmp/pymp-*/listener-* : the
container TMPDIR was $PROJECT_ROOT/tmp on NFS and the multiprocessing sockets vanished. The staged
fold 4 (node-local, STAGE_LOCAL=1) survived and ran ~950 s/epoch vs 1150-1300 on NFS. The fullribs prep
(40165202) hit its 8 h limit inside preprocessing (disc-space derivation made conversion ~4 h), which
made the whole dependency chain DependencyNeverSatisfied; the switch script never fired. Fixes
(commit on L6_Class 2026-09-09): fold jobs use /tmp/<user>_job_<id>_f<fold>_tmp as TMPDIR, STAGE_LOCAL=auto
(stage if /tmp has >= 1300 GB free), resubmit-to-resume on non-zero exit (RETRY up to 6), and
slurm/launch_fullribs_chain.sh (reshape + unpack + 5 folds + patch ablation behind a prep). Prep
resubmitted as 40179764 with --time=20:00:00 (convert skipped: dataset.json present). Benchmark
jobs released. gt decode (bench_score 40164956) TIMEOUT at 6 h: give score.sh 12 h or speed the
erosion split. VinDr download TIMEOUT at 24 h/20 GB, resumed as 40179761 (wget -c).
