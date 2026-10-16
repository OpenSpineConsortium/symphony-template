# The WSU grid and GitHub Actions

What was measured and weighed before Symphony's GitHub Actions were made to run on Wayne State's
grid through Beethoven, and what was built. Written 2026-10-16 in the owner's thread "Symphony on
the WSU grid", from the owner's question of 2026-10-15 23:35 UTC, item 10 of that day's handoff:
"Can I use beethoven to connect my Github actions to the WSU grid and then send results/logs back
to connect Symphony to the WSU grid using Beethoven?", and the owner's note of 23:54 UTC that an
ssh key in a GitHub environment secret could connect to the grid, "especially if the wsu user and
pass was also stored". The owner decided on 2026-10-16 at 00:24 UTC, on the card that put the two
directions side by side: both, the runner on the grid first, then the ssh gate as a second pull
request. Every claim below names what it rests on; what the grid has not yet shown is said so.
The pull requests: OpenSpineConsortium/hpcworker, the runner (tools/grid_runner.sh and its tests),
and OpenSpineConsortium/symphony-template, the workflow, docs/setup/grid.md and this note.

## The answer

Yes, with the connection pointing from the grid out. GitHub's own runners cannot reach the grid,
and no credential of the grid's may sit at GitHub nor one of GitHub's on the grid beyond a job's
own, so Beethoven does what its CI lane already does: a Slurm job on a compute node polls GitHub
over outbound HTTPS. The job serves GitHub's own self-hosted runner, inside GitHub's own runner
image, registered for one GitHub job at a time with a just-in-time credential that the account's gh
sign-in mints on the grid as the registration starts and that GitHub discards once the job has run.
A workflow job that names the runner's labels (`runs-on: [self-hosted, grid]`) then runs on the
node, and GitHub keeps its log and its artifacts as for any job: the results and logs come back the
way every Actions job's do, with nothing of Beethoven's in the workflow and no server of ours. The
runner chain outlives a wall time or a preemption because each job queues its successor first; it
stops registering a margin before its wall time, so a job cut off by the wall time, which GitHub
would report as a lost runner, cannot happen to a job that ends within the margin.

The other direction, GitHub pushing into the grid over ssh, is not first, and the password never
goes to GitHub: Wayne State's ssh and portal ask for a one-time code beside the password, so a
stored password alone does not get in; a key in a GitHub secret is a credential of the grid's at
GitHub, which every writer's workflow can read; and it would run commands on the login node, where
Beethoven's etiquette allows one scheduler call per action and nothing else. What it is good for,
a workflow step that queues one job or reads one file on the grid without a runner waiting in Slurm's
queue, is worth a narrow gate: a key on the grid that accepts one forced command and nothing else,
through hpcworker, used by a workflow from an environment secret, after the owner has tested that
key-only sign-in works from outside the VPN. That is the second pull request.

## What was measured, and where

The grid, from hpcworker's CLAUDE.md ("Grid") and docs/OPEN_QUESTIONS.md, and
framework/profiles/wayne.json:

- The login node, warrior, is CentOS 7 (bash 4.2, python 3.6), and its banner bans python3 among
  other programs ("terminated on sight"; hpcworker's framework/README.md, "The login node"), so a
  tool run there reads the site profile with the framework's awk reader; the compute nodes are EL7 on
  a 3.10 kernel; Apptainer 1.2.2 is at /wsu/el7/gnu7/apptainer/1.2.2/bin/apptainer behind the module
  apptainer/1.2.2. The worker's queue is reqp with the QoS requeue (preemptible); secp/secondary is
  for short allocations; gmsap and gvohp carry GPUs. The lab's volume is /rs/rs_grp_oschome (CephFS);
  $TMPDIR there is not node-local, so a job's temp goes under /tmp/$USER on the node, which is swept
  while jobs run; IPC goes under /dev/shm.
- The portal, https://ondemand.grid.wayne.edu, and ssh sit behind the university's VPN and a one-time
  code; the student types both into Beethoven's own sign-in sheet, which never stores them.
- Egress was measured on 2026-09-28 from the compute node asx15: api.anthropic.com answered directly
  (no proxy), claude.ai answered 403 to curl. github.com was not tried from a compute node; the login
  node's clone of a private repository through gh was measured on 2026-10-03 (the CI lane's first
  open question, in docs/OPEN_QUESTIONS.md).
- Claude Code's Remote Control registered from an sbatch job on 2026-09-29 (job 40496445, asx15):
  a long-lived outbound connection from a batch job works there.
- The host's Slurm client runs inside a container on the nodes with the binds measured on asx1 on
  2026-09-28 (lib/adapters/common.sh, hpcw_slurm_in_container): /usr/bin under /opt/host/bin,
  /usr/lib64/slurm, the munge library and socket, /etc/slurm, and an /etc/passwd that adds the slurm
  and munge users.

