---
name: grid-job-handoff-path
description: How a cloud session hands the WSU grid a job (sbatch) with no paste: a one-shot scheduled task into a grid worker's Remote Control environment; blocked until a grid slot is signed in to the project's own Claude account
metadata:
  type: project
  modified: 2026-10-21T16:41:32.237Z
---

Worked out 2026-10-21 (thread "Beethoven grid node wait", for "SchwingNet video demo plan"). Each grid worker started by `hpcworker accounts start` (control panel Grid tab, or grid-accounts.yml worker-start) is a Claude Code Remote Control environment in a Slurm job, with greg's grid account (lab volume, sbatch, pixi, git). A cloud session can run a job there with `create_trigger` (environment_id = the worker's env_ id, create_new_session_on_fire true, run_once_at a minute ahead, prompt = the job).

Blocker as of 2026-10-21 14:00 UTC: the only grid worker (hao1, slot 1) is signed in to greg's Wayne State Claude account; this project's sessions run on gregoryjschwing@gmail.com and `list_environments` shows only that account's environments (his PC bridges). Greg's one step: Grid tab, Sign in another, signed in to the gmail Claude account; then sessions start a worker on that slot themselves (worker-start, name jobs). Firing a scheduled task into a bridge environment is NOT yet tested.

Jobs this path should carry once it works: the SchwingNet grid runs (video demo plan thread), and the spine-datasets promoter chain (`bash ~/promote.sh start <commit>` or `status`, grid/promote.sh, spine-datasets #101; greg starts it by hand until then). [[dataset-promoter]]

UPDATE 2026-10-21 20:10 UTC: greg chose "Yes, build all of it" (decision card)  -  sessions send fixed gate job words for him, no grid pastes: hpcworker #23 (merged) adds `update` (gate clone ff to main), `promoter status|start|stop`, `schwingnet status|pull|xray-chain`; template #338 adds grid-accounts.yml action=job, job=<update|promoter-status|...>; answer on branch grid logs/job-<job>.json. Live only after greg's Beethoven Connect press pulls hpcworker main; that press failed until beethoven-extension #23 (15 s shell-open timer never cleared after typing). New grid jobs = new gate words, never free-form commands. UPDATE 20:43: beethoven-extension #23 merged (store release); hpcworker #24 (e7c1c61) + template #340 make schwingnet words run SchwingNet's own grid/gate.sh (start|status|leaks|v1|latency|stop|fetch <id>; job=schwingnet-<word> or schwingnet-fetch-<id>), clone with gh if missing, ff to main unless grid/logs/HOLD stands; promoter lab root from profile shared_state_dir (--site). Plan for one grid worker per claude.ai project: https://claude.ai/artifact/UjuFBMxLEL8CnifRofU3Vv, awaiting greg's go.

**Why:** greg wants zero manual grid pastes and no cap on grid jobs; grid.yml's runner deliberately has no scheduler or lab volume, and the gate takes fixed words only.
**How to apply:** once a gmail-account worker shows in list_environments, test one harmless job (e.g. `squeue -u go2432`) before handing real ones; never route arbitrary commands through the ssh gate. [[schwingnet-grid-fetch-chain]]
