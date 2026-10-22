# Moving Beethoven for VS Code onto hpcworker

Oct 7, 2026 · @greg

**Deferred.** On 2026-10-07 at 22:33Z greg deferred the move, since he is the only person using the VS Code edition and nothing else in the ecosystem depends on it. VS Code keeps its own grid scripts for now, including the builder of the lab's shared image. The credential leak in the first of the four things below is being fixed separately.

## Summary

The move can be done, but it is not a quick swap. hpcworker already covers starting, stopping and watching a worker, but it lacks four things VS Code students rely on. Nothing on the grid is deleted at any step. No code is written until you have answered the first four questions in the table below.

Every claim in the sections below cites a file and line in beethoven-vscode at `631226e` or hpcworker at `e77863c`. Each section was checked against the code by a second reader and then corrected.

**What the move is.** Today Beethoven for VS Code copies ten scripts of its own (`grid/`, "grid scripts 9") into each student's `~/.beethoven/bin` and runs its workers through them. After the move it would use the lab's shared hpcworker, as the browser and desktop editions already do, and stop shipping `grid/`.

**What carries over as it is:**

- starting, stopping, status and the log of a worker;
- the Claude sign-in folder, `~/.beethoven/claude`, which both use, so nobody signs in again;
- the student's answer to "Enable Remote Control?";
- the rule that only a Claude subscription counts as signed in.

**What hpcworker must gain first:**

- **Ask.** This is VS Code's Claude handing a task to the grid worker and getting the answer back. It is VS Code's main feature and the largest piece of work. Today it rests on a loop that checks files on the login node four times a second, which hpcworker's etiquette does not allow, so it has to be redesigned.
- **Worker sizes.** Hours, CPUs, memory and GPUs chosen per worker. Without them a moved student gets 2 CPUs, 8G and 8 h instead of VS Code's 4 CPUs, 16G and 24 h, and no GPU worker at all.
- **Remote-SSH lines.** The three lines in `~/.bashrc` that let VS Code's Remote-SSH run on the CentOS 7 compute nodes.
- **Tokens.** A way for the worker to use the student's GitHub and Hugging Face access.

**What goes away instead of moving:**

- the licence check on the grid (the licence stays checked on the laptop);
- VS Code's own lab-access requests, which the access service's readers list replaces;
- the per-student image build;
- the "bypass all permissions" mode;
- the polling loops on the login node.

**Four things to know now:**

- **A credential path in VS Code 5.0.0.** I found this by reading the code; it was not run, because running it would print a credential. The grid command's `result` and its relay check neither the worker name nor the request id (`grid/beethoven:511-514,701-703`). The MCP tool `beethoven_result` passes any id through (`extension/src/mcp/server.ts:152-157`). So the id `../../../claude/.credentials` returns the student's Claude credential file to the laptop's Claude. That breaks the rule that Beethoven never relays a credential. The fix belongs in beethoven-vscode and is small: check both values on both sides. It does not need to wait for the move.
- **Bypass mode.** VS Code 5.0.0 lets the laptop's Claude ask the grid for `bypassPermissions`. The grid then runs `claude -p --dangerously-skip-permissions`. hpcworker's contract refuses that mode, and the plan drops it.
- **The lab image.** VS Code's image builder, `grid/bootstrap.sbatch`, is the only tool that has ever built the image hpcworker runs at Wayne State. Someone has to own rebuilding it before `grid/` goes.
- **Lab access, today.** This matters whether or not the move happens. A VS Code student approved only through VS Code's own lab-access approval, and not on the access service's roster, loses the lab folder at every sync of `tools/grid_access.sh`.

**The order:**

1. hpcworker makes its small additions (framework 18).
2. The new site fields go in.
3. VS Code gets an hpcworker client beside the old path, behind a setting.
4. hpcworker builds Ask.
5. VS Code 6.0.0 switches over, with new terms (`TERMS_VERSION` 8).
6. VS Code 7.0.0 removes `grid/` after one term.

Every beethoven-vscode step waits on your order to work in that repository.

**What you decide.** There are fourteen questions, each with a recommended answer, set out in full in the last section.

| # | Question | Recommended answer | Needed before |
| --- | --- | --- | --- |
| 1 | Where does Ask go? | Build it in hpcworker | any code |
| 2 | Which VS Code licence holders are off the grid's approved list? | Require the extension grant before any key is issued by hand | any code; urgent today |
| 4 | May VS Code choose hours, CPUs, memory and GPUs? | Yes for hours, CPUs and memory now, within new site limits; GPUs after one measured GPU job | any code |
| 7 | How do GitHub and Hugging Face tokens reach the worker? | The student signs in to each tool on a compute node; no Beethoven code holds a token | any code |
| 3 | How does VS Code reach hpcworker? | As the desktop edition does: gate lines over the student's own ssh, and read-only file reads | step 6 |
| 10 | What happens to the MCP tools that run `sbatch` and `squeue` and read files? | Workspace reads only; drop `sbatch` and `squeue` once Ask works | step 6 |
| 6 | Where do the Remote-SSH lines live? | A site field that hpcworker's `~/.bashrc` block writes | step 5 |
| 12 | Release numbers | Framework 18, then 19 for Ask; VS Code 6.0.0 switches over and 7.0.0 removes `grid/` | step 4 |
| 5 | Is `bypassPermissions` ever offered? | Never | step 8 |
| 8 | Does the grid keep a licence check? | No; the laptop checks the licence | step 9 |
| 14 | What replaces phone access? | hpcworker's worker, in 6.0.0 | step 9 |
| 9 | What happens to VS Code's lab-access requests and its container library? | Retire the requests (the readers list replaces them); one image per site; name the image's owner before 7.0.0 | step 10 |
| 11 | What happens to the old grid files? | Leave everything for one term, then offer a tidy the student runs; never results, accounts, the sign-in or the work folder | after 7.0.0 |
| 13 | Does hpcworker gain an `uninstall`? | Later | after 7.0.0 |

## What runs on the grid today

Paths in this section belong to beethoven-vscode at `631226e` unless they carry a prefix. `hpcworker:` means hpcworker at `e77863c`.

**How the scripts get to the grid.**

- The build copies every file of `grid/` except `*.d.ts` into `dist/grid`, with LF line endings (`extension/esbuild.mjs:78-87`).
- The setup step *Grid install* (`extension/src/core/wizard.ts:727-764`) then:
  1. runs a one-line move of an old `~/.ashley` (`wizard.ts:683-691,732`);
  2. copies the files into `~/.beethoven/bin/` with scp (`wizard.ts:738`);
  3. runs `migrate` when both folders exist (`:743`);
  4. writes the licence key, the revocations and the GitHub and Hugging Face tokens over ssh stdin (`wizard.ts:651-672`, called at `:747`). The tokens land in `secrets.env`. The daemon puts that file into the environment of every `claude -p` (`grid/beethovend.js:163,320`), and `verify-tokens` sources it on the login node (`grid/beethoven:1172`). Token renewals push the tokens again outside this step (`wizard.ts:523-527`);
  5. runs `beethoven install` (`wizard.ts:750-757`);
  6. runs `verify-tokens` (`wizard.ts:758-759`), and reports the `restarted worker` lines that install printed (`wizard.ts:761-763`).
- `install` first runs `migrate_home` and `retire_apikey` (`grid/beethoven:220,223`). It then makes the layout, strips CR line endings, links the old names, sets ROOT and rewrites the managed `~/.bashrc` block. Next it cancels and resubmits every RUNNING worker whose heartbeat has no `scripts` field, which means a daemon of grid scripts 8 or older (`grid/beethoven:258-272`). A worker whose daemon is from grid scripts 9 or later keeps its old code until its job ends, whatever is installed. The restart message says "older than $VERSION" whatever version the worker actually ran (`:269`). Finally `install` adopts the lab's shared container, waits for lab access, or submits a build of the student's own image (`grid/beethoven:217-256`).
- Nothing updates the grid by itself: no timer uploads scripts (`extension/src/core/shell.ts:179-180`).
- The version test is string equality with the bundled `grid/VERSION` (`wizard.ts:710-711`; `extension/src/vscode/diagNodes.ts:352`). A grid newer than the laptop's copy therefore also reads as out of date, and running the step again installs the older scripts.
- The same upload, and the same downgrade, also come from two other places:
  - the view's Install item (`extension/src/extension.ts:200,622-629`; `extension/src/vscode/tree.ts:93`);
  - any Troubleshoot run with repairs, because the repair of the `grid.scripts` node runs this step (`diagNodes.ts:343-354`). That covers runs from the menu, from the panel's run-again button and after any fix button (`extension/src/vscode/diagnosticsUi.ts:93,151,177`). The hourly sweep does not repair (`diagnosticsUi.ts:50-55`).

**The grid files.**

| File | Where it runs | What it does |
| --- | --- | --- |
| `grid/VERSION` | read by the command | `9`, the grid-scripts version. Missing reads as `0` (`grid/beethoven:35`). |
| `grid/bashrc.block` | the student's `~/.bashrc` | C&IT's VS Code glibc sysroot under `/wsu/apps/vscode/...` and patchelf 0.19.1 (`:4-6`), and `~/.beethoven/bin` on `PATH` (`:8`) |
| `grid/beethoven` | the login node over ssh; compute nodes through `srun` (`diag-node`, the sign-in); and inside each worker's container, called by the worker's Claude (`grid/beethovend.js:335,447`) | The grid command. It reads no site profile. Its settings come from `config.env` (sourced as bash, `:55`), `READY`, the lab's `library.json`, environment variables, and literals: `/rs/rs_grp_oschome/...`, `/wsu/apps/vscode/...` (`:368,988-989`), `reqp`/`requeue`, `secp`/`secondary`. The daemon puts it on the worker Claude's `PATH` (`grid/beethovend.js:334-335`). It tells that Claude to fan work out with `beethoven send`, `result`, `wait` and `worker start` (`grid/beethovend.js:447`). The host's Slurm clients are wrapped into the container (`grid/worker.sbatch.tpl:49-68`), so a worker can submit further workers. |
| `grid/bootstrap.sbatch` | batch job (`reqp`/`requeue`, 4 CPUs, 16G, 2 h) | Builds the student's own sandbox from `docker://node:22-bookworm` and installs Claude Code 2.1.283 into `$ROOT/npm`. With `LIBRARY=1` it publishes into the lab library instead (`:8-17,34-35,73-143`). It loads the modules `apptainer/1.2.2` and `singularity/3.5.2` by name (`:59,63`). |
| `grid/worker.sbatch.tpl` | batch job (default `reqp`/`requeue`, 24 h, 4 CPUs, 16G) | Rendered by `sed` (`grid/beethoven:420-423`), with `--dependency=singleton` and `--signal=B:TERM@120`. It makes `/dev/shm` scratch, wraps the host's Slurm for use inside the container, then `exec`s `apptainer exec … node beethovend.js` (`:7-20,40-81`). |
| `grid/beethovend.js` | Node inside the container on the compute node | Polls `inbox/` every 250 ms. Runs one `claude -p … --output-format stream-json` per request, up to `--concurrency` (default 2), with a 6 h cap. Each run has the `secrets.env` tokens in its environment (`:163,320`) and a system prompt that names a Wayne State grid node (`:442`). Writes `outbox/<id>.events.jsonl` and `outbox/<id>.json`, keeps named sessions and checks the licence every 60 s (`:8-9,33-36,63,78,242-548`). Rewrites `state.json` on every 250 ms tick and on a 10 s timer (`:231-232,266`). The file is in the worker folder under the home filesystem, so that is at least 4 rewrites a second per worker. Loads and ticks `phone.js` (`:167-173,217-222`). |
| `grid/phone.js` | inside the daemon | When `rc/enable` exists, runs `script -qfc "claude remote-control"` in `$ROOT/workspaces/phone` with no flags. Answers the consent prompt from the record and writes `rc/status.json` with `session_url` (`:23-27,92-104,161-211`). Keeps one host among this account's VS Code workers through a `mkdir` lease, `~/.beethoven/remote/host.lock` (`:105,228-268`). hpcworker's worker uses the same sign-in folder (`hpcworker:framework/profiles/wayne.json:53`) and does not check the lease. Whether two hosts on one sign-in conflict is not yet measured. |
| `grid/license.js`, `grid/license_keys.json` | the daemon (also bundled in the extension) | Ed25519 licence keys with the prefix `BEETHOVEN1.` or `ASHLEY1.`. Only public keys are on the grid. The identity `<user>@wayne.edu` is written into the daemon (`beethovend.js:101-102`). |
| `grid/login_relay.sh` | login node | Documented as a maintainer's tool (`docs/CHECKPOINT_2026-09-28.md:51`). The grid install still uploads it to every student's `~/.beethoven/bin` (`wizard.ts:637-640,738`), install makes it executable (`grid/beethoven:227`), and no laptop code calls it. Relays `claude auth login` in tmux inside the worker's allocation. It evals lines read from the grid command (`:15`). It pastes the sign-in one-time code from a file into Claude Code's prompt (`:57-63`). Its two waits run `squeue` plus `srun` about every 2 s, up to 60 + 45 times (`:22-53`). |

The laptop also holds site literals. A GPU worker goes to the partitions `gmsap,gvohp,galhp` with QoS `gpu` (`extension/src/core/slurm.ts:70`).

The `.bashrc` block exists for Remote-SSH *Connect*. Connect opens VS Code's server on the compute node of a running worker, reached through ProxyJump via the login node (`extension/src/extension.ts:448-499`; `extension/src/core/sshConfig.ts:58-64,139-140`). `cli/beethoven connect` prints the same host (`cli/beethoven:13-17`). hpcworker has no counterpart.

Remote Control differs between the two editions in ways a port depends on:

- `phone.js` runs `claude remote-control` with no flags and reports `session_url` in `<worker>/rc/status.json` (`grid/phone.js:117-126,176,194-197`).
- hpcworker's worker probes for `--name`, `--capacity`, `--continue` and `--permission-mode`, uses them, and writes `connection.json` (`hpcworker:framework/jobs/worker.sbatch.tpl:12,160,258-262`).
- The VS Code worker job carries `--dependency=singleton` and queues no successor (`grid/worker.sbatch.tpl:18`).

**The grid command's subcommands and who calls them.**

| Subcommand | On the grid | Laptop call sites |
| --- | --- | --- |
| `install [--root]` | `migrate_home` and `retire_apikey`, layout, CR strip, links, ROOT, `.bashrc` block, restart of running workers whose daemon predates grid scripts 9, then adopt, wait for access, or bootstrap | `wizard.ts:750-757`. Also `stepLabAccess.check` (`wizard.ts:787-790`), which runs whenever the setup panel opens (`extension.ts:333`; `wizard.ts:872-876`). So a check can install, and through install it can cancel and resubmit a running worker. The view's Install item (`extension.ts:622-629`) and the `grid.scripts` repair (`diagNodes.ts:343-345`) run the whole step. |
| `migrate` | Moves `~/.ashley` entries into `~/.beethoven` and deletes empty placeholder folders (`:182-183`). Then renames the old folder aside (`:156-191`). | `wizard.ts:743` |
| `bootstrap`, `adopt`, `library [--json]`, `library publish` | Build an own image; use the lab's image; list or publish (admin) | through `install`; `extension/src/core/gridApi.ts:105-111`; `extension/src/extension.ts:518` |
| `status [--json]` | Overall state. It may adopt as a side effect (`:338`). | `gridApi.ts:91-97`, `extension/src/vscode/tree.ts:90`, `wizard.ts:706`, MCP `beethoven_status`; plain `status` from `commandGridStatus`, which follows it with a `squeue` (`extension.ts:615-617`) |
| `doctor`, `diag --json [--repair] [--node]`, `diag-node` | Checks. `diag` also runs `verify-tokens` (`:1045`). Repair may install, submit jobs, restart workers or run `access init`, its `rm -rf` included (`:1143`). | `diagNodes.ts:31-57`, the hourly sweep (`diagnosticsUi.ts:50-55`), `extension/src/cli/main.ts:233` |
| `worker start`, `restart`, `stop`, `list`, `log`, `node` | Render and submit, `scancel`, read | `gridApi.ts:154-173`, `extension.ts:440-562`, `diagNodes.ts:408`, MCP `beethoven_worker_start` and `beethoven_workers` |
| `send`, `wait`, `ask`, `result`, `tail`, `sessions` | Inbox and outbox. `wait` checks files every 0.5 s on the login node (`:499`). `result` checks neither the worker name nor the id (`:511-514`); see the defects. | `gridApi.ts:176-287`, `extension.ts:564-605`, MCP `beethoven_ask`/`_send`/`_result`/`_sessions`, `cli/main.ts:276-289` |
| `relay` | One long ssh session that reads with a 0.25 s timeout on the login node (`:676-721`) | `extension/src/core/relay.ts:40`, used by GridApi, the MCP server, the CLI and the diagnostic node `laptop.relay` |
| `claude login`, `claude remote-consent`, `claude status --json`, `claude forget` | `srun --overlap` into a running worker, or a 30-minute `secp`/`secondary` allocation; the seed; the sign-in verdict; a refusal (`:559-672`) | terminals at `wizard.ts:629` and `extension.ts:815,819`; `gridApi.ts:113-116`; `wizard.ts:605` |
| `phone on`, `off`, `status` | Chooses which worker hosts Remote Control (`:952-976`). Anything else hits `die` (`:974`). | `gridApi.ts:139-147`, `extension.ts:779-835`, `diagNodes.ts:421` |
| `accounts list`, `accounts remove --yes` | Reports the sign-in; deletes the old API-key file on request (`:537-556`) | `tree.ts:120`, through `status` |
| `access whoami`, `status`, `requirements`, `request`, `init`, `admin …` | Lab access as held `sbatch --hold` jobs, status files under `shared/access`, `setfacl` (`:749-950`) | `gridApi.ts:118-136`, `wizard.ts:777-826`, `extension.ts:740-777`, `tree.ts:128-131` |
| `verify-tokens` | Sources `secrets.env` and runs `curl` to Hugging Face and GitHub from the login node (`:1168-1181`) | `wizard.ts:758-759`, `doctor`, `diag` (`grid/beethoven:1045`), `access requirements` |
| `uninstall --yes` | Cancels all workers; removes `workers`, `log`, `config.env`, `READY`, `bin` and the block (`:1182-1216`) | `extension.ts:694` through `gridUninstallLine`, which refuses below grid scripts 9 (`shell.ts:175-185`) |
| `signin-kind`, `version`, `help` | Internal verdict, also run inside the container during `claude login` (`:571`); version | `wizard.ts:646`; `version` also from `gridUninstallLine` (`shell.ts:184`) |

**Lines the laptop runs on the login node without the grid command.**

- `hostname` (`wizard.ts:177-181`).
- `squeue` (`gridApi.ts:99-103`).
- `cd … && sbatch --parsable` for the MCP tool `beethoven_sbatch` (`gridApi.ts:278-282`).
- A read guard around `head -c` and `ls -la` (`gridApi.ts:19-27,268-276`).
- The folder move (`wizard.ts:683-691`).
- The licence, revocation and token writes over stdin (`wizard.ts:651-672`), and the token pushes of a renewal (`wizard.ts:523-527`).
- The `authorized_keys` line, installed with the student's password and one-time code (`extension/src/core/sshInstall.ts:27-28,83`; fallback terminal `wizard.ts:449-453`).

Some calls also carry a conditional `touch accounts/apikey/disabled` prefix:

- every call made through `gridCli`, `gridCliLine` or `gridUninstallLine` (`shell.ts:159-184`);
- `pushTokens`, which has its own (`wizard.ts:670`).

