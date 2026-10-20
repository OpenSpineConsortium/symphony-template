---
name: diagnostics-graph-required
description: "Greg 2026-09-28 (standing rule for Ashley): no feature integrates until every tool/package/step it relies on is a node in the diagnostics graph with a check, a failure trace and an auto-repair where safe"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 0599380b-0d32-4e19-b5be-65bdd1017566
  modified: 2026-09-28T04:39:19.681Z
---

Greg (2026-09-28): build a diagnostics/troubleshoot automatic resolver that unit-tests every package and tiny
step as a graph of tools/assumptions/templates, traces a failure to the exact node, auto-resolves where it can
(e.g. install a newer package) for future-proofing as Wayne State updates things, logs to an error bar with
"Show log" like real software, and borrows from Windows "Troubleshoot" / auto-repair. "Make this from now on
be a required pre-integration condition for any features."

**Why:** Wayne State (OS, modules, sshd, VS Code sysroot) and vendors (VS Code, Remote-SSH, Claude Code, APIs)
will change under the students; a failure must name the broken piece, not just say "it didn't work".

**How to apply:** for every new Ashley feature, add its nodes (id, layer, depends_on, assumption, check,
failure signatures, auto_repair, manual_fix, future_risk, source) to the diagnostics graph and make sure the
Troubleshoot run covers them BEFORE merging the feature. Related: [[ashley-extension-project]],
[[students-see-no-internals]].
