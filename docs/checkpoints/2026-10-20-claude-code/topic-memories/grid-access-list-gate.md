---
name: grid-access-list-gate
description: "Approved students reach the lab's shared Beethoven tree through named-user ACL entries on the volume root /rs/rs_grp_oschome, not through group oschome (only C&IT adds members); measured modes 2026-10-02"
metadata:
  node_type: memory
  type: project
  originSessionId: 0599380b-0d32-4e19-b5be-65bdd1017566
  modified: 2026-10-03T00:01:29.522Z
---

Measured on the grid 2026-10-02: the Unix group `oschome` holds only go2432 and ab5188; C&IT alone
adds members. The volume root `/rs/rs_grp_oschome` (a link to the physical dir, owned by go2432,
`drwxrws--T`, other `---`, sticky since 2026-10-02) had only `go2432/` (`drwxr-s---`, Greg's data,
stays closed) and `shared/`. Students like hy9698 are in `wsu`/`hpcgrid` only, so the first real
student setup died with "exit 126: hpcworker: Permission denied".

**The design Greg asked for ("approved = can read hpcworker and the lab utilities"):** the approved
list is the set of `user:<id>:rwx` ACL entries on the volume root (rwx because the site profile puts
each student's state at `/rs/rs_grp_oschome/$USER/hpcworker`, a folder they create; sticky stops
renaming others' entries). Below the gate everything students use is other-readable: `shared/`
`o+rx`, `shared/beethoven` `chmod -R o+rX` plus default `o::r-x` (done by hand 2026-10-02, 34k files,
23 s). `shared/access` and `go2432/` stay closed by their own modes. Invariant: the root keeps
`other::---` and sticky.

**Why:** group membership is not the lab's to change; per-file ACLs on 34k files per student are
slow and leave students half-working; one gate makes approval O(1).

**How to apply:** `tools/grid_access.sh` in ashley-bridge reconciles the list from the access
service's roster (admin.mjs `roster`), only connecting when the list changed; `deploy_shared.sh` no
longer sets `o::---` (it would re-close each new version). By hand: `setfacl -m u:<id>:rwx
/rs/rs_grp_oschome`; remove with `setfacl -x u:<id>`. Related: [[ashley-bridge-project]],
[[grid-ceph-volume-oschome]].