The plain-ssh lines above do not carry it, and neither do `scp` (`shell.ts:188-190`) and the `cli/` forwarders.

The forwarders `cli/beethoven` and `cli/beethoven.ps1` pass every argument to the grid command, and so do their old names `cli/ashley` and `cli/ashley.ps1`. The one exception is `connect`, which `cli/beethoven` resolves itself (`cli/beethoven:13-17`). `beethoven-cli` forwards every command it does not handle in the same way (`extension/src/cli/main.ts:305-310`). Neither forwarder carries the API-key `touch` (`cli/beethoven:12`; `cli/beethoven.ps1:8`).

**Load on the login node.**

- `status --json` runs these `squeue` calls:
  - one `squeue -u` (`grid/beethoven:329`);
  - one `squeue -j` per worker with a job id in `worker_json` (`:302`), and again in `claude_login_json` (`:608`);
  - one more for the bootstrap job when one is on record (`:342`). An account that adopted the lab's container has none.
  - That is 2N+1 to 2N+2 calls for N workers. Each lookup whose job has left the queue adds an `sacct` (`:61`), so a finished worker job costs two.
- The hourly background sweep runs with `repair: false, quick: true` (`diagnosticsUi.ts:50-55`). Each run makes one ssh `hostname`, one `diag --json` (`diagNodes.ts:34`), one `phone status` (`diagNodes.ts:421`) and one relay session for a `PING` (`diagNodes.ts:327-340`).
- One `diag` makes:
  - one `squeue -u` (`grid/beethoven:1022`);
  - up to 4N job-state lookups (`:1051,1096,1111,1124`);
  - `scontrol show config` (`:1023`) and `sacctmgr` (`:1025`);
  - three HTTPS requests from the login node: `api.anthropic.com` (`:1028`), and Hugging Face and GitHub through `verify-tokens` (`:1045,1168-1181`);
  - a `find /tmp` (`:1033`) and a `beethoven relay` subprocess (`:1135`).
- `wait` and `ask` stay on the login node for as long as they wait. They check files every 0.5 s and call the scheduler only on timeout (`grid/beethoven:486-499`). `relay` is one long-lived process that reads with a 0.25 s timeout and makes no scheduler call (`:689-719`).
- `login_relay.sh` runs `squeue` and `srun` about every 2 s (`grid/login_relay.sh:22,47-52`).
- One refresh of the Beethoven view opens 4 to 5 ssh connections.

hpcworker's rule (`hpcworker:CLAUDE.md:106-111`) reads: "Nothing runs on the login node beyond one `sbatch`, `squeue` or `scancel` per action; … scheduler polling never faster than 60 s from clients (the job writes `status.json`; clients read the file)". The calls above break it as follows:

- `status --json` with its 2N+1 or more `squeue` calls, `diag`, and the long-lived `wait`, `ask` and `relay` processes break the first part.
- `login_relay.sh`'s 2 s `squeue` loop breaks the 60 s floor. It is the only scheduler polling under 60 s found.

The VS Code code does hold to 60 s in one place. The phone status wait asks once a minute, because each status runs one `squeue` (`extension/src/extension.ts:797-798`). The VS Code edition's licence is stricter than hpcworker's rule: among the institution's rules it lists that no process may be run on a login node (`extension/LICENSE.txt:80-81`). Its own `wait`, `ask` and `relay` processes contradict that. Its `CLAUDE.md` states neither the one-call rule nor the 60 s floor.

**Defects seen while reading.** They argue against porting the code as it is.

- **A Claude credential can reach the laptop's Claude through `result`.** This was found by reading the code and was not executed.
  - Neither the relay's `RESULT` handler (`grid/beethoven:701-703`) nor `cmd_result` (`:511-514`) checks the worker name or the request id. Only `cmd_wait` checks the id (`:483`).
  - The MCP tool `beethoven_result` takes `id: z.string()` and passes it on unchanged (`extension/src/mcp/server.ts:152-157`, `gridApi.ts:192-196`, `relay.ts:192-197`).
  - Once any worker has an outbox, the id `../../../claude/.credentials` resolves to `$BEETHOVEN_HOME/claude/.credentials.json`. The relay prints that file on one line, `relay.ts:116-125` parses it as a result, and the tool returns it to the laptop's Claude.
  - This gets past the refusal in `GRID_READ_GUARD` (`gridApi.ts:19-27`), and the ssh fallback takes the same path.
  - It breaks the rule that Beethoven never reads, stores, copies, prints or relays a Claude credential.
- **Worker names and request ids are not checked on the request paths.**
  - Relay `SEND` tests only that `$BEETHOVEN_HOME/workers/$worker` is a directory (`grid/beethoven:696-698`), and `enqueue` does the same (`:467-470`). A worker of `../claude` therefore makes `inbox/` and `outbox/` inside the sign-in folder and writes a request file there. The MCP tools `beethoven_send` and `beethoven_ask` can do that, because they take `worker: z.string()` (`extension/src/mcp/server.ts:112,138`).
  - The CLI and the relay take the first `"id"` match with `grep` (`grid/beethoven:463,695`). The daemon uses `req.id` from `JSON.parse` with no check (`grid/beethovend.js:263,341,423`), and `JSON.parse` keeps the last of two duplicate keys. A crafted request can therefore make the daemon write `<anything>.json` outside its outbox.
  - On the laptop, only the plain-ssh `send` of the CLI forwarders (`gridApi.ts:186`) can carry such a request, because `makeRequest` makes its own id (`extension/src/core/protocol.ts:107`). A worker's own Claude can carry one too.
- **Scratch is never cleaned up.** The worker job's cleanup trap never runs, because the script ends in `exec` (`grid/worker.sbatch.tpl:41,78`). This was checked with bash 5.2.21, not with the grid's bash 4.2. `/dev/shm/${USER}_beethoven_<name>_<job>` is therefore left behind unless the node removes it, which is not yet measured.
- **Unescaped job values, reachable from the laptop's Claude.** This was found by reading and was not executed.
  - Values other than `name` and `hours` reach the job script unescaped through `sed` (`grid/beethoven:385-389,420-423`).
  - `beethoven_worker_start` takes `memory: z.string()` (`extension/src/mcp/server.ts:87,94`), and `workerStartArgs` passes it on as `--mem` without validation (`extension/src/core/slurm.ts:65`).
  - In the rendered job that value lands in `#SBATCH --mem=` and inside double quotes on `grid/worker.sbatch.tpl:39`. A `$(...)` in it would therefore run when the job starts on the compute node.
  - `@CONC@` lands unquoted on the exec line (`grid/worker.sbatch.tpl:81`).
- **Bypass mode.** A request's `bypassPermissions` mode becomes `--dangerously-skip-permissions` (`grid/beethovend.js:311`). The laptop's MCP server offers that mode to the laptop's Claude (`extension/src/mcp/server.ts:109,136`).
- **Prompt on argv.** The prompt is passed on `claude -p`'s argv, so it is visible in the compute node's process table (`grid/beethovend.js:310-318`).
- **Write inside the sign-in folder.** The rate-limit cooldown is written there as `state.json` (`grid/beethovend.js:487-489`).
- **Incomplete destructive refusal.** It checks 5 of the 9 agent markers in `hpcworker:interface/contract/rules.json:26-29` (`grid/beethoven:49-54`). Several paths delete without the check at all:
  - `access init` (`rm -rf … inbox`, `:871`);
  - `access admin reset` (`:943`);
  - `migrate`, which deletes empty placeholder folders with `find … -empty -delete` (`:182-183`) and renames `~/.ashley` aside (`:187-188`);
  - `diag --repair`, which the laptop runs over ssh with no terminal and which can run `access init`, its `rm -rf` included (`:1143`, then `:871`).
- **Broken laptop calls.**
  - `GridApi.result`'s ssh fallback cannot parse the pretty-printed result file (`gridApi.ts:290-303` against `beethovend.js:423`; checked on a copy of the parser).
  - The relay ignores `PENDING` (`relay.ts:90-141`). Each result that is not ready yet therefore waits out the 10 s timeout before it returns nothing (`relay.ts:198-203`). MCP `beethoven_result` has the same wait (`server.ts:155`). The CLI's `latency` loop, meant to poll every 250 ms, can take up to 120 × 10 s (`extension/src/cli/main.ts:251-256`).
- **Dead code.** `GridApi.phoneCode` (`gridApi.ts:149-152`) is never called. If it were called, its `phone code` would hit `die` (`grid/beethoven:974`).

## What hpcworker offers

Paths in this section belong to hpcworker at `e77863c` unless they carry a prefix. hpcworker is at framework 17 (`framework/VERSION`; `framework/bin/hpcworker:76`).

**Published surface.** `interface/INTERFACE.json` lists six exports, each at version 1:

- `contract`: `interface/contract/`, with `cli.json`, `lines.json`, three JSON Schemas, `rules.json` and 29 vectors produced by the real writer.
- `contract-text`: `docs/V11_CONTRACT.md` and `docs/V12_CONTRACT.md`.
- `profiles`.
- `module-schema`.
- `testbed`: a fake scheduler.
- `framework`: the program itself, for a client's opt-in tests only.

`OpenSpineConsortium/beethoven-vscode` is already named as a consumer of `contract`, and of nothing else (`interface/INTERFACE.json:14`, added in `ee936ea` on 2026-10-07). It takes nothing yet. It has no `interface/` folder and no copy pinned with an `ORIGIN`. Instead it carries hand copies at `beethoven-vscode:extension/test-fixtures/hpcworker/hpcw_claude_signin.sh` and `clean_env.txt` ("copied verbatim ... at 503ea71"), and compares them with a checkout named by `HPCWORKER_DIR` (`beethoven-vscode:extension/src/core/credentialEnv.test.ts:3-5,50-60`). Rules 1 and 3 of `hub:INTERFACES.md` refuse both practices.

**What a client may type** (`interface/contract/cli.json`). A client checks every value against its pattern in `cli.json` before placing it (`cli.json:4`). hpcworker then refuses a bad value again on its own side (`bin/hpcworker:1643-1655`; `framework/lib/browser_key.sh:534-575`).

The commands, each run against `<shared_install>/bin/hpcworker`:

- `connect`, with a sign-in mode of `auto`, `always` or `never` (`fresh` is refused) and a permission mode of `default`, `acceptEdits` or `plan`, optionally `--no-chain`. The pasted code arrives on stdin.
- `worker status --json`, `worker stop`, `worker restrict`.
- `claude consent --record`.
- `install --shared`.
- `version`.
- `login-setup`, which only the student types, in their own terminal. Its own help marks it "UNPROVEN ON THE GRID" (`bin/hpcworker:1691-1692`).

The published surface has no way to start a worker with chosen resources:

- `cli.json` has no `worker start`. A client starts a worker only through `connect`, which takes `--name`, `--profile`, `--consent`, `--login`, `--permission-mode` and `--no-chain` (`cli.json:15`; `bin/hpcworker:1637-1642,1671`).
- `worker start --hours/--cpus/--mem/--partition/--qos/--capacity/--requeue/--wait` (`bin/hpcworker:1095-1104`) is not in `cli.json`.
- Neither are `worker watch --json`, `worker list`, `worker log`, `worker guide`, `probe`, `discover`, `profile`, `queue report` or `browser-key`. `cli.json:4` says these are for people at a terminal and may change in any release.

VS Code chooses resources for each worker today, so the plan must say whether `cli.json` grows or VS Code gives that up.

`worker status --json`, typed as a `cli.json` line, has no floor on the server side. The floor defaults to 0 (`bin/hpcworker:1096`; `status_refresh` at `:783,790`), so each call while the worker is queued makes one `squeue`. Only the gate passes `--poll-floor 60` (`browser_key.sh:40,552,564`), and `--poll-floor` is not in `cli.json`.

The gate verbs are what a restricted key's forced command accepts, or what a client passes explicitly as `SSH_ORIGINAL_COMMAND`:

- `version`, `status`, `watch`, `stop`, `restrict`, `forget`.
- `connect`, always run with `-` or a 32-hex installation identifier and `--login never` (`browser_key.sh:573-583`). Desktop always sends `-` (`beethoven-desktop:src/contract.ts:72-74`). The Remote Control answer must therefore already be on record, either in Claude Code's own `remoteDialogSeen` or in a marker file. The Wayne State markers are VS Code's (`framework/profiles/wayne.json:54-57`; `beethoven-vscode:grid/beethoven:599-601`).
- `read`, limited to `status.json`, `connection.json`, `progress.log` and `node`.
- Limits (`browser_key.sh:35-40`): 3 worker names per 7 days; 12 connects per rolling hour, where restricts of a name with no run also count; 2 watches at once. A refusal is `HPCW-GATE limit names|hourly|watch|busy`, exit 123. The limits bind any caller of the gate, including a client that sets `SSH_ORIGINAL_COMMAND` itself, and only `browser-key add` clears the name count (`browser_key.sh:313`).
- `status` also carries hpcworker's own 60 s floor (`browser_key.sh:551-552`).
- Whenever `SSH_ORIGINAL_COMMAND` or `HPCW_GATE` is set, `hpcw_signin_barred` refuses any Claude sign-in (`common.sh:151`; `bin/hpcworker:1306,1342,1436-1439`). A client that drives hpcworker through the gate, as desktop does, can never start a sign-in there. The student must type `claude login` in a plain terminal.

**What a client reads.**

- `lines.json` has these families: `HPCW-STEP` (with failure codes and exits), `HPCW-LOGIN`, the `progress.log` sentences, `HPCW-GATE`, `HPCW-KEY`, `version` and `login-setup`.
- Three schemas:
  - `status.json`: 18 required fields, a closed `state` list, a `claude_login` object that is never a token, and a link pattern that accepts `claude.ai` or `claude.com`, followed by `/code?environment=env_…` or `/session_…` (`status.schema.json:70`).
  - `connection.json`: `session_name`, `environment_url`, `environment_id` and more, with the same two hosts accepted (`connection.schema.json:31`).
  - The `worker status --json` line.
- `rules.json`: the 15 credential variables and 2 Remote Control variables removed from every Claude Code environment; the 9 agent markers; the subscription-only sign-in verdict, with 11 cases. `framework/tests/test_interface.py:199-228` holds the code's own lists to it: `CLEAN_ENV` and `clean_env_args`, `hpcw_agent_env`, and `hpcw_claude_signin`. Two copies of the verdict inside the image are tested with their own cases in `test_cli.py` and `test_login_plain.py`, not against the `signin_cases` of `rules.json`: `LOGIN_SITTING`'s `signin()` (`bin/hpcworker:1269-1272`) and `lib/login_plain.sh:140-152`. A client that runs its own verdict should test it against `rules.json`, as `test_interface.py:222-228` does for `hpcw_claude_signin`.

**What the worker does** (`framework/jobs/worker.sbatch.tpl`, rendered by `hpcw_render`).

- **Partition.** `hpcw_render` picks `partition_cpu_batch` with `qos_batch`, falling back to `partition_cpu`. It sets `--requeue` when that QoS is `requeue` (`framework/lib/profile_sh.sh:79-86`). At Wayne State that is `reqp`/`requeue` (`wayne.json:10-11`). The sign-in sittings use `partition_cpu`, which is `secp`/`secondary` (`bin/hpcworker:1358,1463`). Nothing falls back from `reqp` to `secp`, although VS Code's working context says its workers do that when `reqp` sits pending.
- **Run files.** It writes `status.json`, `progress.log` and `connection.json`.
- **Temp.** It uses node-local temp, with a cleanup trap that does run (`:172-185`).
- **Per-job token.** It mints a mode-0600 per-job token that nothing reads yet (`:189`).
- **Environment.** `CLEAN_ENV` sets it up (`:215-219`).
- **Workspace.** The workspace is fixed at `<shared_state_dir>/workspaces/<name>` (`profile_sh.sh:78`). If there is no `CLAUDE.md` guide there, `worker start` writes one (`bin/hpcworker:1113-1119`; `write_workspace_guide` at `:671`). A `.restricted` marker there makes `connect` refuse (`bin/hpcworker:1664-1667,1195-1202`). VS Code's work folder, and any guide it writes, must be reconciled with this.
- **Sign-in check.** The sign-in is judged every 300 s, and a sign-in that is not a subscription stops Remote Control (`:533`).
- **Sign-in abandon.** A worker that has waited `LOGIN_ABANDON_S` for a Claude sign-in stops itself, cancels its successor and ends the chain with `stop_reason` `login_abandoned` (`:418-446`). Wayne State sets `login_abandon_s` to 1200 (`wayne.json:73`); the default is set at `profile_sh.sh:117` and `framework/lib/profile.py:1066`. The `signin.pending` file that `connect` writes moves that clock (`bin/hpcworker:1673-1676,1685`).
- **Slurm.** Slurm works inside the container when the profile says so (`:200-207`).
- **Remote Control.** `claude remote-control` runs under a pseudo-terminal. It gets `--name`, `--capacity` and `--permission-mode` only when `claude remote-control --help` lists them (`:258-261,298-301`), and a resume with `--continue` leaves out `--capacity` (`:312-320`).
- **Resume.** It adds `--continue` when `connection.json` is younger than `RESUME_WINDOW_S`, which defaults to 14400 s, 4 h (`framework/lib/profile_sh.sh:117`; template `:302-307`). The four hours replaced seven days on purpose, following Anthropic's statement that a session can be resumed "for about four hours" (`framework/README.md:1087-1088`; `docs/V11_CONTRACT.md:886`). The job's own preempted message also says four hours (`:415`). The seven days at `CLAUDE.md:265` is stale text.
- **The always-on chain.** At job start, `arm_chain` queues exactly one successor with `afterany:<job>,singleton` (`framework/lib/adapters/slurm.sh:49-54`; template `:265-285`). A stop file ends the chain.
- **Stop.** `worker stop` touches the stop file, waits up to 45 s for `stop.done`, then makes one `squeue` and one `scancel` (`bin/hpcworker:681-725`).
- **Deletion.** The only recursive delete is `hpcw_rm_own_tmp` (`framework/lib/adapters/common.sh:115-129`), which refuses any path whose last component is not `hpcworker_*` or `hpcw_*`. Beyond it, hpcworker removes single control files it made in the run directory (`stop`, `stop.done`, `next.id`, `node` and `job.key`), its lock and watch-slot folders, and, on `login-setup --remove` or a browser-key expiry, its own key files and its lines in `~/.ssh`. It never deletes the sign-in folder, the workspace or anything else under `$HOME`.
- **Claude sign-in.** There are three ways in:
  - `claude login`, which runs `LOGIN_SITTING` in a 30-minute allocation: `claude auth login`, the verdict, then `claude remote-control` once, only if the Remote Control answer is not yet on record (`bin/hpcworker:1264-1292,1445-1471`, the record check at `:1287-1291`);
  - `claude login --plain`;
  - `connect`'s relay of `HPCW-LOGIN` lines.

  `claude auth logout` is never run.

**The shared copy and the profiles.**

- `install --shared` gives `~/.hpcworker` a launcher, a marker and the profile, and copies no code (`bin/hpcworker:379-520`).
  - A copy of the account's own code is moved to `~/.hpcworker/replaced/<time>/` (`bin/hpcworker:443-447,510`).
  - `profile.json` is kept unless `--force` is given. `--force` overwrites it and refuses under an agent (`:466,566`).
  - Install also writes a managed `# >>> hpcworker` block into `~/.bashrc` unless `--no-shell-path` is given (`:359-377,571`). It describes that block as working "the way the grid command of Beethoven for VS Code does it". VS Code's grid script keeps a separate `# >>> beethoven` block (`beethoven-vscode:grid/beethoven:196-198,992-998`), so after the move both can exist in one `~/.bashrc`.
