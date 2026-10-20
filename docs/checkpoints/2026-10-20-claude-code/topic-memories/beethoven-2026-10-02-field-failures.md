---
name: beethoven-2026-10-02-field-failures
description: "What actually failed in Beethoven 12.0.0's first real use (2026-10-02 evening) and what was measured on the grid: dead run records never age out on the direct way; VPN-route sign-in sittings die 5 min after the last keystroke; reqp/requeue preempts workers; group oschome is not the access list"
metadata:
  node_type: memory
  type: project
  originSessionId: 0599380b-0d32-4e19-b5be-65bdd1017566
  modified: 2026-10-03T02:07:43.188Z
---

Measured 2026-10-02 (Greg go2432 on the direct way, Ashley hy9698 on the VPN route), all grid-side
paths proven healthy by hand (connect, the gate's connect, a first-time sitting under a scratch
HPCW_HOME, the Windows bridge with two concurrent connections):

1. **"Connecting to Claude..." forever, no link (direct way).** Not a connect in flight. pollRunDirect
   stamps a run record with the READ time as status_mtime, so a dead run (Greg's worker preempted at
   20:42 whose chained successor had been cancelled) never goes stale; the journey's 'starting' moment
   draws that phase and has no Connect button. The gate's caps file and `last -F` proved no connect
   was ever sent after the key enrolment at 20:43:40. FIXED in Beethoven 13.0.0 + framework 13 (commit e11ae27, 2026-10-03; framework 13 published to the grid; the extension ages out a run it never saw alive and the framework's status checks a preempted job and its successor in one scheduler call). Follow-ups in docs/V12_STATUS.md.
2. **VPN-route Claude sign-in sittings die at ~4 min 20 s after the job starts** (~5 min after the
   student's last keystroke), four times for hy9698 (jobs 40552222/37/39/41, 40552343/46, exit 3).
   The sitting reaches AUTH-URL within a minute; the code budget is 10 min; the extension has no
   timer near that. The relay prints "HPCW-LOGIN: still waiting" every 20 s and the extension sends
   `{}` frames every 20 s, and neither counts: OnDemand's shell idle sweep (OOD_SHELL_INACTIVE_TIMEOUT_MS,
   300 s) evidently resets on real client input only. Unfixed; a terminal sign-in
   (`hpcworker claude login` in the OnDemand shell) worked for hy9698 at 21:22 and her worker ran.
3. **reqp with `--qos=requeue` preempts running workers** (status.json "preempted", the chain
   successor then waits); secp/secondary (priority 200, 90-day MaxWall, 45 idle nodes that night)
   is where workers should live. Profile change still pending (Greg's call).
5. **"Connecting to Claude..." for a HEALTHY online worker (2026-10-03 07:50).** The worker resumed
   its earlier Remote Control session; in that mode Claude Code prints `https://claude.ai/code/session_<id>`
   instead of `claude.ai/code?environment=env_...`, the parser knew only the environment form, so
   status.json went online with no link and the panel mapped that to "connecting". Also found: the
   framework's sed class `[ -\/]` ranged to 0x5C, so a CSI ending in a capital letter (ESC[K) ate the
   next letter, the h of https included. Both fixed in 14.0.0 + framework 14 (2f90319, published).
   A worker started under an older framework keeps that code until restarted: Stop, then Connect.
4. **Group oschome is C&IT's (two members).** Approved students reach the shared tree through named
   ACL entries on the volume root; see [[grid-access-list-gate]].

**Why:** every one of these produced a plausible panel state ("in line for a computer", "Connecting
to Claude...", "the grid didn't accept the code") with nothing wrong on the grid. **How to apply:**
when the panel hangs, read `sacct -u <id> -S <today>`, the run's status.json, the gate's caps file
and `last -F <id>` before touching code; the grid tells the truth and the panel may not. Related:
[[ashley-bridge-project]], [[grid-ssh-second-factor]].
