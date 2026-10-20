---
name: grid-ceph-volume-oschome
description: "20 TB CephFS volume /rs/rs_grp_oschome (group oschome) on the WSU grid, allocated 2026-09-21; working tree /rs/rs_grp_oschome/go2432; check with `df-ceph oschome`; home quota was 93% full"
metadata: 
  node_type: memory
  type: project
  originSessionId: f1bdbd78-151f-470b-b703-dd9af9b3fecc
  modified: 2026-09-21T16:33:05.410Z
---

**The volume** (admin ab5188 created it 2026-09-21): `/rs/rs_grp_oschome` -> CephFS, quota 20 TB, group
`oschome` (go2432 is a member; setgid dirs). Usage: `df-ceph oschome`. The home directory
(`/wsu/home/go/go24/go2432`, Panasas) was at 4,002 GB of a 4,295 GB soft limit that day.

**Working tree** `/rs/rs_grp_oschome/go2432/`: `model_night/` (new experiment roots and logs),
`data/` (datasets moved from ~/data with rsync, then symlinked), `archive/` (finished rounds: anchor_*
roots, refiners), `tmp/` (TMPDIR). README in the root.

**How to apply:** put every NEW large output there; leave `~/model_night` alone while jobs are still
running on it; migrate cold directories with `rsync -a --remove-source-files` then a symlink at the old
path so scripts keep working. `/rs` is a symlink into `/.rs/volumes/...` -- use the `/rs/...` path.
See [[grid-quota-and-deleted-banks]], [[grid-access]].
