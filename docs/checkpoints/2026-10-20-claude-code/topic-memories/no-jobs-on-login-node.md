---
name: no-jobs-on-login-node
description: "Greg's rule (2026-09-21): never run jobs on the grid login node -- every analysis, render, plot and download goes through sbatch; compute nodes have internet"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: f1bdbd78-151f-470b-b703-dd9af9b3fecc
  modified: 2026-09-21T20:06:11.328Z
---

Never run computation on the grid login node (grid.wayne.edu resolves to login hosts such as `warrior`). Every
analysis, render, smoke test, plot and download goes through `sbatch` (partition `reqp --qos=requeue --no-requeue`
for CPU work), even if it would take a minute.

**Why:** Greg said so explicitly on 2026-09-21 after a session had run dozens of smoke tests, renders and a
metadata download directly on the login node. Login nodes are shared by ~95 users.

**How to apply:**
- Write a small slurm script (see `spinesurg-ct-nnunet/slurm/paired_sets_properties.sh` for the minimal
  template) and submit it; read its log afterwards. Use `sbatch --parsable` to capture the job id.
- Compute nodes HAVE internet (job 40409460 on zfh17 reached zenodo.org and tomoradio-warehouse.creatis.insa-lyon.fr
  in under a second), so downloads go in jobs too. This supersedes the old FluoroCap note that network stages
  run on the login node.
- Allowed on the login node: `sbatch`, `squeue`, `scancel`, reading logs, `ls`, `scp`, small `sed` edits, and the
  lightweight `~/remote_wait.sh` squeue poller.
- Related: [[grid-access]], [[grid-ceph-volume-oschome]], [[wsl-for-network]].

**2026-09-28 addendum (C&IT e-mail):** an Apptainer build run on warrior left a 6.9 GB `rootfs-*` under
`/tmp` there (removed the same day; /tmp went 91 % -> 63 %). Rules now enforced in Ashley
(`grid/bootstrap.sbatch` refuses without `SLURM_JOB_ID`; `cmd_diag_node` refuses off a job; diagnostic
`grid.login-tmp` finds and removes leftovers): no container command on warrior, ever; `/tmp` on warrior is
not for user files; inside jobs `APPTAINER_TMPDIR`/`APPTAINER_CACHEDIR` (+ `SINGULARITY_*`) point at the
compute node's local `/tmp` (or `$SLURM_TMPDIR`) with a cleanup trap; shared temp goes under `/wsu/tmp`.

