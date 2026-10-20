---
name: review-space-repos
description: Exact HF repo ids the distributed-review Space uses (review ledger vs dataset)
metadata: 
  node_type: memory
  type: project
  originSessionId: 1af48852-259d-4e9a-8d35-41c5258bbce6
  modified: 2026-08-06T20:58:36.423Z
---

**The v4 per-task Spaces each have their OWN ledger -- there is no single REVIEW_REPO.** `deploy_v4_spaces.py` builds it as `{org}/CTSpinoPelvic1K-reviews-{slug}`, so the spine Space (`anonymous-mlhc/CTSpinoPelvic1K-review-spine`, task `spine_extend`) reads `anonymous-mlhc/CTSpinoPelvic1K-reviews-spine` -- NOT `-triaged`. Live slugs: `spine`, `ribs`, `nerve`, `ili`, `classfix`, `triaged`. Pointing admin/listing tools at the wrong one returns **0 cases with no error**, which reads as "nothing outstanding" rather than "wrong repo".

Inspect any of them with `python3 -m review_service.admin queue` (added 2026-08-06).

The older single Space `gregoryschwingmdphd/ctspinopelvic1k-review-triaged` uses TWO HF datasets -- don't confuse them:

- **REVIEW_REPO (the case ledger / state)** = `gregoryschwingmdphd/CTSpinoPelvic1K-reviews-triaged` (note the `-triaged` suffix). Holds `cases/`, `reviews/`, submitted labels, on the **main** branch (store.py uses no revision = main). To re-triage, wipe `cases/` HERE, then Restart the Space (it reseeds from the dataset's crops_index on every boot; it only ADDS, never prunes, so a stale `cases/` must be deleted to drop cases).
- **dataset repo (CTs/labels/crops)** = `gregoryschwingmdphd/CTSpinoPelvic1K`, branch **v2**. Holds `crops/crops_index.json` (drives which cases seed), `ct/`, `labels/`.

A near-twin `gregoryschwingmdphd/CTSpinoPelvic1K-reviews` (no `-triaged`) EXISTS but is an empty decoy -- wiping it does nothing.

Gotcha: a plain Space **Restart** can reseed from a cached old `crops_index`; use **Factory reboot** to force a fresh download. See [[commit-directly-to-master]].
