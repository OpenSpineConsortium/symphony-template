# A failed fetch's reason is read on the grid, not through the gate

Source: the thread "Owner dataset paperwork", 2026-10-23. The measurements are the two answers of the gate word status sent that day through .github/workflows/grid-accounts.yml (job schwingnet-status), kept on this repository's branch `grid` as logs/job-schwingnet-status.json at commits 01360ac (00:35 UTC) and 75209b4 (01:04 UTC). No Claude Doc or artifact.

## The question

The handoff of 2026-10-22 (spine-datasets #111, comment 6353787441) called five X-ray fetches running, PadChest 40711923, NLST 40711959, the Kaggle fracture set 40712010, ReXGradient 40712197 and CheXpert Plus 40722124, and asked that each claim be marked ready once its fetch landed; BIMCV COVID-19+ was to be fetched once SchwingNet #139 merged. The thread's job was to check them with the status word and report. What it found is a fact about the gate worth keeping: of a fetch that failed, the status word says that it failed and when, and nothing of why.

## What the status word showed

The two answers agree; between them only the two running jobs moved, the VinDr-PCXR fetch and the data platform's VSDFullBody fetch 40697705 (105 GB to 115 GB). At 01:04 UTC:

| job | what | state | elapsed | note |
| --- | --- | --- | --- | --- |
| 40704982 | xr_fetch vindr_pcxr | RUNNING | 9 h 25 min | 88 files, 327 MB; every job the fetch word sent later waits afterany on it |
| 40711923 | xr_fetch padchest | FAILED | 2 min 26 s | fetching at 17:40:20Z, failed at 17:42:39Z on 2026-10-22; 117 of its last 400 lines withheld |
| 40711925 | xr_bank padchest | FAILED | 2 s | nothing to bank |
| 40711927 | xr_catalog padchest | PENDING | | waits on 40704982 |
| 40711959 | dp_idc_nlst | PENDING | | waits on 40704982 and 40711923 |
| 40712010 | xr_fetch kaggle_fracture_multiregion | COMPLETED | 5 min 31 s | about 0.48 GB, unpacked |
| 40712012 | xr_bank kaggle_fracture_multiregion | FAILED | 1 s | the recipe has four fields to confirm |
| 40712014 | xr_catalog kaggle_fracture_multiregion | PENDING | | waits on 40704982 |
| 40712197 | dp_hf_rexgradient_160k | PENDING | | waits on 40704982 and 40712010 |
| 40722124 | dp_chexpert_plus | PENDING | | waits on 40704982 |
| 40731142 | dp_zenodo_magic_ct | PENDING | | sent alone by the fetch word; waits on 40704982 |
| 40732922 | xr_fetch bimcv_covid19 | FAILED | 9 s | sent at 00:10 UTC after SchwingNet #139 merged; its log not shown |
| 40732924 | xr_bank bimcv_covid19 | COMPLETED | 3 s | nothing to bank |
| 40732926 | xr_catalog bimcv_covid19 | PENDING | | waits on 40704982 |

So nothing landed, and no claim could be marked ready. Two fetches failed, one fetch landed but its bank refused, and everything else the fetch word sent, the nine gated or owner-approved sources it sends one job each (NLST, ReXGradient, CheXpert Plus, MAGIC-CT, CADS, OL3I, FluoroSAM, IPCAI 2025 and FluoroSeg), waits afterany on a VinDr-PCXR fetch that has moved 327 MB in nine and a half hours, since the fetch word makes each job wait on every live X-ray fetch. The data platform chain that the start word queued (40697693 to 40697707) runs on its own, each job after the one before, with the VSDFullBody fetch 40697705 running. The volume held 9,605 GB of a 21,991 GB quota.

## Why the reason is not in the answer

Three rules of SchwingNet's grid/gate.sh, each there on purpose (SchwingNet issue #80), keep a failed fetch's reason out of the status word:

- A fetch job can print DICOM header values, person keys and a sign-in, so status shows of its log only the line shapes grid/log-shapes.awk keeps: a Python traceback's frames, an exception line with its message only for the types whose message names types and attributes alone, the stages' start and _RC= lines, Slurm's errors by their phrase, wget's and curl's status lines, the stages' section headers and the `<id>: <status> at <time>` lines. Every other line is counted and withheld. tools/fetch_sources.py reports a failed entry as `<id>: failed at <time>, record <path>` and puts the reason in the record and the stage report, in a line that holds a path or a URL, so the reason is withheld every time, by the rule that keeps a share link or a patient's key off the public side.
- status shows the logs of six failed jobs at most, the newest of each thing the gate makes. The BIMCV fetch was the seventh, so its tail was not shown at all ("1 more failed jobs not shown").
- status is cut at 400 lines and 64 KiB. With 140 groups in the sample index and 170 jobs in sacct's list, the cut fell inside the latency probe's section, before the stage reports, so grid/logs/01-fetch-STAGE-REPORT.md, whose failed line names the reason (shaped, a quoting reason withheld), was not in the answer either.

The gate has no word that shows one job's log, and a cloud session reaches neither the grid nor, for the Kaggle set, kaggle.com, which answers its proxy 403. So the reason is read on the grid alone, in the portal's shell or by a session there:

    hpcworker job log --project schwingnet 40711923
    hpcworker job log --project schwingnet 40732922

or the stage report grid/logs/01-fetch-STAGE-REPORT.md in the gate's clone of SchwingNet. Two of the three failures still say something from here: the BIMCV fetch ended in nine seconds, before any transfer, so its listing step is the first thing to read; and the Kaggle bank's refusal is the recipe's own, since grid/banks/kaggle_fracture_multiregion.json carries four fields "to confirm" (the lumbar spine folder's glob, jpg or png, the person regex, whether frontal and lateral are mixed) and tools/bank.py refuses a recipe with one by design. The PadChest failure, 2 min 19 s between fetching and failed, says nothing of itself; the nextcloud route's listing has a 120 s timeout, so a listing that never answered fits, and so does a transfer that began and was refused.

## What was done and what waits

- The real states are on the claim records and tasks: spine-datasets #12 (PadChest, claude/12 388ed47, back to granted, fetch pending), #111 (BIMCV COVID-19+, claude/111 3b0801a, the same) and #24 (the Kaggle fracture set, claude/24 f47b844, fetching, the bank refused). Each names the command that reads its log.
- The Kaggle recipe is SchwingNet #142, a task for a session on the grid, since only a listing of raw/ settles the four fields.
- No fetch was sent again: a resend is a grid job and waits on the owner's word and count. Nothing was fixed in SchwingNet, since nothing read says what to fix.
- Not asked for, but worth a thought for the gate: a word that shows one named job's log through the same shapes, or status printing the fetch stage report before sacct's list, would let a session read why a fetch failed without the owner's hands. The shapes would still withhold a line that quotes a path, so the fetch tool would have to print the kind of refusal (a timeout, an HTTP status, a refused listing) on a line of its own, as its PhysioNet route already does with masked_login and physionet_why.

The owner's own steps are unchanged and listed in owner-paperwork-sitting.md: the NIA Aging Research Biobank request for the MrOS and SOF images, the BRAX data use agreement, the MAGIC-CT application, the RSPECT rules on Kaggle and the RATIC link that expires on 2026-10-28.
