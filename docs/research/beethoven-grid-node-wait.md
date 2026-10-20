# Beethoven's grid node wait

Source: the thread "Beethoven grid node wait", 2026-10-20, from the owner's message of 22:21 UTC in the
thread "WSU grid files in Folders": why had he waited about five hours for Beethoven to get him a grid
node, with a pasted Show log, and was the multi-partition, first-to-win queue submission ever fixed.
Read on the day: OpenSpineConsortium/hpcworker at a0ac0ed (framework 18) and
OpenSpineConsortium/beethoven-extension at e8ef6f0 (23.0.0). No grid job was run and the worker's own
files on the grid (status.json, rc.log) were not read from the session; what they say is asked of the
owner, through Beethoven's Details sheet.

## What the log says

Show log lists Beethoven's own events and the worker's progress.log oldest first, on the browser's clock
in twelve-hour form with no AM or PM (beethoven-extension extension/src/core/facts.ts, mergeLog). Read
that way, the pasted log is one always-on chain: thirteen times over, "Renewing", "Got a computer" in
the same minute, "Connecting to Claude", and the next "Renewing" 7 h 58 min later, which is the profile's
8 h wall time less the two minutes' warning of --signal=B:TERM@120 (hpcworker framework/profiles/
wayne.json, worker_defaults.hours). The last two lines, "Signed in to the grid as go2432" and "Your grid
account is ready" at 6:20, are Beethoven's own events of 22:20 UTC, the owner opening the panel.

So the grid never made him wait for a node: each link of the chain got its computer at once from its
predecessor. What never happened, in about four days and thirteen jobs, was "Online": Claude Code's
Remote Control started on every node and never printed a link the worker recognised.

## Why nothing said so

- The worker (framework/jobs/worker.sbatch.tpl) had no limit on the wait for a registration. With no
  link it writes state running ("no registration line recognised yet. Last output: ..."), or online
  with no link when Claude Code says Connected, and at the wall time it renews, so the chain spends
  allocation for as long as nobody stops it.
- The panel shows running past three minutes as "Still connecting. This is taking longer than usual."
  with only Show log under it (core/facts.ts SLOW_AFTER_MS, core/steps.ts the starting moment), and an
  online state with no link as "connecting", with no slow and no error at all. Neither ever turns into
  an error or offers a fresh start; Claude Code's last words reach only Details, under rc.log.

## The likely cause, not yet confirmed

The grid's shared Claude Code is 2.1.283 (the profile's claude_bin, docs/WAYNE_STATE_PILOT.md), with
self-update off in the worker (DISABLE_AUTOUPDATER=1). A client that old whose Remote Control registers
no more, or prints its link in a form the parser (lib/adapters/common.sh hpcw_parse_registration, two
forms on claude.ai or claude.com) does not know, gives exactly this log. Which of the two it is, or
something else, is in the rc.log section of Beethoven's Details sheet, asked of the owner on the day.

## The multi-partition, first-to-win submission

Never built. It is greg's ask of 2026-10-04 23:26Z, written up as framework 19's design in
beethoven-extension docs/V19_STATUS.md, section 2.3: measure first with sbatch --test-only over reqp and
secp under each QoS, then either one job over -p reqp,secp or a race of jobs with a candidates line, and
the extension's R1' to follow the winner. The measurement was never run and no code exists in either
repository (no worker_queues, candidates or --race). It would not have helped here, since the wait was
never in the queue.

## What was changed

hpcworker framework 19 (the number the race had been given now goes to this fix; the race, when built,
takes the next): a registration watchdog in the worker job. A job whose Remote Control has printed no
link REGISTER_TIMEOUT_S (600 s by default) after it first started, the clock held while the job waits for
the student's sign-in or consent, starts it once more; the second time it cancels its successor, writes
state error with Claude Code's last line, logs "Couldn't start: ..." in progress.log and leaves, so a
broken registration costs about twenty minutes, not days. Beethoven 23.0.0 already shows state error as
"Your worker couldn't start." with Try again, so the fix reaches the panel with no extension release. A
chain keeps the code it started with, so a chain running now takes the fix only when it is started again.
