# Claude Code on a Slurm + Apptainer Cluster with a Consumer Subscription: Implementation Playbook

Oct 3, 2026 · @greg

## Compliance envelope and site assumptions

This deployment is permitted as long as four things stay true: one person's subscription authenticates only that person's sessions, the Claude Code binary runs unmodified, no one else's work is routed through the account, and nothing is done to multiply or evade the plan's usage limits. Anthropic's own docs describe the credential this playbook uses, a one-year token from `claude setup-token`, as intended "for CI pipelines, scripts, or other environments where interactive browser login isn't available", and the Legal and compliance page preserves the right of an end user to sign in to the unmodified binary with their own subscription even where a platform hosts it. Everything below is built to keep those four conditions mechanically true on a shared cluster.

| Condition | How this playbook enforces it |
| --- | --- |
| One user, one account | The image contains no credentials. Each user mints their own token on their own laptop and stores it under their own `/scratch` path with mode `0600`; nothing is placed in a group-readable or module-shared location |
| Unmodified binary | The Apptainer image installs Anthropic's native binary at build time and pins the version; the auto-updater is disabled because the image is read-only |
| No intermediation | No proxy, wrapper API, or shared service sits between the user and Anthropic. The launcher is a shell script that sets paths and calls `claude` |
| No limit evasion | One account per user, no account rotation, no pooled tokens. Batch jobs are sized to the plan's windows rather than run around the clock |
| Data policy | On Free, Pro and Max plans the account's "Help improve Claude" setting decides whether coding sessions are used for training. Regulated data (PHI, export-controlled, GDPR special categories) stays off a consumer plan; use an API key, a Team or Enterprise seat, or a cloud-provider route for that work |

Two cluster facts shape the design more than any Claude Code setting. First, most compute nodes cannot reach the internet directly; Claude Code needs `api.anthropic.com` on every turn, so the job must run on a partition with egress or through the site's HTTPS proxy. Second, home directories are quota-limited and often read-only from compute nodes, while Claude Code writes session transcripts, caches, and credential refreshes continuously; all of that state is relocated to a parallel filesystem.

### Site discovery

Every script in this document sources one file, `site.env`, which the script below writes from real cluster queries. It fixes the scratch root, the Slurm account, the three partitions, and the egress method, so no later script contains a site-specific value you have to edit by hand. Run it once on a login node and re-run it when the cluster changes.

```bash
#!/usr/bin/env bash
# site-discover.sh — write /scratch/$USER/claude/site.env from live cluster queries
set -euo pipefail

# 1. Scratch root: first writable parallel-filesystem path found
for candidate in "/scratch/$USER" "${SCRATCH:-}" "/work/$USER" "/gpfs/scratch/$USER" "/lustre/scratch/$USER"; do
  if [[ -n "$candidate" && -d "$candidate" && -w "$candidate" ]]; then SCRATCH_ROOT="$candidate"; break; fi
done
: "${SCRATCH_ROOT:?No writable scratch directory found; create one or export SCRATCH}"
CLAUDE_HPC_ROOT="$SCRATCH_ROOT/claude"
mkdir -p "$CLAUDE_HPC_ROOT"/{images,config,secrets,home,cache/npm,cache/uv,cache/pip,tmp,bin,runs,hooks}
chmod 700 "$CLAUDE_HPC_ROOT" "$CLAUDE_HPC_ROOT/secrets" "$CLAUDE_HPC_ROOT/config"

# 2. Project root: where repositories live (bound read-write into the container)
for candidate in "/work/$USER" "$SCRATCH_ROOT/projects" "$HOME/projects"; do
  if [[ -d "$candidate" && -w "$candidate" ]]; then PROJECT_ROOT="$candidate"; break; fi
done
PROJECT_ROOT="${PROJECT_ROOT:-$SCRATCH_ROOT/projects}"; mkdir -p "$PROJECT_ROOT"

# 3. Slurm account and partitions
SLURM_ACCOUNT="$(sacctmgr -nP show user "$USER" format=DefaultAccount 2>/dev/null | head -n1 || true)"
mapfile -t PARTS < <(sinfo -h -o '%P' | tr -d '*' | sort -u)
DEFAULT_PART="$(sinfo -h -o '%P' | grep -F '*' | tr -d '*' | head -n1 || true)"
DEFAULT_PART="${DEFAULT_PART:-${PARTS[0]}}"
pick() { printf '%s\n' "${PARTS[@]}" | grep -Ei "$1" | head -n1 || true; }
PART_INTERACTIVE="$(pick 'interactive|debug|devel|dev$|express|short')"; PART_INTERACTIVE="${PART_INTERACTIVE:-$DEFAULT_PART}"
PART_BATCH="$(pick 'general|standard|compute|batch|normal|cpu')";        PART_BATCH="${PART_BATCH:-$DEFAULT_PART}"
PART_GPU="$(pick 'gpu|a100|h100|v100|l40')";                             PART_GPU="${PART_GPU:-$DEFAULT_PART}"

# 4. Egress: direct, via the login node's proxy variables, or none
PROXY_URL="${HTTPS_PROXY:-${https_proxy:-}}"
probe() { curl -sS -m 10 -o /dev/null -w '%{http_code}' https://api.anthropic.com/v1/models 2>/dev/null || echo 000; }
EGRESS="none"
if [[ "$(probe)" != "000" ]]; then EGRESS="direct"; [[ -n "$PROXY_URL" ]] && EGRESS="proxy"; fi

# 5. Container runtime and GPU presence on this node class
APPTAINER_BIN="$(command -v apptainer || command -v singularity || true)"
: "${APPTAINER_BIN:?Neither apptainer nor singularity is on PATH; module load it first}"

cat > "$CLAUDE_HPC_ROOT/site.env" <<EOF
# generated $(date -Is) by site-discover.sh on $(hostname)
export CLAUDE_HPC_ROOT="$CLAUDE_HPC_ROOT"
export CLAUDE_SIF="$CLAUDE_HPC_ROOT/images/claude-code.sif"
export PROJECT_ROOT="$PROJECT_ROOT"
export SLURM_ACCOUNT="$SLURM_ACCOUNT"
export PART_INTERACTIVE="$PART_INTERACTIVE"
export PART_BATCH="$PART_BATCH"
export PART_GPU="$PART_GPU"
export EGRESS="$EGRESS"
export PROXY_URL="$PROXY_URL"
export APPTAINER_BIN="$APPTAINER_BIN"
EOF
chmod 600 "$CLAUDE_HPC_ROOT/site.env"
cat "$CLAUDE_HPC_ROOT/site.env"
[[ "$EGRESS" == "none" ]] && echo "WARNING: no route to api.anthropic.com from this node; set HTTPS_PROXY or use a partition with egress" >&2
exit 0
```

The partition heuristics pick the first partition whose name matches the common conventions; if your site uses other names, edit the three `PART_*` lines in the generated `site.env` once. The `EGRESS` value is tested again at job start by the launcher, because login nodes and compute nodes often differ.

