---
name: wandb-tab
description: The control panel's W&B tab (site #133, symphony-app #87, 2026-10-21): how it reads W&B and where the key lives
metadata:
  type: project
  modified: 2026-10-21T20:43:26.990Z
---

The control panel has a W&B tab (after Grid) at /symphony/control/#wandb, live 2026-10-21 20:40 UTC. It reads W&B's GraphQL through the sign-in Worker's POST /wandb/graphql (read-only queries, same origin, 16 KB body / 4 MB answer caps, only a 401 means a refused key). The key is pasted once per browser from wandb.ai/authorize and kept in localStorage `symphony_panel_wandb` under the GitHub login; Forget W&B or Forget the token clears it. Never in a repo or page code. Default project SchwingNet, entity is the key's default (matches SchwingNet tools/wandb_log.py). Browser checks: symphony-app signin/panel-checks/e2e2/wandb.test.mjs + mutants wb01-wb20. Research: symphony-template docs/research/wandb-in-the-control-panel.md (#339).

See [[schwingnet-witness-wandb]], [[panel-design-system]], [[panel-checks-run]].
