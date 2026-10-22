---
name: panel-design-system
description: The control panel's shared --ds-* tokens and card classes (site #121, 2026-10-21); new panel UI must use them
metadata:
  type: project
  modified: 2026-10-21T04:45:55.374Z
---

Since site #121 (merged 2026-10-21, checks symphony-app #75), every control panel tab draws from one design system at the end of assets/css/control.css: tokens `--ds-*` on `.console` (12px card radius, 44px icon tile, surfaces, borders, shadows) and classes `.ds-card`, `.ds-card--press`, `.ds-card--add`, `.ds-icon`, `.ds-ctl`, `.ds-seg`, `.ds-table`, `.ds-note`. A card is the Workers tab's shape, with a 3px inner edge in `--card-accent`. Tasks has seven views (`data-taskview`, kept in localStorage `symphony_panel_tasks_view`); readouts switch view without overwriting the kept one. The Claude mark is an inline SVG `.claudemark` filled #D97757. Research note: symphony-template docs/research/panel-design-system.md (#327).

**Why:** greg (2026-10-21) hated per-tab style variations and asked for one common set of objects shaped like the Workers buttons.

**How to apply:** new tabs or Folders/Explore work use `var(--ds-*, fallback)` and the shared classes rather than their own shapes; chips/add buttons honour `[hidden]`; Folders' head is exempt from the shared head rule. Related: [[panel-checks-run]], [[phone-home-screen]].
