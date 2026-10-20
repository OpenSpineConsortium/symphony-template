---
name: windows-junction-worktree-trap
description: git worktree remove --force follows Windows junctions and deletes the TARGET (it wiped ashley/extension/node_modules and .vscode-test on 2026-09-28); delete junctions with rmdir first
metadata:
  node_type: memory
  type: feedback
  originSessionId: 0599380b-0d32-4e19-b5be-65bdd1017566
  modified: 2026-09-28T17:53:40.016Z
---

On Windows, `git worktree remove --force <path>` recurses through directory junctions inside the
worktree and deletes the junction's *target* contents. On 2026-09-28 the three Ashley worktrees held
junctions `extension/node_modules` and `extension/.vscode-test` pointing at the main checkout; removing
the worktrees emptied both in `C:\Users\grego\OneDrive\Desktop\ashley\extension` (recovered with
`npm ci` and a fresh VS Code test download).

**Why:** git's recursive delete does not treat a junction as a link.

**How to apply:** before `git worktree remove`, delete every junction in the worktree with
`cmd //c rmdir <junction>` (removes the link only), or `Remove-Item <junction>` without `-Recurse`
after confirming `(Get-Item <p>).LinkType -eq 'Junction'`. Prefer giving worktrees their own
`npm ci` when time allows. Also: the Workflow tool's `isolation: 'worktree'` makes worktrees of the
session's primary repo (CTSpinoPelvic1K-1), not of another repo; for Ashley create worktrees by hand
under `C:\Users\grego\ashley-wt\` and pass the paths in the prompts. Related: [[ashley-extension-project]].
