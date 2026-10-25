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

## Measured once the move was merged

- job submit queued a real chain on the grid: SchwingNet's #78 merged on 2026-10-22, and the next
  gate word (fetch of one PhysioNet set) queued its fetch, bank and catalog jobs through it with
  their afterany waits, each asked with --check first, and status read them back.

## Reading a .netrc as wget does

- A tool that names the login wget will send must read ~/.netrc as wget does, not with Python's
  netrc module: that module refused the grid's file, which wget reads, and stopped every PhysioNet
  fetch before its first request (SchwingNet #100, #102). The reader there is a port of wget 1.21's
  parse_netrc_fp and search_netrc: keywords matched as written, a backslash taken out in any token,
  the character after a closing quote eaten, an entry with no login dropped, the file read as bytes,
  and no fallback to default, since wget given --user ignores it. A review against wget's source and
  a real wget found each of those differences in the first version.
- PhysioNet answering 401 and then 403 means wget's first request went without a login and the
  second, with it, was refused: the login was taken and the account lacks access to that project,
  which its page grants once its data use agreement is signed.
- That reading names an account, not which one, and the owner's page showed the agreement signed
  while the grid was still refused. The fetch report now names the login wget sent, masked to its
  first two characters, its last and its length, first on the line so the status word's 200
  character cut keeps it (SchwingNet #108, #109). The next fetch (job 40702978) showed a 19
  character login beginning op and ending m, the organization's PhysioNet account, while the owner
  signed as his own: the agreement belongs to one PhysioNet account, and ~/.netrc must name that
  account. Only the owner can type the password, so the edit is his, through the portal's file
  editor; no workflow holds a PhysioNet password.
- With ~/.netrc naming the owner's account the fetch ran (job 40704982 from 15:36 UTC on
  2026-10-22, bank 40704984 and catalog 40704986 after it), but the space tally showed nothing of it
  for hours, since it rounds to whole GB and status shows a job's log only once it ends. Status now
  prints, for each live fetch of one set, its raw folder's file count, size and last write, read
  from CephFS's recursive directory attributes with no walk (SchwingNet #125, #126). At 23:17 UTC,
  7 h 38 min in, it read 81 files and 295 MB of the set's 34.1 GB, last written 29 s before: alive,
  and at its average so far weeks from done. Not yet measured: whether the first hours went to
  listing files, so the rate is taken from two readings an hour or more apart, by sending
  schwingnet-status and comparing the line. Once it ends: sha256sum -c against the set's
  SHA256SUMS, the bank and catalog run on their own, and spine-datasets records the set fetched.
  Never resend the fetch while the job runs.

## The protocol check and a moving default branch

- The protocol check (symphony-protocol's checkout_of) counts the checkout as GitHub's test merge
  only when its first parent is the event's base sha. When the default branch moved while a pull
  request was pushed and marked ready, the ready_for_review event's run failed with "the checkout
  is neither the head the event names, nor GitHub's test merge of it", and a re-run, which reads the
  same event, failed the same way; a push that brought the default branch in gave the next event a
  base that matched, and the check passed. Twice on 2026-10-22 (SchwingNet #78, #102). The fix
  belongs in symphony-protocol, not in a copy.

## What is not measured yet

- Whether Slurm on the grid accepts `sbatch --test-only` with `--array`.
- A full start graph, setup to the version 1 run, queued through job submit.
