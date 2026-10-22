---
name: dataset-promoter
description: spine-datasets' path from a collaborator's dataset PR to the read-only shared grid tree: required-check review plus a promoter Slurm chain under greg's grid account; collaborators never get write ACLs
metadata:
  type: project
  modified: 2026-10-21T16:41:16.904Z
---

Built 2026-10-21 (thread "Automated dataset PR review", spine-datasets #100, PR #101 merged as cc49222; research note symphony-template docs/research/trusted-dataset-promotion.md, #335).

- Collaborator PR = record at status `fetching` + manifests/<id>.json (files with https url, bytes, sha256 or source md5). `python3 tools/dataset_review.py manifest <id> --mendeley X --version N` (or `--zenodo N`) writes it from the source API.
- tools/dataset_review.py runs in the required check: FAILs banned confidentiality words in added record/manifest/letter lines and PR title/body, history edits, committed data files, tokens, invalid manifests, promoter-code/budget changes in a PR greg did not open, promote/<id> branches touching more than their record.
- tools/promote.py + grid/promote.sh: singleton Slurm chain on reqp as go2432, folder /rs/rs_grp_oschome/go2432/spine-datasets-promoter; every 10 min promotes manifests merged by greg (never from promote/ branches), X-ray first, 100 GB budget (grid/promote.json, owner-only), 1 TB reserve, installs 0444/0555 + PROMOTED.json, opens promote/<id> record PR with auto-merge pinned to its commit. Self-updates code only from greg's own PRs with no other account's commits.

**Why:** Ashley's job 40689730 (Fraiwan #31) failed because hy9698 can't write shared/; greg wanted an automated review and an intermediary instead of ACLs.
**How to apply:** greg started the chain once (job 40696334, 2026-10-21 19:36 at cc49222) and said never to hand him grid commands again (19:37). Start, status and stop are to go through fixed Beethoven gate words promoter-start, promoter-status and promoter-stop, sent via symphony-template grid-accounts.yml and owned by the "Beethoven grid node wait" thread, pending greg's yes. Never give greg a grid shell line. Never tell collaborators to setfacl. [[spine-datasets-repository]]