Sources: [Claude Code authentication](https://code.claude.com/docs/en/team), [Legal and compliance](https://code.claude.com/docs/en/legal-and-compliance), [Enterprise network configuration](https://code.claude.com/docs/en/network-config).

## Architecture at a glance

&#91;embedded content: deployment architecture · laptop, login node, Slurm, compute node, scratch, API egress\]

The token is minted on the laptop and pasted into a 0600 file on the user's scratch; the login node writes configuration and submits jobs; Slurm places the job on a compute node, where the read-only image runs Claude Code against state bound from scratch. The only connection that leaves the cluster is HTTPS to Anthropic's API, directly or through the site proxy.

## 1. Container architecture and filesystem bindings

The image is a read-only SIF that holds the pinned Claude Code binary, git, Node, `uv` and a managed policy file, and nothing else: no credentials, no user state, no project code. Everything mutable is bound in from `/scratch` at launch, and the container runs with `--containall --no-home --cleanenv` so the host home directory, host environment and host `/tmp` are invisible to the agent. The only host binaries it can reach are the Slurm client commands, bound in read-only through a generated bind list.

### Definition file

The base matches the RHEL family that most university clusters run, so that host Slurm binaries bound into the container load against a compatible glibc (the container's glibc must be at least as new as the host's). On an Ubuntu host, change the base to `ubuntu:24.04` and the `dnf` lines to their `apt-get` equivalents; nothing else in the file is distribution-specific.

```text
Bootstrap: docker
From: rockylinux:9

%arguments
    CLAUDE_VERSION=stable
    NODE_MAJOR=22

%labels
    org.opencontainers.image.title Claude Code HPC runtime
    org.opencontainers.image.description Pinned Claude Code native binary with git, Node, uv and managed policy; no credentials or state inside

%help
    Run through the claude-hpc launcher. The image contains no credentials.
    Required at runtime: CLAUDE_CONFIG_DIR, HOME and TMPDIR bound to writable scratch paths.
    Policy: /etc/claude-code/managed-settings.json (read-only, cannot be overridden by user settings).

%files
    managed-settings.json /etc/claude-code/managed-settings.json
    claude-guard.sh /opt/claude-hpc/hooks/claude-guard.sh

%post
    set -euo pipefail
    dnf -y install epel-release
    dnf -y install ca-certificates curl git jq ripgrep python3 python3-pip tar gzip xz bzip2 unzip which procps-ng less file findutils diffutils patch make glibc-langpack-en
    dnf -y clean all

    # Node (for npx-based MCP servers) and uv (for Python MCP servers and project envs)
    curl -fsSL https://rpm.nodesource.com/setup_{{ NODE_MAJOR }}.x | bash -
    dnf -y install nodejs && dnf -y clean all
    curl -LsSf https://astral.sh/uv/install.sh | env UV_INSTALL_DIR=/usr/local/bin INSTALLER_NO_MODIFY_PATH=1 sh

    # Claude Code native binary, pinned, installed under a build-time HOME that stays in the image
    export HOME=/opt/claude-home
    mkdir -p "$HOME"
    curl -fsSL https://claude.ai/install.sh | bash -s "{{ CLAUDE_VERSION }}"
    ln -sf /opt/claude-home/.local/bin/claude /usr/local/bin/claude
    chmod -R a+rX /opt/claude-home

    # policy and hook files are world-readable, never writable
    chmod 644 /etc/claude-code/managed-settings.json
    chmod 755 /opt/claude-hpc/hooks/claude-guard.sh
    mkdir -p /opt/slurm-bin

%environment
    export LANG=C.UTF-8 LC_ALL=C.UTF-8
    export PATH=/opt/slurm-bin:/usr/local/bin:/opt/claude-home/.local/bin:/usr/bin:/bin
    export DISABLE_AUTOUPDATER=1
    export NPM_CONFIG_UPDATE_NOTIFIER=false
    export UV_LINK_MODE=copy

%runscript
    exec claude "$@"

%test
    claude --version
    git --version && node --version && uv --version && rg --version | head -n1
    test -r /etc/claude-code/managed-settings.json && jq empty /etc/claude-code/managed-settings.json
```

Build it where you have root or fakeroot, then copy the SIF into place. Pin a real version for reproducibility; `stable` is the installer's current stable channel.

```bash
# on a laptop or build host with egress (Apptainer 1.2+ for %arguments)
apptainer build --fakeroot --build-arg CLAUDE_VERSION=2.1.271 claude-code.sif claude-code.def
apptainer test claude-code.sif
source /scratch/$USER/claude/site.env   # on the cluster
scp claude-code.sif cluster:"$CLAUDE_HPC_ROOT/images/claude-code.sif"
```

### State relocation: every path Claude Code writes, moved off the home quota

Claude Code writes to three places by default: `~/.claude.json` (global state and onboarding flags), `~/.claude/` (settings, credentials, session transcripts under `projects/`, memory, plugins, shell snapshots, debug logs) and tool caches. One variable moves the first two, and the rest follow the XDG and per-tool conventions. The launcher sets all of them; they are listed here because the whole design depends on them.

| Variable | Value | What it relocates |
| --- | --- | --- |
| `CLAUDE_CONFIG_DIR` | `$CLAUDE_HPC_ROOT/config` | `settings.json`, `.credentials.json` (0600, written by `/login` and every token refresh), `.claude.json`, `projects/` transcripts, `memory/`, `plugins/`, `todos/`, `debug/`, `shell-snapshots/` |
| `HOME` | `$CLAUDE_HPC_ROOT/home` | `.gitconfig`, `.npmrc`, `.config`, anything a tool writes to `~`; the real home is never bound |
| `XDG_CACHE_HOME`, `XDG_DATA_HOME`, `XDG_CONFIG_HOME`, `XDG_STATE_HOME` | `$CLAUDE_HPC_ROOT/cache`, `/data`, `/xdgconfig`, `/state` | caches of `uv`, `pip`, `node`, `git`, language servers |
| `npm_config_cache`, `UV_CACHE_DIR`, `PIP_CACHE_DIR` | `$CLAUDE_HPC_ROOT/cache/{npm,uv,pip}` | package caches for `npx`-launched MCP servers and project environments |
| `TMPDIR` | `/tmp` inside, bound from `$SLURM_TMPDIR` or `$CLAUDE_HPC_ROOT/tmp` | Claude Code's temp files and the artifact scratch dir; `--containall` otherwise gives a 64 MiB session tmpfs |
| `DISABLE_AUTOUPDATER` | `1` (baked) | stops the binary trying to write a new version into the read-only image |
| `HTTPS_PROXY`, `NO_PROXY`, `NODE_EXTRA_CA_CERTS` | from `site.env` | egress through the site proxy and trust of a site CA; Claude Code honours the standard variables and does not support SOCKS |

Transcript retention is the one knob that still grows: set `cleanupPeriodDays` (section 3) so old sessions are pruned, and expect `$CLAUDE_HPC_ROOT/config/projects/` to hold hundreds of megabytes after a month of batch runs.

### Bind policy

| Bound | Mode | Why |
| --- | --- | --- |
| `$CLAUDE_HPC_ROOT` at the same path | rw | config, caches, secrets, logs, home |
| The project directory, at the same path | rw | the code being worked on; the launcher refuses a project outside `$PROJECT_ROOT` or `$CLAUDE_HPC_ROOT` |
| `$SLURM_TMPDIR` or `$CLAUDE_HPC_ROOT/tmp` → `/tmp` | rw | node-local scratch for builds and the agent's temp files |
| Slurm client stack (generated) | ro | `sbatch`, `squeue`, `sacct`, `scontrol`, `scancel`, `sinfo`, `srun`, `salloc`, their `libslurm`/`libmunge` libraries, `/etc/slurm`, and the munge socket |
| GPU devices (`--nv`) | — | only when `nvidia-smi` is on the node |

Not bound: `/home`, host `/tmp`, host `/opt` and `/usr` beyond Apptainer's default `/etc/passwd`, `/etc/group`, `/etc/hosts` and `/etc/resolv.conf` injections, any other user's scratch, `/dev/shm` of the host. `--cleanenv` strips the host environment, so `SLURM_*` variables from the enclosing job do not leak into `sbatch` submissions the agent makes (sbatch inherits allocation options from them otherwise), and no token or proxy credential reaches the container except through the explicit `--env`/`--env-file` lines.

### Slurm client passthrough

The generator below discovers the host's Slurm binaries, the libraries they link that belong to Slurm or munge, the configuration directory and the munge socket, and prints one bind argument per line for the launcher. It binds the binaries into `/opt/slurm-bin` (already on `PATH` in the image) rather than over `/usr/bin`, so the container's own tools are never shadowed.

```bash
#!/usr/bin/env bash
# slurm-binds.sh — print Apptainer bind arguments for the host Slurm client stack, one per line
set -euo pipefail
emit() { printf -- '--bind\n%s\n' "$1"; }

BINDIR=""
for cmd in sbatch squeue sacct scontrol scancel sinfo srun salloc sstat sshare sprio; do
  p="$(command -v "$cmd" 2>/dev/null || true)"; [[ -z "$p" ]] && continue
  real="$(readlink -f "$p")"
  emit "$real:/opt/slurm-bin/$cmd:ro"
  BINDIR="$(dirname "$real")"
done
[[ -z "$BINDIR" ]] && exit 0   # no Slurm on this node; launcher proceeds without passthrough

# libraries the clients link that come from Slurm, munge or their plugin trees
declare -A SEEN=()
for cmd in sbatch squeue sacct scontrol scancel sinfo srun salloc; do
  p="$(command -v "$cmd" 2>/dev/null || true)"; [[ -z "$p" ]] && continue
  while read -r lib; do
    [[ -z "$lib" || -n "${SEEN[$lib]:-}" ]] && continue
    SEEN["$lib"]=1; emit "$lib:$lib:ro"
  done < <(ldd "$(readlink -f "$p")" 2>/dev/null | awk '/slurm|munge|pmix|hwloc/ && /=>/ {print $3}')
done

# plugin directory, configuration, munge socket
PLUGDIR="$(scontrol show config 2>/dev/null | awk -F'= ' '/^PluginDir/ {print $2}' | head -n1 || true)"
[[ -n "$PLUGDIR" && -d "$PLUGDIR" ]] && emit "$PLUGDIR:$PLUGDIR:ro"
CONF="$(scontrol show config 2>/dev/null | awk -F'= ' '/^SLURM_CONF/ {print $2}' | head -n1 || true)"
CONF="${CONF:-${SLURM_CONF:-/etc/slurm/slurm.conf}}"
[[ -f "$CONF" ]] && emit "$(dirname "$CONF"):$(dirname "$CONF"):ro"
for sock in /run/munge /var/run/munge; do [[ -d "$sock" ]] && { emit "$sock:$sock"; break; }; done
printf -- '--env\nSLURM_CONF=%s\n' "$CONF"
```

If your site's security policy forbids binding the munge socket into containers, use the submit shim at the end of this section instead; the agent's `CLAUDE.md` does not change.

### The launcher: `claude-hpc`

All three execution patterns in section 5 call this script. It validates the project path, verifies egress from the node it is actually on, assembles the binds, injects the token only if one exists, and `exec`s Apptainer. Arguments pass straight through to `claude`, so `claude-hpc -p "..."`, `claude-hpc --resume`, and `claude-hpc remote-control` all work.

```bash
#!/usr/bin/env bash
# claude-hpc — launch Claude Code inside the Apptainer image with cluster-safe bindings
set -euo pipefail
SITE_ENV="${CLAUDE_HPC_ROOT:-/scratch/$USER/claude}/site.env"
[[ -r "$SITE_ENV" ]] || { echo "missing $SITE_ENV; run site-discover.sh first" >&2; exit 64; }
# shellcheck source=/dev/null
source "$SITE_ENV"

# --- self-test mode: claude-hpc --selftest -------------------------------------------------
if [[ "${1:-}" == "--selftest" ]]; then
  "$APPTAINER_BIN" exec "$CLAUDE_SIF" claude --version
  mapfile -t B < <("$CLAUDE_HPC_ROOT/bin/slurm-binds.sh" 2>/dev/null || true)
  if ((${#B[@]})); then "$APPTAINER_BIN" exec --containall --cleanenv "${B[@]}" "$CLAUDE_SIF" sbatch --version; else echo "slurm passthrough: not available on this node"; fi
  exit 0
fi

# --- project directory must be under PROJECT_ROOT or CLAUDE_HPC_ROOT ---------------------------
PROJECT="$(readlink -f "${CLAUDE_PROJECT:-$PWD}")"
case "$PROJECT" in
  "$PROJECT_ROOT"|"$PROJECT_ROOT"/*|"$CLAUDE_HPC_ROOT"/*) ;;
  *) echo "refusing to run: $PROJECT is outside $PROJECT_ROOT" >&2; exit 64 ;;
esac

# --- egress from THIS node (compute nodes differ from login nodes) --------------------------------
if [[ -n "${PROXY_URL:-}" ]]; then
  export HTTPS_PROXY="$PROXY_URL" HTTP_PROXY="$PROXY_URL" NO_PROXY="localhost,127.0.0.1"
fi
http_code="$(curl -sS -m 10 -o /dev/null -w '%{http_code}' https://api.anthropic.com/v1/models 2>/dev/null || echo 000)"
if [[ "$http_code" == "000" ]]; then
  echo "no route to api.anthropic.com from $(hostname); run on $PART_INTERACTIVE or set PROXY_URL in site.env" >&2; exit 65
fi

# --- writable scratch for /tmp inside the container -------------------------------------------
TMP_HOST="${SLURM_TMPDIR:-${TMPDIR:-$CLAUDE_HPC_ROOT/tmp}}"
mkdir -p "$TMP_HOST" "$CLAUDE_HPC_ROOT"/{config,home,cache/npm,cache/uv,cache/pip,data,xdgconfig,state,runs}

# --- optional pieces: Slurm passthrough, GPU, token file -------------------------------------------
SLURM_ARGS=(); [[ -x "$CLAUDE_HPC_ROOT/bin/slurm-binds.sh" ]] && mapfile -t SLURM_ARGS < <("$CLAUDE_HPC_ROOT/bin/slurm-binds.sh")
GPU_ARGS=(); command -v nvidia-smi >/dev/null 2>&1 && GPU_ARGS=(--nv)
TOKEN_ARGS=(); if [[ "${CLAUDE_HPC_AUTH:-token}" == "token" && -r "$CLAUDE_HPC_ROOT/secrets/claude.env" ]]; then TOKEN_ARGS=(--env-file "$CLAUDE_HPC_ROOT/secrets/claude.env"); fi   # CLAUDE_HPC_AUTH=login uses /login credentials instead
CA_ARGS=(); [[ -r /etc/pki/tls/certs/ca-bundle.crt ]] && CA_ARGS=(--bind /etc/pki/tls/certs/ca-bundle.crt:/etc/pki/tls/certs/ca-bundle.crt:ro --env NODE_EXTRA_CA_CERTS=/etc/pki/tls/certs/ca-bundle.crt)

exec "$APPTAINER_BIN" exec \
  --containall --cleanenv --no-home --pwd "$PROJECT" \
  "${GPU_ARGS[@]}" \
  --bind "$CLAUDE_HPC_ROOT:$CLAUDE_HPC_ROOT" \
  --bind "$PROJECT:$PROJECT" \
  --bind "$TMP_HOST:/tmp" \
  "${SLURM_ARGS[@]}" "${CA_ARGS[@]}" \
  --env HOME="$CLAUDE_HPC_ROOT/home" --env USER="$USER" --env LOGNAME="$USER" \
  --env TERM="${TERM:-xterm-256color}" --env TMPDIR=/tmp \
  --env CLAUDE_CONFIG_DIR="$CLAUDE_HPC_ROOT/config" \
  --env XDG_CACHE_HOME="$CLAUDE_HPC_ROOT/cache" --env XDG_DATA_HOME="$CLAUDE_HPC_ROOT/data" \
  --env XDG_CONFIG_HOME="$CLAUDE_HPC_ROOT/xdgconfig" --env XDG_STATE_HOME="$CLAUDE_HPC_ROOT/state" \
  --env npm_config_cache="$CLAUDE_HPC_ROOT/cache/npm" --env UV_CACHE_DIR="$CLAUDE_HPC_ROOT/cache/uv" --env PIP_CACHE_DIR="$CLAUDE_HPC_ROOT/cache/pip" \
  --env HTTPS_PROXY="${HTTPS_PROXY:-}" --env HTTP_PROXY="${HTTP_PROXY:-}" --env NO_PROXY="${NO_PROXY:-}" \
  --env CLAUDE_HPC_ROOT="$CLAUDE_HPC_ROOT" --env PROJECT_ROOT="$PROJECT_ROOT" \
  --env SLURM_ACCOUNT="${SLURM_ACCOUNT:-}" --env PART_INTERACTIVE="$PART_INTERACTIVE" --env PART_BATCH="$PART_BATCH" --env PART_GPU="$PART_GPU" \
  --env SLURM_JOB_ID="${SLURM_JOB_ID:-}" --env CLAUDE_HPC_MODE="${CLAUDE_HPC_MODE:-interactive}" --env CLAUDE_RUN_ID="${CLAUDE_RUN_ID:-}" \
  --env CLAUDE_MAX_ARRAY="${CLAUDE_MAX_ARRAY:-200}" --env CLAUDE_CODE_DISABLE_ARTIFACT="${CLAUDE_CODE_DISABLE_ARTIFACT:-}" \
  "${TOKEN_ARGS[@]}" \
  "$CLAUDE_SIF" claude "$@"
```

Install both scripts with `install -m 700 claude-hpc slurm-binds.sh "$CLAUDE_HPC_ROOT/bin/"` and put `$CLAUDE_HPC_ROOT/bin` on your login-shell `PATH`. `SLURM_JOB_ID` is passed through deliberately: it is the one job variable the `CLAUDE.md` rules use to tell the agent whether it is inside an allocation, and it carries no submission defaults.

### Fallback when the munge socket cannot be bound: a submit shim

Inside the container, `sbatch` becomes a script that drops the job file into a queue directory; a runner outside the container, started by the same job script, submits it with the real `sbatch` and writes the job ID back. The agent sees the same command names and output format; only the trust boundary moves.

```bash
#!/usr/bin/env bash
# sbatch (shim, installed at $CLAUDE_HPC_ROOT/shim/sbatch and bound over /opt/slurm-bin/sbatch)
set -euo pipefail
Q="$CLAUDE_HPC_ROOT/queue"; mkdir -p "$Q"
id="$(date +%s%N)-$$"
{ printf '#ARGS %q ' "$@"; printf '\n'; cat "${@: -1}"; } > "$Q/$id.sbatch"
for _ in $(seq 1 600); do
  if [[ -s "$Q/$id.result" ]]; then cat "$Q/$id.result"; rm -f "$Q/$id.result" "$Q/$id.sbatch"; exit 0; fi
  sleep 1
done
echo "sbatch shim: no runner answered within 600 s" >&2; exit 1
```

```bash
#!/usr/bin/env bash
# queue-runner.sh — run OUTSIDE the container in the same job: submits queued scripts with the real sbatch
set -euo pipefail
source "${CLAUDE_HPC_ROOT:-/scratch/$USER/claude}/site.env"
Q="$CLAUDE_HPC_ROOT/queue"; mkdir -p "$Q"
while :; do
  for f in "$Q"/*.sbatch; do
    [[ -e "$f" ]] || { sleep 2; continue 2; }
    args="$(head -n1 "$f" | sed 's/^#ARGS //')"
    body="${f%.sbatch}.job"; tail -n +2 "$f" > "$body"
    # the runner enforces the account and partition allow-list regardless of what the agent asked for
    if eval "set -- $args" && sbatch --account="${SLURM_ACCOUNT:-}" "${@:1:$#-1}" "$body" > "${f%.sbatch}.result" 2>&1; then :; fi
    mv "$f" "$f.done"
  done
  sleep 2
done
```

The same pattern covers `squeue`, `sacct` and `scancel` with a read-only runner that executes the queued command line and writes its stdout back; the agent's rules in section 4 already restrict those commands to the user's own jobs.

Sources: [Enterprise network configuration](https://code.claude.com/docs/en/network-config), [Claude Code settings](https://docs.anthropic.com/en/docs/claude-code/settings), [Sandboxing](https://docs.claude.com/en/docs/claude-code/sandboxing), [Tools reference: Bash tool behavior](https://code.claude.com/docs/en/tools-reference).

## 2. Flat-rate OAuth authentication persistence

Use two credentials for two jobs. A one-year token from `claude setup-token`, minted on the laptop and stored on scratch, authenticates every batch and non-interactive run: it never needs refreshing, so a job that starts at 03:00 cannot fail on an expired access token. A full `/login` performed once on the cluster, with the manual-code flow, authenticates interactive and Remote Control sessions: it is the only credential that can open Remote Control or publish artifacts, and the running process refreshes it. Claude Code's precedence rule decides which is used: `CLAUDE_CODE_OAUTH_TOKEN` in the environment wins over `.credentials.json`, so the launcher injects the token file only when `CLAUDE_HPC_AUTH` is `token` (the default) and leaves it out when you ask for `login`.

### Minting the token on the laptop

```bash
# laptop, already signed in to Claude Code with the claude.ai account
claude setup-token
# a browser window opens for consent; the command then prints a token of the form sk-ant-oat01-...
# valid for one year; it can only make model requests (no Remote Control, no claude.ai connectors)
```

The token is a bearer credential for your whole subscription. It belongs in exactly one place on the cluster, a file only you can read, and nowhere else: not in `.bashrc`, not in a job script, not on an `sbatch --export` line, not in a module file.

### Transferring and storing it

Paste it through an interactive prompt on the cluster so it never lands in shell history, a command line, or a log. The installer writes the env file the launcher consumes and verifies it with a one-turn request.

```bash
#!/usr/bin/env bash
# token-install.sh — store a setup token for the launcher; run on a login node
set -euo pipefail
source "${CLAUDE_HPC_ROOT:-/scratch/$USER/claude}/site.env"
umask 077
mkdir -p "$CLAUDE_HPC_ROOT/secrets"
read -rsp "Paste the token printed by 'claude setup-token' on your laptop: " TOKEN; echo
[[ "$TOKEN" == sk-ant-oat01-* ]] || { echo "that is not a setup token (expected prefix sk-ant-oat01-)" >&2; exit 65; }
printf 'CLAUDE_CODE_OAUTH_TOKEN=%s\n' "$TOKEN" > "$CLAUDE_HPC_ROOT/secrets/claude.env"
unset TOKEN
chmod 600 "$CLAUDE_HPC_ROOT/secrets/claude.env"
date -d '+1 year' +%F > "$CLAUDE_HPC_ROOT/secrets/claude.env.expires"
# verify with the smallest possible request, from a node with egress
"$CLAUDE_HPC_ROOT/bin/claude-hpc" -p 'Reply with exactly: TOKEN_OK' --max-turns 1 --model sonnet --output-format json \
  | jq -r 'if .is_error then "VERIFY FAILED: " + .result else "verified: " + .result end'
```

If you must move the token without an interactive prompt, pipe it over SSH from the laptop so it only ever exists in memory on both ends: `claude setup-token | tail -n1 | ssh cluster 'umask 077; sed "s/^/CLAUDE_CODE_OAUTH_TOKEN=/" > /scratch/$USER/claude/secrets/claude.env'`. Confirm the first line of the file starts with `CLAUDE_CODE_OAUTH_TOKEN=sk-ant-oat01-` afterwards, since the installer's output format is not guaranteed to keep the token on the last line.

### Injection into the container

The launcher passes `--env-file $CLAUDE_HPC_ROOT/secrets/claude.env` to Apptainer, which sets the variable in the container process only. Because the container runs with `--cleanenv`, the token is not inherited from the host shell and cannot be read from the host process tree by anyone but you (`/proc/<pid>/environ` is owner-readable only). Inside the container Claude Code reads the variable at startup and makes every API call with it; nothing is written to disk.

### Full `/login` for Remote Control and artifacts

On a login node, or a compute node with egress, start an interactive session without the token and complete the browser step on the laptop:

```bash
CLAUDE_HPC_AUTH=login claude-hpc
# inside Claude Code:
#   /login  → choose the claude.ai account option → choose the manual-code option
#   open the printed URL on your laptop, approve, copy the code it shows, paste it into the terminal
```

The result is `$CLAUDE_HPC_ROOT/config/.credentials.json`, mode 0600, holding an access token, a refresh token and an expiry. A running Claude Code process refreshes the access token on its own and rewrites the file, which is why `config/` must be on writable scratch and never inside the image. The login as a whole does expire: Claude Code warns at startup from five days out ("Your login expires in N days · run /login to renew"), and renewing is another `/login`. There is a documented failure mode to design around: a headless `-p` run started after the access token has already expired has been reported not to refresh it (issue #50743, v2.1.114, 401 `authentication_error`). That is the reason batch runs use the setup token and only interactive or Remote Control sessions rely on `/login`.

### Expiry, rotation and revocation

| Credential | Lifetime | Refresh | Rotation |
| --- | --- | --- | --- |
| `claude setup-token` | 1 year | none needed | run `claude setup-token` again on the laptop, replace `secrets/claude.env`, update `claude.env.expires`; a `cron` reminder 30 days before the date in that file is enough |
| `/login` credentials | access token expires in hours, refreshed in place; the login itself expires on a longer horizon | automatic while a session is running | `/login` again when the startup warning appears |

Anthropic's documentation describes generating the token but not revoking one. If the file is exposed, the available remedies are to sign out of sessions from the account's security settings on claude.ai and to contact support; change the file immediately in any case, since the launcher reads it on every start.

### Rate limits on a flat-rate plan

Subscription limits apply to the account, not to the node, so eight parallel sessions on eight nodes draw down one budget eight times faster. The structure has two layers: a rolling five-hour session window, and weekly caps (one for all models and a separate one for Opus-class models) introduced in August 2025 specifically to curb continuous background use. `/usage` inside a session shows both and their reset times; Pro and Max tiers differ by multiples, and "extra usage" credits can be enabled on the account to continue past a cap at pay-as-you-go rates, which is the sanctioned overflow path. The consumption unit is tokens per turn multiplied by turns, so an agent loop that re-reads a large log every iteration drains the window far faster than a chat does.

Strategies that work on a cluster:

- Size batch jobs to the window: one job of roughly four hours per five-hour window, chained with `--begin` so the next one starts after the reset rather than retrying into a wall.
- Default to `--model sonnet` and medium effort (`CLAUDE_CODE_EFFORT_LEVEL=medium`) for implementation runs; reserve Opus-class models for plan mode, where turns are few and reasoning matters.
- Cap turns (`--max-turns`) and context (`/compact`-friendly prompts, logs piped through `tail`), and avoid subagent fan-out in batch, since each subagent is its own context window.
- Treat a limit hit as a requeue, not a failure: Claude Code already retries transient 429/529 responses with backoff; when a `-p` run returns `is_error` with a usage-limit message, the pipeline in section 5 resubmits itself with `--begin=now+<minutes-to-reset>` and `--resume <session>` instead of looping.
- Keep it one account. Rotating accounts or pooling several users' tokens to widen the window is the behaviour Anthropic's terms prohibit; if the workload needs more than one subscription's window, it is a workload for an API key.

Sources: [Authentication precedence and credential storage](https://code.claude.com/docs/en/team), [Issue #50743: headless runs and OAuth refresh](https://github.com/anthropics/claude-code/issues/50743), [Issue #16238: env token overrides credentials file](https://github.com/anthropics/claude-code/issues/16238), [Manage usage credits for paid Claude plans](https://support.claude.com/en/articles/12429409-), [Usage limit best practices](https://support.claude.com/en/articles/9797557-usage-limit-best-practices).

## 3. Permissions and guardrails

The guardrails live in three layers with different override rights. Managed settings baked into the read-only image carry the deny rules, the hard timeouts and the guard hook; they take precedence over every other settings file, cannot be edited by the agent, and switch off `bypassPermissions` entirely. User settings on scratch carry the allow list that gives the agent autonomy over git, Python and Slurm. A PreToolUse hook closes the gap that prefix-matched permission rules leave open (`rm ./x -rf`, `xargs rm`, `git push origin main --force`) and confines writes to the project tree. Non-interactive runs add `--permission-mode dontAsk`, which turns every would-be prompt into a denial instead of a hang.

### Layer 1: `managed-settings.json` (baked into the image at `/etc/claude-code/`)

```json
{
  "$schema": "https://json.schemastore.org/claude-code-settings.json",
  "permissions": {
    "disableBypassPermissionsMode": "disable",
    "deny": [
      "Bash(sudo *)", "Bash(su *)", "Bash(su)", "Bash(doas *)",
      "Bash(rm -r*)", "Bash(rm -R*)", "Bash(rm -f -r*)", "Bash(rm -fr*)", "Bash(rm -fR*)", "Bash(rm --recursive*)",
      "Bash(find * -delete*)", "Bash(find * -exec rm*)", "Bash(shred *)",
      "Bash(git push --force*)", "Bash(git push -f*)", "Bash(git reset --hard*)", "Bash(git clean *)",
      "Bash(chmod -R *)", "Bash(chown -R *)", "Bash(chgrp -R *)",
      "Bash(dd *)", "Bash(mkfs*)", "Bash(fdisk *)", "Bash(shutdown*)", "Bash(reboot*)", "Bash(systemctl *)",
      "Bash(kill -9 -1*)", "Bash(pkill *)", "Bash(killall *)", "Bash(nohup *)", "Bash(setsid *)", "Bash(crontab *)",
      "Bash(ssh *)", "Bash(scp *)", "Bash(sftp *)", "Bash(nc *)", "Bash(ncat *)", "Bash(telnet *)", "Bash(socat *)",
      "Bash(sacctmgr *)", "Bash(scontrol update*)", "Bash(scontrol hold*)", "Bash(scontrol release*)",
      "Bash(scontrol requeue*)", "Bash(scontrol reconfigure*)", "Bash(scontrol cancel*)",
      "Bash(scancel -A *)", "Bash(scancel --account*)", "Bash(scancel -p *)", "Bash(scancel --partition*)",
      "Read(//scratch/**/claude/secrets/**)", "Read(//home/**)", "Read(~/.ssh/**)",
      "Read(**/.env)", "Read(**/.env.*)", "Read(**/*.pem)", "Read(**/id_rsa*)", "Read(**/id_ed25519*)", "Read(**/.netrc)",
      "Edit(//scratch/**/claude/config/**)", "Edit(//scratch/**/claude/bin/**)", "Edit(//scratch/**/claude/hooks/**)",
      "Edit(//scratch/**/claude/images/**)", "Edit(//scratch/**/claude/site.env)",
      "Edit(//etc/**)", "Edit(//usr/**)", "Edit(//opt/**)", "Edit(//var/**)", "Edit(//boot/**)", "Edit(//home/**)"
    ]
  },
  "env": {
    "BASH_DEFAULT_TIMEOUT_MS": "600000",
    "BASH_MAX_TIMEOUT_MS": "1800000",
    "MCP_TIMEOUT": "30000",
    "MCP_TOOL_TIMEOUT": "600000",
    "MAX_MCP_OUTPUT_TOKENS": "25000",
    "CLAUDE_CODE_TOOL_MEMORY_LIMIT": "16G",
    "DISABLE_AUTOUPDATER": "1"
  },
  "sandbox": { "enabled": false },
  "hooks": {
    "PreToolUse": [
      { "matcher": "Bash|PowerShell",
        "hooks": [ { "type": "command", "command": "/opt/claude-hpc/hooks/claude-guard.sh", "timeout": 10 } ] },
      { "matcher": "Edit|Write|NotebookEdit",
        "hooks": [ { "type": "command", "command": "/opt/claude-hpc/hooks/claude-guard.sh", "timeout": 10 } ] }
    ]
  }
}
```

Three design points. Deny rules are evaluated before ask and allow rules, so nothing in a user or project file can re-enable them, and a `Read` deny also blocks `Edit` and `Write` on the same path. The `//` prefix anchors a path pattern at the filesystem root, which lets one image serve every user's `/scratch/<user>/claude/secrets` without knowing the username at build time. The sandbox is off because Claude Code's bubblewrap sandbox cannot normally nest inside an unprivileged Apptainer; the container itself is the isolation layer. On sites whose Apptainer permits unprivileged user namespaces, `{ "enabled": true, "enableWeakerNestedSandbox": true, "failIfUnavailable": false }` adds a second layer and falls back silently when it cannot start.

### Layer 2: user `settings.json` on scratch

The installer below writes `$CLAUDE_HPC_ROOT/config/settings.json` with the one absolute path it needs. `acceptEdits` auto-approves file edits inside the project; the allow list auto-approves the shell commands a research workflow uses; `ask` covers reversible-but-costly actions, which interactive sessions can approve and batch runs cannot.

```bash
#!/usr/bin/env bash
# settings-install.sh — write the user-level settings.json into CLAUDE_CONFIG_DIR
set -euo pipefail
source "${CLAUDE_HPC_ROOT:-/scratch/$USER/claude}/site.env"
umask 077
mkdir -p "$CLAUDE_HPC_ROOT/config" "$CLAUDE_HPC_ROOT/runs"
cat > "$CLAUDE_HPC_ROOT/config/settings.json" <<EOF
{
  "\$schema": "https://json.schemastore.org/claude-code-settings.json",
  "model": "sonnet",
  "cleanupPeriodDays": 14,
  "includeCoAuthoredBy": true,
  "askUserQuestionTimeout": "10m",
  "permissions": {
    "defaultMode": "acceptEdits",
    "additionalDirectories": ["$CLAUDE_HPC_ROOT/runs"],
    "allow": [
      "Read", "Edit", "Write", "Glob", "Grep", "LSP", "NotebookEdit", "WebSearch",
      "WebFetch(domain:code.claude.com)", "WebFetch(domain:docs.python.org)", "WebFetch(domain:slurm.schedmd.com)",
      "WebFetch(domain:github.com)", "WebFetch(domain:pypi.org)", "WebFetch(domain:apptainer.org)",
      "Bash(git status*)", "Bash(git diff*)", "Bash(git log*)", "Bash(git show*)", "Bash(git branch*)",
      "Bash(git switch*)", "Bash(git checkout -b *)", "Bash(git add *)", "Bash(git commit *)", "Bash(git stash*)",
      "Bash(git fetch*)", "Bash(git pull*)", "Bash(git merge*)", "Bash(git tag*)", "Bash(git restore --staged *)",
      "Bash(python *)", "Bash(python3 *)", "Bash(uv run *)", "Bash(uv sync*)", "Bash(uv add *)", "Bash(uv pip *)",
      "Bash(uv venv*)", "Bash(uv lock*)", "Bash(pytest*)", "Bash(ruff *)", "Bash(mypy *)", "Bash(black *)",
      "Bash(pip install *)", "Bash(pip list*)", "Bash(pip show*)", "Bash(pip freeze*)",
      "Bash(make*)", "Bash(cmake *)", "Bash(ninja *)",
      "Bash(ls*)", "Bash(cat *)", "Bash(head *)", "Bash(tail *)", "Bash(wc *)", "Bash(du *)", "Bash(df *)",
      "Bash(find *)", "Bash(grep *)", "Bash(rg *)", "Bash(sort *)", "Bash(uniq *)", "Bash(cut *)", "Bash(awk *)",
      "Bash(sed -n *)", "Bash(jq *)", "Bash(tree *)", "Bash(file *)", "Bash(stat *)", "Bash(diff *)",
      "Bash(mkdir *)", "Bash(cp *)", "Bash(mv *)", "Bash(touch *)", "Bash(ln -s *)",
      "Bash(tar *)", "Bash(gzip *)", "Bash(gunzip *)", "Bash(zip *)", "Bash(unzip *)",
      "Bash(env)", "Bash(printenv *)", "Bash(which *)", "Bash(echo *)", "Bash(date*)", "Bash(sleep *)",
      "Bash(nproc*)", "Bash(free *)", "Bash(nvidia-smi*)", "Bash(module *)", "Bash(ml *)",
      "Bash(sbatch *)", "Bash(squeue *)", "Bash(sacct *)", "Bash(sinfo*)", "Bash(scontrol show *)",
      "Bash(sstat *)", "Bash(sprio *)", "Bash(sshare *)", "Bash(seff *)"
    ],
    "ask": [
      "Bash(scancel *)", "Bash(git push*)", "Bash(git rebase*)", "Bash(git checkout -- *)", "Bash(git restore *)",
      "Bash(rm *)", "Bash(salloc *)", "Bash(srun *)", "Bash(curl *)", "Bash(wget *)",
      "Bash(pip uninstall *)", "Bash(uv remove *)", "Bash(npm *)", "Bash(npx *)", "WebFetch"
    ]
  },
  "env": {
    "CLAUDE_CODE_EFFORT_LEVEL": "medium",
    "DISABLE_TELEMETRY": "1",
    "DISABLE_ERROR_REPORTING": "1"
  }
}
EOF
jq empty "$CLAUDE_HPC_ROOT/config/settings.json" && echo "wrote $CLAUDE_HPC_ROOT/config/settings.json"
```

Bash rules are prefix matches with `*` wildcards; Claude Code strips wrappers such as `timeout 30` and `xargs` before matching, so `Bash(pytest*)` also covers `timeout 600 pytest -q`. Project-level `.claude/settings.json` files can add allow rules for a repository's own commands (`Bash(snakemake *)`, `Bash(nextflow *)`) without touching this file.

### Layer 3: the guard hook

Permission rules see the start of a command; the hook sees the whole string and the resolved target path. It blocks by exiting 2 with the reason on stderr, which Claude Code feeds back to the model so it adjusts instead of retrying variants, and it downgrades two borderline cases to a prompt with the hook's JSON `ask` decision.

```bash
#!/usr/bin/env bash
# claude-guard.sh — PreToolUse hook for Bash, PowerShell, Edit, Write and NotebookEdit
# exit 0 = allow, exit 2 = block (reason on stderr reaches the model), JSON on stdout = ask
set -euo pipefail
input="$(cat)"
tool="$(jq -r '.tool_name' <<<"$input")"
cwd="$(jq -r '.cwd // empty' <<<"$input")"
root="${CLAUDE_PROJECT_DIR:-$cwd}"
hpc="${CLAUDE_HPC_ROOT:-/scratch/$USER/claude}"
max_array="${CLAUDE_MAX_ARRAY:-200}"
deny() { printf 'claude-guard: blocked (%s). %s\n' "$1" "$2" >&2; exit 2; }
ask()  { jq -cn --arg r "$1" '{hookSpecificOutput:{hookEventName:"PreToolUse",permissionDecision:"ask",permissionDecisionReason:$r}}'; exit 0; }

case "$tool" in
  Edit|Write|NotebookEdit)
    f="$(jq -r '.tool_input.file_path // .tool_input.notebook_path // empty' <<<"$input")"
    [[ -z "$f" ]] && exit 0
    [[ "$f" != /* ]] && f="$cwd/$f"
    f="$(readlink -m "$f")"
    case "$f" in
      "$hpc"/secrets/*|"$hpc"/config/*|"$hpc"/bin/*|"$hpc"/hooks/*|"$hpc"/images/*|"$hpc"/site.env)
        deny "protected path" "$f is Claude Code infrastructure, not project code" ;;
      "$root"/*|/tmp/*|"$hpc"/runs/*) exit 0 ;;
      *) deny "write outside project" "$f is outside $root, /tmp and $hpc/runs" ;;
    esac ;;

  Bash|PowerShell)
    cmd="$(jq -r '.tool_input.command // empty' <<<"$input")"
    [[ -z "$cmd" ]] && exit 0
    c="$(printf '%s' "$cmd" | tr '\n' ' ' | sed -E 's/[[:space:]]+/ /g; s/^ *(command|exec|time|nice( -n [0-9]+)?|timeout [0-9smh]+|env) //')"

    # 1. recursive or forced deletion in any spelling
    if grep -Eq '(^|[;&|] *)(/bin/|/usr/bin/)?rm +(-[a-zA-Z]*[rR][a-zA-Z]* |--recursive)|(^|[;&|] *)rm .* -[a-zA-Z]*[rR]|find .* (-delete|-exec +(rm|shred))|xargs +(-[a-zA-Z0-9]+ +)*rm|git +clean +-[a-zA-Z]*f|(^|[;&|] *)shred ' <<<"$c"; then
      deny "recursive deletion" "delete named files one at a time, or ask the user"; fi
    # 2. deleting a root: /, $HOME, /scratch, /work, /tmp, the current directory or its parent
    if grep -Eq '(^|[;&|] *)rm +(-[a-zA-Z]+ +)*("?\$HOME"?|~|/|/scratch|/work|/tmp|\.|\.\.)/?( |$)' <<<"$c"; then
      deny "root deletion" "refusing to delete a top-level directory"; fi
    # 3. privilege, device and system operations
    if grep -Eq '(^|[;&|] *)((sudo|su|doas|chroot|mount|umount|dd|fdisk|parted|shutdown|reboot|systemctl|modprobe|insmod)( |$)|mkfs[. ]|sysctl +-w)' <<<"$c"; then
      deny "privileged operation" "the container is unprivileged; no system changes"; fi
    if grep -Eq '> */dev/(sd|nvme|mem|kmem|hd)' <<<"$c"; then deny "device write" "refusing raw device writes"; fi
    # 4. recursive permission changes
    if grep -Eq '(^|[;&|] *)(chmod|chown|chgrp) +(-[a-zA-Z]*R|--recursive)' <<<"$c"; then
      deny "recursive chmod/chown" "change permissions on named files only"; fi
    # 5. processes that outlive the job, mass kills, fork bombs
    if grep -Eq '(^|[;&|] *)(nohup|setsid|disown|at|crontab|pkill|killall)( |$)|kill +-9 +-1' <<<"$c"; then
      deny "daemon or mass kill" "background work must stay inside this job's allocation"; fi
    if grep -Eq ':\(\) *\{ *:\|:& *\};' <<<"$c"; then deny "fork bomb" "no"; fi
    # 6. remote shells, transfers off the cluster, pipe-to-shell
    if grep -Eq '(^|[;&|] *)(ssh|scp|sftp|nc|ncat|telnet|socat)( |$)|rsync[^|;&]* [^ /]+:' <<<"$c"; then
      deny "remote shell or transfer" "data leaves the cluster only through the user"; fi
    if grep -Eq '(curl|wget)[^|]*\| *(ba|z|da|k)?sh( |$)' <<<"$c"; then
      deny "pipe to shell" "download to a file and inspect it before running"; fi
    # 7. Slurm: scheduler administration and other users' jobs
    if grep -Eq '(^|[;&|] *)(sacctmgr( |$)|scontrol +(update|hold|release|requeue|reconfigure|cancel|create|delete))' <<<"$c"; then
      deny "scheduler administration" "only scontrol show is permitted"; fi
    if grep -Eq '(^|[;&|] *)scancel .*(-u|--user[= ]|-A|--account[= ]|-p|--partition[= ])' <<<"$c" \
       && ! grep -Eq "scancel .*(-u|--user[= ]) *$USER( |$)" <<<"$c"; then
      deny "scancel scope" "cancel only your own job IDs"; fi
    if grep -Eq "(^|[;&|] *)scancel .*(-u|--user[= ]) *$USER( |$)" <<<"$c"; then
      ask "scancel -u would cancel every job you own; confirm"; fi
    # 8. job-array size cap; --wrap bypasses job-script review
    re='--array[= ]+([0-9]+)-([0-9]+)'
    if [[ "$c" =~ $re ]]; then
      n=$(( BASH_REMATCH[2] - BASH_REMATCH[1] + 1 ))
      (( n > max_array )) && deny "array too large" "arrays are capped at $max_array tasks; use %k throttling or loop inside the task"
    fi
    if grep -Eq '(^|[;&|] *)sbatch .*--wrap' <<<"$c"; then ask "sbatch --wrap skips the job-script file; write a .sbatch file instead"; fi
    # 9. git history rewrites, force pushes, working-tree wipes
    if grep -Eq 'git +(push +[^|;&]*(-f|--force)|reset +--hard|branch +-D|checkout +-- *\.( |$)|filter-branch|filter-repo)' <<<"$c"; then
      deny "git history or working-tree destruction" "use a new branch or a revert commit"; fi
    exit 0 ;;

  *) exit 0 ;;
esac
```

The hook runs with `CLAUDE_PROJECT_DIR` set by Claude Code and `CLAUDE_HPC_ROOT` passed by the launcher, so it needs no site edits. `CLAUDE_MAX_ARRAY` raises the array cap per job if a workflow legitimately needs more tasks.

### Timeouts and resource caps

Nothing in Claude Code sets a wall-clock limit on the agent as a whole; that limit comes from Slurm and from the job script. The settings above bound every individual step, and section 5 bounds the whole run.

| Limit | Where | Value | Effect |
| --- | --- | --- | --- |
| Per-command timeout | managed `env` | `BASH_DEFAULT_TIMEOUT_MS=600000`, `BASH_MAX_TIMEOUT_MS=1800000` | A command without an explicit timeout stops after 10 minutes; the model can request up to 30; past that the command is backgrounded, never left hanging in the foreground |
| Tool memory | managed `env` | `CLAUDE_CODE_TOOL_MEMORY_LIMIT=16G` | cgroup cap on Bash, PowerShell and Monitor commands where the container can create one; silently uncapped where it cannot |
| MCP | managed `env` | `MCP_TIMEOUT=30000`, `MCP_TOOL_TIMEOUT=600000`, `MAX_MCP_OUTPUT_TOKENS=25000` | Server start and tool-call ceilings; output truncation |
| Background watches | built in | 30 minutes maximum per `Monitor` watch, 10 in `-p` runs | A watch never outlives a job window |
| Unanswered questions | user settings | `askUserQuestionTimeout=10m` | A question in an unattended tmux session closes itself and the agent proceeds on its own judgement |
| Agent turns | job script | `--max-turns` | Bounds the number of model calls in a non-interactive run |
| Wall clock | job script | `timeout --signal=INT --kill-after=60 <seconds>` derived from the Slurm time limit | The agent receives SIGINT, writes its final result, and the job ends before Slurm kills it |

Sources: [Claude Code settings](https://docs.anthropic.com/en/docs/claude-code/settings), [Permissions](https://code.claude.com/docs/en/permissions), [Tools reference](https://code.claude.com/docs/en/tools-reference), [Sandboxing](https://docs.claude.com/en/docs/claude-code/sandboxing).

## 4. `CLAUDE.md` blueprint for HPC

`CLAUDE.md` is loaded into the system prompt of every session and every subagent, so it is where cluster facts and etiquette are enforced as standing instructions rather than repeated in prompts. The blueprint below is a project-level file committed to the repository root; it reads the account and partition names from the environment the launcher exports (`SLURM_ACCOUNT`, `PART_BATCH`, `PART_GPU`, `PART_INTERACTIVE`) so one file works for every user of the repository. A dedicated subagent is the only agent allowed to submit jobs, and a skill holds the job-script template so the agent never writes an `sbatch` header from memory. The slash command that manages subagents is `/agents`; `/agent` is not a command.

### `CLAUDE.md`

```markdown
# Project operating rules for Claude Code on this cluster

You are running inside an Apptainer container on a shared Slurm cluster, as one user, under
that user's own subscription. Two facts decide what you may do:

- If `SLURM_JOB_ID` is set, you are inside a compute allocation and may run work here.
- If it is not set, you are on a login node: edit, inspect, submit and monitor only. Never run
  anything that uses more than one CPU core for more than 60 seconds, loads a GPU, or exceeds
  4 GB of memory on a login node. Submit it with sbatch instead.

## Paths

- Project code: this directory (`$CLAUDE_PROJECT_DIR`). Write results under `results/`, job
  scripts under `jobs/`, logs under `logs/`. These are the only places you write inside the repo
  besides source files.
- Node-local scratch for a running job: `$SLURM_TMPDIR` if set, else `/tmp`. Stage large inputs
  there, write outputs there, copy final outputs back to `results/` before the job ends.
- `$CLAUDE_HPC_ROOT/runs/` holds run manifests and status files for non-interactive sessions.
- Never write to `$HOME`, to another user's space, or to any path under `$CLAUDE_HPC_ROOT`
  other than `runs/`.

## Slurm on this cluster

- Account: `$SLURM_ACCOUNT` (empty means the site default; omit `--account` then).
- Partitions: `$PART_BATCH` for CPU jobs, `$PART_GPU` for GPU jobs, `$PART_INTERACTIVE`
  for short tests under 30 minutes. Confirm limits with `sinfo -s -p <partition>` and
  `scontrol show partition <partition>` before the first submission of a session; do not guess
  `MaxTime`, `MaxMemPerNode` or GPU counts.
- Submit with a job-script file under `jobs/`, never `sbatch --wrap`, so the script is reviewable
  and re-runnable. Use the template in the `slurm-submit` skill.
- One task at a time: at most 4 of your jobs pending or running concurrently, and arrays no
  larger than 200 tasks (use `--array=1-1000%20` style throttling only when the user asks).
- Only the `slurm-operator` subagent submits, monitors or cancels jobs. Other subagents write
  code and job scripts and return; they never call sbatch, srun, salloc or scancel.

## Resource etiquette

- Request what the work needs, measured, not what the node has. First run of a new script:
  `--time` at twice your estimate, `--mem` at 8 GB per task, `--cpus-per-task` equal to the
  thread count the code actually uses, and set `OMP_NUM_THREADS=$SLURM_CPUS_PER_TASK`.
- After the first completed job, read `seff <jobid>` and `sacct -j <jobid> --format=JobID,
  Elapsed,MaxRSS,TotalCPU,State` and resize the next submission to 1.5x the observed peak.
- GPUs: `--gres=gpu:1` only for code that uses one, on `$PART_GPU`; never request a GPU for
  preprocessing or tests.
- Never request whole nodes (`--exclusive`), never use `--qos` or `--reservation` values the
  user did not name, and never submit to a partition that is not listed above.
- Long jobs checkpoint: add `--signal=B:USR1@300` and trap it so the job saves state before
  the time limit; prefer resumable scripts over longer `--time`.

## Monitoring

- `squeue --me -o "%.10i %.12j %.9P %.2t %.10M %.6D %R"` lists your jobs; check at most once a
  minute and never in a tight loop. For jobs expected under 20 minutes, submit with
  `sbatch --wait` in a background Bash command and read the log when it returns.
- After every job: read the last 50 lines of its log, check `sacct -j <jobid> -o State,ExitCode`
  and treat any state other than COMPLETED as a failure to diagnose, not a job to resubmit.
  Never resubmit an unchanged failing script more than once.
- Record every submission in `runs/jobs.tsv` as `timestamp<TAB>jobid<TAB>script<TAB>purpose`.

## Software environment

- Python: `uv run` inside the project (`pyproject.toml` is the source of truth); `uv sync`
  after dependency changes. No system `pip install`.
- Site modules (`module load ...`) are available on the host, not inside this container:
  put `module load` lines in the job script, never in commands you run here.
- Job scripts run on the host: they call `apptainer exec` on the image recorded in
  `jobs/_template.sbatch` for the project's runtime, not on the Claude Code image.

## Non-interactive runs

- When `CLAUDE_HPC_MODE=batch` is set there is no one to ask. Make the safest reasonable
  choice, record it in `runs/$CLAUDE_RUN_ID/STATUS.md`, and continue.
- Keep `runs/$CLAUDE_RUN_ID/STATUS.md` current: what is done, what is running (job IDs),
  what is next. If you receive an interrupt, finish the current file edit, update STATUS.md,
  and stop; a later run resumes from it.

## Data

- Scratch filesystems are purged on a schedule; anything that matters is copied to `results/`
  and committed or listed in `results/MANIFEST.md` the same session.
- No protected health information, no export-controlled data, no credentials in the repo or
  in prompts. If an input looks like it contains any of these, stop and say so.

@docs/cluster-notes.md
```

The trailing import pulls in a site-specific `docs/cluster-notes.md` (purge policy, filesystem quotas, module names, known partition quirks) that changes more often than the rules above; keep that file short and factual.

### The job-submission subagent: `.claude/agents/slurm-operator.md`

Subagents inherit `CLAUDE.md` but get their own tool list and turn cap. Restricting submission to one agent means the guard hook, the permission rules and these instructions all apply at a single point, and an implementer subagent cannot queue jobs as a side effect of "testing".

```markdown
---
name: slurm-operator
description: Submits, monitors and reports on Slurm jobs for this project. Use for anything that needs sbatch, squeue, sacct, seff or scancel. Never edits source code.
tools: Bash, Read, Glob, Grep
model: sonnet
maxTurns: 40
---

You are the only agent that talks to Slurm. You receive a job script path or a monitoring
request and return a short factual report.

Before submitting:
1. Read the script. Refuse it if it lacks `--time`, `--mem` or `--mem-per-cpu`, `--cpus-per-task`,
   `--output`, `--job-name`, or uses a partition other than `$PART_BATCH`, `$PART_GPU`,
   `$PART_INTERACTIVE`, or asks for `--exclusive`, a QoS, or a reservation.
2. Count the user's current jobs with `squeue --me -h | wc -l`; if 4 or more are queued or
   running, report that and do not submit.
3. Submit with `sbatch --parsable <script>`, append a line to `runs/jobs.tsv`, and report the job ID.

When monitoring: use `squeue --me`, `sacct -j <id> -o JobID,State,Elapsed,MaxRSS,ExitCode`,
and `seff <id>` for completed jobs. Read the last 50 lines of the job log. Report state, resource
usage versus request, and the exact error text if it failed. Do not resubmit; the main agent decides.

Cancel only a job ID the main agent names, with `scancel <id>`, and confirm it disappeared
from `squeue --me`.
```

### The job-script skill: `.claude/skills/slurm-submit/SKILL.md`

A skill loads on demand when the task matches its description, so the template costs no context until a job script is being written. The template encodes every rule the operator checks, which makes compliance the default rather than a correction.

```markdown
---
name: slurm-submit
description: Write a Slurm job script for this cluster from the project template, with correct partition, account, resources, checkpoint signal and container invocation. Use whenever a task must run as a batch job.
---

Copy `jobs/_template.sbatch` to `jobs/<purpose>.sbatch`, fill the marked lines, and hand the path
to the `slurm-operator` subagent. Rules:

- Resources come from measurement: for a new script use `--time` at 2x the estimate, `--mem=8G`,
  `--cpus-per-task` equal to the thread count the code uses. After one completed run, resize to
  1.5x the peak reported by `seff`.
- GPU jobs: `--partition=$PART_GPU --gres=gpu:1`; everything else `--partition=$PART_BATCH`.
- Stage inputs to `$SLURM_TMPDIR`, write outputs there, copy back with `rsync -a` to `results/`
  at the end and in the USR1 trap.
- The script runs the project's runtime container, not the Claude Code image. Record the image
  path in `jobs/_template.sbatch` once.
```

```bash
#!/usr/bin/env bash
#SBATCH --job-name=CHANGE_ME
#SBATCH --partition=general
#SBATCH --time=02:00:00
#SBATCH --cpus-per-task=4
#SBATCH --mem=8G
#SBATCH --output=logs/%x-%j.out
#SBATCH --error=logs/%x-%j.err
#SBATCH --signal=B:USR1@300
# jobs/_template.sbatch — the slurm-operator refuses scripts that drop any header line above.
# Add on GPU jobs:  #SBATCH --gres=gpu:1   and set --partition to the GPU partition.
# Add when SLURM_ACCOUNT is non-empty:  #SBATCH --account=<value of $SLURM_ACCOUNT>
set -euo pipefail
export OMP_NUM_THREADS="${SLURM_CPUS_PER_TASK:-1}"
PROJECT="${SLURM_SUBMIT_DIR}"
RUNTIME_SIF="$PROJECT/env/runtime.sif"          # the project's own runtime image, built separately
WORK="${SLURM_TMPDIR:-/tmp/$USER-$SLURM_JOB_ID}"; mkdir -p "$WORK/in" "$WORK/out"

save() { rsync -a "$WORK/out/" "$PROJECT/results/$SLURM_JOB_NAME-$SLURM_JOB_ID/"; }
trap 'echo "USR1: time limit near, saving"; save; exit 0' USR1

rsync -a "$PROJECT/data/" "$WORK/in/"
module load apptainer 2>/dev/null || true
apptainer exec --nv --bind "$WORK:/work" --bind "$PROJECT:/project" "$RUNTIME_SIF" \
  python /project/src/run.py --input /work/in --output /work/out &   # background so the trap can fire
wait $!
save
```

The `--partition=general` line is the one value in the template that is site-specific; `site-discover.sh` reports the real name as `PART_BATCH`, and the skill tells the agent to substitute it. Keeping it literal in the template means a human can also submit the script without the Claude Code environment.

Sources: [Manage Claude's memory (CLAUDE.md)](https://code.claude.com/docs/en/memory), [Subagents](https://code.claude.com/docs/en/sub-agents), [Skills](https://code.claude.com/docs/en/skills), [Tools reference: Agent tool behavior](https://code.claude.com/docs/en/tools-reference).

## 5. Execution matrix and lifecycle

The three patterns share the launcher and the policy files; they differ in who drives the session and how the job's time limit is handled. Interactive allocations are driven by you at the keyboard; persistent workspaces run `claude remote-control` inside a job so you drive them from a browser or phone and re-attach with `tmux` when you want the terminal; the pipeline runs `claude -p` with a session ID it can resume in the next job window.

| Pattern | Runs on | Auth | Driven by | Ends when |
| --- | --- | --- | --- | --- |
| 1 Interactive allocation | compute node, `srun --pty` | token or `/login` | your terminal | you exit or `--time` expires |
| 2 Persistent workspace | compute node, batch job | `/login` (Remote Control) | claude.ai/code, the mobile app, or `tmux attach` | `--time` expires (USR1 trap exits cleanly) |
| 3 Non-interactive pipeline | compute node, batch job | token | a task file; resumes itself across windows | the agent reports DONE, or the continuation cap is reached |

### Pattern 1: interactive compute allocation

```bash
#!/usr/bin/env bash
# claude-interactive.sh [hours] [cpus] [mem] [gpus] — Claude Code at your keyboard, inside an allocation
set -euo pipefail
source "${CLAUDE_HPC_ROOT:-/scratch/$USER/claude}/site.env"
HOURS="${1:-4}"; CPUS="${2:-4}"; MEM="${3:-16G}"; GPUS="${4:-0}"
export CLAUDE_PROJECT="${CLAUDE_PROJECT:-$PWD}"
ACCT=(); [[ -n "${SLURM_ACCOUNT:-}" ]] && ACCT=(--account="$SLURM_ACCOUNT")
PART="$PART_INTERACTIVE"; GRES=()
if (( GPUS > 0 )); then PART="$PART_GPU"; GRES=(--gres="gpu:$GPUS"); fi
exec srun "${ACCT[@]}" --partition="$PART" --time="${HOURS}:00:00" --cpus-per-task="$CPUS" --mem="$MEM" "${GRES[@]}" \
  --job-name=claude-interactive --pty \
  bash -lc 'cd "$CLAUDE_PROJECT" && exec "$CLAUDE_HPC_ROOT/bin/claude-hpc"'
```

`srun` propagates your login environment to the compute node, so `CLAUDE_PROJECT` and `CLAUDE_HPC_ROOT` arrive intact; the launcher then strips everything again with `--cleanenv` before Claude Code starts. On sites that provide `sinteractive` or require `salloc`, request the allocation that way and run `claude-hpc` from the resulting shell; the launcher does not care how the allocation was obtained. For editing-only work on a login node, `claude-hpc` runs there directly, and the `CLAUDE.md` rules keep it from computing.

### Pattern 2: persistent background workspace

The workspace is a batch job that starts a `tmux` server on the compute node's local disk (Unix sockets do not work on Lustre or NFS), runs `claude remote-control` inside it with the `/login` credential, and waits. You drive the session from claude.ai/code or the Claude mobile app, and attach the terminal with `srun --overlap` when you want it. Two minutes before the time limit the job receives USR1, tells Claude Code to exit, and ends on its own.

```bash
#!/usr/bin/env bash
#SBATCH --job-name=claude-ws
#SBATCH --time=08:00:00
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --signal=B:USR1@120
# claude-workspace.sbatch — submit with claude-workspace.sh; partition, account and output path come from there
set -euo pipefail
source "$CLAUDE_HPC_ROOT/site.env"
: "${CLAUDE_PROJECT:?set by claude-workspace.sh}"
SOCK="${SLURM_TMPDIR:-/tmp}/claude-$SLURM_JOB_ID.sock"
export CLAUDE_HPC_AUTH=login            # Remote Control needs the /login credential, not the setup token
export CLAUDE_HPC_MODE=interactive

tmux -S "$SOCK" new-session -d -s claude -c "$CLAUDE_PROJECT" \
  "$CLAUDE_HPC_ROOT/bin/claude-hpc remote-control --name ws-$SLURM_JOB_ID; sleep 20"

cat <<EOF
workspace job $SLURM_JOB_ID on $(hostname)
  browser/phone : open claude.ai/code and pick the session named ws-$SLURM_JOB_ID
  terminal      : srun --jobid=$SLURM_JOB_ID --overlap --pty tmux -S $SOCK attach -t claude
  stop          : scancel $SLURM_JOB_ID
EOF

shutdown() {
  tmux -S "$SOCK" send-keys -t claude C-c '' 2>/dev/null || true
  sleep 3
  tmux -S "$SOCK" send-keys -t claude '/exit' Enter 2>/dev/null || true
  for _ in $(seq 1 20); do tmux -S "$SOCK" has-session -t claude 2>/dev/null || break; sleep 3; done
  tmux -S "$SOCK" kill-server 2>/dev/null || true
}
trap shutdown USR1 TERM
while tmux -S "$SOCK" has-session -t claude 2>/dev/null; do sleep 30 & wait $!; done
```

```bash
#!/usr/bin/env bash
# claude-workspace.sh [hours] — submit the persistent workspace job for the current project
set -euo pipefail
source "${CLAUDE_HPC_ROOT:-/scratch/$USER/claude}/site.env"
HOURS="${1:-8}"
export CLAUDE_PROJECT="${CLAUDE_PROJECT:-$PWD}"
[[ -s "$CLAUDE_HPC_ROOT/config/.credentials.json" ]] || { echo "no /login credential yet: run  CLAUDE_HPC_AUTH=login claude-hpc  and /login first" >&2; exit 65; }
ACCT=(); [[ -n "${SLURM_ACCOUNT:-}" ]] && ACCT=(--account="$SLURM_ACCOUNT")
mkdir -p "$CLAUDE_HPC_ROOT/runs/workspace"
sbatch --parsable "${ACCT[@]}" --partition="$PART_BATCH" --time="${HOURS}:00:00" \
  --export=ALL,CLAUDE_HPC_ROOT="$CLAUDE_HPC_ROOT",CLAUDE_PROJECT="$CLAUDE_PROJECT" \
  --output="$CLAUDE_HPC_ROOT/runs/workspace/%x-%j.out" \
  "$CLAUDE_HPC_ROOT/bin/claude-workspace.sbatch"
```

The `while ... sleep 30 & wait` loop is what lets the USR1 trap run promptly; a bare `sleep` would delay it. `--overlap` is required on Slurm 20.11 and later to start a second step inside a running allocation; sites that enable `pam_slurm_adopt` also allow `ssh <node>` followed by the same `tmux attach`. `claude-workspace.sh` refuses to submit until a `/login` credential exists, because Remote Control with only the setup token fails with `Remote Control requires a claude.ai subscription`. If `tmux` is absent on compute nodes, `screen -dmS claude ...` and `screen -r claude` are the drop-in replacements.

### Pattern 3: resumable non-interactive pipeline

A task file holds the multi-step prompt. The job computes its own wall-clock budget from Slurm, runs `claude -p` under `timeout` with a fixed session ID, captures the stream as JSONL, reads the final `result` event, and resubmits itself with `--resume` when the window closed before the agent reported DONE. A usage-limit error becomes a delayed resubmission rather than a retry loop.

```markdown
# runs/example/task.md — a multi-step task for the pipeline
Goal: add a `toolbox validate` CLI subcommand that checks every dataset manifest under data/ against
schema/manifest.json, with tests, and verify it on the real data as a batch job.

Steps:
1. Read docs/specs/validate.md and the existing CLI in src/toolbox/cli.py. Plan before editing.
2. Implement the subcommand with jsonschema; write tests in tests/test_validate.py first and make
   them pass with `uv run pytest -q tests/test_validate.py`.
3. Write jobs/validate-all.sbatch from the slurm-submit skill (CPU partition, 1 hour, 4 GB) that
   runs the subcommand over data/ and writes results/validate-report.json.
4. Ask the slurm-operator subagent to submit it and wait for completion (use sbatch --wait in a
   background command). Read the log and the report.
5. Fix any failures that are code bugs; do not edit datasets. Commit on branch feat/validate with
   a message that lists what changed.
6. When everything passes, write runs/$CLAUDE_RUN_ID/STATUS.md with the final state and print the
   single word DONE as your last line.
```

```bash
#!/usr/bin/env bash
#SBATCH --job-name=claude-batch
#SBATCH --time=04:30:00
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --signal=B:USR1@600
# claude-batch.sbatch — one window of a resumable Claude Code pipeline; submitted by claude-batch.sh
set -euo pipefail
source "$CLAUDE_HPC_ROOT/site.env"
: "${CLAUDE_PROJECT:?}" "${CLAUDE_RUN_ID:?}" "${CLAUDE_TASK_FILE:?}"
RUN="$CLAUDE_HPC_ROOT/runs/$CLAUDE_RUN_ID"; mkdir -p "$RUN"
MAX_CONT="${CLAUDE_MAX_CONTINUATIONS:-6}"
cd "$CLAUDE_PROJECT"

# --- wall-clock budget from Slurm, minus 15 minutes for the agent to finish and write STATUS.md ----
to_seconds() { local t="$1" d=0 a b c; [[ "$t" == *-* ]] && { d="${t%%-*}"; t="${t#*-}"; }
  IFS=: read -r a b c <<<"$t"; if [[ -z "${c:-}" ]]; then c="$b"; b="$a"; a=0; fi
  echo $(( d*86400 + 10#$a*3600 + 10#$b*60 + 10#$c )); }
if [[ -n "${SLURM_JOB_END_TIME:-}" ]]; then REMAIN=$(( SLURM_JOB_END_TIME - $(date +%s) ))
else REMAIN="$(to_seconds "$(squeue -h -j "$SLURM_JOB_ID" -o %L)")"; fi
BUDGET=$(( REMAIN - 900 )); (( BUDGET < 600 )) && { echo "window too short ($REMAIN s)"; exit 75; }

# --- first window starts a session with a fixed ID; later windows resume it ------------------------
if [[ -s "$RUN/session_id" ]]; then
  CONT=$(( $(cat "$RUN/continuations" 2>/dev/null || echo 0) + 1 )); echo "$CONT" > "$RUN/continuations"
  (( CONT > MAX_CONT )) && { echo "continuation cap $MAX_CONT reached; stopping" | tee -a "$RUN/STATUS.md"; exit 1; }
  SESSION_ARGS=(--resume "$(cat "$RUN/session_id")")
  PROMPT="You are resuming run $CLAUDE_RUN_ID in a new job window. Read $RUN/STATUS.md and the task in $CLAUDE_TASK_FILE, verify the state of the working tree with git status, and continue from the Next section. Print DONE as your last line only when every step is complete."
else
  SESSION_ID="$(uuidgen)"; echo "$SESSION_ID" > "$RUN/session_id"; echo 0 > "$RUN/continuations"
  SESSION_ARGS=(--session-id "$SESSION_ID")
  PROMPT="$(cat "$CLAUDE_TASK_FILE")"
fi

export CLAUDE_HPC_MODE=batch CLAUDE_RUN_ID CLAUDE_CODE_DISABLE_ARTIFACT=1
SYS="Non-interactive run $CLAUDE_RUN_ID with a hard time budget of $((BUDGET/60)) minutes. Nobody will answer questions: choose the safest reasonable option and record it in $RUN/STATUS.md. Keep $RUN/STATUS.md current with Done, Running (job IDs) and Next sections after every major step. On an interrupt, finish the current edit, update STATUS.md, and stop."

# --- run under timeout; USR1 from Slurm also triggers a clean interrupt ---------------------------------
EVENTS="$RUN/events-$SLURM_JOB_ID.jsonl"
trap 'echo "USR1: time limit near" >&2; pkill -INT -P $$ timeout 2>/dev/null || true' USR1
timeout --signal=INT --kill-after=120 "$BUDGET" \
  "$CLAUDE_HPC_ROOT/bin/claude-hpc" -p "$PROMPT" "${SESSION_ARGS[@]}" \
    --permission-mode dontAsk --max-turns "${CLAUDE_MAX_TURNS:-150}" --model "${CLAUDE_MODEL:-sonnet}" \
    --append-system-prompt "$SYS" --output-format stream-json --verbose \
    > "$EVENTS" 2> "$RUN/stderr-$SLURM_JOB_ID.log" &
wait $! && rc=0 || rc=$?

# --- outcome: the last result event tells us how the window ended -------------------------------------
RESULT="$(jq -c 'select(.type=="result")' "$EVENTS" 2>/dev/null | tail -n1 || true)"
printf '%s\n' "$RESULT" > "$RUN/result-$SLURM_JOB_ID.json"
SUBTYPE="$(jq -r '.subtype // "none"' <<<"${RESULT:-{}}")"
TEXT="$(jq -r '.result // ""' <<<"${RESULT:-{}}")"
echo "window $SLURM_JOB_ID: rc=$rc subtype=$SUBTYPE turns=$(jq -r '.num_turns // 0' <<<"${RESULT:-{}}")" | tee -a "$RUN/windows.log"

resubmit() { sbatch --parsable "$@" --export=ALL,CLAUDE_HPC_ROOT,CLAUDE_PROJECT,CLAUDE_RUN_ID,CLAUDE_TASK_FILE \
  --output="$RUN/slurm-%j.out" "$CLAUDE_HPC_ROOT/bin/claude-batch.sbatch" | tee -a "$RUN/jobids"; }

if [[ "$SUBTYPE" == "success" && "$TEXT" == *DONE* ]]; then
  echo "run $CLAUDE_RUN_ID complete" | tee -a "$RUN/STATUS.md"; exit 0
elif { cat "$RUN/stderr-$SLURM_JOB_ID.log"; printf '%s\n' "$TEXT"; } | grep -qiE 'usage limit|rate limit|limit reached|try again (at|in)'; then
  echo "usage limit hit; resubmitting after the next window"; resubmit --begin=now+5hours
elif (( rc == 124 )) || [[ "$SUBTYPE" == "error_max_turns" || "$SUBTYPE" == "success" ]]; then
  echo "window ended before DONE; resubmitting"; resubmit --begin=now+2minutes
else
  echo "window failed (rc=$rc, $SUBTYPE); not resubmitting. See $RUN/stderr-$SLURM_JOB_ID.log" | tee -a "$RUN/STATUS.md"; exit 1
fi
```

```bash
#!/usr/bin/env bash
# claude-batch.sh <project-dir> <task-file> [hours] [run-id] — start a pipeline run
set -euo pipefail
source "${CLAUDE_HPC_ROOT:-/scratch/$USER/claude}/site.env"
PROJECT="$(readlink -f "$1")"; TASK="$(readlink -f "$2")"; HOURS="${3:-4}"
RUN_ID="${4:-$(date +%Y%m%d-%H%M%S)-$(basename "$PROJECT")}"
RUN="$CLAUDE_HPC_ROOT/runs/$RUN_ID"; mkdir -p "$RUN"; cp "$TASK" "$RUN/task.md"
[[ -s "$CLAUDE_HPC_ROOT/secrets/claude.env" ]] || { echo "no setup token installed; run token-install.sh first" >&2; exit 65; }
ACCT=(); [[ -n "${SLURM_ACCOUNT:-}" ]] && ACCT=(--account="$SLURM_ACCOUNT")
export CLAUDE_HPC_ROOT CLAUDE_PROJECT="$PROJECT" CLAUDE_RUN_ID="$RUN_ID" CLAUDE_TASK_FILE="$RUN/task.md"
sbatch --parsable "${ACCT[@]}" --partition="$PART_BATCH" --time="${HOURS}:30:00" \
  --export=ALL,CLAUDE_HPC_ROOT,CLAUDE_PROJECT,CLAUDE_RUN_ID,CLAUDE_TASK_FILE \
  --output="$RUN/slurm-%j.out" "$CLAUDE_HPC_ROOT/bin/claude-batch.sbatch" | tee "$RUN/jobids"
echo "run $RUN_ID submitted; follow with: tail -f $RUN/STATUS.md"
```

Four details carry the design. `--session-id` on the first window and `--resume` on every later one keep a single transcript in `$CLAUDE_HPC_ROOT/config/projects/`, so the agent re-enters with its own context (compacted as needed) rather than re-reading the repository from scratch. `--permission-mode dontAsk` makes any action outside the allow list a denial the model can see and route around, which is the only safe meaning of "autonomous" in a job with no one watching. `--output-format stream-json --verbose` writes every event as a JSON line, so `jq` can pull the final `result` (fields `subtype`, `is_error`, `result`, `num_turns`, `session_id`), and the raw file doubles as the audit log. `--begin` turns a usage-limit hit into a scheduled retry after the five-hour window instead of a tight loop that burns the next window too.

Sizing: a 4-hour job inside a 4.5-hour limit with a 15-minute margin leaves the agent a 3h45m budget, which is close to one five-hour window of ordinary use on the larger plans; set `CLAUDE_MAX_TURNS` lower (60 to 80) for implementation tasks that re-run test suites, since each turn that reads a test log costs more than one that edits.

### Preflight, lifecycle and troubleshooting

Run the preflight after every image rebuild, token rotation, or site change:

```bash
claude-hpc --selftest                                              # binary, Slurm passthrough, policy file
claude-hpc -p 'Reply with exactly: TOKEN_OK' --max-turns 1 --output-format json | jq -r '.result'
claude-hpc -p 'Run: squeue --me -h | wc -l' --max-turns 3 --output-format json | jq -r '.result'   # Slurm from inside
```

| Task | Command or setting |
| --- | --- |
| Upgrade Claude Code | rebuild the SIF with `--build-arg CLAUDE_VERSION=<new>`, run `apptainer test`, copy over the old image; sessions in flight keep the old binary until they exit |
| Rotate the token | `claude setup-token` on the laptop, then `token-install.sh`; the launcher reads the file on every start |
| Renew the `/login` credential | `CLAUDE_HPC_AUTH=login claude-hpc` then `/login` when the startup warning appears |
| Prune state | `cleanupPeriodDays: 14` in user settings handles transcripts; `find $CLAUDE_HPC_ROOT/runs -maxdepth 1 -mtime +30 -type d` lists run directories to archive; `apptainer cache clean` on the build host |
| Check limits | `/usage` in an interactive session; `windows.log` in each run directory shows turns per window |

| Symptom | Cause and fix |
| --- | --- |
| `no route to api.anthropic.com` from the launcher | The node has no egress; use `PART_INTERACTIVE`, set `PROXY_URL` in `site.env`, or ask the site for an allow-list entry for `api.anthropic.com`, `claude.ai` and `statsig.anthropic.com` |
| `401 authentication_error` in a batch run | Token file missing, malformed, or expired; `token-install.sh` verifies before saving. In `login` mode after a long gap, the access token expired without a running process to refresh it: use the token for batch |
| `Remote Control requires a claude.ai subscription` | The session was started with the setup token; use `CLAUDE_HPC_AUTH=login` |
| `sbatch: error while loading shared libraries` inside the container | Host and image glibc families differ, or a library was missed by `slurm-binds.sh`; rebuild from the base matching the host, or use the submit shim |
| `tmux: error connecting to socket` | The socket is on a network filesystem; the workspace script keeps it under `$SLURM_TMPDIR` or `/tmp` and you must attach on the same node with `srun --overlap` |
| Sandbox warning at startup | Expected: the bubblewrap sandbox is disabled in managed settings and Apptainer provides isolation |
| `Shell cwd was reset to <dir>` in tool output | The agent tried to `cd` outside the bound project; the rule in `CLAUDE.md` is doing its job |
| Job stuck at the end of a window | A background command outlived `claude`; `timeout --kill-after` ends the launcher, and Slurm's job cgroup reaps the rest when the step ends |

Sources: [Headless mode](https://code.claude.com/docs/en/headless), [CLI reference](https://code.claude.com/docs/en/cli-reference), [Remote Control](https://code.claude.com/docs/en/remote-control), [Tools reference: background commands and timeouts](https://code.claude.com/docs/en/tools-reference).

## Sources and version notes

Facts about Claude Code were checked against Anthropic's documentation on October 3, 2026. Several features this playbook relies on are version-gated, and the image pins the version, so rebuild from the current stable channel if any of the following is missing from `claude --version`'s build.

| Feature used | Minimum Claude Code version | Where it matters |
| --- | --- | --- |
| `claude setup-token` and `CLAUDE_CODE_OAUTH_TOKEN` precedence | long-standing | Section 2 |
| `/login` manual-code flow and the five-day expiry warning | long-standing | Section 2 |
| Remote Control (`claude remote-control`, `--name`) | v2.1.51 | Pattern 2 |
| `--session-id`, `--resume`, `--max-turns`, `--output-format stream-json --verbose`, `--permission-mode dontAsk` | long-standing | Pattern 3 |
| Managed settings at `/etc/claude-code/managed-settings.json`, `disableBypassPermissionsMode` | long-standing | Section 3 |
| `Read` deny rules blocking `Edit`/`Write` on the same path | v2.1.208 (edits), v2.1.228 (writes) | Section 3 |
| `CLAUDE_CODE_TOOL_MEMORY_LIMIT` | v2.1.233 | Section 3 |
| `askUserQuestionTimeout` | current | Section 3 |
| Subagent `maxTurns` frontmatter | current | Section 4 |
| Artifacts disabled by `CLAUDE_CODE_DISABLE_ARTIFACT` | v2.1.183 and later | Pattern 3 |

| Topic | Page |
| --- | --- |
| Authentication, credential storage, precedence, setup token | [Set up Claude Code for your team](https://code.claude.com/docs/en/team), [Authentication (localized mirror of the same page)](https://code.claude.com/docs/ja/authentication) |
| Headless OAuth refresh issue | [anthropics/claude-code #50743](https://github.com/anthropics/claude-code/issues/50743), [#16238](https://github.com/anthropics/claude-code/issues/16238) |
| Network requirements and proxies | [Enterprise network configuration](https://code.claude.com/docs/en/network-config), [Corporate proxy](https://code.claude.com/docs/en/corporate-proxy) |
| Settings files, precedence, managed policy | [Claude Code settings](https://docs.anthropic.com/en/docs/claude-code/settings) |
| Permission rules and modes | [Permissions](https://code.claude.com/docs/en/permissions), [IAM](https://code.claude.com/docs/en/iam) |
| Tool behaviour, timeouts, output limits, Agent tool | [Tools reference](https://code.claude.com/docs/en/tools-reference) |
| Sandboxing in containers | [Sandboxing](https://docs.claude.com/en/docs/claude-code/sandboxing) |
| Headless mode and CLI flags | [Headless mode](https://code.claude.com/docs/en/headless), [CLI reference](https://code.claude.com/docs/en/cli-reference) |
| Remote Control and cloud sessions | [Remote Control](https://code.claude.com/docs/en/remote-control), [Use Claude Code on the web](https://code.claude.com/docs/en/claude-code-on-the-web) |
| Artifacts availability and the `CLAUDE_CODE_DISABLE_ARTIFACT` switch | [Share session output as artifacts](https://code.claude.com/docs/en/artifacts) |
| Terms governing subscription use, intermediation and hosting | [Legal and compliance](https://code.claude.com/docs/en/legal-and-compliance) |
| Usage limits and extra usage | [Usage limit best practices](https://support.claude.com/en/articles/9797557-usage-limit-best-practices), [Manage usage credits for paid Claude plans](https://support.claude.com/en/articles/12429409-) |

Two things are inference rather than documentation and should be validated on your cluster: the Slurm client passthrough depends on your site's library layout and the glibc relationship between host and image (`claude-hpc --selftest` exercises it), and the `enableWeakerNestedSandbox` option is documented for Docker, not Apptainer, so its behaviour under your Apptainer configuration is a test, not a promise. The hook regexes were written against GNU grep's extended syntax and bash 5; run `bash -n` on every script and `jq empty` on every JSON file after any edit.
