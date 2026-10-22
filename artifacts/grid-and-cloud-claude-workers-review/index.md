# Grid and cloud Claude workers: review

Oct 21, 2026 · @Someone

## Summary

The system lets the control panel start, watch, stop and open Claude workers on two kinds of computer. On the Wayne State grid, a press in the Grid tab runs a GitHub workflow, which speaks one fixed word to the grid over a locked-down ssh key; hpcworker turns that word into a Slurm job that runs Claude Code under Remote Control on one of your signed-in accounts. In the cloud, workers.yml runs workers in GitHub Actions on the token pool, and the Runs tab can cancel them. Both kinds coordinate the same way: each worker claims an issue by pushing a branch, so two workers never take the same task.

**State today (read at 12:03 UTC, 21 Oct):** the grid answers with framework 22. It lists one worker, `worker`, online on node hao1, and account 1 (your Wayne State Max account) signed in. The Start and Stop buttons for named workers are live. Nothing has started a second worker yet, since that spends allocation.

**Compared with industry practice,** the design is sound where it counts. No port is open on the grid, no Claude credential leaves it, a start by a name that is already running submits nothing, and git is the durable record of who works on what. It falls short of mature systems in three places: requests can be lost or slowed on the way in, it only finds out a worker's state when someone asks, and it does not say why a failure happened.

**The five changes worth making first:**

1. **Stop losing presses.** GitHub keeps at most one waiting run per concurrency group, so a third quick press of Start replaces the second one, which never runs. Fix: the panel writes each request as a file, and one run carries out every waiting request.
2. **Start several workers in one call.** Each start waits out the gate's one-a-minute floor, so five workers take five minutes or more. Fix: one word that starts a count of workers.
3. **Keep claims alive while a grid worker works.** The board releases a claim after 24 hours with no push, even when a grid worker is busy on it. Fix: the worker pushes its work in progress on a timer and before its job's time runs out.
4. **Check on workers without being asked.** A scheduled list every 15 minutes, plus a stale flag in the panel, turns silent failures into visible ones.
5. **Say why a press failed.** The Beethoven Connect failure showed only "the grid stopped answering"; the real error was in the debug log. Show it, and split the long setup into short steps.

## How it works

&#91;embedded content: grid and cloud workers · from a press to a claimed task\]

A press in the Grid tab runs grid-accounts.yml, which holds the gate's ssh key in the environment `grid` and speaks one fixed word, such as `accounts start 1 alpha`. On the grid, the key can run only the gate script, which accepts a short list of words and refuses a second start within a minute. hpcworker turns the word into one sbatch: a job on a compute node that runs Claude Code under Remote Control on the account the word named, keeps the worker on that account even when the default account changes, and names the worker `grid-alpha` for its claims. Before its time runs out, the job queues its own successor, which continues the same session. The run then lists the workers again and writes the answer to the branch `grid`, which the panel reads (the line on the left).

In the cloud, workers.yml starts each registered worker in GitHub Actions on a token from the pool, and the Runs tab cancels a run through GitHub's API. Both kinds of worker take work the same way: a worker claims issue N by pushing the branch `claude/N` first, and the board releases a claim whose branch has had no push for 24 hours.

## Compared with industry practice

The comparison sets each part of the system beside the tool the industry would usually reach for. It covers GitHub's Actions Runner Controller (self-hosted runners scaled on Kubernetes), plain Slurm (job arrays, requeue, checkpointing), Kubernetes operators (a controller that keeps actual state equal to desired state), hosted coding agents (GitHub's Copilot coding agent, Devin, OpenHands), and durable workflow engines such as Temporal. The industry columns describe each tool's documented design, not a test run here.

| Concern | This system | Usual practice | Verdict |
| --- | --- | --- | --- |
| Launching | A press runs workflow\_dispatch; one ssh word; one sbatch per press | A controller scales workers from a queue (Runner Controller); sbatch --array for many jobs at once | Behind: one worker per press, one press a minute |
| Request intake | GitHub concurrency group, one waiting run | A durable queue that never drops a request | Behind: a burst of presses can lose one |
| Tracking | The panel asks; the answer is written to the branch grid | A control loop compares desired and actual state all the time; squeue and sacct | Behind: state is known only when someone asks |
| Cancel | `accounts stop NAME` (a stop file, then scancel); the Actions cancel API for the cloud | The same, plus a graceful drain | On par |
| Continuation | A successor job queued with afterany; `claude remote-control --continue` within 7 days; the workspace on shared disk | Slurm --requeue with application checkpoints; Temporal replays history; Copilot's agent pushes commits as it works | Mostly on par; progress is not pushed to git while the worker runs |
| Coordination | A claim is the first push of `claude/N`; the board releases claims idle for 24 hours | Leases with renewal (Kubernetes Lease), work queues with acknowledgement | On par, and simpler; but the lease is renewed only by pushes |
| Idempotency | Start by a name that is already running submits nothing | Desired-state controllers are idempotent by design | On par |
| Admission and limits | The gate's floor: 60 seconds between start, login and usage calls; at most 10 Claude runs a day per repository in Actions | Quotas and admission control per user or account | On par for safety, slow for bursts |
| Credentials | A forced-command ssh key that takes fixed words only; no Claude credential leaves the grid | Short-lived credentials: OIDC, ssh certificates with expiry, just-in-time runner tokens | Good on scope; behind on lifetime, since the key never expires |
| Observability | Run logs, the branch grid's history, the Grid and Runs tabs | Heartbeats, metrics, alerts, one dashboard for every worker | Behind: no heartbeat history, no alert, two tabs |
| Errors | A short sentence; details only in a debug log | A structured error with its cause shown where the action was taken | Behind |

