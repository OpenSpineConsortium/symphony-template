---
name: panel-checks-run
description: How to run symphony-app's panel suites and mutants correctly from a cloud session, and what fails if not
metadata:
  type: project
  modified: 2026-10-20T06:30:26.013Z
---

Pull symphony-app to origin/main before every run of signin/panel-checks: a stale checkout failed 41 checks against site #98/#99 (Folders, Explore rebuilt) that pass on main (2026-10-20). Link Playwright with `ln -sfn /opt/node22/lib/node_modules/playwright e2e2/node_modules/playwright`; run the ten suites in parallel with run-suite.sh, each its own PORT and SITE=<checkout>; about 10 minutes. run-mutants.sh (590 mutants, serial, needs a server on 8077) takes about 2 hours; on site master 751fcfb k40_box_out_of_sight (K24) survives and m7_no404 (E5) is stale, both pre-existing.

**Why:** a red run from a stale checkout looks like a real regression.
**How to apply:** `git -C /home/user/symphony-app pull --ff-only origin main` first; built site pages conflict on every merge (stamps): take master's, rebuild with tools/build_site.py.
