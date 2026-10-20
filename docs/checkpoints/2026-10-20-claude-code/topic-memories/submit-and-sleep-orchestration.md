---
name: submit-and-sleep-orchestration
description: "Greg 2026-09-24 -- never keep agents running/waiting on grid jobs; submit, ESTIMATE the wall time, write job ids + ETA + what-to-collect into the resume checkpoint, then stop until Greg says \"reactivate / check again\"; never repeat finished work"
metadata:
  node_type: memory
  type: feedback
  originSessionId: f1bdbd78-151f-470b-b703-dd9af9b3fecc
  modified: 2026-09-24T19:28:16.890Z
---

Greg (2026-09-24 afternoon): "please don't have all the agents running continuously if that constantly burns
tokens. When you submit a grid job, estimate how long it will take, save its state to the resume checkpoint
file, and sleep the agents until I say to reactivate and check again. Make sure you don't repeat any work and
pick up exactly where you left off."

**Why:** workflow agents polling `squeue` in loops for hours burned his session limit four times in one day
while the grid was doing the real work; every relaunch re-ran agents whose outputs already existed.

**How to apply:**
- A workflow agent SUBMITS grid work and RETURNS: job ids, an ETA (per-item cost x items / parallelism, plus
  queue wait), and the exact files to collect. Never `while squeue ...; do sleep` beyond ~10 min total.
- The coordinator writes those into `docs/RESUME_2026-09-22_PM.md` under a PENDING JOBS table (job, submitted,
  ETA, output path, which step collects it) and ends the turn. No background workflows are left running.
- On "reactivate / check again": ONE collect workflow reads the PENDING table, collects only finished outputs,
  submits only what is missing, updates the table, stops.
- Before any agent works: check the output already exists (cached run result, file on disk, grid job COMPLETED)
  and skip if so. Prompts must name what exists so agents do not rebuild it.
Related: [[resume-2026-09-24]], [[no-jobs-on-login-node]].
