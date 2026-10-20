---
name: guided-acquisition-loop
description: "The closed acquisition loop (commanded displacement + digital fiducial) -- where it lives, how to resume it, and what must not be quoted"
metadata: 
  node_type: memory
  type: project
  originSessionId: e44eca96-f48c-494d-ba1f-7dae68bdf06d
  modified: 2026-09-19T02:23:46.111Z
---

Built 2026-09-18 to make patent aspects A (commanded displacement) and E (digital fiducial) real before
filing a provisional. **Start at `docs/GUIDED_ACQUISITION.md`, which opens with a status block**, then
`python tools/pipeline_state.py` (stages `guided_calibrate`, `guided_validate`).

Code: `tools/acquisition.py` (engine, orientation, `plan_run`, `FiducialBoard`), `tools/validate_guided.py`
(closed-loop harness, three arms), `tools/guided_console.py` (one image in, one instruction out),
`tests/test_acquisition.py` (phantom, all passing), `slurm/guided_validate.sh` (calibrate then five arms;
each arm skips itself if its `guided.json` exists, so resubmitting is always safe).

**Grid job 40376577** was live at session end; read `~/model_night/logs/guided_40376577.out`.
**Nothing from jobs 40375024 / 63 / 64 / 66 may be quoted.** 40375066 did produce the first sound tau on
this corpus -- 0.033, from 59 correctly-paired links -- but its arms inherited two faults.

**CHECK THE CONTROL BEFORE READING ANY ARM.** The `frame` arm must land near sweep_map's published ~85% at
three vertebrae on this corpus. It is the only quantity in the harness whose value is known independently.
For two runs it read 31% and I read the other arms anyway; it was a raw per-box argmax where sweep_map means
`anchor_decode`. If `frame` is far from 85%, the harness is still wrong and nothing else counts.

Measured where: naming/overlap are on 801 renders; the acquisition-loop numbers (geometry recovered to
1.2 mm, marker assertions) are **phantom only** until `guided.json` exists. Never timed at all: linking,
composition, registration -- so no latency claim. `docs/provisional/SPECIFICATION.md` (note on reduction to
practice) and `docs/INVENTION_DISCLOSURE.md` sec. 8 both carry that split and are what gets updated when the
corpus numbers land. If the numbers are bad, narrow the claims rather than requoting the phantom.

Related: [[commercialization-stance]], [[fluorocap-repo-private]], [[sweep-map-replaces-registration]],
[[level-service-serving]], [[bash-heredoc-backslashes]], [[fluorocap-pipeline-resume]].