- `tools/deploy_shared.sh` publishes `v<N>` beside the older versions and switches `current`, never back below 11. Folders are 2555, and files 0444 except `bin/*` and `*.sbatch` at 0555 (`deploy_shared.sh:59-61`). The root is 2755 and `deploy.log` is 0644.
- Who may enter is decided by the volume-root ACL that `tools/grid_access.sh` keeps equal to `admin.mjs roster`. That roster holds the extension grant only (`tools/grid_access.sh:26-31`), and the tool removes every named entry that is neither on the roster nor a reader (`:67-69,417`).
- The Wayne State profile (`framework/profiles/wayne.json`) names:
  - the partitions;
  - the state folder `/rs/rs_grp_oschome/$USER/hpcworker` (`:22`) and the shared install (`:23`);
  - the shared image `…/containers/claude-node22` and the `claude_bin` (`:27-31`);
  - `claude_config_dir` `$HOME/.beethoven/claude` (`:53`);
  - `consent_markers`, which are VS Code's own two marker files (`:54-57`);
  - the ssh host and its pinned host key (`:68-71`);
  - the login-node rules (`:74-77`);
  - worker defaults of 2 CPUs, 8G, 8 h, permission mode `default` and capacity 4 (`:81-87`).

  The image is the sandbox shared with Beethoven for VS Code, and `claude_config_dir` is VS Code's sign-in folder (`:27-31,53,88`). The two editions therefore already share the image and the sign-in folder.
- Profiles are composed from beethoven-sites modules and are never edited by hand.

**What hpcworker does not have.**

- No request channel: no `send`, `wait`, `ask` or `result`, and no `claude -p`.
- No `--account` for several Claude accounts; there is one sign-in folder per profile.
- No licence check, by design.
- No `uninstall`.
- No GPU support: the profile names GPU partitions, but nothing sets `HPCW_NV` (`common.sh:322,333` only read it).
- `diag --json` exists (`bin/hpcworker:2172-2276`) but is not in `cli.json`.
- `worker list` prints text only (`:1236-1239`).
- No deliberate way to hand the worker a token: no store, no flag, no file. Even so, whatever the submitting shell exports reaches Claude Code, minus the 17 stripped names. No `--export=NONE` or `--cleanenv` is used (`slurm.sh:45`; `common.sh:333`; `worker.sbatch.tpl:215-219`), and the successor inherits the job's environment minus the per-node variables (`worker.sbatch.tpl:272-274`). Whether this happens on the grid is not yet measured.

Which framework version is live on the grid is not established. `docs/guides/LAB_LEAD.md:54` says 10, `docs/V12_STATUS.md:560` says 13 is not deployed, and commit `0c51fb6` records v15 published on 2026-10-03.

**How the browser and desktop editions use it.** Both follow the hub's standard (`hub:INTERFACES.md`). They pin exports with an `ORIGIN`, using their own `interface/pull.sh` through `gh` from a commit on `main`. They keep one hand-typed contract module whose builders throw on a bad value. A conformance test runs every vector through the real readers and holds every constant equal to the pinned export. A boundary test enforces rules 1 to 3, and an opt-in lane runs the pinned framework behind the testbed.

The two differ in transport:

- **Browser** (beethoven-extension):
  - pins `profiles`, `contract`, `contract-text`, `framework` and `testbed` at `e77863c`;
  - types `connect` with `exec` into an interactive Shell session of Open OnDemand, unframed (`beethoven-extension:extension/src/core/shell.ts:323-330`; `extension/src/core/contract.ts:282-285`);
  - types every other `cli.json` line as one framed line through `runShellCommand` (`shell.ts:105-111,479-482`);
  - on its direct way, sends gate verbs over ssh through its native bridge, with a restricted key;
  - runs the Claude sign-in as a `connect --login auto|always` sitting the student sees;
  - floors are 60 s for the scheduler and status, and 15 s for the shell (`beethoven-extension:extension/src/core/audit.ts:47-55`).
- **Desktop** (beethoven-desktop):
  - pins the same exports at `ee08fa1`, an ancestor of `e77863c`, plus beethoven-agents' `registry`. That pin is effectively current: `git diff ee08fa1 e77863c` touches no exported path, only `tools/grid_access*`, `LAB_LEAD.md` and tests;
  - uses the student's own OpenSSH with a kept ControlMaster, and every call is `env SSH_ORIGINAL_COMMAND='<verb>' bash '<shared>/bin/hpcworker' gate` (`beethoven-desktop:src/contract.ts:79-84`). It is therefore bound by the gate's limits and by the sign-in bar above;
  - floors are 60 s for status, 60 s for start and stop, and 5 s for reads, with one ssh at a time (`beethoven-desktop:src/grid.ts:23-25`; `src/ssh.ts:227-235`);
  - pins the host key from the profile and never trusts on first use (`src/ssh.ts:237-293`);
  - never runs a Claude sign-in itself; it prints `bash <shared>/bin/hpcworker claude login` for the student to type (`src/tools.ts:74-77`);
  - reads every worker's `status.json` and the workspace through a read-only sftp client (`src/runs.ts`; `src/grid.ts:327-354`).

Desktop is the closest model for VS Code: the same OpenSSH, an MCP server, and a student who already has an ssh sign-in.

## Side by side

Each row puts one thing VS Code does on the grid today beside what hpcworker has for it. Fit is *same*, *close*, *missing* or *hpcworker only*.

How to read the citations:

- In the VS Code column, a bare `:N` means `grid/beethoven:N` in beethoven-vscode. Other paths there are also beethoven-vscode's.
- In the hpcworker column, paths are hpcworker's. `wayne.json` is `framework/profiles/wayne.json`, `common.sh` is `framework/lib/adapters/common.sh`, `slurm.sh` is `framework/lib/adapters/slurm.sh` and `worker.sbatch.tpl` is `framework/jobs/worker.sbatch.tpl`. Paths that start with `bin/`, `jobs/` or `lib/` are under `framework/`. `cli.json` is `interface/contract/cli.json` and `rules.json` is `interface/contract/rules.json`.
- In the Note column, a bare `:N` and any `grid/` path are beethoven-vscode's. The short hpcworker names above are hpcworker's. Any other path is given with the name of its repository.

