# Running a project's grid work through the gate

Source: the thread "SchwingNet video demo plan", 2026-10-21 and 2026-10-22, resuming part 5 of the
handoff docs/checkpoints/2026-10-22/handoff.md. The work is in OpenSpineConsortium/SchwingNet's
pull requests #86 and #91 (merged), #94 (merged 2026-10-22) and #78 (issue #77), and in hpcworker's
framework/lib/jobs.sh at framework 27. SchwingNet is confidential until its provisional is filed, so
this note keeps what was learned about operating a project on the WSU grid through the gate, and no
method or result of the model.

## What the gate gave a project

A project's grid work ran end to end from GitHub alone: each gate word, sent through
grid-accounts.yml's job action (`schwingnet <word>`), fast-forwarded ~/SchwingNet to main and ran
its grid/gate.sh, whose answer came back on the branch grid as logs/job-<job>.json. The owner typed
no grid command. The words that queued jobs (start, v1, fetch, samples) and the one that read them
(status) were enough to set up the container and environments, fetch and ingest data, build and
split-check a catalog, and train and score a first model run on a GPU node.

## What broke on the grid, and the rule each fix became

- A GPU job written with a partition but no QoS was refused ("Invalid qos specification"). The
  rule: a project never writes placement. Every job now goes through hpcworker's `job submit` with
  a class (cpu, batch, gpu), and the site profile (profiles/wayne.json) gives the partitions, the
  QoS, the account and the GPU request. SchwingNet's .sbatch headers keep only time, CPUs and memory,
  and its tests fail on a header or a script that places a job.
- Apptainer printed an INFO line on every `exec`, which landed in output a stage read as JSON. The
  rule: run the container with `apptainer --quiet exec` wherever its output is parsed.
- A status filter that cut every `/<word>` as a path turned a count like 21/21 into `21<path>`. The
  rule: a redaction filter for logs needs a test with ordinary text in it, not only with secrets.
- A job queued under `%x_%A_%a` that is no array logs with Slurm's NO_VAL as its task id
  (`_4294967294`). job submit names a plain job `<name>_<id>.out` and only an array
  `<name>_<id>_<task>.out`, so the case is gone for jobs it queues.

## Moving a project onto hpcworker's job submit

- One sourced helper (SchwingNet's grid/hpcw.sh) is the only caller: it takes NAME CLASS, then K=V
  pairs for the job's environment, then job submit's options and `-- SCRIPT`. job submit hands the
  job the caller's environment (framework 27), so settings travel as environment and never through
  sbatch's comma-separated `--export` list.
- sbatch's dependency text maps one to one onto `--after ID:ok|any`; anything else (singleton,
  afternotok, an array task id) is refused rather than dropped, since a dropped wait lets a stage
  run before its input. job submit adds `--kill-on-invalid-dep=yes` itself.
- Each shape is asked with `--check` (sbatch --test-only) before it is queued, except arrays, since
  whether --test-only takes --array was not measured on the grid.
- The helper refuses an hpcworker older than framework 27 (`job version`): an older one lacks
  --partition, --no-requeue and the caller's environment, so the job would run without its settings.
- The old dry run (SBATCH=echo) becomes a real submission once hpcworker is on PATH, so it is refused;
  HPCW_DRY=1 is the dry run.
- Live jobs are still read from squeue. hpcworker's `job status` falls back to sacct when squeue does
  not answer and calls a job ended when neither does; a gate that read that as "nothing live" would
  queue a second graph beside the first.
- A job's output moves from the repository's grid/logs to hpcworker's log folder for the project, and
  status reads it with `job log`, falling back to grid/logs for jobs queued before the move.

## What is not measured yet

- Whether Slurm on the grid accepts `sbatch --test-only` with `--array`.
- A full start graph queued through job submit on the grid; the move was checked against the real
  hpcworker 27 with a stand-in sbatch, not against Slurm itself.
