# One Slurm protocol for every grid job

Source: the thread "Beethoven grid node wait", from its handoff of 2026-10-22 00:02 UTC (docs/checkpoints/2026-10-22/grid-slurm-protocol.md) and its restart of 2026-10-22 04:21 UTC, item 4 of part 6 of docs/checkpoints/2026-10-22/handoff.md. This note was skipped at the stop of 2026-10-22 00:01 UTC and is written here from that handoff and the merged code.

## The question

Each project that ran work on Wayne State's grid wrote its own sbatch lines: its own partition, QoS, GPU request and output path. SchwingNet's first version 1 run on 2026-10-21 was refused because it asked a GPU partition with no QoS, while Beethoven for VS Code had known the grid's GPU request since 2026-09-28. The question was how every thread, and every project, queues a Slurm job the same tested way, so that what the grid needs is written down once.

## What was built

- hpcworker framework 25 to 27 (hpcworker #29 and #30, live on the grid since 2026-10-21 23:49 UTC at 682ca31): `hpcworker job submit | status | log | cancel | version`, job interface 2. A caller names a project, a job name and a class, cpu, batch or gpu, and the deployment's site profile supplies the partition, the QoS, the account and the GPU request. Every job goes into the project's ledger, `<shared_state_dir>/jobs/<project>/jobs.tsv`, with its log beside it, so status and logs are read the same way for every project. `--check` asks the scheduler with `sbatch --test-only` and queues nothing. The script keeps only its own time, CPUs, memory and rules such as singleton; sbatch takes its command line over a script's #SBATCH lines, so an older script's partition line cannot win over the profile.
- beethoven-sites #5: the Wayne site module records the GPU partitions gmsap, gvohp and galhp, the GPU QoS gpu and the node domain nas.grid.wayne.edu, which framework 26 composes into the published profile.
- beethoven-base #5 and #6: profile.ts gains jobClassOf, sbatchOptionsOf and nodeHostOf, and the VS Code export carries profile.ts, so the extension and hpcworker read placement from one record.
- spine-datasets #121 (merged 2026-10-21): the dataset promoter queues its chain through `hpcworker job submit --class batch`, under the job name spine-datasets-promoter it had before.
- hpcworker #31 and symphony-template's companion pull request (2026-10-22): the gate word `promoter restart` and the job `promoter-restart` in grid-accounts.yml, described below.

## Why the promoter needed a word of its own

The promoter updates its own code only from commits of the owner's that carry no other account's commits (docs/research/trusted-dataset-promotion.md). #121 was committed with a co-author line, so the chain running on the grid kept the code from before it and still called sbatch itself. The owner chose on 2026-10-22 a fixed gate word over a grid command typed by hand.

`promoter restart` takes no argument. It reads main's head of spine-datasets with gh, fetches tools/promote.py and grid/promote.sh at that commit into .tmp files before anything stops, so a fetch that fails leaves the chain as it was, runs the copy on disk's `promote.sh stop`, waits until squeue lists none of the chain's jobs, puts the two files in place and runs `promote.sh start <sha>`. The wait matters: a cancelled job stays in squeue while it ends, past Slurm's KillWait of 30 seconds and the epilog, and `promote.sh start` would read it as a chain still queued and start nothing. The gate waits about 90 seconds and stops the chain again every 30 while jobs remain, since a job that started while stop read the queue may have queued a successor stop never saw; the queue, not stop's answer, decides, since a stop that fails part way may still have cancelled jobs. If jobs remain, or squeue never answers, the gate answers 75 and says the chain may still run on its old code. Its downloads are named *.gate.tmp so they never meet the *.tmp files the promoter's own self-update writes in the same folder. The review before the pull request found those four cases. Every promoter word now hands promote.sh the gate clone's hpcworker as HPCWORKER, as the SchwingNet words do. Every folder and file it runs is held to the account, as the gate holds everything it runs.

A session sends it with grid-accounts.yml, action job, job promoter-restart, once the gate's clone has taken hpcworker #31 through the job update.

## Where it stands

- Live: framework 27 on the grid; the promoter's code on spine-datasets main.
- Waiting: the promoter's running chain moves onto main's code once `update` and then `promoter-restart` are sent after both pull requests merge.
- SchwingNet's jobs, the CT priors' census and samples among them, move onto `hpcworker job submit` in SchwingNet #78 (issue #77), owned by the SchwingNet threads, which also own SchwingNet's gate words.
- beethoven-vscode #20 (draft) reads placement and the node domain from beethoven-base and the profile; its typecheck, 128 unit tests and build pass, and `npm run test:vscode` still has to run on a machine with VS Code, which the cloud container cannot download.

## What is not measured yet

- A restart on the grid itself: the gate's tests stand in for squeue, gh and promote.sh; the first real `promoter-restart` is the first measurement of how long a cancelled promoter job stays in squeue.
- Whether `hpcworker job status` reads the promoter's jobs queued before #121, which wrote their logs under the promoter's own logs folder and are in no ledger; promote.sh status falls back to that folder.
