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

## Built

- Rank 1, 2026-10-21: only lists share a concurrency group in grid-accounts.yml; every other action
  runs in a group of its own, scripts/grid-accounts.sh asks a busy gate again up to eight times after
  the seconds it names, and each run also writes its answer to answers/<request>.json on the branch
  grid (the newest 50 of the last day), so a panel whose run another overtook on accounts.json still
  finds its own. The panel itself sends one press at a time per page, so a burst was lost only across
  pages or people; it reads answers/ once the site's change lands.
- Rank 2, 2026-10-21, on this side alone: worker-start takes a count, 1 to 8, and starts NAME-1 to
  NAME-N one call after another in one run, each waiting out the gate's floor, so one press starts
  several workers with nothing changed on the grid; a word that starts many in one call, which would
  also drop the minute between them, waits for a framework release and the lab lead's pull.
- Rank 10, 2026-10-21: the Claude step in workers.yml has a deadline of its own, 75 minutes inside
  the job's 90, and a run it cuts off, or one cancelled or failed, reaches scripts/keep-unpushed.sh,
  which commits what the worker left and pushes it to the worker's own claim branch, never forced,
  never on another worker's claim or a branch that is no claim, and never with a file that looks like
  a secret; the push keeps the claim alive and the next run carries the work on.
- Ranks 4 and 5, 2026-10-21, in part: the Grid tab flags a worker the grid has not heard from in 15
  minutes, counted from the list's own age, and Beethoven's Connect press now says what it saw and
  the last line the grid printed (beethoven-extension#22). The scheduled list every 15 minutes is
  not built: each list spends a gate call, and a press already lists; it waits until the flag
  shows a need. Splitting the gate setup into a pull step waits for the next failed press's log.
- Rank 7, 2026-10-21: each account's tile counts the workers on it, and the start box says when a
  new worker would share an account's five-hour window with another; it warns and never refuses.
  Picking the account by its use, as tools/pool.py picks a cloud slot, is not built.

## Deferred, and why

- Rank 3, the timed push from grid workers: a grid worker is an interactive Claude session that
  pushes as it works, and an autonomous job on the grid follows docs/agents/routines/worker.md,
  which pushes each step; a timer in the job template would commit in a workspace a person may be
  typing in. Revisit if the board releases a grid worker's claim it still meant to hold.
- Rank 6, the multi-partition first-to-win start: Slurm takes --partition=a,b only where each
  partition accepts the same QoS, and Wayne State's secp and reqp take different ones; two jobs
  with a cancel of the loser need a measurement on the grid of how long each queue waits first.
- Rank 8, an expiry on the gate key: OpenSSH takes expiry-time in authorized_keys from 7.7, and the
  grid's login node runs CentOS 7, whose OpenSSH is 7.4, so the option would lock the gate out. An
  ssh certificate or a scheduled rotation needs the lab lead's grid shell and is the next step.
- Rank 9, one Workers view: medium work in the panel, not started.
