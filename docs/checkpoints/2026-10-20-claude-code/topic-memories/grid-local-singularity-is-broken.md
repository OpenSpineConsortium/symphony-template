---
name: grid-local-singularity-is-broken
description: "On the WSU grid, ~/.local/bin/singularity is a partial install that dies with \"starter not found\"; use the conda one with a pre-unpacked sandbox and bind /rs/rs_grp_oschome/go2432, never -B /rs"
metadata:
  node_type: memory
  type: reference
  originSessionId: f1bdbd78-151f-470b-b703-dd9af9b3fecc
  modified: 2026-09-27T13:17:50.456Z
---

`~/.local/bin/singularity` is first on PATH on the **login** node and is a partial install. It pulls images fine and
then dies at exec:

```
INFO:    Converting SIF file to temporary sandbox...
FATAL:   while executing starter: /usr/libexec/singularity/bin/starter not found
```

On **compute** nodes there is usually no container runtime on the default PATH at all, so a job that just calls
`singularity` dies at **exit 127** before doing any work.

This has now cost jobs twice: the U251 GSEA leave-one-out (40464589/40464590, resubmitted as 40464722/40464723) and the
GEO methylation staging (40483631 exit 127, 40483632 starter-not-found, 40483633 bad bind).

**The route that works**, used by every R step in the U251 study:

```bash
SING=$HOME/mambaforge/envs/nextflow/bin/singularity          # conda, not ~/.local, not a module
SANDBOX=/rs/rs_grp_oschome/go2432/u251_meth/containers/bioconductor_docker_RELEASE_3_22-R-4.5.2.sandbox
RLIB=/rs/rs_grp_oschome/go2432/u251_meth/rlib/bioc-3.22_R-4.5.2   # already holds minfi + the EPIC manifest
"$SING" exec -B /rs/rs_grp_oschome/go2432 -B "$HOME" -B "$TMP:/tmp" "$SANDBOX" Rscript /tmp/script.R
```

Three separate traps in that one line:

1. Use a **pre-unpacked sandbox directory**, not a `.sif` -- the SIF-to-sandbox conversion is what fails, and some
   nodes also lack the `unsquashfs` that singularity 3.8 needs to unpack.
2. Bind the **specific group path** `/rs/rs_grp_oschome/go2432`. Plain `-B /rs` does not make the tree visible inside,
   and the symptom is "cannot open file" for a script that is demonstrably on the host.
3. Bind a writable `/tmp`, or even `Rscript -e` fails with "creating temporary file for '-e' failed". Pass scripts and
   input files through that bound `/tmp`.

**How to apply:** resolve and **smoke-test** the runtime in step 0 of any job that needs a container, and refuse there
rather than after staging data. See [[no-jobs-on-login-node]] and [[grid-ceph-volume-oschome]].
