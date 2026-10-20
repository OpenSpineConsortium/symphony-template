---
name: grid-bash-4-2-quoting
description: "The grid runs bash 4.2.46; a quoted replacement inside ${var/pat/\"$new\"} keeps its quotes there (WSL bash 5.2 drops them), so a suite that passes locally can fail on the grid; write grid bash for 4.2 and test the quoting difference"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 0599380b-0d32-4e19-b5be-65bdd1017566
  modified: 2026-10-08T17:35:18.660Z
---

Found 2026-10-08 by the dedup hash job: `"${base/"$old"/"$new"}"` produced `img/"gl"146.npy` on the grid (bash
4.2.46, RHEL) while the 106-check test suite under WSL bash 5.2.21 passed. The fix is an unquoted replacement
inside the double-quoted expansion: `"${base/"$old"/$new}"`.

**Why:** compute nodes and warrior run bash 4.2; every dedup, migration and visibility job is bash-only because
warrior bans python by name, so a 5.x-only idiom fails silently in the job and surfaces as a wrong verdict, not an
error.

**How to apply:** when writing or reviewing a grid job, avoid constructs newer than bash 4.2 (nameref `declare -n`,
negative array indices, `${var@Q}`, `wait -n`, `mapfile -d`, and quoted replacement strings in pattern
substitution); run `bash -n` and, where it matters, a smoke test on a compute node before trusting a local suite.
Related: [[data-platform-migration-2026-10]], [[no-jobs-on-login-node]], [[bash-heredoc-backslashes]].
