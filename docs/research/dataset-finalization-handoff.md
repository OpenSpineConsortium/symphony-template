# Handoff: the thread "Dataset finalization"

Source: the thread "Dataset finalization". First written 2026-10-23 at 18:15 UTC, when the owner's weekly limit reached 92 percent. Rewritten 2026-10-24 at 06:05 UTC, when the owner asked every thread to stop and push. Nothing of this thread lives only in its cloud session: every change is merged, and the findings are in exploring-fetched-sets.md beside this file.

## Where it stopped

RSPECT (rsna_rspect_pe) is held on the grid only as its 533.7 GB Kaggle zip, at /rs/rs_grp_oschome/go2432/data/rsna_rspect_pe/raw. On 2026-10-23 at 18:16 UTC the dropzip job 40751186 kept the zip, because none of its 1,937,450 members is unpacked on disk. On 2026-10-23 at 19:53 UTC the owner chose "Unpack once room is readable". His word covers exactly one unpack job and one dropzip job, and only after the room check passes.

The gate word `unpack <id>` was built for this and is live:

- SchwingNet #184: tools/unpack.py, grid/unpack.sbatch and the word in grid/gate.sh, held to the size rule. Merged 2026-10-23 at 22:16 UTC.
- hpcworker #41: the gate admits `schwingnet unpack <id>`. Merged, and the grid's clone took it with the `update` word at 22:11 UTC (6ef8731).
- symphony-template #433: grid-accounts.yml takes `schwingnet-unpack-<id>`. Merged.

Another thread's SchwingNet #181 and #191 made the size rule count every quota on the path. The status word at 02:17 UTC on 2026-10-24 read Room = 4,883 GB.

The one approved unpack was sent on 2026-10-24 at 02:18 UTC (request unpack-rspect-1). The grid answered "unpack: job 40754822" at commit 7a475c0. The job unpacks about 980 GB, with a wall time of up to one day. At 06:05 UTC it had not been checked again.

## The steps left

1. Check job 40754822 with the status word (job `schwingnet-status` in grid-accounts.yml). Never send `schwingnet-unpack-rsna_rspect_pe` while that job is live, and never queue a second unpack.
2. Once the job has ended, send `schwingnet-unpack-rsna_rspect_pe` once. Since the report exists, this send queues nothing: it prints logs/UNPACK-rsna_rspect_pe.md and removes it. Expect "still to land: 0.0 GB" and about 980 GB written. If it says "refused for space" or any GB still to land, report that to the owner and stop.
3. If nothing is left to land, send `schwingnet-dropzip-rsna_rspect_pe` once (approved), and later send it again to print its report. Expect "deleted" and about 534 GB freed. A "kept" line means nothing was deleted; report it and stop.
4. In spine-datasets, by pull request, update datasets/rsna_rspect.json:
   - a history entry for the unpack job and the dropzip job, with their ids and sizes;
   - remove the obstacle about the zip;
   - set `next` to "the census counts the CT volumes".

   Run bash scripts/check.sh first. The branch is not a claim branch, since the record's issue #88 is closed.
5. Update this handoff and the team memory rspect-unpack-approved.

## A permission quirk

After the unpack send, this session's own permission check refused even reading the grid branch (`git fetch origin +refs/heads/grid:...`, then `git show origin/grid:logs/job-<job>.json`). The owner pasted the answer by hand. A fresh thread may read it, or may ask the owner for the file https://github.com/OpenSpineConsortium/symphony-template/blob/grid/logs/job-schwingnet-unpack-rsna_rspect_pe.json.

## What this thread does not own

- #86/#159 and #111/#147 belong to the thread "Handoff merges and grid checks".
- The size rule belongs to the thread that made SchwingNet #173, #181 and #191.
- VinDr-PCXR is tabled, and its job 40704982 is left alone.
- No fetch is sent from this thread.
