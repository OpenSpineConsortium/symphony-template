---
name: grid-quota-and-deleted-banks
description: "Grid quota is a Panasas SOFT limit (pan_quota, not df); five allspine banks deleted 2026-09-20 and holdout refs repointed to v7"
metadata: 
  node_type: memory
  type: project
  originSessionId: f1bdbd78-151f-470b-b703-dd9af9b3fecc
  modified: 2026-09-21T00:18:45.598Z
---

**Reading the quota.** `df -h $HOME` on the grid shows the whole `/wsu` volume and tells you nothing
about the user limit. The real number is **`pan_quota`**:

```
   <GB>   <soft>   <hard> : <files>    <soft>
 4200.44  4294.97  8589.93 : 2484057  10000000
```

So the limit that bites is a **4 TB soft** limit with an **8 TB hard** ceiling -- crossing the soft line
starts a grace timer rather than failing writes immediately. File count is nowhere near its limit.

**`du` is very slow on Panasas** with 2.5M files. Run one `du -sx` per top-level entry through
`xargs -P 24` and it finishes in minutes instead of hours; run it detached with `nohup setsid`.

**Deleted 2026-09-20 to recover 259.6 GB** (4200 -> 3923 GB): `allspine_v2/v3/v4/v5/v5c_fov96_ctx`
(206.5 GB of superseded crop banks, rebuildable by `slurm/build_allspine_v*.sh`), `singularity_cache`,
`conda_cache`, `.cache/pip`, `.cache/torch`, `~/tmp` older than 2 days, and all `epoch*.pt`.

**The trap that created.** ~90 scripts named those banks as `--holdout-bank`, and an unreadable bank
left the trained-on set EMPTY so the evaluation silently ran over cases the model was FITTED on. That
error only ever flatters the result. `tools/holdout.py` now raises, and the 57 references that supply
a holdout were repointed to **`allspine_v7_fov96_ctx`**, whose train set is a strict superset of v6 and
v7nofluoro (measured: zero v6-only cases), so it refuses MORE than the original did. Builders keep
their own bank names. Split lists recovered to `~/bank_splits.json`.

**Still large and NOT deleted, if more space is needed:** `data/rsna_cspine` 236.8, `nnunet/results`
348.6 (regenerable), `ablate` 234.8, `u251-xenograft-murine-RNASeq-study` 193.9 (a different project
entirely, untouched since 2026-07-27 -- ask before removing), `implant_verse` 186, `VerSeFusion` 138.9,
`scaling` 129.2, `.cache` 103.9.

See [[level-model-bank-coverage]], [[grid-access]].
