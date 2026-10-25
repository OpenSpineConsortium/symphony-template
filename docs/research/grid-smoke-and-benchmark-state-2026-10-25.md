# Grid state at 19:42 UTC on 2026-10-25: the five smoke jobs and the benchmark fetches

Source: the thread "Report grid smoke jobs and fetches" in the claude.ai project "symphony_3", 2026-10-25. The grid was read once, with the status word (grid-accounts.yml, action job, job schwingnet-status, run 230 at 19:42:03 UTC, request smoke-status-1940); the answer is logs/job-schwingnet-status.json on the branch grid at commit e514e7a, stamped 19:42:25 UTC. No other grid word was sent. SchwingNet's numbers and methods stay in SchwingNet; this page carries job states and counts only, as the handoff does.

## Why this read was taken

Section 0 of handoff-2026-10-25.md said the five smoke jobs sent between 13:15 and 13:23 UTC had not been read since dispatch. The branch grid already held a status readout of 14:03:16 UTC (grid-accounts.yml run 227, taken by another thread), whose sacct table listed all five in their final states; the owner asked for one more read, so the word was sent once, and the 19:42 readout shows each of the five unchanged. Between the two reads no job of SchwingNet's started or ended on the grid: the sacct table still ends at 40781628.

## The five smoke jobs

SchwingNet at commit fc027a6, sent within the owner's count of 3 GPU and 3 CPU jobs.

| Job | What | State | Elapsed | Node |
| --- | --- | --- | --- | --- |
| 40781593 | sweep A, the synthetic smoke plan (GPU) | COMPLETED, exit 0 | 20:16 | voh3 |
| 40781617 | sweep B, the real smoke plan (GPU) | COMPLETED, exit 0 | 12:17 | voh3 |
| 40781621 | bank vindr_spinexr (CPU) | FAILED, exit 1 | 20:29 | mdt46 |
| 40781623 | catalog, queued behind the bank (CPU) | CANCELLED before it started | 00:00 | none |
| 40781628 | sweep C, the two_source smoke plan, queued behind the catalog (GPU) | CANCELLED before it started | 00:00 | none |

What the readout says of each:

- Sweep A, synthetic: 27 rows, 23 ran, 4 refused, 0 not applicable, 0 failed, 0 to come, and every row did what the check predicted. The synthetic catalog was built in the job (version 1, split check passed); the launcher exited 0 and Metaflow reports the run successful. Its state was last updated at 13:45:47 UTC.
- Sweep B, real: 27 rows, 10 ran, 12 refused, 5 not applicable, 0 failed, 0 to come, every row as the check predicted, on catalog version 7 with the split check passed; the launcher exited 0. Updated at 13:58:08 UTC.
- The bank: the job ran for 20 minutes, so the bank itself was written, and then the stage 2 report says "vindr_spinexr: ingest refused". The reason is withheld from the readout because that line can quote a value (grid_accounts.py's scrubbing, grid-readout-limits.md); it is the last line the ingest tool printed, kept in the job's log and the stage 2 report on the grid, and nothing read here says what it was.
- The catalog and sweep C waited on the bank and on the catalog in turn, and Slurm cancelled both when the bank failed; neither took a node.

Of the owner's count, 2 GPU jobs and 1 CPU job ran; 1 GPU job and 1 CPU job were submitted and never started; 1 CPU job was never submitted. Whether a job cancelled before it started spends the count is the owner's to say. No resend was made.

## The benchmark fetches and jobs

The three fetches of the public-benchmark thread (SchwingNet's docs/checkpoints/2026-10-25-public-benchmark/HANDOFF.md) completed, and their inputs are in place on the grid:

| Job | What | State | Elapsed | Node |
| --- | --- | --- | --- | --- |
| 40780681 | dp_hf_flexray_weights | COMPLETED, exit 0 | 02:31 | mdt4 |
| 40780691 | dp_hf_xvr_data | COMPLETED, exit 0 | 06:32 | mdt18 |
| 40780696 | dp_hf_xvr_models | COMPLETED, exit 0 | 06:57 | zfh1 |

The three benchmark jobs stand as that handoff left them: 40781570 bench_flexray_carmlspine COMPLETED in 04:27; 40781578 bench_flexray_deepfluoro FAILED after 9 seconds, the label reader that SchwingNet #314 fixes (merged at 14:56 UTC); 40781587 bench_xvr_deepfluoro FAILED after 04:14, the compile step that SchwingNet #387 addresses (merged at 15:28 UTC). No bench job has run since, so the two reruns the owner approved, one of each, are still unsent. This status call moved the gate's SchwingNet checkout from fc027a6 to f1dcf3c, since the gate pulls main on a status word, so both fixes are in the code a bench word would now run.

## The grid itself

Nothing of SchwingNet's is live: no entry in the sacct table is running or pending, and the readout counts 0 running fetches owing 0 GB. The lab volume holds 17,573.95 GB of its 21,990.23 GB quota (79.92 percent), which leaves 4,416.28 GB of room for a fetch that lands whole or not at all; the quota two levels above the volume leaves 26,406.51 GB. The data root lists 14,520 GB across its sets and the shared datasets 140 GB.

## What follows, none of it started here

- The smoke results are recorded in SchwingNet, under its issue #268, from the state folders on the grid, by the thread that carries the workflow-state handoff on.
- The ingest refusal's reason is read from the job's log on the grid before any resend of the bank; a resend is a grid job and waits for the owner's word and count.
- The two approved benchmark reruns, FleXray on DeepFluoro and xvr on DeepFluoro, are the public-benchmark thread's to send, one word each, once; they need no further approval but were not sent from here.
