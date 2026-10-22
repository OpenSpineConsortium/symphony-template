---
name: beethoven-worker-never-online
description: greg's grid worker ran 4 days without Remote Control because the grid was signed in as a cancelled Claude account; fixes shipped, multi-account design written
metadata:
  type: project
  modified: 2026-10-21T02:01:45.023Z
---

2026-10-20/21 (thread "Beethoven grid node wait"): greg's "5 hours waiting for a grid node" was never the queue. His always-on chain on reqp ran 13 x 8 h links, each given a node at once; Claude Code printed "Remote Control isn't enabled for this account" every 5 min and the worker retried for 4 days with the panel at "Still connecting". Root cause: the grid's claude_config_dir was signed in as gregoryamdg@gmail.com, an account greg had cancelled.
Shipped: hpcworker framework 19 (#18, registration watchdog) and 20 (#19, merged 2026-10-21 02:07 UTC, that message is fatal: chain ends with state error; reaches the grid's shared copy via the grid CI watcher); beethoven-extension #20 (Stop/Cancel on first-run In line and Starting screens; before, a browser that never saw the worker online had no Stop at all), published via release.yml. Findings: symphony-template docs/research/beethoven-grid-node-wait.md.
Fix for greg: `hpcworker claude login` in the warrior shell with the account he keeps; `claude` is not on the login node, never tell him `claude auth logout` there.
Multi-partition first-to-win queue submission: never built (design only, beethoven-extension docs/V19_STATUS.md 2.3); framework 19/20 took the numbers, the race takes the next.
greg re-signed the grid in on 2026-10-21 ~02:05 UTC with a working account (Claude Code's new OAuth flow completes on Authorize with no pasted code). Design, not built, merged as template #321: docs/research/grid-claude-accounts.md (one Claude Code folder per pool slot on the grid, `hpcworker accounts`, sign-in via Beethoven, Tokens tab the single registry, gate word `account <slot>`, grid jobs pick a slot not a token). Tokens thread owns pool.py; message it before touching pool code. Anthropic AUP forbids hopping accounts to dodge limits; auto-rotation stays optional. [[fine-grained-locking-on]]
