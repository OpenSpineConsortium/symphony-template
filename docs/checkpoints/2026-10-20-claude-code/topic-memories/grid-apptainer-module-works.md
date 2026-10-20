---
name: grid-apptainer-module-works
description: "On WSU compute nodes `module load apptainer/1.2.2` builds an unprivileged sandbox from docker:// (6 min for node:22-bookworm) and execs it; Claude Code 2.1.283 runs inside via npm --prefix on CephFS; claude -p cold start ~5-7 s"
metadata:
  node_type: memory
  type: reference
  originSessionId: 0599380b-0d32-4e19-b5be-65bdd1017566
  modified: 2026-09-28T00:46:52.749Z
---

Measured 2026-09-28 (jobs 40486327 on asx1 secp, 40486353): `module load apptainer/1.2.2` gives
`/wsu/el7/gnu7/apptainer/1.2.2/bin/apptainer` on compute nodes; `apptainer build --sandbox DIR
docker://node:22-bookworm` works unprivileged (6 min, 1.1 GB) with `APPTAINER_CACHEDIR/TMPDIR` on CephFS;
`apptainer exec -B $HOME -B /rs/rs_grp_oschome/$USER -B /dev/shm/scratch:/tmp DIR node` works. Inside:
node 22.23.3, git 2.39.5, glibc 2.36, python3, curl to api.anthropic.com OK. `npm install -g --prefix
<cephfs>/npm @anthropic-ai/claude-code@2.1.283` took 35 s; `claude --version` works; `claude -p` wall ~7 s
including an auth failure. The conda singularity 3.8.6 and `module singularity/3.5.2`, `/usr/bin/apptainer`
also exist on asx1. `~/.local/bin/singularity` stays broken ([[grid-local-singularity-is-broken]]).

Queue reality that day: `reqp --qos=requeue` sat PENDING (Priority) for 30+ min; `--partition=secp
--qos=secondary` started at once (77 idle nodes). Node FQDN pattern: `<name>.nas.grid.wayne.edu`.

**How to apply:** for any Node/modern-glibc tool on the grid, prefer the apptainer module + pre-built
sandbox on CephFS; probe the runtime in step 0. See [[ashley-extension-project]], [[no-jobs-on-login-node]].
