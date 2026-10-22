---
name: stale-branch-statistics
description: Where the stale-branch (curse of coordination) statistics live and when the up-to-date rule went off, 2026-10-20
metadata:
  type: project
  modified: 2026-10-21T00:28:14.358Z
---

symphony-template tools/staleness.py + .github/workflows/staleness.yml (template #302, #306) record per-PR catch-ups of main, redone check runs and green-but-stale wall-clock on the branch `staleness` after every merge; findings in docs/research/stale-branch-failures.md. Retroactive (to 2026-10-20): template 50% of 256 merged PRs took main in, 34% stale after green (79 h), 35% of check runs redone; rises 8% alone to 93% with 6+ PRs beside it. Only 8 of 256 came from claim branches (threads claim nothing), so history is the protocol-off arm.

"Require branches to be up to date" went off on 2026-10-20 (greg's ask): SchwingNet ~21:08 UTC, coordbench 21:17:06, symphony-start 21:17:08, symphony-template 21:31:55, symphony-protocol 22:26:34; symphony-app/marketplace already off. Overlap check live on template 23:04:45 (#315). Clean "after" for the template starts at the 0.6.1 sync, 00:25 UTC 2026-10-21 (#317); copies start when their weekly protocol workflow brings 0.6.1.

**Why:** greg wants this as the first empirical test of Symphony against coordbench's curse of coordination.
**How to apply:** compare before/after at these times; the snapshot's up_to_date_required field dates later switches.
