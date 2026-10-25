# Handoff of 2026-10-24 at 06:20 UTC, thread "Paired CT and X-ray datasets"

Source: the thread "Paired CT and X-ray datasets", written because the owner asked every thread at 06:03 and 06:14 UTC to stop, checkpoint and push. A session that picks this thread up reads this page, then the board. No secret, token or e-mail is written here.

## Where this thread stands

- Its goal, the owner's rule that every dataset selected for storage knows its exact size and is refused whole when it would overflow, is done: SchwingNet #191 (merged 2026-10-24 02:16 UTC as 7a475c0, issue #190 closed by hand) counts every quota on the lab volume's path, and the status word of 02:17 UTC (request room-after-191) read Used 17,107.21 GB and Room 4,883.02 GB, the volume's own 20 TiB quota binding, the group's 40 TiB leaving 26,873 GB.
- Dataset finalization was told the room is readable and that the RSPECT unpack (about 980 GB) fits. That thread sent the one approved unpack (job 40754822, symphony-template #441's handoff); this thread sent nothing to the grid.
- Merged and pushed: SchwingNet #191; symphony-template #436 (the #191 section of docs/research/lab-volume-room.md). This page's pull request adds docs/research/lab-volume-room-tests/, the harnesses that were only in the cloud session. Every clone this thread used was clean, with nothing unpushed, at 06:15 UTC.
- The research is docs/research/lab-volume-room.md; its section "Handoff, 2026-10-23 18:10 UTC" is stale, and its last section, "#191 merged", is current.

## What is left, each waiting on the owner's word

1. A probe on a compute node, to read whether its CephFS mount has the same root as the login node's (lab-volume-room.md, finding 4 of #191). Harmless while the volume's own quota binds, by about 22 TB. A grid job, so it needs the owner's word and count.
2. The automatic segmentation pass: the owner's word and count, the suggestion being C-ArmLSpine's 149 cases.
3. LUMOS: whether its non-commercial licence is acceptable, then the fetch's word and count (46.4 GB, which fits the room).
4. The items of sections 7 and 8 of the paired annotation plan (paired-ct-xray-annotation-plan.md): when the masks are corrected, LUMOS's 280 CTs after spine-datasets #207, and which cases are read before 2 November.

Before any resend to the grid, read the status word (schwingnet-status through grid-accounts.yml) first, as the owner's rule says.
