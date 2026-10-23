# Handoff: the thread "Dataset finalization"

Source: the thread "Dataset finalization", 2026-10-23, written at 18:15 UTC when the owner's weekly limit reached 92 percent. Nothing of this thread lives only in its cloud session: every change is pushed and every finding is in exploring-fetched-sets.md beside this file.

## Where it stopped

The owner asked, on 2026-10-23, for RSPECT's 534 GB Kaggle zip to be deleted ("you can delete it"), through GitHub Actions rather than the grid's shell. The zip sits beside the 1,937,450 files the fetch unpacked from it, at /rs/rs_grp_oschome/go2432/data/rsna_rspect_pe/raw; explore proved those files complete (980.24 GB, the competition page's figures).

A new gate word, `dropzip <id>`, does it in one batch job that deletes a zip only when every member sits unpacked beside it at the same size. Three pull requests carry it:

- hpcworker #40, the gate admits `schwingnet dropzip <id>`: merged, and the grid's clone took it by the `update` job word at 18:04 UTC (`update ok ..a6e6fe2a39c3`, framework 28).
- symphony-template #424, grid-accounts.yml takes `schwingnet-dropzip-<id>`: merged.
- SchwingNet #174, the word itself (tools/dropzip.py, grid/dropzip.sbatch, grid/gate.sh): merged at 18:07 UTC.

## What the job found

The zip was kept and nothing was deleted: none of its members is unpacked on disk, so RSPECT is held only as the 533.7 GB zip (exploring-fetched-sets.md, the last section). The spine-datasets record rsna_rspect.json says the files sit unpacked beside the zip; that is wrong and needs correcting by pull request. Unpacking it (about 980 GB) or keeping it zipped is the owner's choice; no job runs without his word.

## The steps as first written, now superseded after step 3

1. Done: SchwingNet #174 merged at 18:07 UTC.
2. Done: the one approved job was sent at 18:16 UTC (request dz-rspect-1) and queued as job 40751186; the grid's SchwingNet pulled to e064e3c first. Do not send the word again while that job is live, or it is refused; never queue a second.
3. Check it with the status word (job `schwingnet-status`) until the job is done, then send the same dropzip word again: it prints logs/DROPZIP-rsna_rspect_pe.md once. Expect "deleted, 534 GB ... all 1,937,450 files" (the zip holds 1,937,450 members; the exact size printed is the zip's own) and "freed" near 534 GB. Any "kept" line means nothing was deleted; report it to the owner and stop.
4. In spine-datasets, by pull request, update datasets/rsna_rspect.json: a history entry that the zip was deleted (the job id and the freed size), the obstacle about the zip removed, and `next` left as "the census counts the CT volumes". Run bash scripts/check.sh first; the record's issue #88 is already closed, so the branch is not a claim branch.
5. Correct the team memory grid-deletions-are-greg-shell: a deletion of a set's own download zip now goes through `dropzip`; anything else is still the owner's shell.

## What this thread does not own

#86/#159 and #111/#147 belong to the thread "Handoff merges and grid checks". The size rule refuses every fetch until another thread's fix lands (SchwingNet #170, #171), so no fetch is resent from here. VinDr-PCXR is tabled and its job 40704982 is left alone.