**Where this design is better than the usual tools.** It needs no server of its own and no open port on the grid. GitHub never holds a Claude credential, so a leaked workflow log or secret cannot reach your Claude accounts. The record of who did what is ordinary git history that any later session can read. Most hosted agent platforms run on their own vendor's machines, while this runs on the H200s you already have.

## Weak points and improvements

The changes are ranked by how much they help against how much they cost. Effort is a rough size: small is one pull request in one repository, medium is a pull request in each of two or three repositories, large is a new piece. Changes to the grid side raise the framework version and reach the grid through the watcher, or through one pull from the lab lead's clone.

| Rank | Weak point | Fix | Effort | Where |
| --- | --- | --- | --- | --- |
| 1 | Presses lost in a burst: the group `grid-accounts` keeps one running run and one waiting run, and GitHub cancels the older waiting run when a newer one arrives | The panel writes each request as a file on the branch grid; each run carries out every request that is waiting, oldest first, and marks each done | Small | symphony-template, site |
| 2 | Starting N workers takes about N minutes, because every start waits out the gate's 60 second floor | One word, `accounts start SLOT NAME COUNT`, makes COUNT workers in one call (names NAME-1 to NAME-COUNT), still one floor per call | Medium | hpcworker, gate, symphony-template, site |
| 3 | A grid worker that works for a day without pushing loses its claim to the board's 24 hour release | The worker commits and pushes its claim branch every 30 minutes and on the TERM the job already receives 120 seconds before its time runs out (`--signal=B:TERM@120`) | Small | hpcworker worker template |
| 4 | State is known only when someone presses List | A scheduled list every 15 minutes (the accounts words' floor is 3 seconds, so it costs nothing); the panel flags a worker whose last word is older than its threshold | Small | symphony-template, site |
| 5 | A failed press shows a vague sentence; the cause sits in More, Copy debug log | Beethoven shows the shell's error with the press; the gate setup is split into a short pull step and the rest, so one slow step cannot time the whole press out | Medium | beethoven-extension, hpcworker |
| 6 | A worker waits in the queue of one partition while another partition is free | Submit to two partitions at once and cancel the loser when the first starts (designed, never built) | Medium | hpcworker |
| 7 | Several workers on one account share its five-hour window and stall together | The panel shows how many workers each account carries and warns before a start that would crowd one; later, pick the account the way pool.py picks a cloud slot | Small | site, later hpcworker |
| 8 | The gate's ssh key never expires | An ssh certificate with a lifetime, signed by a key that stays on the grid, renewed by the lab lead's press; or rotate the key on a schedule | Medium | hpcworker, symphony-template |
| 9 | Grid workers and cloud workers live in two tabs | One Workers view lists both, with the same columns: name, where, account, state, age, claim, and Open, Stop or Cancel | Medium | site |
| 10 | A cloud worker stopped at its 90 minute limit keeps only what it pushed | The same push on a timer as rank 3, in workers.yml's prompt and a step that pushes before the limit | Small | symphony-template |

**Continuation, in particular.** On the grid a worker already survives the end of its job: the successor job continues the same Remote Control session for up to seven days, and the workspace stays on the shared disk. What does not survive is the claim, which only pushes keep alive (rank 3), and what a node failure takes is only work not yet written to disk. In the cloud, nothing survives a run except what it pushed (rank 10).

**Robustness, in particular.** The parts that fail quietly are the intake (rank 1), the silence between presses (rank 4) and errors without causes (rank 5). Each fix makes a failure visible rather than adding a new mechanism, which fits the project's rule of as few moving parts as possible.

## What was verified and what is not measured yet

**Verified.**

- The grid takes framework 22's words: the list run of 12:03 UTC (request verify22) succeeded and returned a `workers` array, one worker online on hao1, account 1 on a Max subscription.
- Start and Stop of a named worker, and Cancel of a cloud run, are covered by the panel's checks (grid tests G9 and G10, runs test R1, with mutants that each fail them) and by the template's tests with a fake ssh and git.
- The gate's floor is read from its code: 60 seconds for start, login and usage, 3 seconds for the other accounts words, one call at a time under a lock.
- A start by a name already running submits nothing, from hpcworker's own check.
- The lost-press behaviour of rank 1 is GitHub's documented rule for concurrency groups; the workflow sets cancel-in-progress to false, which does not change it.

**Not measured yet.**

- Two or more grid workers running at once on real nodes: no second worker has been started, since that spends allocation and waits on your word and a number.
- How long a start takes from press to online, and how long a job waits in each partition's queue.
- Whether a successor job's `--continue` keeps a long session whole across several job ends.
- The cause of the Beethoven Connect failure (parked; it needs the debug log from the next failed press).
