---
name: commit-directly-to-master
description: "Git workflow for the CTSpinoPelvic1K repo -- commit and push directly to master, no feature branches"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 4b6b7e20-25dc-44f9-88a3-f46d7b0c12a2
---

In the CTSpinoPelvic1K repo, commit and push directly to `master` -- do NOT create a feature branch, even though master is the default branch (the usual branch-first rule).

**Why:** Solo research repo (single-author history, everything lands on master); branching just adds friction the user doesn't want.

**How to apply:** When the user asks to commit/push here, stage the relevant tracked files and `git push origin master` directly. Still only commit/push when explicitly asked. Exclude session artifacts like `.claude/` and `CTSpinoPelvic1K-1.code-workspace`.
