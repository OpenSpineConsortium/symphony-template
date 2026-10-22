# Beethoven build roadmap

Oct 3, 2026 · @greg

## Summary

Build the research engine as six phases on top of what already works: the always-on Remote Control worker (hpcworker) and the side panel (beethoven-extension). The first phase is a one-job measurement that decides whether the inner loop can be headless `claude -p` on the student's own login; everything after it adds one capability and one measured gate.

&#91;embedded content: build roadmap · 6 phases, 6 gates\]

Phase 0 is highlighted because its answer reshapes phases 1 and 2. The outer orchestrator runs as a chained Slurm job rather than a login-node service, because the grid rules allow nothing there beyond one `sbatch`, `squeue` or `scancel` per action. Sources: the 12 notes in the Beethoven-notebook folder, both repositories' `CLAUDE.md` and `docs/ARCHITECTURE.md` at hpcworker 2e5bcf8 and beethoven-extension 4b1d870.

## Starting point

The two repositories today are the transport layer of the engine, not the engine. They get a student's own Claude Code onto a compute node and in front of them in claude.ai; nothing yet plans research, runs it headless or enforces REFORMS.

| Repository | What exists (main, 2026-10-03) | What the engine still needs from it |
| --- | --- | --- |
| hpcworker (framework 11) | Site profiles, the eight-call scheduler adapter (Slurm, PBS, LSF), an always-on `claude remote-control` worker in the shared Apptainer image with `afterany` successors, `status.json` / `connection.json` / `progress.log`, the lab's shared copy, grid CI on real compute nodes | A run model (projects, runs, stages), a headless job template, a run ledger, the REFORMS gates and research templates |
| beethoven-extension (12.0.0) | Chrome side panel, Open OnDemand shell driver, the native ssh bridge, approval check, kill-list, terms flow, mock portal and hermetic CI | Project and run views, a prompt box that becomes a run request, live stage progress, the compliance report and paper preview |

No Hydra, run hashing, clean-tree gate, MONAI splits, W&B, CodeCarbon, LaTeX macros, Zenodo, Hugging Face, LangGraph or Metaflow code exists in either repository. `docs/ARCHITECTURE.md` section 2 already reserves a place for workflow templates beside `jobs/`, rendered from the site profile.

## Phases

Six phases, each ending at a gate that is measured on the grid, not asserted. Every phase changes both repositories, and every new file the jobs write enters the contract in both in the same change.

