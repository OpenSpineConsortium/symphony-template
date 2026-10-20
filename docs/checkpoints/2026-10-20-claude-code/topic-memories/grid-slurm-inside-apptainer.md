---
name: grid-slurm-inside-apptainer
description: How to make sbatch/squeue work inside an Apptainer container on the WSU grid (measured 2026-09-28 on asx1); needed whenever code in a container must submit or watch Slurm jobs
metadata:
  node_type: memory
  type: reference
  originSessionId: 0599380b-0d32-4e19-b5be-65bdd1017566
  modified: 2026-09-28T07:03:01.828Z
---

A container on the WSU grid has no Slurm. The host client works inside it with these read-only binds
(Apptainer 1.2.2, node:22-bookworm sandbox, measured on asx1 2026-09-28):

- `/usr/bin` -> `/opt/host/bin` (call `/opt/host/bin/sbatch` etc.; do not put all of host /usr/bin on PATH)
- `/usr/lib64/slurm` -> same path (libslurmfull.so and the auth plugin)
- `$(readlink -f /usr/lib64/libmunge.so.2)` -> `/usr/lib/libmunge.so.2` (a default search folder, so no
  LD_LIBRARY_PATH leaks into submitted jobs)
- `/etc/slurm`, `/var/run/munge` -> same paths
- an `/etc/passwd` and `/etc/group` = the container's own plus `getent passwd slurm munge $USER` /
  `getent group slurm munge $(id -gn)`. Without the slurm user: "Invalid user for SlurmUser slurm" then
  "Unable to process configuration file".

Bind sources must be on a filesystem the compute node sees (home), not the login node's /dev/shm. A wrapper
that unsets APPTAINER_*/SINGULARITY_* and sets the host PATH makes a job submitted from inside run on the host
with the normal environment. Implemented in Ashley's `grid/worker.sbatch.tpl`. See also
[[grid-apptainer-module-works]], [[ashley-extension-project]].
