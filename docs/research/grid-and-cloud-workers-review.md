# Grid and cloud Claude workers: a review against industry practice

Source: the thread "Beethoven grid node wait", 2026-10-21, from the owner's message of 12:03 UTC
asking for a reanalysis of the multi-worker system, a comparison with industry standard and the
places it could improve for continuation and robustness. The Claude Doc with the diagram is
https://claude.ai/artifact/L7nL3xkYzoitmWf4ab8ARN. Read on the day: hpcworker at framework 22
(framework/lib/accounts.sh, framework/jobs/worker.sbatch.tpl, tools/grid_gate.sh), this
repository's grid-accounts.yml, grid-gate.yml, workers.yml and scripts/grid-accounts.sh, and the
branch grid as the list run verify22 of 12:03 UTC wrote it. The industry columns describe each
tool's documented design (Actions Runner Controller, Slurm, Kubernetes controllers and leases,
hosted coding agents, Temporal); none of them was run here.

## The system as it stands

A press in the control panel's Grid tab dispatches grid-accounts.yml, which holds the gate's ssh
key in the environment grid and speaks one fixed word to tools/grid_gate.sh on the grid. The gate
takes a short list of words under a lock, 60 seconds apart for start, login and usage and 3 seconds
for the other accounts words. hpcworker turns `accounts start SLOT NAME` into one sbatch of a
worker kept to that account (account.pin), claiming as grid-NAME; a start by a name already queued
or running submits nothing. The job queues its successor with afterany and continues the same
Remote Control session with --continue for up to seven days. The run lists the workers again and
writes the answer to the branch grid, which the panel reads. Cloud workers are workers.yml runs on
the token pool, cancelled from the Runs tab through the Actions API. Both coordinate by the claim
protocol: the first push of claude/N holds issue N, and the board releases a claim with no push
for 24 hours.

On 2026-10-21 at 12:03 UTC the grid answered with framework 22, a workers array, one worker online
on node hao1 and account 1 on a Max subscription. No second worker has been started, since that
spends allocation.

## Where it stands against usual practice

On par or better: no open port on the grid and no server of ours; no Claude credential leaves the
grid; starts are idempotent by name; git is the durable record of who works on what; cancel exists
on both sides; the successor chain gives continuation of the session across job ends.

Behind: requests can be lost in a burst (below); one worker per press and one press a minute where
a controller or a job array would start many at once; state is known only when someone asks,
where a control loop or heartbeat would notice by itself; the gate's key never expires, where
short-lived credentials are the norm; errors reach the person without their cause.

## Improvements, ranked

1. Lost presses. The concurrency group grid-accounts keeps one running and one pending run, and
   GitHub cancels the older pending run when a newer one arrives, whatever cancel-in-progress
   says. Fix: the panel writes each request as a file on the branch grid and each run carries out
   every request waiting, oldest first.
2. Slow bursts. N starts take about N minutes. Fix: one word that starts a count of workers in one
   call.
3. Claims lost by busy grid workers. Only pushes keep a claim; fix: push the claim branch every 30
   minutes and on the TERM the job already gets 120 seconds before its time ends.
4. Silence between presses. Fix: a scheduled list every 15 minutes (the 3 second floor makes it
   cheap) and a stale flag in the panel.
5. Errors without causes. The Beethoven Connect press said only that the grid stopped answering.
   Fix: show the shell's error with the press, and split the gate setup into a short pull step and
   the rest.
6. Queue waits in one partition while another is free: the multi-partition first-to-win
   submission, designed and never built.
7. Several workers crowding one account's five-hour window: show the count per account, warn
   before a start that crowds one, later pick the account as tools/pool.py picks a cloud slot.
8. The gate key's lifetime: an ssh certificate with an expiry, or a scheduled rotation.
9. One Workers view for grid and cloud workers alike.
10. Cloud workers lose what they did not push at the 90 minute limit: the same timed push as 3.

## Not measured yet

Two or more grid workers at once on real nodes; the time from press to online and the queue wait
per partition; whether --continue keeps a long session whole over several job ends; the cause of
the Beethoven Connect failure, parked until the next failed press gives its debug log.
