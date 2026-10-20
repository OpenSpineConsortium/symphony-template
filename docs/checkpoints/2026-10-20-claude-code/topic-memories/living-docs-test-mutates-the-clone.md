---
name: living-docs-test-mutates-the-clone
description: "In symphony-template and every repo made from it (SchwingNet), `python3 tools/living_docs.py test` (step of scripts/check.sh) runs lesson commands IN the working copy -- never run check.sh in a real clone on Windows"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 0599380b-0d32-4e19-b5be-65bdd1017566
  modified: 2026-10-20T22:21:32.289Z
---

Measured 2026-10-20 in the SchwingNet clone (Desktop\SchwingNet). `bash scripts/check.sh` runs `tools/living_docs.py test`,
which executes docs/learn/ lessons command by command in the current working copy. On this laptop the lessons failed
(`/usr/bin/python3: No module named sdlc_protocol`, also on main), and before failing they:
- set LOCAL `user.name=""` and `user.email=@example.invalid` (next commit: "Author identity unknown");
- created branch `claude/7` and SWITCHED the clone onto it;
- staged `docs/agents/claims/7.md` and unstaged another claim file;
- left STATE.md, answer.txt, course.json, guard.sh, origin.git/, setup/ at the root.
A worktree shares .git/config, so running it in a scratch worktree also blanks the main clone's identity. Nothing was
pushed (the remote URL was untouched); the global ~/.gitconfig was untouched.

**Why:** the lessons are written for CI's throwaway checkout, not a person's clone.

**How to apply:** locally, run only the pieces: `python tools/check_docs.py`, `python -m unittest tests.test_<x>`,
`python tools/sources.py check`, `pytest tests/schwingnet/...` (venv with pydantic, beartype, icontract, typeguard,
hypothesis, pytest). Never `bash scripts/check.sh` and never `living_docs.py test` in a clone you commit from. If it
happened: `git config --local --unset user.name/user.email`, switch back, delete claude/7, `git status`, remove the
root files. The full unittest suite also takes >500 s on Windows; CI runs it.

Related: [[schwingnet-repo-and-registry]], [[symphony-spine-program-adoption]].