| VS Code today | hpcworker today | Fit | Note |
| --- | --- | --- | --- |
| scp of `grid/*` into `~/.beethoven/bin`, then `beethoven install` (`extension/src/core/wizard.ts:738,750`) | `install --shared`: launcher, marker and profile, no code copied (cli.json `install-shared`; `bin/hpcworker:379-520`) | close | This is the heart of the move. It needs the student on the grid's approved list. |
| Layout `~/.beethoven/{bin,log,accounts,workers,sessions}` (`:222`), `config.env` (`:34`), `READY` (`:141`), ROOT `/rs/rs_grp_oschome/$USER/beethoven`, else `$HOME/beethoven` (`:67-70`, set at `:230-233`) | `~/.hpcworker` and the state folder `/rs/rs_grp_oschome/$USER/hpcworker` (`wayne.json:22`) | close | The two layouts are in different places. Both editions use the same sign-in folder, `~/.beethoven/claude` (`:38`; `wayne.json:53`), so nothing has to move. The workspaces are in different trees. VS Code's are `ROOT/workspaces/<session>` (`grid/beethovend.js:507`) and `ROOT/workspaces/phone` (`grid/phone.js:89`). hpcworker's are `workspaces/<name>` under its state folder (`bin/hpcworker:1111`), and it writes a `CLAUDE.md` guide there (`bin/hpcworker:671-680`). Files do not need to move, but hpcworker's `--continue` and its trust seeding apply only to its own workspace (`worker.sbatch.tpl:294-297,302-307`). How a VS Code session in another folder carries over is not yet measured. |
| `.bashrc` block, the PATH line (`grid/bashrc.block:8`) | `shell_path_block`, PATH to `~/.hpcworker/bin` (`bin/hpcworker:359-377`) | same | `install --shared` writes this block too. `cmd_install` runs `shell_path_block` whenever its home is `~/.hpcworker`, and the `install-shared` line has no `--no-shell-path` (`bin/hpcworker:571`; `cli.json:20`). A student who moves therefore ends up with both managed blocks. They can coexist because their marker patterns do not overlap (`:198` against `bin/hpcworker:359-360,366`). |
| `.bashrc` block, VS Code server sysroot exports (`grid/bashrc.block:4-6`) | none | missing | This is site data. It belongs in a beethoven-sites field that hpcworker's block writes. |
| `migrate`: `~/.ashley` to `~/.beethoven`, run first by every `install` (`:150-191,220`) | none. hpcworker never creates or moves `~/.ashley`; it names it only to refuse deleting it (`common.sh:121`) | missing | The move is only for accounts still on `~/.ashley` (grid scripts older than 7). How many such accounts exist is not yet measured. `install` also creates `~/.ashley -> .beethoven` for every new account (`:160-161`), which hpcworker never does. That link matters only to builds up to 7.0.0. |
| `adopt` a container from the lab's `library.json`, binding the whole lab folder `/rs/rs_grp_oschome/shared` (`:79,124-143`) | the profile's `image_store`, `claude_bin` and `binds` (`wayne.json:27-36`) | close | Each profile names one image. A library entry named `claude-node22` published by `library publish` would land exactly at the profile's two paths. The build puts the sandbox at `$ROOT/containers/$LIB_NAME` and the npm prefix at `$ROOT/npm-$LIB_NAME` (`grid/bootstrap.sbatch:24-39`), with ROOT set to the lab's `shared/beethoven` (`:119`). That matches `wayne.json:29,31`, and the profile says its image is the sandbox shared with Beethoven for VS Code (`wayne.json:88`). The one thing not yet measured is the `default` value in `library.json`, which is on the grid and in neither repository. The binds differ. VS Code binds the whole lab folder for "containers, datasets, software" (`:139`). The Wayne State profile binds only `/rs/rs_grp_oschome/shared/beethoven`, plus `$HOME` and `/rs/rs_grp_oschome/$USER` (`wayne.json:32-36`). A student who moves loses the lab's shared datasets and software inside the worker unless a beethoven-sites field adds that bind. |
| `worker start --container NAME` (`:411-417`) | none | missing | This is the choice of image per worker. |
| `bootstrap`: a per-student image build (`grid/bootstrap.sbatch`) | none for students. `jobs/build_image.sbatch` is for a site that has no image, and it has never run on a real cluster (`jobs/build_image.sbatch:2-4`) | missing | Drop. The lab's shared image is the 2026-09-29 decision. |
| `library publish` (admin), which submits `grid/bootstrap.sbatch` as a library build (`:119`) | none | missing | This is lab tooling. If it is kept, it goes to hpcworker's `tools/`. |
| `status --json`, the overall state (`:335-359`) | `worker status --json` per worker; gate `status` (worker-status schema) | close | hpcworker has no overall line. It does not report the quota, the token names, the licence fingerprint, the account's whole `squeue` job list (`jobs_json`, `:324-330`), the bootstrap, container and library state, `awaiting_access`, the accounts with their cooldown, or `claude_dir` (`:347-350`). In VS Code, `status`, `worker start` and `diag --repair` also adopt the library container as a side effect (`:338,395,1083`). |
| `doctor` and `diag --json [--repair] [--node]` with `grid.*` ids (`:361-380,1001-1157`) | `diag [--json]` with `hpcw.*` ids (`bin/hpcworker:2172-2276`), not in `cli.json`, no repair | close | This needs a contract entry, and the browser extension already types `diag --json` without one (beethoven-extension `extension/src/core/contract.ts:263`). The VS Code graph needs a diagnostic node per feature. VS Code's `diag` also makes network calls from the login node: it curls `https://api.anthropic.com/` (`:1028`), runs `verify-tokens` (`:1045`) and opens the prompt relay (`:1135`). Its `--repair` changes things over ssh with no terminal and without `refuse_destructive_from_agent`. It runs `install` (`:1015,1019`) and `worker restart` (`:1130`). For the admin it also runs `access init` (`:1143`), which deletes `$ACCESS_ROOT/inbox` with `rm -rf` (`:871`) and runs `chmod -R` over the lab folder (`:865-867`). Neither the network calls nor this repair is allowed under hpcworker's rules. |
| `diag-node`: a probe inside a running worker's allocation (`:1158-1166`) | `probe`: a 10-minute job writing `probe.json` (`bin/hpcworker:633-660`) | close | `probe` is not in `cli.json`, but the browser extension already types it (beethoven-extension `extension/src/core/contract.ts:257`). |
| `worker start` with hours, CPUs, memory, partition and QoS (`:393-426`) | `connect` takes name, site, consent, sign-in mode, permission mode and chain. `worker start --hours --cpus --mem` exists but is not in `cli.json`. | close | Resources chosen by the client need a contract change. The browser extension already types `worker start --name … --permission-mode …`, which `cli.json` does not list (beethoven-extension `extension/src/core/contract.ts:259`). The defaults also differ. VS Code uses 24 h, 4 CPUs and 16G on `reqp`/`requeue` with concurrency 2 (`:384`). hpcworker's Wayne State profile uses 8 h, 2 CPUs and 8G, with permission mode `default` and capacity 4 (`wayne.json:81-87`). |
| `--gpus N`, giving `--gres=gpu:N` and `--nv` (`:409`; `grid/worker.sbatch.tpl:72`) | GPU partitions in the profile (`lib/profile.py:77`), named only in the workspace guide's text (`lib/profile.py:1150-1154`). There is no `--gres` anywhere. `HPCW_NV` is read but never set (`common.sh:322,333`) | missing | hpcworker has no GPU support of any kind. Both a GPU request in the job header and `--nv` are missing. |
| `--concurrency K`: parallel `claude -p` requests (`grid/beethovend.js:33,247`) | Remote Control `--capacity` (`worker.sbatch.tpl:298-301`; profile capacity 4) | close | This is the same idea for a different payload. hpcworker adds `--capacity` only when `remote-control --help` lists it (`worker.sbatch.tpl:258-262,299-301`). It leaves the flag out whenever `--continue` is passed (`worker.sbatch.tpl:312-320`). What capacity a resumed session runs with is not yet measured. |
| `worker restart`: scancel, re-render, sbatch (`:427-437`) | stop, then connect; the chain renews by itself | close | VS Code's `diag --repair` also restarts a worker that is running but whose daemon has gone silent (`:1099-1100,1130`; beethoven-vscode `extension/src/vscode/diagNodes.ts:403-410`). That is the client's only automatic restart. |
| `worker stop`: stop file and an immediate `scancel` (`:438-443`) | `worker stop` and gate `stop`: stop file, up to 45 s for `stop.done`, then one `scancel` (`bin/hpcworker:681-725`) | same | hpcworker's stop is gentler. |
| `worker list --json` (`:444-446`) | `worker list` prints text (`bin/hpcworker:1236-1239`); desktop reads every `status.json` over sftp | close | Follow desktop. |
| `worker log` (`:447-452`) | `worker log` (rc.log and job output); gate `read <name> progress.log` | close |  |
| `worker node` (`:453-455`) | `node` in `status.json`; gate `read <name> node` | same | This feeds Remote-SSH. |
| End of wall time: nothing queues a successor. The job carries `--dependency=singleton` (`grid/worker.sbatch.tpl:18`). It also carries `--requeue` only under QoS requeue (`grid/worker.sbatch.tpl:20`, filled by `:408-410`). Per Slurm's documentation, `--requeue` covers preemption and node failure, not the time limit. | Always-on chain: `afterany:<job>,singleton`, ended by a stop file (`slurm.sh:49-54`; `worker.sbatch.tpl:265-285`) | same | hpcworker has more here, and VS Code gains it. |
| `/dev/shm` scratch with an EXIT trap that never runs (`grid/worker.sbatch.tpl:40-42,78`) | Node-local temp with a trap that runs (`worker.sbatch.tpl:172-185`) | same | hpcworker has it right. |
| Slurm inside the container through wrappers (`grid/worker.sbatch.tpl:49-71`) | `scheduler_in_worker` (`worker.sbatch.tpl:200-207`; `wayne.json:79`) | same |  |
| Remote-SSH to the worker's node, ProxyJump through the login node (`extension/src/extension.ts:448-499`; `extension/src/core/sshConfig.ts:58-65`) | the node in `status.json`; nothing about the VS Code server | close | This is on the client side. It needs the sysroot row. |
| `send`: an inbox file (`:466-479`) | none | missing |  |
| `wait`, `ask --stream`, `result`, `tail` (`:480-520`) | none | missing | `wait` loops every 0.5 s on the login node. The nearest thing in hpcworker is `worker watch` (and the gate's `watch`). It reads the run's files every 5 s and asks the scheduler at most once a minute (`bin/hpcworker:954-957,1190-1194`; `cli.json:29`). |
| `relay`: one ssh session with a 0.25 s loop on the login node (`:676-721`) | none | missing | It cannot move as built, because it breaks the login-node etiquette. |
| `beethovend.js`: one `claude -p` per request, stream-json events and a result file (`grid/beethovend.js:8-9,242-424`) | none; the worker runs only `claude remote-control` | missing | This is the largest gap. |
| Permission modes including `bypassPermissions`, which becomes `--dangerously-skip-permissions` (`grid/beethovend.js:311`) | `default`, `acceptEdits`, `plan` (`cli.json`) | missing | Recommended: never offer `bypassPermissions`. VS Code's `-p` requests default to `acceptEdits` (`grid/beethovend.js:312`; beethoven-vscode `extension/src/mcp/server.ts:109,136`). |
| Named sessions resumed with `--resume`; `sessions --json` (`grid/beethovend.js:492-519`) | Remote Control `--continue` when `connection.json` is younger than `RESUME_WINDOW_S`, 4 h by default, tried once per job (`worker.sbatch.tpl:302-307,526`; `lib/profile_sh.sh:117`; `lib/profile.py:1064`) | missing | Named sessions are missing for `-p` requests. hpcworker's `CLAUDE.md` says the resume window is seven days, but the code uses 4 h. |
| A 6 h cap per request (`grid/beethovend.js:63`) | none | missing |  |
| Rate-limit cooldown in `~/.beethoven/claude/state.json`; a `rate_limited` result (`grid/beethovend.js:379-389,487-489`) | none | missing | No new version may write inside the sign-in folder. VS Code writes there today: `state.json` (`grid/beethovend.js:488`), the two consent markers (`:664`), and `chmod 700` on the folder itself (`:562`). It also checks in many places whether `.credentials.json` exists and is non-empty, without reading it (`:313,350,374,667,963`; `grid/beethovend.js:212,471`, the first while watching the folder). hpcworker checks only that the folder exists (`bin/hpcworker:1495,2246`). |
| Peer note: hand-off to another worker through `beethoven send` (`grid/beethovend.js:426-450`) | the workspace guide, which mentions no peers (`jobs/workspace-guide.md.tpl`) | missing |  |
| `BEETHOVEN_REQUEST_ID` and `BEETHOVEN_WORKER` set per request (`grid/beethovend.js:325-333`) | read as agent markers (`common.sh:137-140`); the job sets `HPCW_JOB` and `HPCW_SITE` | close | A request channel would set them. |
| `phone on`, `off`, `status`; `phone.js` runs `claude remote-control` without flags and writes `rc/status.json` with `session_url` (`:952-976`; `grid/phone.js:117-176`) | The worker is Remote Control: `--name`, `--capacity`, `--permission-mode`, `--continue`; `status.json` and `connection.json` with `environment_url` | close | hpcworker has more. |
| One Remote Control host per sign-in, through the `host.lock` lease (`grid/phone.js:23-27,105-106,223-268`) | none | missing | Both editions use one sign-in folder, `~/.beethoven/claude` (`:38`; `grid/beethovend.js:51`; `wayne.json:53`), and nothing coordinates their Remote Control hosts. hpcworker's workers cannot see VS Code's lease. hpcworker itself runs several named workers on one sign-in with no lease; its gate allows 3 names (`cli.json:36`). hpcworker's `framework/README.md:1766-1767` lists two Remote Control hosts on one login as not verified. Whether a lease is needed is not yet measured. |
| Consent prompt answered `y` from the record (`grid/phone.js:184-193`) | `rc_send y` from the record (`worker.sbatch.tpl:352-353,464`) | same |  |
| `claude login`: `srun --overlap` into a running worker's allocation, else a 30-minute `secp` allocation; `auth login`, the verdict, `remote-control` once (`:559-651`) | `claude login`: `LOGIN_SITTING` in a new 30-minute allocation, the same three steps (`bin/hpcworker:1264-1292,1445-1471`) | close | hpcworker never reuses a worker's allocation. It asks for a new 30-minute one each time, or 20 minutes under `--plain` (`bin/hpcworker:1358,1462-1463`). For an account that is not set up yet, it first sets the account up for the shared copy (`bin/hpcworker:1392-1414,1440`). `claude login` is not in `cli.json`, yet clients already use it. The browser extension types `claude login` and `claude login --plain` (beethoven-extension `extension/src/core/contract.ts:269,277`). The desktop edition prints `bash <shared>/bin/hpcworker claude login` for the student to type (beethoven-desktop `src/tools.ts:75-77`). It must be listed before VS Code opens it in a terminal. |
| `claude remote-consent`; marker files inside the sign-in folder (`:601,652-665`) | `claude consent` puts Remote Control's question to the student in a 30-minute allocation. If Claude Code did not record the answer, it asks the student and, on y, writes the fallback marker `~/.hpcworker/consent` (`bin/hpcworker:1472-1492`). `claude login` asks the question in the same sitting (`LOGIN_SITTING`, `bin/hpcworker:1286-1292`). The Wayne State profile also counts VS Code's two marker files (`wayne.json:54-57`). | same | Consent carries over, because both editions read the same sign-in folder. The browser extension types `claude consent`, which `cli.json` does not list; it lists only `claude consent --record` (`cli.json:19`). The extension still calls `claude consent` an alias that explains (beethoven-extension `extension/src/core/contract.ts:278-279`), which is out of date. |
| `claude status --json` (`:666-669`) | `claude status`; `claude_login` and `needs` in `status.json` | close |  |
| `claude forget` refuses (`:670-671`) | no sign-out anywhere; `claude auth logout` is never run | same |  |
| `signin-kind` (`:585-597`) | `hpcw_claude_signin`, following `rules.json` `subscription_signin` | same |  |
| Strips 15 credential and 2 Remote Control variables in `claude_in_alloc` (`:576-582`) | the same 15 + 2 names, written out in `worker.sbatch.tpl:215-219` and `bin/hpcworker:345-349`, which `framework/tests/test_interface.py` holds equal to `rules.json:5-25` | same | VS Code's other two processes use different environments. `beethovend.js` deletes the 15 credential variables (`grid/beethovend.js:339`) but sets `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1` and `DISABLE_TELEMETRY=1` (`grid/beethovend.js:323-324`). `phone.js` deletes both Remote Control switches (`grid/phone.js:131-132`). hpcworker already names beethoven-vscode as a consumer of its `contract` export (hpcworker `interface/INTERFACE.json:14`; `interface/README.md:11`). VS Code does not use a pinned `rules.json`. It checks its list against a fixture copy (beethoven-vscode `extension/test-fixtures/hpcworker/clean_env.txt`) and, when `HPCWORKER_DIR` is set, against another checkout's `worker.sbatch.tpl` (beethoven-vscode `extension/src/core/credentialEnv.test.ts:50-68`). The plan must say how VS Code takes the export. |
| Destructive refusal on 5 agent markers (`:49-54`) | 9 markers (`rules.json:26-29`) | close | VS Code is four markers short. |
| `accounts list` reports whether the Claude sign-in is present, and its cooldown (`:310-317,545`). `accounts remove --yes` removes the old API-key file (`:548-553`). `retire_apikey` (`:537-541`) runs on every install and worker start. | none | missing | Drop `accounts remove`: the key has been unused since 5.0.0. What `accounts list` reports is covered by the `claude status` row and the cooldown row. |
| `secrets.env` (GitHub, Hugging Face) passed into `claude -p`'s environment (`grid/beethovend.js:163,320`; `wizard.ts:661-665`) | none | missing | Decision for greg. |
| `verify-tokens`: `curl` from the login node (`:1168-1181`) | none | missing | Drop: no network calls from the login node. `diag` runs it too (`:1045`). |
| Licence: `worker start` refuses without `license.key`, and the daemon verifies it every 60 s (`:400`; `grid/beethovend.js:78-106`) | none, by design | missing | Drop on the grid. |
| `access whoami`, `status`, `requirements`, `request`: held `sbatch --hold` jobs (`:877-914`) | the approved list: the root ACL, kept equal to `admin.mjs roster` by `tools/grid_access.sh` | missing | This is a different system. Decision for greg. VS Code refuses a lab access request unless both tokens pass the login-node check (`access requirements`, `:891-893,910`), so these access rows depend on `secrets.env`. |
| `access init` and `access admin …`: `setfacl`, `rm -rf $ACCESS_ROOT/inbox` (`:849-947`) | `tools/grid_access.sh`, the maintainer's tool | missing | Drop. `diag --repair` also runs `access init` for the admin (`:1143`). |
| `uninstall --yes` (`:1182-1216`) | none | missing | Decision for greg. |
| `version` (`:1243`) | `version` (`cli.json`; `lines.json` version family) | same |  |
| Direct login-node lines: `squeue` (also used by the Connect picker and the Grid status command, `extension/src/extension.ts:464,617`), plus `sbatch`, `head -c` and `ls -la` for the MCP tools (`extension/src/core/gridApi.ts:19-26,99-103,268-282`; `extension/src/mcp/server.ts:174-198`) | none in `cli.json`; desktop reads the workspace over read-only sftp | missing | Decision for greg. |
| `authorized_keys` line installed with the student's password and code (`extension/src/core/sshInstall.ts:27-28,83`) | `login-setup` (a different job); `browser-key add` (not in `cli.json`) | close | Close in purpose only: both are client transport, like desktop's ssh sign-in. In what the key allows, they are not equivalent. VS Code appends an unrestricted line with no `from=`, `command=` or `restrict` (beethoven-vscode `extension/src/core/sshInstall.ts:27-28`), which opens a full shell from anywhere. hpcworker's browser key is forced to `restrict,command="<root>/bin/hpcworker gate"` (`bin/hpcworker:2199`). Its login-setup key carries `from="..."` and no agent, port or X11 forwarding (`bin/hpcworker:1760`). |
| `grid/login_relay.sh` (`:22-66`) | connect's `HPCW-LOGIN` relay; `claude login --plain` | close | Retire. |
| none | `worker watch` and the gate's `watch` (`cli.json:29`; `bin/hpcworker:1190-1194`); `worker restrict` (`cli.json:18`); `worker guide`; `discover`; `queue report` (`bin/hpcworker:2117-2124`); `profile`; `claude consent --record` (`cli.json:19`); the gate's `forget` (`cli.json:34`) | hpcworker only | No row above uses these commands. `worker watch` is the nearest thing to VS Code's `wait`. The browser extension already types `discover`, which `cli.json` does not list (beethoven-extension `extension/src/core/contract.ts:254-255`). |

## What hpcworker lacks today

**What hpcworker would need to gain.**

Every change below to `cli.json`, a gate verb or a schema regenerates the real-writer vectors with `python3 framework/tests/vectors.py --write` in the same pull request. When a client must act, it also raises the version of the `contract` export, which is 1 today (`hpcworker:interface/INTERFACE.json`). Without both, `test_interface.py` fails. The browser and desktop then re-pin the export in pull requests of their own. This applies to items 1, 2, 4, 5 and 7.

1. **A request channel.** This is the largest gap.
   - **Why VS Code needs it.** The Ask command and the MCP tools `beethoven_ask`, `beethoven_send`, `beethoven_result` and `beethoven_sessions` let the laptop's Claude Code hand work to the grid worker and stream the answer back (`beethoven-vscode:extension/src/mcp/server.ts:99-165`).
   - **What a request carries today.** The daemon passes `--max-turns`, `--model`, `--allowedTools` and `--append-system-prompt`, which adds a note about the worker's peers. It starts a session's first turn with `--session-id <uuid>`, so the id is known even if the run dies (`beethoven-vscode:grid/beethovend.js:310-318`; `beethoven-vscode:docs/ARCHITECTURE.md:115-117`). The MCP tools expose `max_turns` and `model` (`beethoven-vscode:extension/src/mcp/server.ts:110,113`). The request schema needs these fields, or a decision to drop them.
   - **Existing sessions.** VS Code keeps its sessions in `~/.beethoven/sessions/<name>.json`. Each is bound to its cwd, which by default is `ROOT/workspaces/<session>` (`beethoven-vscode:grid/beethovend.js:492-518`). Claude Code resumes a session only from the running config folder's `projects/` for that cwd (`beethoven-vscode:docs/ARCHITECTURE.md:113-120`). hpcworker's workspace is `<state_dir>/workspaces/<worker>` (`hpcworker:framework/bin/hpcworker:325`). The new channel must honour a request's cwd and read the old session map, or those conversations stop resuming.
   - **What it replaces.** When a window is spent, VS Code's daemon writes `state.json` inside the sign-in folder (`CLAUDE_HOME`) (`beethoven-vscode:grid/beethovend.js:472,487-488`). That breaks VS Code's own rule, and the bullet below about the sign-in folder replaces it.
   - **Where it is built.** hpcworker, as a second payload in the worker job beside Remote Control. It would have:
     - request, event and result files under the run folder, each with a JSON Schema and real-writer vectors;
     - one `claude -p` per request inside `CLEAN_ENV`, with the prompt on stdin rather than argv;
     - permission modes from `cli.json`'s list only, so no `--dangerously-skip-permissions`;
     - named sessions resumed with `--resume`, in the cwd the request names;
     - a concurrency cap and a wall-time cap per request;
     - a `rate_limited` result carrying the reset time, with no file written inside the sign-in folder;
     - `BEETHOVEN_REQUEST_ID` and `BEETHOVEN_WORKER` set, so the destructive refusals still hold.
   - **Transport.** It cannot be the relay's 0.25 s loop on the login node (`beethoven-vscode:grid/beethoven:684-690`). It also cannot be the 0.5 s loop of `ask` and `wait` (`beethoven-vscode:grid/beethoven:480-510`), which VS Code falls back to (`beethoven-vscode:extension/src/core/gridApi.ts:226`).
     - **Gate verbs.** One verb would send a request on stdin. Another would read a result, or new event bytes from an offset, with a read floor that the gate itself enforces.
     - **No read floor exists today.** The gate's `read` answers at once, as often as it is asked (`hpcworker:framework/lib/browser_key.sh:584`). The gate's only floor, 60 s, applies to `status` and `watch` (`hpcworker:framework/lib/browser_key.sh:39,552,564`). Desktop's 5 s floor is enforced by the client (`beethoven-desktop:src/grid.ts:25`). At a 5 s floor a first event can take up to 5 s to arrive, against the relay's 0.19 s.
     - **`read` cannot carry these files today.** It accepts four fixed names: `status.json`, `connection.json`, `progress.log` and `node` (`hpcworker:interface/contract/cli.json:12`). It refuses any file over 256 KB except `progress.log`, which it tails (`hpcworker:framework/lib/browser_key.sh:31,436`). Results larger than that would need a size rule.
     - **Caps.** The gate allows 3 worker names per key, 12 connects per hour and 2 watches at once (`hpcworker:interface/contract/cli.json:36`; `hpcworker:framework/lib/browser_key.sh:34-39`). A working session sends many requests an hour, so the request verbs need caps of their own.
     - **Reading on the compute node.** The other option is to read the files on the compute node over the ProxyJump hop through the login node's sshd, which VS Code already uses for Remote-SSH (`beethoven-vscode:extension/src/core/sshConfig.ts:58-64`). This runs no process of ours on the login node, but the traffic still passes through it.
     - **Speed.** On 2026-09-28 the relay measured 0.19 s, and a fresh ssh to a compute node measured about 25 s (`beethoven-vscode:docs/ARCHITECTURE.md:75-109`, line 89 for the ssh figure). How fast the gate verbs are, and how fast reads are over a kept (multiplexed) node connection, is not yet measured.
   - **Other editions.** Desktop would benefit directly: its MCP server could hand a task to the worker the same way. The browser would not, since it opens claude.ai.
2. **Resources and GPUs chosen by the client on `connect`.**
   - **Why VS Code needs it.**
     - For each start, VS Code asks for the hours and whether to use a CPU node or one GPU (`beethoven-vscode:extension/src/extension.ts:501-538`).
     - CPUs, memory, partition and QoS are settings, with defaults of 4, 16G, `reqp`/`requeue` and 24 h (`beethoven-vscode:extension/package.json:366-405`). The `beethoven.worker.gpu` setting is declared there, but no code reads it.
     - A GPU sets partition `gmsap,gvohp,galhp` and QoS `gpu` (`beethoven-vscode:extension/src/core/slurm.ts:69-71`).
     - The MCP tool takes hours, CPUs, memory, QoS and up to 4 GPUs, but hard-codes partition `reqp` (`beethoven-vscode:extension/src/mcp/server.ts:83-94`).
   - **What hpcworker has.**
     - `connect` takes none of these options (`hpcworker:framework/bin/hpcworker:1638-1641`).
     - `worker start`, which `connect` calls (`hpcworker:framework/bin/hpcworker:1671-1672`), already takes `--hours`, `--cpus`, `--mem`, `--partition` and `--qos` (`hpcworker:framework/bin/hpcworker:1095-1097`). For CPU resources, then, the gap is passing the options through and listing them in the contract.
     - GPUs are absent everywhere.
     - The Wayne State defaults are 2 CPUs, 8G and 8 h (`hpcworker:framework/profiles/wayne.json:81-87`), against VS Code's 4, 16G and 24 h (`beethoven-vscode:grid/beethoven:384`). hpcworker's worker renews itself every 8 h through a chained successor (`hpcworker:framework/jobs/worker.sbatch.tpl:266-277`), while VS Code's job ends at its hours unless the student restarts it. The difference that matters is CPUs and memory per job, not how long the worker lasts.
   - **Where it is built.** hpcworker:
     - new options on `connect` and on the gate's `connect`, passed through to `worker start`, each with a pattern in `cli.json`;
     - `--gpus` on both `connect` and `worker start`;
     - `HPCW_NV=--nv` exported in `in_image.sh` when GPUs are asked for (`hpcworker:framework/jobs/worker.sbatch.tpl:223`). `hpcw_runtime_exec` already reads it (`hpcworker:framework/lib/adapters/common.sh:322,333`), but nothing exports it today;
     - the GPU line (Slurm's `--gres=gpu:N` and the PBS and LSF forms) in both job-header renderers, which must agree (`hpcworker:framework/lib/profile_sh.sh:119-141`; `hpcworker:framework/lib/profile.py:908-930`);
     - new profile fields for the maximum CPUs, memory, hours and GPUs and for a GPU QoS, defined in `profile.py` and filled in through beethoven-sites as in item 3. "Bounded by the profile" has nothing to bound with today. The only bound field, `max_walltime`, is empty at Wayne State (`hpcworker:framework/profiles/wayne.json:17`) and is only printed in the workspace guide (`hpcworker:framework/lib/profile.py:79`; `hpcworker:framework/lib/profile.awk:593`). Wayne State's `partitions_gpu` names `gmsap` and `gvohp` and leaves out VS Code's `galhp` (`hpcworker:framework/profiles/wayne.json:12-15`);
     - one measured GPU job on `gmsap` or `gvohp` before it ships.
   - **Other editions.** The browser and desktop would benefit, since imaging students need GPUs.
3. **The VS Code server's environment lines.**
   - **Why VS Code needs it.** Remote-SSH puts the VS Code server on a CentOS 7 compute node, and C&IT's sysroot exports make it run there (`beethoven-vscode:grid/bashrc.block:4-6`).
   - **Where it is built.**
     - A site field, defined in hpcworker's `framework/lib/profile.py` (`FIELD_LAYERS`, `SUBFIELDS`) and published as `module-schema`. beethoven-sites then fills in Wayne State's values with a dated note of where they were observed.
     - The awk and bash profile reader (`hpcworker:framework/lib/profile.awk`, `hpcworker:framework/lib/profile_sh.sh`) must be able to read the field, because no verb runs `python3` on `warrior` (`hpcworker:framework/bin/hpcworker:2222`).
     - `install --shared` writes the lines in its managed block only when the profile names them. hpcworker writes that `~/.bashrc` block only for the default `HPCW_HOME` and without `--no-shell-path` (`hpcworker:framework/bin/hpcworker:571-573`). `connect_setup` installs with no block at all (`hpcworker:framework/bin/hpcworker:1532`), so an account set up through the browser never gets the lines. The plan must say where they are written on that path.
   - **What a static value loses.** VS Code finds moved sysroot paths again: when C&IT moves them, `discover_sysroot` and `diag --repair` rewrite the block (`beethoven-vscode:grid/beethoven:986-999,1017-1020`). A static, dated site value loses that, and a moved path waits for a module change.
   - **The old block.** VS Code's `# >>> beethoven` block (`beethoven-vscode:grid/bashrc.block`) also puts `~/.beethoven/bin` on `PATH`. It needs a plan for removal, or for living beside hpcworker's block.
   - **Other editions.** No direct benefit to the browser or desktop.
   - Whether VS Code could carry these lines in its own Remote-SSH settings instead was not checked.
4. **Diagnostics in the contract.**
   - **Why VS Code needs it.** The VS Code edition's rule is that every feature ships with a diagnostic node. Its graph would read hpcworker's `hpcw.*` ids instead of the `grid.*` ids.
   - **Where it is built.** hpcworker. `diag --json` already exists (`hpcworker:framework/bin/hpcworker:2213-2214`), so this is contract work: add it to `cli.json`, with a schema for its one line and a vector.
     - **Its shape differs from VS Code's.** It has no `repaired` field, it adds `version`, `host` and `user`, and it has no `--node` mode (`hpcworker:framework/bin/hpcworker:2171-2174,2213-2214`; `beethoven-vscode:grid/beethoven:979-985,1158`).
     - **It needs a client floor.** On the login node it runs `sinfo` and `sacctmgr` (`hpcworker:framework/bin/hpcworker:2177-2181`; `hpcworker:framework/lib/adapters/slurm.sh:139,170`), which is more than the one scheduler call per action the etiquette allows.
   - **Other editions.**
     - The browser has a `diag --json` builder (`beethoven-extension:extension/src/core/contract.ts:263`) that no code under `src/` types. Its conformance test lists the builder outside `cli.json` for that reason (`beethoven-extension:extension/test/conformance.test.ts:230`). Putting `diag --json` in `cli.json` would let that entry move to `TYPED`.
     - Desktop's `grid_check` could use it only through a new gate verb. Desktop runs only gate lines (`beethoven-desktop:src/contract.ts:46-51`), and the gate has no `diag` verb (`hpcworker:interface/contract/cli.json:26-35`).
5. **`claude login` in `cli.json`.**
   - **Why VS Code needs it.** VS Code opens a terminal in which the student signs in with Claude Code's own flow. hpcworker has `claude login [--plain] [--profile SITE]` (`hpcworker:framework/bin/hpcworker:1427-1434`). Today `cli.json` lists `connect --login auto|always|never` (`hpcworker:interface/contract/cli.json:10`) and `login-setup` (`hpcworker:interface/contract/cli.json:21`), but not `claude login`.
   - **Where it is built.** hpcworker adds two lines to `cli.json`:
     - `claude login`, typed by the student and listed the way `login-setup` is;
     - `claude login --plain`, which the browser's login port types (`beethoven-extension:extension/src/core/contract.ts:277`), so it is not only a line the student types.
   - **Other editions.** The browser's entries `claudeLogin` and `claudeLoginPlain`, now outside `cli.json` (`beethoven-extension:extension/test/conformance.test.ts:227,231`), and desktop's printed line (`beethoven-desktop:src/tools.ts:74-77`) would then be held to the contract.
6. **Tokens for the worker. Only if greg keeps this as a product feature (decision).**
   - **Why VS Code has it.** The laptop writes the student's `GITHUB_TOKEN`, `GH_TOKEN` and `HF_TOKEN` over ssh stdin into `~/.beethoven/secrets.env` (`beethoven-vscode:extension/src/core/wizard.ts:663-664`). The daemon gives them to `claude -p` (`beethoven-vscode:grid/beethovend.js:163,320`), never to VS Code's Remote Control host: `grid/phone.js` has no reference to them.
   - **Where it would be built.** hpcworker:
     - `secrets set <NAME>` reads the value on stdin, for a closed list of names, and writes a mode-0600 file in the state folder;
     - `secrets list` prints names only;
     - at start, the values are exported into Claude Code's process inside the container from the 0600 file, for example by a wrapper inside the image. They must not be added to `CLEAN_ENV` (`hpcworker:framework/jobs/worker.sbatch.tpl:215-219`), because the job writes every word of it with `printf %q` into `in_image.sh` in the run folder (`hpcworker:framework/jobs/worker.sbatch.tpl:222-228`). They never go into argv, a log, a job file or `sbatch --export`;
     - no check from the login node.
   - **Other editions.** The browser and desktop would benefit: a Remote Control session could push to GitHub.
7. **Listing workers and reading the workspace for a client.**
   - **If VS Code follows desktop, hpcworker needs no change.** VS Code would read every `status.json` and `<state_dir>/workspaces/<name>` through a read-only sftp client (`beethoven-desktop:src/runs.ts`; `beethoven-desktop:src/grid.ts:327-354`; `beethoven-desktop:src/workspace.ts:1,61`). That narrows VS Code. `beethoven_read_file` and `beethoven_list_dir` would shrink from the whole grid home (`beethoven-vscode:extension/src/mcp/server.ts:167-181`) to the worker's workspace. Sessions bound to other directories (`beethoven-vscode:extension/src/mcp/server.ts:108`) could no longer be read.
   - **Otherwise hpcworker adds `worker list --json` to `cli.json`.** `worker list` prints text only today (`hpcworker:framework/bin/hpcworker:1236-1239`), so the `--json` form is new code as well as a contract entry.
8. **Optional: `uninstall`.**
   - **What it would remove.** The launcher, the `shared` marker and the managed `~/.bashrc` block.
   - **What it would keep.** `profile.json`, the consent marker, the log and the run directories, which are the student's own (`hpcworker:framework/bin/hpcworker:565`). It would leave them in place or move them aside with `move_aside`, never delete them (`hpcworker:framework/bin/hpcworker:443`).
   - **Refusals.** It would refuse under the 9 agent markers and without a terminal.
   - **Who would use it.** VS Code's Reset, which runs its grid uninstall over `ssh -t` (`beethoven-vscode:extension/src/extension.ts:674-694`). The browser's Forget this computer is the gate's `forget` verb, which already exists (`hpcworker:interface/contract/cli.json:34`; `beethoven-extension:extension/src/entrypoints/background.ts:3384`). Desktop has no such step and leaves out `forget` on purpose (`beethoven-desktop:src/contract.ts:39`).
   - **Not needed for the move.** Without it, VS Code's Reset would leave hpcworker's install in place.
9. **Optional: several images per lab.**
   - A lab module would list several images, and `connect` would choose one, replacing `worker start --container` and `library.json`.
   - It is only worth building if the GPU images differ from the default image. `library.json` entries already carry a `gpu` flag and a purpose (`beethoven-vscode:grid/beethoven:106,522`), and `library publish --gpu` builds GPU images (`beethoven-vscode:grid/beethoven:107-121`). So whether the lab's published GPU images differ can be read from `library.json` on the grid. It has not been read yet.

**What hpcworker should not gain.**

- A licence check. Authorization is the approved list.
- A lab-access request system. That role belongs to the access service and `tools/grid_access.sh`.
- A per-student image build.
- A polling loop on the login node.
- A one-host lease, until it is measured whether two Remote Control hosts on one sign-in conflict.

**What VS Code could drop instead of moving.**

- **The licence check on the grid.** The licence stays a check on the laptop. The grid side covers:
  - `grid/beethovend.js:65-106,174-175,220,274-277`;
  - `grid/beethoven:331-333,350,400,1106-1119`;
  - the files `grid/license.js` and `grid/license_keys.json`.
- **The lab-access section** (`grid/beethoven:723-950`). This covers the held-job requests and the subcommands `access init`, `whoami`, `status`, `requirements`, `request` and `admin`.
- **`bootstrap` and `library publish`.**
- **`accounts remove` and the `accounts/apikey/disabled` touch**, once no grid scripts 7 worker can still be running. VS Code's diagnostic node tells students to run `beethoven accounts remove --yes` to delete a stored key (`extension/src/vscode/diagNodes.ts:386`). That text has to change in the same release, and the student needs another way to delete the key. This plan does not yet name one.
- **`verify-tokens`.**
- **`relay`, `wait` and `tail`**, together with `grid/login_relay.sh`.
- **`diag --repair`'s actions** (`grid/beethoven:1001-1157`): the old-name links, install, sysroot rediscovery, adopt, the runtime switch, worker restart (`scancel` and `sbatch`), `access init` and the API-key marker.
- **The Remote Control host.** This is `grid/phone.js`, `beethoven phone on|off|status` (`grid/beethoven:952-976`) and its `host.lock` lease (`grid/phone.js:20-23,105`). hpcworker's worker is itself the Remote Control host, so these are replaced rather than moved.
- **`migrate` and the home-quota report.** `migrate` is the old `~/.ashley` move and its old-name links (`grid/beethoven:156-198`). The home-quota report is what `status` and `doctor` give (`grid/beethoven:293-298,343,376`). hpcworker has neither, so the quota report is either dropped or added to hpcworker as a new item.
- **The direct `squeue` and `sbatch` MCP tools** (`beethoven_squeue`, `beethoven_sbatch`). The worker's own Claude already has Slurm inside the job.
- **The `bypassPermissions` mode.**
- **`phoneCode`**, which calls a subcommand that does not exist.
- **If greg chooses, the whole request channel.** The student would then reach the worker only through claude.ai Remote Control, or through a Claude Code terminal on the worker's node over Remote-SSH.

## The order of work

Each step names the repository it lands in. beethoven-vscode is never edited from this project thread, so its steps are for a session working in that repository. Every beethoven-vscode step also waits on greg's explicit order to work there. greg merges its pull requests by hand, because it has no CI, no ruleset and no auto-merge (`hub:REPOS.md:19`). Hub line numbers below are those of `origin/main` at `65d94f7`.

1. **greg decides.** Settle at least decisions 1 (the request channel), 2 (the approved list), 4 (resources) and 7 (tokens) from the last section before any code is written. The decision on the two job tools in step 6 is needed only before step 9. This waits on nothing.
2. **beethoven-vscode adopts the interface standard, with no change in behaviour.**
   - Add `interface/INTERFACE.json`.
     - Its `exports` are `[]` for now. That leaves three things other repositories already take from beethoven-vscode outside the standard (`hub:SEAMS.md:128,137-138,145`):
       - the access-check wire and `services.json` (seam 9, `tools/intake/worker.js` and `tools/intake/ACCESS_CHECK.md`). Since 2026-10-07 this is `beethoven-access`'s, published there as its `http-api` and `http-api-text` exports, and it leaves beethoven-vscode with that repository's pull request #14;
       - the kill-list signer, with its public key k1 and its token format (seam 10, `tools/license/beethoven-license.mjs` against `grid/license_keys.json`);
       - the agreement texts, which the site renders (seam 11).
     - beethoven-extension's manifest imports nothing from beethoven-vscode today, so no manifest names these yet. The hub's `SEAMS.md` records the gap with this step, and step 9 declares the three exports once the key file has left `grid/`.
     - Its imports are hpcworker's `contract`, `contract-text` and `profiles`, plus beethoven-agents' `registry` at version 1 into `registry/`. beethoven-agents already names beethoven-vscode as a consumer of `registry` (`beethoven-agents:interface/INTERFACE.json:9-14`), and `extension/src/core/accounts.ts:1-2,16` reads exactly those files, as desktop does through the same import (`beethoven-desktop:interface/INTERFACE.json:46-49`). The `framework` and `testbed` imports wait for step 6, where the lane that runs them is built.
   - Add `interface/pull.sh`, copied from desktop's form with the `--pinned` byte check (`beethoven-desktop:interface/pull.sh:174-176`). Pin hpcworker's current `main`, `e77863c`.
   - Replace the two `HPCWORKER_DIR` reads and the hand copies in `extension/test-fixtures/hpcworker/` with the pinned `rules.json` (`extension/src/core/credentialEnv.test.ts:50-69`; `extension/src/core/signin.test.ts:72-85`). Rule 1 of `hub:INTERFACES.md:19` forbids `HPCWORKER_DIR` by name.
   - Rule 1 also catches two maintainer tools that reach the site repository's checkout:
     - `tools/intake/deploy.sh:33`, through `BEETHOVEN_SITE_REPO` and its default `$REPO/../openspineconsortium.github.io`;
     - `tools/intake/service.mjs:17`, through `path.join(REPO, '..', 'openspineconsortium.github.io')`.
     - Both leave with beethoven-vscode's pull request #14: the deploy moved to `beethoven-access`, and that pull request keeps `service.mjs` under `tools/license` without the read of the site checkout. If this step lands before #14 merges, it lists the two as known exceptions, each with its reason, the way hpcworker's `test_boundary.py` does (`hpcworker:interface/README.md:50-52`).
   - Add a boundary test for rules 1 to 3.
   - This waits only on greg's order to work in beethoven-vscode.
   - **Tests:**
     - the boundary test;
     - the sign-in verdict over `rules.json` `signin_cases`;
     - the strip list equal to `credential_variables`;
     - `accounts.ts` read against the pinned `registry` schemas.
     - beethoven-vscode has no CI (its `.github/` holds no workflow), so these tests run locally under `npm run test:unit`, and nothing runs them on a push. A CI workflow, holding no secret, is greg's choice. If he adds one, the "Where it runs" cell of the VS Code row in `hub:INTERFACES.md` changes with it.
   - **Optional, only if the switch-over is more than a few weeks away:** grid scripts 10, which raises the destructive refusal to all 9 agent markers and fixes the `exec` that keeps the worker job's cleanup trap from running. This costs every student a reinstall, so it is not recommended otherwise.
3. **hpcworker names the new consumer.**
   - Add `OpenSpineConsortium/beethoven-vscode` to the informative `consumers` of `contract-text`, `profiles`, `testbed` and `framework` (`hpcworker:interface/INTERFACE.json:22,30,46,54`).
   - In the same pull request, update the "Taken by" column of `hpcworker:interface/README.md:12-16`. `framework/tests/test_interface.py:61-64` checks only the manifest's `consumers`, so the README would drift unseen.
   - **Tests:** `test_interface.py`.
   - It can ride with step 4.
4. **hpcworker makes the small additions (framework 18).**
   - Each addition goes in its own pull request, with the vectors rewritten by `python3 framework/tests/vectors.py --write`:
     - a. `diag --json` in `cli.json`, with a schema and a vector.
       - `cmd_diag` already takes `--json` (`framework/bin/hpcworker:2213-2214`).
       - It runs `sinfo` (through `adapter_partitions`, `framework/bin/hpcworker:2179`), `sacctmgr` (`framework/lib/adapters/slurm.sh:170`), `ps` and `find /tmp` on the login node. That is more than hpcworker's own etiquette of one `sbatch`, `squeue` or `scancel` per action (`hpcworker:CLAUDE.md:106`).
       - It is also not a gate verb. The entry therefore says a client types it over plain ssh only when the student presses, never on a poll, as VS Code's own diagnostics do now (`beethoven-vscode:extension/src/vscode/diagNodes.ts:34`).
     - b. `claude login` listed as a line the student types in their own terminal. The command already exists (`framework/bin/hpcworker:1445-1470`).
     - c. If greg chooses it: hours, CPUs, memory and GPUs on `connect` and on the gate's `connect`.
       - Each value has a pattern and is bounded by the new profile fields of step 5. Today the profile has no CPU, memory or GPU bound, and Wayne State's `max_walltime` is empty (`framework/profiles/wayne.json:17`).
       - Each is an optional part of both connect lines, so a line without them still matches desktop's template (`beethoven-desktop:test/contract.test.ts:171-185`).
       - GPU renders `--gres=gpu:N` and `HPCW_NV=--nv`. `connect` passes no `--partition` today (`framework/bin/hpcworker:1667`), so the partition (`gmsap` or `gvohp`, `wayne.json:12`) and QoS a GPU worker gets come from those same profile fields.
     - d. If greg chooses it: `secrets set` and `secrets list`. These are `commands` entries, not gate verbs, and `secrets set` takes the value on stdin, never in argv.
   - These are additions under the two conditions in c and d, so the browser and desktop need not act. A new gate verb would fail beethoven-extension's conformance test at its next pin, because that test requires a builder for every gate verb in `cli.json` (`beethoven-extension:extension/test/conformance.test.ts:258`). Resource values that were not optional would fail desktop's template match. If either condition is broken, the pull request says which client must add a builder or change its match when it re-pins.
   - Whether `contract` goes to version 2 follows hpcworker's rule (`hpcworker:interface/README.md:31-41`).
   - 4a and 4b wait on nothing. 4c waits on step 1 and on step 5's bound fields. 4d waits on step 1.
   - **Tests:**
     - the suite on ubuntu and in the CentOS 7 container;
     - `tools/grid_ci.sh` on compute nodes;
     - one GPU job on `gmsap` or `gvohp`, which is not yet measured.
   - Publish with `tools/deploy_shared.sh`, then check `version` at `current`.
5. **hpcworker, then beethoven-sites, then hpcworker: the new site fields.** There are two sets of fields: the VS Code server's sysroot values, and, if greg chooses resources, the bounds on hours, CPUs, memory and GPUs together with how a GPU worker's partition and QoS are chosen.
   - hpcworker adds the fields and publishes `module-schema`.
   - beethoven-sites runs `tools/pull_schema.sh`, then adds Wayne State's values.
     - The sysroot values are two paths and one path list, taken from the three `export` lines of `beethoven-vscode:grid/bashrc.block:4-6`. They are carried as data, because a module may carry no code (`beethoven-sites:CLAUDE.md:25`).
     - Their note marks them as declared, not measured. Their source is the C&IT knowledge-base article "How to SSH to the Grid in Visual Studio Code", which the block names (`grid/bashrc.block:3`) and which was first copied there on 2026-09-27 (commit `1a47118`).
   - hpcworker runs `framework/sites/pull.sh` and `profile.py compose-all`.
     - `install --shared` renders the three `export` lines in its managed block.
     - That block is written only by `install` when `HPCW_HOME` is `~/.hpcworker` (`framework/bin/hpcworker:571`), never by `connect`'s setup (`framework/bin/hpcworker:1532`). A student set up only through the browser or desktop edition therefore has no block until VS Code's new setup step in step 6 runs `install --shared`.
   - This waits on step 1.
   - **Tests:**
     - `tools/check_modules.py` and `profile.py validate`;
     - an extension of the existing test that the block is rewritten in place and never duplicated (`framework/tests/test_cli.py:535-565`), so that it covers the new lines;
     - on the grid, one Remote-SSH session to a worker's node carrying only hpcworker's block, which is not yet measured.
6. **beethoven-vscode builds an hpcworker client beside the old path.**
   - Pin the framework 18 contract and the profiles.
   - Add the imports `framework` and `testbed` for the opt-in real lane, git-ignored except their `ORIGIN`, as desktop does.
   - Write `extension/src/core/contract.ts` by hand. It holds:
     - the value patterns from `cli.json`;
     - builders that throw on a bad value;
     - the `lines.json` patterns it reads;
     - types shaped by the schemas;
     - the link shapes it may open.
   - Write a conformance test. Every vector goes through the real reader, and every builder is either mapped to a `cli.json` id or listed with a reason.
   - The grid client follows desktop:
     - the student's own OpenSSH, which the wizard already configures;
     - the host key pinned from the profile;
     - gate verbs sent as `env SSH_ORIGINAL_COMMAND='…' bash '<shared>/bin/hpcworker' gate`;
     - one ssh at a time;
     - floors of 60 s for status, 60 s for start and stop, and 5 s for reads.
   - A new setup step, *the lab's shared copy*, runs `install --shared` instead of the scp and `beethoven install`.
   - The calls map onto hpcworker like this:
     - worker start: gate `connect`;
     - status: gate `status`;
     - stop: gate `stop`;
     - log: gate `read <name> progress.log`;
     - node for Remote-SSH: `node` in `status.json`;
     - *Open in Claude*: `environment_url` in `connection.json`;
     - phone access on and off (`extension/src/core/gridApi.ts:139`): gate `connect` and `stop`, since every hpcworker worker hosts Remote Control;
     - Claude sign-in: a VS Code terminal running `ssh -t <alias> bash '<shared>/bin/hpcworker' claude login`;
     - worker list: read-only sftp reads of `<state_dir>/<name>/status.json` and nothing else of a run folder, as desktop does (`beethoven-desktop:src/runs.ts:1-2,62-100`);
     - workspace reads: a read-only sftp client confined to `<state_dir>/workspaces/<name>`;
     - diagnostics graph: hpcworker's `hpcw.*` ids from `diag --json`, over plain ssh only when the student presses.
   - The other grid calls have no direct counterpart:
     - `beethoven_squeue` and `beethoven_sbatch` (`extension/src/mcp/server.ts:177-197`; `extension/src/core/gridApi.ts:99,278`) have no hpcworker verb. They use plain ssh and nothing of `grid/`. Whether they stay or go is a decision for greg, in the last section.
     - The container library (`extension/src/core/gridApi.ts:106`) is removed in step 9. An hpcworker worker runs the profile's image, and `cli.json` has no call that chooses among the lab's containers.
     - The access verbs (`extension/src/core/gridApi.ts:118-137`) follow decision 2.
     - `verify-tokens` (`extension/src/core/wizard.ts:758`) and the copy of the GitHub and Hugging Face tokens in `pushTokens` (`extension/src/core/wizard.ts:650-672`) map to `secrets list` and `secrets set` if greg chooses 4d. Otherwise they are removed in step 9.
     - The licence and revocation copies in `pushTokens` are removed in step 9, since the licence check stays on the laptop.
   - What changes for the student:
     - Worker start through the gate inherits its caps. These are at most 3 worker names in 7 days, 12 connects an hour and 2 watches at once, per account, in one caps file shared with the browser and desktop editions (`hpcworker:framework/lib/browser_key.sh:35-38,440`).
     - The defaults drop. VS Code now starts 24 h, 4 CPUs and 16G on `reqp`/`requeue` (`beethoven-vscode:grid/beethoven:384`). hpcworker starts 8 h, 2 CPUs and 8G on the same partition (`hpcworker:framework/profiles/wayne.json:82-84`).
     - The default worker name changes from `default` to `worker` (`cli.json` `values.name.default`).
     - `beethoven_read_file` and `beethoven_list_dir` narrow from the whole grid home, less sign-in folders, `~/.ssh` and credential-named files (`extension/src/mcp/server.ts:161-175`; `extension/src/core/gridApi.ts:10-28`), to the worker's workspace.
   - All of this sits behind a setting, with the old path as the default.
   - This waits on steps 2 and 4, and on step 5 for Remote-SSH.
   - **Tests:**
     - the conformance test;
     - a stand-in held to the contract;
     - the opt-in real lane: the pinned framework and testbed behind a local sshd, as in `beethoven-desktop:test/lab.ts`;
     - then the maintainer's own account on the grid. There, during the overlap of steps 6 to 9, VS Code's phone host (`grid/phone.js:12,176`) and an hpcworker worker both run `claude remote-control` on `~/.beethoven/claude` (the profile's `claude_config_dir`; `grid/beethoven:38`). hpcworker does not take the phone host's one-host lease (`hub:SEAMS.md:102`), and running both at once is not yet measured (`hub:SEAMS.md:104`). It is measured here, before step 9.
7. **hpcworker builds the request channel, if greg chooses it.**
   - First a design text, a contract text beside V11 and V12. Then the code, the schemas and the vectors, as described under "What hpcworker lacks today", item 1.
   - This waits on step 1.
   - **Tests:**
     - the vectors and `test_interface.py`;
     - the suite;
     - `tools/grid_ci.sh`;
     - a measured round trip through the gate.
   - How a `claude -p` and `claude remote-control` behave together in one job on one subscription is not yet measured.
8. **beethoven-vscode moves Ask, send, result and sessions onto hpcworker.**
   - Pin the new contract. Point these at it:
     - the Ask command (`extension/src/extension.ts:198`);
     - the four MCP tools;
     - the laptop CLI's `ask` (`extension/src/cli/main.ts:276`);
     - the `cli/` forwarders, which now send `ask` and `send` to the old grid command (`cli/beethoven:1-8`, `cli/beethoven.ps1`, and `cli/ashley` and `cli/ashley.ps1` under their old names).
   - An ask's free working directory becomes `<state_dir>/workspaces/<name>`.
   - Remove `bypassPermissions` everywhere hpcworker's contract already refuses it (`cli.json` `values.permission_mode` allows only `default`, `acceptEdits` and `plan`):
     - from the MCP schema (`extension/src/mcp/server.ts:109,136`);
     - from the shared `PermissionMode` type (`extension/src/core/protocol.ts:29`);
     - from the manual (`extension/media/manual.html:1484-1486`).
     - Its mapping to `--dangerously-skip-permissions` (`grid/beethovend.js:311`) goes with `grid/` in step 10.
   - If greg drops the channel instead, this step removes those tools, the command, the CLI's `ask` and the forwarders' `ask` and `send`.
   - This waits on step 7, or on greg's choice to drop it.
   - **Tests:** as in step 6.
9. **beethoven-vscode ships the switch-over release, 6.0.0.**
   - First, move `license.js`, `license.d.ts` and `license_keys.json` out of `grid/`, for example into `tools/license/` or `extension/src/core/`. The laptop's licence check, its tests, the release check and the kill-list signer all read them there today, and all of them are pointed at the new place:
     - `extension/src/core/license.ts:13-18`;
     - `extension/esbuild.mjs:22`;
     - `tools/license/beethoven-license.mjs:39,45`;
     - `extension/src/core/license.test.ts:8`;
     - `extension/src/core/daemon.test.ts:11`.
   - Declare the exports step 2 left out, and update seams 10 and 11 in `hub:SEAMS.md`:
     - the kill-list public keys in their new place;
     - the agreement texts.
     - Seam 9, the access-check wire, is `beethoven-access`'s since 2026-10-07 and needs nothing from this release.
   - The hpcworker path becomes the only path for setup.
   - The old path keeps only two calls, for the student's old workers until they end: a read of their state, and their stop button.
   - `extension/esbuild.mjs` stops copying `grid/`, and the wizard stops running scp and `pushTokens`.
     - Drop the `grid/` entries from `tools/release_check.mjs:56` and `extension/src/vscode-test/package.test.ts:26`. Both now require `dist/grid/license.js` and `dist/grid/license_keys.json` to ship.
     - Remove the calls step 6 marks for removal here.
   - The licence check stays on the laptop.
   - The texts describe the grid side in many places, and each passage changes:
     - `extension/LICENSE.txt`: "the scripts it installs in your own computing account" (`:30`), uninstall from the grid (`:112-116`), the token copy on the grid (`:123-127`), the `disabled` marker on the grid copy (`:137-139`), and the licence key copied to the grid, where the worker refuses to run without it (`:147-148`);
     - `extension/LICENSE-FULL.txt:31,110,122-123,134-135,144`;
     - `extension/PRIVACY.md:36-41,47-56`.
     - `TERMS_VERSION` follows both agreements and `PRIVACY.md` (`extension/src/core/terms.ts:22-23`). The texts and `TERMS_VERSION` therefore change together, from 7 to 8, and students accept again. The site's rendered copies under `/beethoven/vscode/` follow at its next build (seam 11).
   - This waits on step 6, and on step 8 or the choice to drop.
   - **Tests:**
     - the full suite;
     - a dry run on the maintainer's account, starting from a grid scripts 9 setup;
     - then the pilot students.
10. **beethoven-vscode retires `grid/` in 7.0.0.**
    - Before it, someone takes over `claude-node22` and `npm-claude-node22`.
      - These two are not old containers. They are the image every hpcworker build runs at Wayne State (`hpcworker:framework/profiles/wayne.json` `image_store` and `claude_bin`; `hpcworker:tools/grid_access.sh:92`).
      - `grid/bootstrap.sbatch:37-39,99` is the only builder of them that has run on the grid (seam 7, `hub:SEAMS.md:110`).
      - The named owner rebuilds and updates them. hpcworker's `framework/jobs/build_image.sbatch` would be the candidate, but it says it is not run at Wayne State and is untested on a real cluster (`:2-4`). It runs once in a grid job, and the result is measured, before `grid/` goes.
    - Remove from the repository:
      - `grid/`, with `grid/beethovend.js` and its `bypassPermissions` mapping, and the ACL writers of seam 8;
      - the scp step and `GRID_HOME_MOVE`;
      - the `disabled` touch and `gridUninstallLine`;
      - the old path of the forwarders in `cli/`.
    - This release removes nothing on the grid. What happens to the old files there is decision 11.
    - This waits on step 9, on one term without old workers, and on the image's new owner.
11. **The hub and the documents.**
    - **Hub:**
      - Update `REPOS.md`.
      - Update the VS Code row of `SEAMS.md` (`hub:SEAMS.md:28`) and these seams:
        - seam 6;
        - seam 7, the image builder;
        - seam 8, the ACL writers `path_traverse`, `acl_grant` and `access init` that leave with `grid/`;
        - seams 9 to 11, as step 9 left them;
        - seam 13, the strip list in five VS Code places and the agent markers its daemon sets;
        - seam 14, for the `registry` import.
      - Add VS Code to seams 2 and 3, the gate and its per-account caps file, which it now shares with the browser and desktop (`hub:SEAMS.md:64,73`).
      - Update the row for beethoven-vscode in `hub:INTERFACES.md` (`:137`).
      - Add one ledger row per unit of work.
    - **hpcworker:**
      - `docs/ARCHITECTURE.md` names VS Code as a client.
      - Fix the text that describes VS Code's grid pieces as live:
        - `framework/bin/hpcworker:333,357`;
        - `framework/lib/adapters/common.sh:133-134`, where the markers themselves stay, since the rule names them;
        - `framework/jobs/build_image.sbatch:2-3`.
      - The Wayne State note behind `framework/profiles/wayne.json:88` is changed in `beethoven-sites:sites/wayne/site.json:59` and composed again, because the profile is never edited by hand.
    - **The lab lead:** leave `shared/access`, the lab's `library.json` and the old containers untouched until no build reads them. `claude-node22` and `npm-claude-node22` stay as hpcworker's image.

## Students already set up

**What a set-up student has today.**

- **`~/.beethoven/`:**
  - `bin/`, holding grid scripts of some version;
  - `config.env` and `READY`;
  - `workers/<name>/`, with `inbox/`, `outbox/` (each request's result `<id>.json` and its events `<id>.events.jsonl`), `log/`, `state.json` (the heartbeat), `job.id`, `node`, `params`, `job.sbatch`, `container`, possibly `stop`, `rc/` (phone access: `enable` and `status.json`) and `slurm/` (`beethoven-vscode:grid/beethoven:401-440`, `beethoven-vscode:grid/phone.js:14-16`, `beethoven-vscode:grid/worker.sbatch.tpl:52-53`);
  - `sessions/`, `log/`, `secrets.env`, `license.key`, `license.state` and possibly `license.revoked` (`beethoven-vscode:grid/beethovend.js:87-96`);
  - `remote/`, which holds the phone host's lease (`beethoven-vscode:grid/phone.js:19`), and `tmp/`, the sign-in relay's folder (`beethoven-vscode:grid/login_relay.sh:11,18`);
  - the sign-in folder `claude/`;
  - `accounts/`, which holds the engine's sign-in directories and possibly the old `apikey/`. It may also hold Claude tokens that an earlier version stored under `accounts/<name>/` (`token` or `.credentials.json`), which the current scripts only report (`beethoven-vscode:grid/beethoven:1058-1071`). It may also hold an empty `accounts/default/` made by the laptop's folder-move step (`beethoven-vscode:extension/src/core/wizard.ts:689`). Only the engine's `accounts.json` says which entries are engine accounts;
  - `engine/` and `projects/`.
- `~/.ashley` is a link to `~/.beethoven`, or a real folder on accounts older than grid scripts 7. There may also be `~/.ashley.before-beethoven.<time>/` folders that `migrate --merge` set aside (`beethoven-vscode:grid/beethoven:187-189`).
- The managed `beethoven` block in `~/.bashrc`. On an account older than grid scripts 7 it is the `ashley` block instead, whose PATH line names `$HOME/.ashley/bin` (`grid/bashrc.block` at commit `b188223`).
- The work folder ROOT, which is whatever `~/.beethoven/config.env` names (`beethoven-vscode:grid/beethoven:67-70`):
  - for an account set up since the rename (grid scripts 7), `/rs/rs_grp_oschome/$USER/beethoven`, or `$HOME/beethoven` when the volume was not writable;
  - for an account set up before the rename, `/rs/rs_grp_oschome/$USER/ashley` or `$HOME/ashley`;
  - or any folder given with `install --root`, which the laptop setting `beethoven.gridRoot` passes (`beethoven-vscode:grid/beethoven:230`, `beethoven-vscode:extension/src/core/wizard.ts:749`).
  - ROOT holds `workspaces/`, including `workspaces/phone` (`beethoven-vscode:grid/phone.js:89`). For a student who built their own container it also holds `containers/`, `npm/` and `npm-cache/` (`beethoven-vscode:grid/bootstrap.sbatch:37-45`). The new client reads ROOT from `config.env` and never derives it.
- The VS Code laptop's public key line in the grid's `~/.ssh/authorized_keys` (`beethoven-vscode:extension/src/core/wizard.ts:449`, `beethoven-vscode:extension/src/core/sshInstall.ts:28`). hpcworker's `login-setup` adds three things beside it: its own key `~/.ssh/beethoven_ed25519`, a managed `~/.ssh/config` block and one restricted `authorized_keys` line (`hpcworker:framework/bin/hpcworker:1700-1755`). Neither tool may touch the other's lines.
- Possibly running workers, named `beethoven_<name>`, or `ashley_<name>` if started before grid scripts 7. A worker runs 24 h by default and up to 720 h (`beethoven-vscode:extension/package.json:381-386`). By default it runs on `reqp`/`requeue` with `--requeue` (`beethoven-vscode:grid/beethoven:384,410`), so a preempted worker goes back in the queue and starts again.
- Possibly other jobs of the old edition that are not workers:
  - a held `ashley_access` request job that never runs (`beethoven-vscode:grid/beethoven:761,913`);
  - a `beethoven_bootstrap` job (`beethoven-vscode:grid/bootstrap.sbatch:8`);
  - the 30-minute `beethoven_claude` sign-in allocation (`beethoven-vscode:grid/beethoven:582`).
  - The client identifies workers from `~/.beethoven/workers/*/job.id`, never from a job-name prefix.

**The Claude sign-in carries over without a new login.**

- In hpcworker, `claude_config_dir` is a product-level value, `$HOME/.beethoven/claude` (`hpcworker:framework/lib/profile.py:427,472`). So every composed profile names it, Wayne State's included (`hpcworker:framework/profiles/wayne.json:53`, a composed file that is never edited by hand).
- Its `consent_markers` are product-level too, and they are VS Code's own two marker files (`hpcworker:framework/lib/profile.py:428,473-474`; `wayne.json:54-57`). Claude Code's own `remoteDialogSeen` in `.claude.json` is read the same way by both.
- Neither side reads `.credentials.json`.
  - The VS Code grid scripts test only that it is non-empty (`beethoven-vscode:grid/beethoven:313,350,374,667`). The daemon tests that it exists and watches its name (`beethoven-vscode:grid/beethovend.js:210-213,471`).
  - hpcworker never names the file. It judges the sign-in only from `claude auth status` (`hpcworker:framework/jobs/worker.sbatch.tpl:235-239`, `hpcworker:framework/bin/hpcworker:1269`).
- hpcworker's worker writes to the same `.claude.json` that the VS Code daemon and `phone.js` use. When a session is about to start, it adds three keys if they are missing: `hasCompletedOnboarding`, `theme` and its new workspace's `hasTrustDialogAccepted`. It writes nothing else (`hpcworker:framework/jobs/worker.sbatch.tpl:288-298`). That is the one write the rules allow.
- That an hpcworker worker accepts a VS Code student's folder end to end is not yet measured. The first pilot student checks it before anyone else moves.

**Running workers are never cut off by the move.**

- The new client never cancels a VS Code worker by itself. It says plainly that the older worker is still running and gives the end time the scheduler reports, re-read at the 60 s floor. It never promises a fixed end, because a requeued worker starts again with a new wall time.
- It offers one Stop button that uses the old `worker stop`, as the student's own action.
- Otherwise the old worker runs until the scheduler ends it.
- The new path never runs the old `install`, `diag --repair` or `worker restart`, because each of them restarts running workers (`beethoven-vscode:grid/beethoven:258-272`, `beethoven-vscode:grid/beethoven:1130`, `beethoven-vscode:extension/src/vscode/diagNodes.ts:408`).
- An old phone host can be found. `phone.js` keeps a lease at `~/.beethoven/remote/host.lock/holder.json` (`beethoven-vscode:grid/phone.js:19,103-104`), and `beethoven phone status --json` reports it (`beethoven-vscode:grid/beethoven:967-973`). `beethoven phone off --worker <name>` stops only Remote Control and leaves the worker running (`beethoven-vscode:grid/beethoven:966`), a gentler step than `worker stop`.
- Starting an hpcworker worker while an old Remote Control host runs on the same sign-in is not yet measured. Both would use the same `remoteControlMachineId` in `.claude.json`.
  - `beethoven-vscode:grid/phone.js:22-24` says two hosts on one login "would fight over it".
  - `hpcworker:docs/OPEN_QUESTIONS.md:19` infers the opposite: a second host on the same login joins the same environment.
  - Neither claim is measured. Until one is, the client finds the host from the lease and asks the student to turn phone access off first.

**Tokens for other services.**

- The VS Code worker loads `~/.beethoven/secrets.env` (`GITHUB_TOKEN`, `HF_TOKEN`) into every Claude request's environment (`beethoven-vscode:grid/beethovend.js:56,163,320`). hpcworker has no equivalent: no file under its `framework/` names `secrets.env`, `GITHUB_TOKEN` or `HF_TOKEN`.
- So a moved student's worker loses those tokens. What replaces them is not decided. Whatever does must keep them off command lines, out of logs, out of job files and out of `sbatch --export`, in a mode-0600 file.
- `secrets.env` itself stays where it is.

**What is never deleted.**

- Everything under `~/.beethoven` stays:
  - `claude/`, `accounts/`, `engine/`, `projects/` and `sessions/`;
  - `workers/`, including every request's result;
  - `secrets.env`, `license.key`, `license.state`, `remote/`, `tmp/` and `log/`.
- The old work folder and everything in it stay. So do `~/.ashley`, every link and any `~/.ashley.before-beethoven.<time>/` folder.
- On the lab side, `shared/access` and `library.json` stay.
- The new client never runs the old `uninstall`, `uninstall --purge-root` or `claude forget --yes`, at any version. Grid scripts 8 and older deleted the whole folder on `uninstall`, which is why `gridUninstallLine` refuses below 9 (`beethoven-vscode:extension/src/core/shell.ts:175-185`).
- The new client never touches `accounts/`, which is now also the engine's folder of sign-in directories (`$HOME/.beethoven/accounts/<label>/claude`). That includes any stored tokens there, which nothing of ours reads.
- The old `apikey` file is left for the student to remove.

**Work folder and conversations.**

- An hpcworker worker starts in `<state_dir>/workspaces/<name>`, that is `/rs/rs_grp_oschome/$USER/hpcworker/workspaces/<name>`, not in the old ROOT. The student's files stay where they are, and Remote-SSH can open either folder.
- Old conversations stay in Claude Code's history for that sign-in. On accounts that ran grid scripts 8 or older, that history is in `~/.beethoven/projects`, behind the `claude/projects` link (`beethoven-vscode:grid/beethoven:526-529`), and new hpcworker transcripts will share it.
- hpcworker's worker continues only its own last session, with `--continue` in its workspace (`hpcworker:framework/jobs/worker.sbatch.tpl:302-306`). It never passes the VS Code session ids kept in `~/.beethoven/sessions/*.json` (`beethoven-vscode:grid/beethovend.js:316,495-519`), so old conversations are not continued. Nothing is lost.
- Whether `--resume <id>` from the new folder would find them is not yet measured.

**Older grid scripts versions.**

- **Before 7** (a real `~/.ashley` folder):
  - The sign-in is at `~/.ashley/claude`, where hpcworker does not look.
  - Until retirement, the old path's one-time move stays the only thing that moves it. That move is refused while a worker runs (`beethoven-vscode:grid/beethoven:164-165`, `beethoven-vscode:extension/src/core/wizard.ts:686`) and whenever `~/.beethoven` already exists (`beethoven-vscode:grid/beethoven:171`).
  - On such an account the new client must not start an hpcworker sign-in or worker first. `hpcworker claude login` creates `~/.beethoven/claude` (`hpcworker:framework/bin/hpcworker:1307-1308`). After that, the laptop's step sees both folders and runs `migrate --merge`, which keeps the old sign-in aside in `~/.ashley.before-beethoven.<time>/` instead of moving it (`beethoven-vscode:grid/beethoven:179-189`, `beethoven-vscode:extension/src/core/wizard.ts:687,743`). The client first sends the student to the old one-time move.
  - The laptop's busy check counts only RUNNING jobs named `ashley_*` or `beethoven_*` (`beethoven-vscode:extension/src/core/wizard.ts:686`). A running hpcworker worker is named `hpcw_<run>` (`hpcworker:framework/lib/profile.py:1028`), so it does not block a move of a folder whose sign-in it may be using.
  - After retirement, the client tells the student in a sentence to ask the lab lead. How many such accounts exist is not measured.
- **7:**
  - A worker runs the old daemon and honours `accounts/apikey/disabled` (`beethoven-vscode:grid/beethoven:533-536`).
  - Nothing updates an account's grid scripts by itself (`beethoven-vscode:extension/src/core/shell.ts:180`). So such a worker can still be started today on an account whose grid scripts were never updated, and it can run up to 720 h.
  - The marker is set by `retire_apikey` at install, worker start and diag repair (`beethoven-vscode:grid/beethoven:537-541`), by the laptop's `GRID_CLI_FIND` on every grid command (`beethoven-vscode:extension/src/core/shell.ts:159`) and by `beethoven-vscode:extension/src/core/wizard.ts:670`.
  - No line of beethoven-vscode ties the touch to a release. Ending it at a given version would be the plan's decision.
- **7 and 8:** `uninstall` deletes the whole folder, `uninstall --purge-root` deletes the work folder ROOT and `claude forget --yes` deletes the sign-in folder (at `710d74e`, `grid/beethoven:590-593,1087`; at `0475b63`, `grid/beethoven:581-584,1064-1079`). The new client runs none of them.
- **9:** the current version.
  - Its uninstall keeps the sign-ins, the accounts and the history (`beethoven-vscode:extension/src/core/shell.ts:174`).
  - It still cancels every worker and deletes `workers/` (every result), `log/`, `bin/`, `config.env`, `READY` and the `.bashrc` block (`beethoven-vscode:grid/beethoven:1197-1203`).
  - The new client never runs it.

**The two `.bashrc` blocks.**

- The two blocks can coexist, because neither tool's marker matches the other's (`beethoven-vscode:grid/beethoven:196-198`, `hpcworker:framework/bin/hpcworker:359-366`). VS Code's `install` replaces an old `ashley` block in place (`beethoven-vscode:grid/beethoven:238-239`).
- hpcworker's block holds only a PATH line for `~/.hpcworker/bin` (`hpcworker:framework/bin/hpcworker:366-368`) and carries no sysroot lines. A student may not have one at all:
  - only `hpcworker install` writes it, for the default `HPCW_HOME` without `--no-shell-path` (`hpcworker:framework/bin/hpcworker:357-358,571`);
  - the `connect` path that the browser and desktop editions use writes no block (`hpcworker:framework/bin/hpcworker:1532`).
- The VS Code sysroot lines live only in the old block, whether `beethoven` or `ashley` (`beethoven-vscode:grid/bashrc.block:2-6`). Their values may have been rewritten by `diag --repair` (`beethoven-vscode:grid/beethoven:986-998`), so they cannot be assumed to be the defaults.
- If the old block is ever removed, hpcworker must carry the sysroot lines first (step 5 of the order). Otherwise Remote-SSH breaks. That needs new hpcworker work, a profile field and a line in its block, because neither exists today.

**The approved list.**

- The student must be on the grid's approved list before the switch-over. The shared copy and the state folder sit under a volume root that is closed to everyone not on it.
- `tools/grid_access.sh` keeps the root's named entries equal to the roster (`rwx`) plus the readers from `admin.mjs readers` (`--x`). It removes every other entry (`hpcworker:tools/grid_access.sh:67-68`).
- That includes the `--x` entry a VS Code lab approval adds (`beethoven-vscode:grid/beethoven:776-779,932-935`). So a VS Code student who is not on the roster already loses the lab folder at the next sync, not only at the switch-over.
- Which VS Code students are on the roster today was not checked. It is decision 2, and it is urgent today, independent of the move.

**Old names and how long they stay.**

- Kept indefinitely, because they cost nothing and removing them is a deletion:
  - the `~/.ashley` link;
  - the `ashley` and `ashleyd.js` links in `~/.beethoven/bin`;
  - the `.ashley-remote-consent` marker name;
  - the `ASHLEY_*` variable twins.
- `~/.ashley` also carries load on some accounts. Where grid scripts 6 or older ran a request, `~/.beethoven/claude/projects` is an absolute link to `$HOME/.ashley/projects` (at `b188223`, `grid/ashleyd.js:35,428,445`). Every Claude Code transcript on that sign-in goes through it, hpcworker's included.
- The new client creates none of these.
- The old `bin/` and the old block stay until greg's tidy decision (decision 11). If they are removed at all, only that student-run tidy removes them.

## Risks and what is not yet measured

**Things that can go wrong.**

- **The approved list.** `tools/grid_access.sh` keeps the volume root's `user:<id>:rwx` entries equal to `admin.mjs roster`, which prints the accounts with the extension grant only (`hpcworker:tools/grid_access.sh:27-33`). Readers from `admin.mjs readers` get `--x` on the root (`:11-15, 384-385`). The owner's entry is left alone, and so are bare-uid entries, which belong to accounts that do not resolve at that moment (`:386-391, 412-415`). Every other named entry is removed (`:67-68, 408-418`). After the switch-over, an account that is neither on the roster nor a reader cannot enter the volume. A reader can enter it and read `shared/beethoven`, but has no w on the root and so cannot create a folder there. For a reader, hpcworker's state folder works only where `/rs/rs_grp_oschome/$USER` already exists. The extension grant covers both editions (`beethoven-vscode:tools/intake/worker.js:158-162`, the access service's code before it moved to `beethoven-access` on 2026-10-07), so a VS Code student approved through the access service is already on the roster. Two groups are at risk. The first is lab-only approvals (grant `lab`). The second is students approved only by VS Code's grid-side `beethoven access admin approve`. That is a separate list in `shared/access/status/*.json` (`beethoven-vscode:grid/beethoven:811`), and it gives only a `--x` root entry (`:776-780`). `grid_access.sh` removes that entry, and VS Code says so itself (`:932-935`). VS Code falls back to `$HOME/beethoven` when `/rs/rs_grp_oschome/$USER` is not writable (`grid/beethoven:67-70`). hpcworker has no fallback and refuses (`hpcworker:framework/bin/hpcworker:1111`). Which VS Code students are in the second group was not checked.
- **The request channel is the largest piece and is not designed yet.**
  - No gate verb can carry a prompt. The gate takes one line of at most 200 bytes in the characters `[A-Za-z0-9._ -]`, and only the eight verbs `version`, `status`, `watch`, `connect`, `stop`, `restrict`, `read` and `forget` (`hpcworker:framework/lib/browser_key.sh:533-535, 550-585`; `interface/contract/cli.json`, gate). A request channel through the gate needs a new verb that reads stdin. That is a contract change, with new vectors and a raised export version. Its latency, and its cost on the compute node, are not yet measured.
  - Today's baseline is VS Code's login-node relay. Its round trip was about 20 ms and its receipt about 0.19 s, against 2.0 s for one ssh per prompt (`beethoven-vscode:docs/ARCHITECTURE.md:75-109`). The relay is a long-lived process on the login node. It wakes every 250 ms to read the workers' outbox files (`grid/beethoven:676-720`). The etiquette allows only one `sbatch`, `squeue` or `scancel` per action there, so this is a reason to drop the relay, not only a number to match.
  - ControlMaster is not available in Windows' own OpenSSH (`beethoven-desktop:src/ssh.ts:4-6, 74`; `beethoven-vscode:docs/DEPENDENCY_MAP.md:1938`). On Windows each call is a fresh connection, about 2.6 s to the login node (`beethoven-vscode:docs/ARCHITECTURE.md:84`), unless it goes through a long-lived ssh of our own. The cost of a ControlMaster client call on the grid from macOS or Linux is not yet measured.
  - A `claude -p` and `claude remote-control` sharing one job and one subscription window is not yet measured.
- **Two Remote Control hosts on one sign-in.** VS Code's `phone.js` holds a lease, `~/.beethoven/remote/host.lock`, because two Remote Control hosts on one login "would fight over it" (`beethoven-vscode:grid/phone.js:20-27, 105`). hpcworker never takes that lease: `host.lock` appears nowhere under `hpcworker/framework`. So an old `phone.js` and an hpcworker worker can run at once, and what happens then is not yet measured. The environment id is stable per machine id, which both read from the same `.claude.json`. Every program that seeds that file writes through the same temporary file, `<CLAUDE_CONFIG_DIR>/.claude.json.part`, and then renames it (`beethoven-vscode:grid/phone.js:78-79`; `grid/login_relay.sh:33`; `hpcworker:framework/jobs/worker.sbatch.tpl:293`). Two seeders running at once can overwrite each other's `.part`. Each seeder's read-modify-write also races Claude Code's own writes of the file. How often either happens is not yet measured.
- **Smaller workers by default.** VS Code's defaults are 4 CPUs, 16G, 24 h, concurrency 2 and `acceptEdits` (`beethoven-vscode:grid/beethoven:384`; `grid/beethovend.js:312`; `extension/src/mcp/server.ts:85-90`). Wayne State's profile has 2 CPUs, 8G, 8 h, capacity 4 and permission mode `default` (`hpcworker:framework/profiles/wayne.json:81-87`). The contract's `connect` takes no resources (`hpcworker:interface/contract/cli.json`), so until resources are in it a VS Code student gets a smaller worker. The chain queues a successor with `afterany:<parent>,singleton` (`hpcworker:framework/lib/adapters/slurm.sh:49-54`). Each renewal is still a new job that must leave the queue, and Remote Control restarts with it. That happens at least every 8 h instead of every 24 h. Whether `--continue` keeps the session across it is not yet measured (`hpcworker:docs/OPEN_QUESTIONS.md:22`).
- **Fewer workers.** The gate allows each account at most 3 worker names, 12 connects an hour and 2 watches at once (`hpcworker:interface/contract/cli.json`, gate.limits). VS Code allows any number of named workers (`beethoven-vscode:grid/beethoven:390`; `extension/src/mcp/server.ts:84`).
- **No GPU workers.** hpcworker has no GPU workers. `worker start` takes no `--gpus` (`hpcworker:framework/bin/hpcworker:27, 1097-1103`). The rendered header has no `--gres` (`framework/lib/profile_sh.sh:124-130`). Nothing sets `HPCW_NV`, the only `--nv` hook (`framework/lib/adapters/common.sh:333`). VS Code offers GPU workers (`beethoven-vscode:grid/beethoven:387, 409`; `grid/worker.sbatch.tpl:72`; `extension/src/mcp/server.ts:88`). A VS Code student who uses one has no equivalent until hpcworker and its contract gain one.
- **The lab folder's datasets and software.** VS Code binds all of `/rs/rs_grp_oschome/shared` into the worker (`beethoven-vscode:grid/beethoven:139`; `grid/worker.sbatch.tpl:32`). hpcworker's Wayne State profile binds only `$HOME`, the student's own folder and `shared/beethoven` (`hpcworker:framework/profiles/wayne.json:32-36`). Anything a VS Code student reads under another folder of `shared/` is not visible in an hpcworker worker.
- **The work folder moves.** VS Code works in `$ROOT/workspaces/<session>`, where ROOT is `/rs/rs_grp_oschome/$USER/beethoven` or `$HOME/beethoven` (`beethoven-vscode:grid/beethoven:67-70`; `grid/beethovend.js:507`). hpcworker uses `/rs/rs_grp_oschome/$USER/hpcworker/workspaces/<name>` (`hpcworker:framework/profiles/wayne.json:22`; `framework/bin/hpcworker:325, 1111`). Claude Code keys transcripts by working directory (`beethoven-vscode:docs/ARCHITECTURE.md:116-118`), so existing conversations do not follow.
- **Resume window and named sessions.** `hpcworker:CLAUDE.md:265` and `hpcworker:docs/DIAGNOSTICS.md:200` say seven days. The code (`hpcworker:framework/lib/profile_sh.sh:117`; `framework/lib/profile.py:1064`), `docs/ARCHITECTURE.md:609-611` and `docs/OPEN_QUESTIONS.md:22` say 4 h. That window decides only whether a successor runs `remote-control --continue` (`framework/jobs/worker.sbatch.tpl:302-307`). VS Code's named sessions are `claude -p --resume <session id>`, looked up by name, with no age limit (`beethoven-vscode:grid/beethovend.js:495-509, 317`). hpcworker's contract has no session value or verb. A VS Code student therefore does not get a different rule: they lose resume by name.
- **GitHub and Hugging Face tokens.** VS Code loads `~/.beethoven/secrets.env` into Claude Code's environment on every request (`beethoven-vscode:grid/beethovend.js:163, 320`), and the agreement promises the copy on the grid (`extension/LICENSE.txt:123-127`). hpcworker has no equivalent: no `secrets.env`, `GITHUB_TOKEN` or `HF_TOKEN` appears in its `framework/bin`, `framework/lib` or `framework/jobs`. A student's worker loses `gh` and Hugging Face access. Any replacement must keep the tokens off argv, job files and `sbatch --export`.
- **Unknown deployed version.** Which framework version is live at `current` is not established. `hpcworker:docs/guides/LAB_LEAD.md:54` says 10. `docs/V12_STATUS.md:560` says 13 is not deployed. Commit `0c51fb6` says v15 was published from kbt2 and its ACL entries were completed by hand. Commits `c4b8fdb` (framework 15) and `6bf8167` (framework 16) record grid jobs. The desktop stand-in answers `HPCW-GATE ok 16` (`beethoven-desktop:test/gate-standin.sh:20`), while `hpcworker:framework/VERSION` is 17. Whether 16 or 17 has been published since is not established. The client must read `version` and refuse below the minimum it pins.
- **Unmeasured parts of hpcworker.** None of these has been measured on the grid:
  - framework 17's subscription-only sign-in (`hpcworker:docs/OPEN_QUESTIONS.md:65-89`);
  - `--continue` across a renewal (`:22`).
  - `login-setup` is marked unproven on the grid (`hpcworker:framework/bin/hpcworker:1691-1692`). `build_image.sbatch` is untested on a real cluster (`hpcworker:framework/jobs/build_image.sbatch:2-4`).
- **Remote-SSH and the `.bashrc` block.** hpcworker's `~/.bashrc` block sets only PATH (`hpcworker:framework/bin/hpcworker:363-369`), and `connect` installs no block at all (`:1532`). VS Code's block carries the C&IT glibc sysroot exports that it uses for Remote-SSH on the CentOS 7 grid (`beethoven-vscode:grid/bashrc.block:2-6`), and its `doctor` fails without them (`grid/beethoven:367-368`). Removing VS Code's block removes them. Remote-SSH without them is not yet measured, so the exports should stay.
- **Two clients during the transition.** For a while both paths may poll the same student's account. `beethoven status --json` makes up to 1 + 2N + 1 `squeue` calls. The first is for the bootstrap job, if one is recorded (`beethoven-vscode:grid/beethoven:342`). Then come two per worker (`:302, 608`) and one listing (`:329`). On top of those come up to 1 + 2N `sacct` calls for jobs that have ended (`:57-62`). The new client must not add its own polling while an old worker is shown. VS Code's wizard step `GRID_HOME_MOVE` moves `~/.ashley`, which holds the sign-in, to `~/.beethoven` when `~/.ashley` is still a folder and `~/.beethoven` does not exist. Its busy check looks only for running jobs named `ashley_*` or `beethoven_*` (`beethoven-vscode:extension/src/core/wizard.ts:683-690`). hpcworker's jobs are named `hpcw_<run>` (`hpcworker:framework/lib/profile_sh.sh:107`), so the check does not see a running hpcworker worker.
- **`/dev/shm` leak.** VS Code's worker trap does not run (`beethoven-vscode:grid/worker.sbatch.tpl:41,78`). Whether nodes clean up after it is not yet measured. The leak ends with retirement.
- **Terms.** `beethoven-vscode:extension/LICENSE.txt:30, 123-127` describes grid scripts and a token copy on the grid. The switch-over changes the agreement, and every student must accept again.

**Code that must not be carried into the new path.** Each item below is in today's VS Code grid side:

- a result id used as a file name with no check. `beethoven_result` takes `id` as a plain `z.string()` (`beethoven-vscode:extension/src/mcp/server.ts:148-160`); the relay writes it unchecked (`extension/src/core/relay.ts:192-197`); `cmd_result` and the relay's `RESULT` handler put it into `workers/$worker/outbox/$id.json` and print that file (`grid/beethoven:511-514, 701-703`). An id that climbs out of `outbox/` reaches the sign-in folder, so the laptop's Claude can be handed the Claude credential file. Confirmed by reading the code; not run. This is the first of the four things to know now, and its fix in beethoven-vscode does not wait for the move;
- `bypassPermissions`, which becomes `--dangerously-skip-permissions` and is reachable from the laptop's MCP server (`beethoven-vscode:grid/beethovend.js:311`; `extension/src/mcp/server.ts:109,136`);
- the prompt on argv (`grid/beethovend.js:310-318`);
- job values that `sed` places unescaped into the job script (`grid/beethoven:385-389, 420-423`). The laptop's MCP reaches this through `memory`, an unchecked `z.string()` (`extension/src/mcp/server.ts:87`) that `workerStartArgs` passes on unchanged (`extension/src/core/slurm.ts:65`). hpcworker refuses a quote or a newline in any rendered value (`hpcworker:framework/lib/profile_sh.sh:144-151`);
- an `eval` of a line of our own script (`grid/login_relay.sh:15`);
- a file written inside the sign-in folder (`grid/beethovend.js:487-489`);
- deletes without the agent check: `access init` and `access admin reset` (`grid/beethoven:871,943`);
- "read" commands that write or cancel: `status` adopts (`:338`), `access whoami` and `access status` may `scancel` the held request job (`grid/beethoven:832`, called at `:879, 883`), and `stepLabAccess.check` runs `install` (`extension/src/core/wizard.ts:787-791`).

hpcworker has a way of its own back to `bypassPermissions`. `connect` and the gate accept only `default`, `acceptEdits` or `plan` (`hpcworker:framework/bin/hpcworker:1655`; `framework/lib/browser_key.sh:574`; `interface/contract/cli.json`, values.permission\_mode). The terminal verb `worker start --permission-mode` is not checked (`framework/bin/hpcworker:1100`), and its value goes straight to `claude remote-control --permission-mode` (`framework/jobs/worker.sbatch.tpl:301`). The VS Code client must use only the contract's lines, never `worker start`, or `bypassPermissions` comes back.

**Out-of-date documents.** These can mislead a session that trusts them:

- `hub:SEAMS.md`, which says it was checked on 2026-10-05. Seams 3, 6 and 8 are out of date in substance, not only in line numbers.
  - Seam 8 says `admin.mjs` has no `roster` (`hub:SEAMS.md:122`) and that `access init` closes `shared/beethoven` (`:120`). `admin.mjs` now has `roster` (`beethoven-vscode:tools/intake/admin.mjs:26-27, 147-151`), and `access init` keeps `shared/beethoven` readable by other (`grid/beethoven:862-866`).
  - Seam 6 says `claude forget --yes` deletes the sign-in and that uninstall removes all of `~/.beethoven` (`hub:SEAMS.md:102`). `claude forget` now refuses (`grid/beethoven:670-671`), and uninstall removes, by name, only what install made (`:1200-1203`).
  - Seam 3 says neither repository names the desktop edition and that desktop's `FAIL_CODES` lacks the two sign-in codes (`hub:SEAMS.md:74, 76`). hpcworker's `interface/INTERFACE.json:14, 22` names desktop as a consumer, and `beethoven-desktop:src/contract.ts:233` has `signin-billed` and `signin-method`.
- The VS Code edition's `docs/ARCHITECTURE.md`:
  - The poll interval disagrees with itself and with the code (`:63` against `:79` and `grid/beethovend.js:36`).
  - It says the wizard has ten steps; the code has twelve (`:495` against `extension/src/core/wizard.ts:831`).
  - The volume root's mode 2770 leaves out the sticky bit that `grid_access.sh` requires, and `access init` does not set that mode anyway (`:363` against `grid/beethoven:852` and `hpcworker:tools/grid_access.sh:5-6`).
  - "Beethoven writes nothing there but Claude Code's first-run settings" is wrong for the sign-in folder (`:144-145` against `grid/beethovend.js:487-489`).
- hpcworker's statement of when the successor is queued. `docs/ARCHITECTURE.md:490-495` puts it last, before the wall time ends. The job actually queues it right after the sign-in check, before Remote Control starts (`hpcworker:framework/jobs/worker.sbatch.tpl:264-285`). The stop behaviour the document describes does match the code (`:169`).
- The seven-day resume rule in `hpcworker:CLAUDE.md:265`, `hpcworker:docs/DIAGNOSTICS.md:200` and `beethoven-extension:CLAUDE.md:298`, where the code says 4 h.

**Not checked here.**

- Whether hpcworker's `test_interface.py` and the two client suites pass at their current pins.
- Whether the profile's shared image is the lab library's default container.
- How many students use the MCP tools `beethoven_sbatch`, `beethoven_squeue` and `beethoven_ask`, which this plan drops or moves.

## What greg decides

The Summary's table gives each question with its recommended answer in one line. This section gives the evidence and the options behind each one.

1. **Where does the request channel go?** Today the channel is more than ask, send, result and sessions with one `claude -p` per request. It also has `wait`, `tail` and the long-lived `relay` session that the MCP server keeps open (`beethoven-vscode/extension/src/mcp/server.ts:25`). The relay polls files on the login node every 250 ms (`beethoven-vscode/grid/beethoven:676-721`, comment at `684-685`), and `wait` polls every 0.5 s for up to 3600 s (`beethoven:480-500`). hpcworker's login-node rules allow a file watch only every 5 s and at most 2 watches at once (`hpcworker/framework/bin/hpcworker:29`, `58-62`; `hpcworker/interface/contract/cli.json:36`). The streaming therefore has to be redesigned under those caps rather than carried over. A VS Code session also runs in any `cwd` the caller names, such as a folder under `~/Student_Projects` (`server.ts:108`; `beethoven-vscode/grid/beethovend.js:307-309`), with `--resume`, `--model`, `--allowedTools` and `--append-system-prompt` (`beethovend.js:310-317`). An hpcworker worker lives in `<state_dir>/workspaces/<name>`. The plan must say whether the new payload may run outside the workspace, and how it shares one job and one `CLAUDE_CONFIG_DIR` with `claude remote-control`. The daemon's `--concurrency` (`beethoven:384`; `beethoven-vscode/grid/worker.sbatch.tpl:81`; at most 8 through MCP, `server.ts:90`) has no counterpart in hpcworker, whose `capacity` is Remote Control's own (`hpcworker/framework/jobs/worker.sbatch.tpl:79`, `300`). Options: build it in hpcworker as a second payload with its own contract; drop it from VS Code; keep VS Code's daemon. **Recommended:** build it in hpcworker before the switch-over release, because desktop's MCP server would gain it too and students keep Ask. It is not a small addition, and it needs a route the gate cannot give it today (decision 3). Drop it only if greg wants `grid/` gone sooner than hpcworker can build it.
2. **Which VS Code licence holders are not on the grid's approved list (`admin.mjs roster`)?** Holders of keys that the access service issues are on it already. The `extension` grant covers both Beethoven and Beethoven for VS Code (`beethoven-vscode/tools/intake/worker.js:158-161`). `/trial` issues a key only to an account that holds that grant (`worker.js:1098-1102`, through `approvedFor` at `212-220`). The roster is exactly the accounts with that grant (`worker.js:379-382`, served at `1713` and read by `beethoven-vscode/tools/intake/admin.mjs:26-27`, `147-150`), and it is what `tools/grid_access.sh` applies. The open case is a key issued offline with `beethoven-vscode/tools/license/beethoven-license.mjs issue`, which never asks the service (`beethoven-license.mjs:5-7`). This matters today, not only after the move. VS Code's own lab-access approval adds only a `--x` entry on the volume root (`beethoven:775-780`, `927`). `grid_access.sh` removes every named entry that is neither on the roster nor a reader (`hpcworker/tools/grid_access.sh:69-71`), as the VS Code script already warns (`beethoven:932-935`). A VS Code student who is off the roster therefore loses lab access at the next sync. Options: require the extension grant (`admin.mjs add` or `grant`) before an offline key is issued; no change. **Recommended:** require the extension grant and add no new grant kind, because a new kind would change `GRANTS`, `normalGrants` and `approvedFor` in the service. The access service and `admin.mjs` moved to their own repository, `beethoven-access`, on 2026-10-07 and deploy from there since 19:37Z. The `tools/intake` citations above are to the copy still on beethoven-vscode's `main` at `631226e`, which its pull request #14 removes. Retiring `grid/` therefore does not touch the source of the roster (`hpcworker/docs/ARCHITECTURE.md:45` still names the old place).
3. **How does VS Code reach hpcworker?** Desktop sends its actions and status through gate verbs over the student's own ssh (`beethoven-desktop/src/contract.ts:79-83`). It lists workers and reads workspace files over read-only sftp, with no gate line and no scheduler call (`beethoven-desktop/src/grid.ts:327-354`). Options: the same split as desktop; `cli.json` command lines typed into a shell; both. **Recommended:** gate verbs for version, status, watch, connect, stop, restrict and read, and read-only sftp for the worker list and workspace reads (decision 10). The gate cannot carry the request channel of decision 1. A gate line is at most 200 bytes and holds only letters, digits, `.`, `_`, `-` and single spaces (`hpcworker/framework/lib/browser_key.sh:534-535`), and it must be one of eight fixed verbs (`browser_key.sh:546-591`). A prompt therefore needs a gate verb of its own that takes its payload on stdin, or another route. VS Code's worker names must also fit the gate. Today `worker_start` takes any name (`server.ts:84`), and the script takes any name matching `^[A-Za-z0-9_-]+$` of any length (`beethoven:390`). The contract allows 1 to 32 characters on its shell lines and `^[A-Za-z0-9][A-Za-z0-9_-]{0,31}$` at the gate (`cli.json:6-7`). The gate also allows 3 names a key may use, each counting for 7 days after its last use, 12 connects an hour and 2 watches at once (`cli.json:36`; `browser_key.sh:35-36`). The Claude sign-in is not a client call. `hpcworker claude login` is not among the commands in `cli.json` (`cli.json:14-23`), and `cli.json` says that everything else may change in any release (`cli.json:4`). VS Code should therefore show the line and let the student type it in a terminal they can see, as desktop does (`beethoven-desktop/src/tools.ts:75-76`). The alternative is a `claude-login` entry in `cli.json` that the student types, the way `login-setup` is listed (`cli.json:21`).
4. **Should resources chosen by the client enter `cli.json` and the gate?** VS Code's defaults are 24 h, 4 CPUs and 16G (`beethoven:384`), and MCP allows up to 720 h, 64 CPUs and 4 GPUs (`server.ts:85-87`). Partition and QoS are client choices in VS Code as well (`beethoven:17`, `386-387`; QoS `requeue`, `primary` or `secondary` at `server.ts:89`). The Wayne profile's defaults are 8 h, 2 CPUs and 8G (`hpcworker/framework/profiles/wayne.json:81-87`), so the switch shrinks a student's worker unless the client sends values. None of these values is in `cli.json` or the gate. The profile also has nothing to bound them with. `max_walltime` is its only limit field (`hpcworker/framework/lib/profile.py:79`) and is empty at Wayne State (`wayne.json:17`). `worker_defaults` covers cpus, mem, hours, permission\_mode and capacity only (`profile.py:120`). GPUs are missing from hpcworker itself, not only from the contract. `worker start` takes `--hours`, `--cpus`, `--mem`, `--partition`, `--qos`, `--permission-mode` and `--capacity` and has no `--gpus` (`hpcworker:27`, `1095-1100`), and `worker.sbatch.tpl` has no gres line. The gate's `connect` takes exactly six words (`browser_key.sh:572-575`). Adding any resource changes that count, which is a contract change every client must act on: the vectors are rewritten and the `contract` export goes from version 1 to 2 (`hpcworker/interface/INTERFACE.json:11`; `hpcworker/CLAUDE.md:315-316`). Options: yes, within new profile limit fields (maximum CPUs, memory and hours), added first to hpcworker's schema (`profile.py` `SCHEMA` and `FIELD_LAYERS`) and then in beethoven-sites; no, profile defaults only. **Recommended:** yes for hours, CPUs and memory now, within the new limits; GPUs after one measured GPU job. GPUs also need `worker start --gpus`, a gres line in `worker.sbatch.tpl` and a choice from `partitions_gpu`. The decision must also say whether partition and QoS remain the profile's choice.
5. **Is `bypassPermissions` ever offered?** VS Code 5.0.0 offers it today. `beethoven_ask` and `beethoven_send` list it (`server.ts:109`, `136`), the daemon turns it into `--dangerously-skip-permissions` (`beethovend.js:311-312`), and `beethoven-vscode/docs/LIMITS.md:53` describes it as available. VS Code's default mode is `acceptEdits`, while the Wayne profile's is `default` (`wayne.json:85`). `cli.json` allows only `default`, `acceptEdits` and `plan` (`cli.json:11`), and both the gate (`browser_key.sh:574`) and `connect` (`hpcworker:1655`) enforce that. `worker start --permission-mode`, however, takes its value as given (`hpcworker:1100`), and the template passes it through (`worker.sbatch.tpl:301`). Options: never; only on the laptop's word. **Recommended:** never, matching `cli.json`. For current users this removes a feature, and VS Code's texts must say so. The switch also changes the default to the profile's unless the client sends `acceptEdits`. hpcworker's `worker start` should gain a check of the value, so that "never" holds on every path and not only on the client paths.
6. **Where do the VS Code server's sysroot lines live?** Today VS Code's script writes them into `~/.bashrc`, following C&IT's knowledge-base article (`beethoven-vscode/grid/bashrc.block:2-6`). It rewrites the block when C&IT moves the paths (`discover_sysroot`, `beethoven:986-999`, `1017-1020`). hpcworker's `~/.bashrc` block is written only by `hpcworker install` at the default location (`hpcworker:355-358`, `571`). `connect` sets an account up without the block (`hpcworker:1532`), and the gate sets an account up only through `connect` (`browser_key.sh:584-588`). A VS Code student set up through the gate would therefore never get the lines. Options:
   - A site field holding the three paths: linker, library path and patchelf. It would be added first to hpcworker's schema (`FIELD_LAYERS`, `profile.py:394`) and then in beethoven-sites, whose modules hold data only and never export lines (`beethoven-sites/CLAUDE.md:25`). `connect`, or a new step that VS Code calls, would write the paths into hpcworker's block.
   - VS Code's own Remote-SSH settings on the laptop. This is not yet measured: nothing in the four checkouts shows a laptop-side setting that sets `VSCODE_SERVER_CUSTOM_GLIBC_LINKER`, `VSCODE_SERVER_CUSTOM_GLIBC_PATH` and `VSCODE_SERVER_PATCHELF_PATH` on the remote.

   **Recommended:** the site field. The rediscovery in `beethoven:986-999` is then either dropped or moved into `hpcworker diag`.
7. **How do the student's GitHub and Hugging Face tokens reach the worker?** Today VS Code merges `secrets.env` into each `claude -p` environment (`beethovend.js:320`). Nothing in hpcworker's framework reads `secrets.env`, `GITHUB_TOKEN` or `HF_TOKEN`. Options: an hpcworker `secrets` file (written from stdin, mode 0600, with only names in listings); the student's own sign-in of each tool, so that no product code holds a token; drop the feature. **Recommended:** the student's own sign-in, done from their own terminal on a compute node in a sitting like `claude login`, and never through a Claude session. A token typed into a Remote Control conversation becomes part of the transcript, which hpcworker's own notice says Anthropic stores (`hpcworker:1150-1152`). The worker also sets `BROWSER=/bin/false` (`worker.sbatch.tpl:219`). Neither image carries `gh` or a Hugging Face CLI: hpcworker's builder installs neither (`hpcworker/framework/jobs/build_image.sbatch:60`), and neither does the Wayne image that VS Code built (`beethoven-vscode/grid/bootstrap.sbatch:34`, `99`). The image must gain both tools first. Whether each sign-in completes there is not yet measured. The old `secrets.env` is left in place and unused. VS Code tells the student that the file still holds their tokens, and how to revoke the tokens and delete the file.
8. **Does the grid keep any licence check?** VS Code enforces its licence on the grid today in three places. `worker start` refuses without `license.key` (`beethoven:400`), the daemon refuses every request (`beethovend.js:274-277`), and phone access needs the key (`beethovend.js:217-220`). `beethoven-vscode/extension/LICENSE.txt:146-148` tells the student so. Options: none, with the licence checked on the laptop only (`beethoven-vscode/extension/src/vscode/licenseGate.ts`); port it into hpcworker. **Recommended:** none. hpcworker stays free of licence keys, and access is decided by the approved list. Enforcement then becomes laptop-only, and the agreement text changes together with `TERMS_VERSION` (7 today, `beethoven-vscode/extension/src/core/terms.ts:23`) in the switch-over release (decision 12).
9. **What happens to VS Code's lab-access requests (held Slurm jobs, `shared/access`) and lab library (`library.json`, `--container`, `library publish`)?** The image hpcworker runs at Wayne State (`containers/claude-node22` and `npm-claude-node22`, `wayne.json:27-31`) is a VS Code library entry. It was made by `library publish` through `bootstrap.sbatch` with `LIBRARY=1` (`beethoven:107-120`; `bootstrap.sbatch:38-39`). hpcworker's own builder says it is "NOT RUN ON WAYNE STATE" and "untested on a real cluster" (`build_image.sbatch:2-4`), although `hpcworker/docs/ARCHITECTURE.md:124` names it as the updater. Removing `grid/` therefore removes the only builder that has actually built or updated the Wayne image. VS Code's lab-access approval also grants read on other lab folders such as datasets and software (`beethoven:744-746`, `788-799`). The access service's readers list already replaces that: `admin.mjs` sets it (`admin.mjs:28-37`, `storage-approve` and `readers`), and `grid_access.sh` applies it (`grid_access.sh:11-15`). Options: retire both; keep the library as a lab-module list of images. **Recommended:** retire the access requests, with the readers list as their replacement. Keep one image per profile until a GPU image is needed. Before 7.0.0, either run hpcworker's `build_image.sbatch` once at Wayne State as a Slurm job and record the result, or name who updates Claude Code in the existing image and how. Leave the folders untouched.
10. **What happens to the MCP tools that run `sbatch` and `squeue` and read files directly on the login node?** VS Code's `beethoven_read_file` and `list_dir` read anywhere in the home except credential paths (`beethoven-vscode/extension/src/core/gridApi.ts:19-27`). Desktop's sftp reads only `<state_dir>/workspaces/<name>` (`beethoven-desktop/src/workspace.ts:1-7`), so the replacement narrows what can be read. Options: workspace reads over read-only sftp, as in desktop, with `sbatch` and `squeue` dropped; keep them as direct one-per-action lines. **Recommended:** the sftp reads, and drop `beethoven_sbatch` and `beethoven_squeue` (`server.ts:183-201`), because the worker's own Claude has Slurm inside the job wherever the profile turns that on. The switch is `scheduler_in_worker`, which defaults to false (`profile.py:118`) and is true at Wayne State (`wayne.json:79`). The laptop's Claude reaches that Slurm only through the request channel of decision 1, so dropping the two tools has to wait for decision 1. At a site where the switch is off, the worker has no Slurm at all.
11. **What happens to the old grid files after retirement?** Options: leave everything in place; a student-run tidy that removes only `~/.beethoven/bin` and the old `.bashrc` block, after hpcworker's block carries the sysroot lines; nothing ever. **Recommended:** leave everything for one term, then offer the tidy. Never remove `workers/` results, `accounts/`, the sign-in folder or the work folder. Two things in place today would break that rule:
    - `beethoven uninstall --yes` removes `workers/`, `log/`, `config.env`, `READY` and `bin` (`beethoven:1201`), and VS Code's Reset runs it (`beethoven-vscode/extension/src/extension.ts:694`; `LICENSE.txt:112-113`). 6.0.0 must stop Reset from running it, or change it so that it keeps `workers/`.
    - Removing `~/.beethoven/bin` is unsafe while any VS Code worker job is queued, running or requeueable. The job runs `node $BEETHOVEN_HOME/bin/beethovend.js` (`beethoven-vscode/grid/worker.sbatch.tpl:81`), and QoS `requeue` sets `--requeue` (`beethoven:410`). The tidy needs a busy-worker check like `busy_workers` (`beethoven:151-155`). It would also remove the `bin/ashley` and `bin/ashleyd.js` links that Ashley for VS Code 3.0.0 runs (`beethoven:192-195`).

    No program offers the tidy yet (decision 13).
12. **Release numbers and order.** Today hpcworker is at framework 17 (`hpcworker/framework/VERSION`) and VS Code at 5.0.0 (`beethoven-vscode/extension/package.json:5`). Not all of the hpcworker work is small. The request channel (decision 1) is a second payload with its own contract. Resources (decision 4) and the sysroot field (decision 6) change the gate, the profile schema and beethoven-sites. The switch also changes VS Code's agreement. Its `LICENSE.txt` describes the licence key copied to the grid (`LICENSE.txt:146-148`) and the tokens copied there (`LICENSE.txt:123-126`), so `LICENSE.txt`, `PRIVACY.md` and `TERMS_VERSION` (7, `terms.ts:23`) must change together. hpcworker's `INTERFACE.json` already lists `OpenSpineConsortium/beethoven-vscode` as a consumer of the `contract` export (`hpcworker/interface/INTERFACE.json:14`), but beethoven-vscode has no `interface/` folder and no pinned copy of the contract. The switch-over release therefore also needs the interface standard's pull and pin step, like beethoven-desktop's `bash interface/pull.sh`. Options:
    - Framework 18 adds resources to `connect` and the gate, and the sysroot field. Framework 19 (or 18, if 18 waits for it) adds the request channel. VS Code 6.0.0 needs both, and ships the new texts with `TERMS_VERSION` 8. VS Code 7.0.0 removes `grid/`.
    - The same, but with the request channel after 6.0.0, and Ask unavailable in between.
    - One VS Code release that does both.

    **Recommended:** the first, with the framework releases first and two VS Code releases.
13. **Does hpcworker gain an `uninstall`?** It has none today (the dispatch at `hpcworker:2281-2293`). Options: now; later; never. **Recommended:** later, because the move itself does not need it. The tidy of decision 11 still needs a home, since `grid/` leaves the VS Code repository in 7.0.0 and hpcworker has no uninstall. The plan must name which program offers the tidy after one term: the old grid script, which stays on the grid untouched, or an hpcworker subcommand added then. Either way the tidy is a destructive step that runs only for a person at a terminal. It must refuse under an agent marker or without a terminal (`hpcworker:333`; `beethoven:49-54`).
14. **What replaces VS Code's phone access?** VS Code's `grid/phone.js` runs Remote Control under its own host lease (`~/.beethoven/remote/host.lock`, `phone.js:20`, `105`). It uses the same sign-in folder as hpcworker's workers, `$HOME/.beethoven/claude` (`wayne.json:53`). Options: hpcworker's worker replaces phone access at the switch-over, and VS Code stops starting its phone host then; both run for the term, each aware of the other. **Recommended:** hpcworker's worker replaces it in 6.0.0. How the two hosts behave on one sign-in folder while both still run is not yet measured.