| Phase | Goal | hpcworker (server) | beethoven-extension (client) | Gate to pass |
| --- | --- | --- | --- | --- |
| 0. Ground truth | Settle what the inner loop may be and measure it | A probe job: `claude -p --output-format stream-json` in the shared image on the student's own login, under `sbatch`, no pty; record the credential source the run reports and the 5-hour limit behaviour | None beyond reading the probe's result in the existing checks list | A headless run completes from a batch job on the subscription login, or the fallback is chosen (decision 1) |
| 1. One headless run | A prompt typed in the side panel becomes one research job and its result comes back | `jobs/run.sbatch.tpl`: one `claude -p` session in a per-run directory, wall time, node-local scratch with a cleanup trap, image-baked `managed-settings.json` and a `PreToolUse` guard; writes `run.json` (state) and `events.jsonl` (stage events from stream-json); `hpcworker run start / status / stop` | A Runs view: prompt box, run list, live stage feed read from `events.jsonl` at the 60 s floor, open-in-Claude for the run's session | A run started from the panel finishes, its events render in the panel, nothing of ours is on the login node beyond one `sbatch` |
| 2. Outer loop | Runs survive wall times, rate-limit windows and node changes | The orchestrator as a chained job (the worker's `afterany` successor pattern), stages plan, code, experiment, analyse, write; state in a run ledger (SQLite in WAL mode on node-local disk, checkpointed back to CephFS); `PreCompact` and `SessionStart` hooks that save and re-inject decisions; child `sbatch` for CPU prep and GPU training through the adapter | Stage timeline per run, pause, resume and cancel (stop file, one `scancel`), notification when a stage needs the student | A run crosses at least two wall-time boundaries and one compaction and finishes with the same decisions on record |
| 3. REFORMS gates | A run cannot produce a result that skips a REFORMS module | A research template the outer loop starts every project from (Hydra configs, run-ID hashing, clean-tree gate, group-level splits, bootstrapped CIs, CodeCarbon) and a stdlib checker that writes `reforms.json` per run; the gate refuses to dispatch on a failed check | A compliance view: one line per REFORMS module, pass or the plain reason it failed, exportable with the run | A deliberately leaky split and a dirty tree are both refused before any GPU time is spent |
| 4. Paper and archive | Numbers reach the manuscript and the archive without hand copying | LaTeX macro injection from the run's metrics, the paper build, Zenodo and Hugging Face uploads prepared as drafts; publication tokens as mode-0600 files, never in argv | Paper preview, a diff of the macros against the last build, and an explicit Publish step the student presses for the DOI and the model card | A DOI is minted only after the student's press, and every number in the PDF traces to a `run.json` |
| 5. Scale and sites | More than one run, more than one site | Concurrency bounded by the account's own limits (queueing and backoff, no extra accounts), a second site profile, grid CI covering the run template | Multi-run dashboard, per-site setup checks, store release | Two concurrent projects at Wayne State and one run at a second site, with the pilot's students |

Phase 0 is small and decides the rest: if a headless run on the student's own login is not allowed or does not work from a batch job, the inner loop becomes a Remote Control session steered by the outer loop, and phases 1 and 2 change shape (decision 1 below).

## REFORMS enforcement

Every REFORMS control lands in phase 3 or 4, and each is enforced by code that runs before or after the agent, not by the agent's own report. The agent writes the research code; the gate checks it.

| Control | REFORMS module | Phase | Where it runs | How it is enforced |
| --- | --- | --- | --- | --- |
| Hydra configs, no hyperparameters in code | 2, 5 | 3 | Research template (container) | Template layout; the checker flags literals in training entry points |
| Immutable run ID: hash of Hydra config, git SHA, image digest, Slurm environment | 2, 5 | 3 | hpcworker gate, before `sbatch` | Written to `run.json`; recomputed at the end of the run |
| Clean-tree gate | 2, 5 | 3 | hpcworker gate, before `sbatch` | `git status --porcelain` non-empty means no dispatch |
| Patient or group-level splits (PatientID, StudyInstanceUID) | 6, 8 | 3 | Research template (MONAI) | The checker verifies zero group overlap between split manifests |
| Bootstrapped confidence intervals on primary metrics | 7 | 3 | Research template, W&B | A metric without an interval fails `reforms.json` |
| Energy telemetry (CodeCarbon, kWh, CO2e) | 7 | 3 | Research template, CPU and GPU jobs | A run with no energy record fails `reforms.json` |
| Hounsfield-unit calibration and MetaTensor affines | Data quality | 3 | Research template (imaging projects only) | Preprocessing asserts slope and intercept were read from the header |
| LaTeX macro injection | Reporting | 4 | hpcworker, after the run | Macros generated from `run.json` metrics only; hand-typed numbers in the manuscript are flagged |
| Zenodo DOI and Hugging Face model card | Reproducibility | 4 | hpcworker, on the student's Publish press | Drafts prepared automatically; the irreversible publish waits for the student |

The module numbers follow the project topic's own mapping and have not been checked against the REFORMS paper (Kapoor et al., 2024); confirming them is a phase 3 task. Imaging-specific controls apply only to imaging projects, so the template carries them as an optional module.

## Rules that shape the design

The repositories' standing rules (both `CLAUDE.md` files) already decide several things the project topic leaves open. Each phase below is written to fit them.

| Rule | What it means for the engine |
| --- | --- |
| Beethoven never reads, stores or relays a Claude credential; one person, one account | The inner loop runs on the student's own `claude auth login` in `claude_config_dir`. A LiteLLM proxy that rotates commercial keys to dodge rate limits is out; rate limits are handled by queueing and backoff, not by more accounts. |
| No code on claude.ai; the only content script is on the Open OnDemand origin | The research UI lives in the extension's own side panel and pages, reading the files the jobs write. claude.ai stays the conversation window through Remote Control, untouched. |
| Nothing on the login node beyond one `sbatch`, `squeue` or `scancel` per action | The outer orchestrator cannot be a resident daemon (LangGraph server, Metaflow service, Redis) on the login node. It runs as a Slurm job itself, or as files plus a short-lived submit. |
| Scheduler polling no faster than 60 s; every job has a wall time | Progress flows through files the jobs write (as `status.json` does today), and long runs chain with `afterany`, never `afterok`. |
| Container temp on node-local `/tmp/$USER/...`; never trust `$TMPDIR` at Wayne State | Matches the topic's node-local scratch staging; transcripts and SQLite go there and are copied back at checkpoints. |
| Nothing deleted outside the framework's run directories and node-local temp; destructive commands refuse under `CLAUDECODE` | The `PreToolUse` guard (`claude-guard.sh`) is a second line; the framework's own guard stays the first. |
| The seam is the contract (`docs/V11_CONTRACT.md` and `contract.ts`) | Every new file the engine writes (run ledger, stage events, compliance report) is added to the contract in both repositories in the same change. |
| Framework: bash 4.2 and Python 3.6 standard library on the login node | Anything heavier (Hydra, MONAI, W&B, CodeCarbon) lives inside the research container on compute nodes, never in `framework/` itself. |

## Decisions for greg

Each is answerable in a word; the roadmap above assumes the recommended option.

1. **Who pays for the inner loop's tokens.** The student's own subscription login (recommended: it is what the product is built on, and notes 01, 07 and 09 class single-person headless use as compliant) or per-student commercial API keys (needed if fan-out outgrows "ordinary, individual usage"). Pooled keys behind LiteLLM (note 06) is not an option under the one-account rule.
2. **Workflow engine for experiments.** Plain `sbatch` templates through the existing adapter (recommended for phase 2: no new dependency, works on CentOS 7) or Metaflow with `metaflow-slurm` (notes 02, 10, 12) once the gates are in place.
3. **Where the research template lives.** A new third repository (recommended: it holds heavy Python and is cloned into each project) or `framework/research/` inside hpcworker.
4. **Environment pinning.** Pixi lockfiles inside the Apptainer image (recommended, notes 06 and 10) or conda/pip with the image digest alone.
5. **Verification extras in the first REFORMS release.** Defer contracts, CrossHair and RO-Crate to after phase 4 (recommended) or include them in phase 3.
6. **Human approval points.** Only the Publish press (recommended) or also before each GPU-heavy dispatch.

### What the notebook proposes that this plan leaves out

- Intercepting or spoofing claude.ai (notes 04, 10 section 2, 11): rejected by the research report; the plan uses Remote Control and the extension's own panel.
- `setup-token` or `CLAUDE_CODE_OAUTH_TOKEN` injected into jobs (notes 07, 08, 09): forbidden by the credential rule; the student's `claude auth login` is used where it sits.
- A resident basecamp, LangGraph server or Redis on the login node (notes 02, 03, 06): replaced by the outer loop as a chained Slurm job.
- Copying or remapping transcripts across accounts or mount points (notes 03, 08, 10): replaced by resume in the same directory and hooks that re-inject decisions.
- An Isolated Web App with direct sockets (note 05): superseded by the native bridge chosen for 12.0.0.
- Claims not yet checked against Claude Code's own documentation: the `ultracode` effort level, the subagent cap variables, `promptCacheTtl`, the compaction bug workaround and `--forward-subagent-text`. Phase 0 verifies whichever phase 1 depends on.
- The notes assume Lustre; Wayne State is CephFS with a Panasas home, which changes none of the node-local scratch advice.