GitHub's rules for self-hosted runners, read on 2026-10-16 from the github/docs repository's content
files, since docs.github.com is blocked from the cloud session (the paths are the pages'):

- A self-hosted runner should almost never be used for a public repository: a fork's pull request
  could run its code on the runner (actions/reference/security/secure-use.md, "Hardening for
  self-hosted runners").
- Just-in-time runners: the REST API creates an ephemeral runner that performs at most one job and
  is then removed from the repository automatically; the encoded configuration it returns is passed
  to the runner at startup, and reused hardware is to be cleaned between jobs (the same page, "Using
  just-in-time runners"). The endpoint is POST /repos/{owner}/{repo}/actions/runners/generate-jitconfig
  with name, runner_group_id, labels and work_folder; it needs repository administration (the REST
  reference for self-hosted runners). GitHub adds the labels self-hosted, linux and x64 itself.
- A job for a self-hosted runner can wait in the queue for 24 hours before it is cancelled
  (actions/reference/limits.md).
- A runner must be updated within 30 days of a new version when automatic updates are off; the
  runner updates itself otherwise (actions/reference/runners/self-hosted-runners.md).
- The runner application supports Red Hat Enterprise Linux 8 or later, CentOS 8 or later, Debian 10
  or later and Ubuntu 20.04 or later (the same page, "Supported architectures and operating systems"):
  not an EL7 node, hence the container.
- The runner's exit codes, from actions/runner's source (src/Runner.Common/Constants.cs, ReturnCode):
  1 terminated, 2 retryable error, 3 updating, 4 run-once updating, 0 success; an ephemeral runner
  exits after its one job (src/Runner.Listener/Runner.cs), and the configuration it holds is the
  files .runner, .credentials and .credentials_rsaparams in its folder
  (src/Runner.Listener/Configuration/ConfigurationManager.cs). Passing the encoded configuration on
  the command line, as the documented `./run.sh --jitconfig` does, puts a credential in argv, which
  Beethoven's rules forbid; the chain writes the three files itself, mode 0600, from gh's answer in a
  mode-0600 file on the node's disk.
- GitHub's runner image is ghcr.io/actions/actions-runner (actions/runner, images/Dockerfile): Ubuntu
  22.04 with the runner, git and the runner's own node, and no python. What else it carries is read
  from that file, not measured here.

Apptainer: `--no-mount bind-paths`, which keeps the site's own bind paths (the home, the volume) out
of the container, exists since 1.2.0 (its CHANGELOG.md, v1.2.0 of 2023-07-18), so the grid's 1.2.2
has it; whether the site's configuration lets `--home` point at a folder on the node's disk is not
yet measured.

## The two directions weighed

GitHub pushes into the grid. A workflow step opens ssh to the login node with a key held as a
GitHub secret, and the WSU user and password beside it as the owner suggested. What it would give:
a step that runs a command on the grid with no runner waiting in Slurm's queue, from any workflow.
What it needs: a credential of the grid's at GitHub, readable by every writer's workflows
(docs/start/team.md takes the repository's secrets out before anyone else gets Write for the same
reason); the VPN or an exception for GitHub's address ranges, which change; and the one-time code,
which a stored password does not supply. Beethoven's rules say never a credential on a command line,
in a job file or in a log, and nothing on the login node beyond one scheduler call per action, so
the only form of it that fits is the gate above: a key that may run one forced command, with the
password nowhere.

The grid pulls from GitHub. The CI lane's direction: a job on a compute node reads GitHub with the
account's own gh sign-in and posts back. For Actions, GitHub's own runner does the polling, and the
job's log, artifacts and status land where every job's do. What it needs: gh signed in on the grid
as an administrator of the repository, outbound HTTPS from compute nodes to github.com, api.github.com,
pipelines.actions.githubusercontent.com and ghcr.io, and a container for the runner. What it costs:
a chain of jobs on reqp/requeue, idle most of the time (one registration listening), the margin before
each wall time during which no new job starts, a job queued for up to 24 hours when the chain itself
waits in Slurm's queue, and a GitHub job lost when its chain job is preempted. What it rules out: a
public repository, and any step that needs the home or the lab volume, which the container does not
see (a step that needs the grid's files queues a job of its own with --slurm, or reads them through
a bind the chain is told to add).

The decision, on the card of 2026-10-16 00:24 UTC: both, the runner first.

## What was built

In OpenSpineConsortium/hpcworker, on the branch claude/grid-runner: tools/grid_runner.sh
(--install, --start, --stop, --status on the login node; --pull and --serve inside the jobs),
tools/grid_runner_install.sbatch (one job that pulls the image as a SIF under
/rs/rs_grp_oschome/$USER/hpcworker-runner/image and runs the runner's --version inside it with the
chain's exact flags, so a flag the site refuses is seen there and never in a chain),
tools/grid_runner.sbatch (a chain's job: queue the successor, mint, listen, one GitHub job at a time,
until the margin or STOP), and tools/tests/test_grid_runner.sh with the stand-ins
tools/tests/shim/apptainer and tools/tests/shim/runner-listener beside the extended shim/gh and
shim/slurm: 163 checks against stand-ins (nothing reaches GitHub, a registry, a scheduler or the
grid), among them that no token and no registration ever leaves a job, that the job looks at the
runner once a minute and never faster, and that every bind the container gets is on the node's own
disk or the test's folder. The README's paragraph "A GitHub Actions runner on the grid" and the
section of the same name in docs/OPEN_QUESTIONS.md describe it; CLAUDE.md there carries the rule.

In this repository: .github/workflows/grid.yml (one command, from the workflow's page or another
workflow, on `runs-on: [self-hosted, grid]`, only while the repository is private and never for a
fork's event, Python 3.12 set up unless unticked, the output as the job's log and the artifact
grid-<run>-<attempt>), docs/setup/grid.md (how it works, what it takes, the owner's eight steps with
their links), the memory fact "The grid runs a job through Beethoven", and this note.

## What is not yet measured

Nothing of it has run on the grid. hpcworker's docs/OPEN_QUESTIONS.md lists each question with the
first test that answers it; in short:

- compute nodes reaching ghcr.io (the image) and github.com, api.github.com and
  pipelines.actions.githubusercontent.com (the runner's long poll);
- `--no-mount bind-paths`, `--home` and `--cleanenv --containall` as the chain uses them, on the
  grid's Apptainer 1.2.2 and under the site's configuration;
- the runner, .NET 8 in an Ubuntu 22.04 image, on an EL7 node's 3.10 kernel;
- whether Slurm at Wayne State exports SLURM_JOB_END_TIME to a batch job (the job's clock; without
  it the margin is read from the start time and --hours);
- the chain: a successor queued from inside a job with `--dependency=afterany:<id>,singleton` on
  reqp/requeue, and a requeued job finding its successor instead of queuing a second;
- how long a GitHub job takes to start on the runner, and whether GitHub holds a job that arrives
  while no runner is online until the next registration;
- actions/setup-python and actions/checkout inside the runner's container on the grid, and `--slurm`
  with this image rather than the worker's sandbox.

The install job is the first test of the first three; the first chain job and the first Run workflow
press answer the rest.

## Where it meets a Claude Code session on the grid

The owner's other thread of 2026-10-16, "Beethoven worker opening", is after a cloud-enabled Claude
Code session running on the grid worker itself, with Projects, cloud sessions and the grid's own
hardware, from one Beethoven session. The runner and that session meet in four places, and this
note says so, since both are built on the same account:

- The same gh sign-in: the runner's registrations and a session's own GitHub work use the account's
  one gh sign-in on the grid, under the owner's own login. Nothing the runner writes is where a
  session reads: its registration lives in mode-0600 files on the node's disk inside the chain's
  job, and its chain folder on the volume holds STOP, status.json, the jobs' logs and a copy of the
  runner's own diagnostic logs when a run ended badly, no credential.
- The same queue: a chain job and a worker job both run on reqp/requeue and count against the
  account's job limits; a chain started with --cpus, --mem or --gres takes that from the same share.
  One chain per repository and account, and one GitHub job at a time on it.
- The same tools: tools/grid_runner.sh lives beside the worker's job template in hpcworker, reads the
  same site profile with the same awk reader (the runtime, the worker queue and the folder beside
  the account's state), and reuses lib/adapters/common.sh's Slurm binds for --slurm; a change to
  those binds changes both.
- No Claude credential near the runner, by construction: a session's sign-in lives under $HOME
  (the profile's claude_config_dir), which the runner's container does not mount
  (`--containall --cleanenv --no-mount bind-paths`), and the chain's job files unset the agent
  markers and GITHUB_TOKEN before anything runs. A session on the grid may start, watch and stop a
  chain itself, since those are file work, gh, one squeue and one sbatch on the login node, the same
  calls the CI lane's watcher makes from a job; and a workflow job on the runner may in turn be what
  checks a session's push, since it runs the repository's own check on a node.

## Sources

- OpenSpineConsortium/hpcworker: CLAUDE.md ("Rules that are not negotiable", "Grid", "This
  repository"), docs/OPEN_QUESTIONS.md ("The grid's CI lane installs main's head"),
  framework/profiles/wayne.json, framework/lib/adapters/common.sh (hpcw_slurm_in_container),
  tools/grid_ci.sh (the CI lane's direction and conventions), tools/tests/test_grid_ci.sh.
- github/docs, content files read on 2026-10-16: actions/reference/security/secure-use.md,
  actions/reference/limits.md, actions/reference/runners/self-hosted-runners.md,
  actions/concepts/runners/self-hosted-runners.md, actions/how-tos/manage-runners/self-hosted-runners
  (add-runners, configure-the-application, remove-runners, manage-access), rest/actions/self-hosted-runners.
- actions/runner: src/Runner.Common/Constants.cs, src/Runner.Listener/Runner.cs,
  src/Runner.Listener/Program.cs, src/Runner.Listener/Configuration/ConfigurationManager.cs,
  images/Dockerfile, docs/start/envlinux.md.
- apptainer/apptainer: CHANGELOG.md (v1.2.0, 2023-07-18).
- The thread "Symphony on the WSU grid" in the Symphony project: the owner's messages of 2026-10-15
  23:35 and 23:54 UTC, the decision card answered at 2026-10-16 00:24 UTC, and the coordinator's
  relays of 00:25 UTC (research notes accumulate in the repository) and 00:29 UTC (the session on
  the grid is the other thread's).
