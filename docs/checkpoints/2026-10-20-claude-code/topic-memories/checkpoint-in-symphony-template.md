---
name: checkpoint-in-symphony-template
description: "Greg 2026-10-20 -- this session's knowledge is consolidated in symphony-template docs/checkpoints/2026-10-20-claude-code/ (PR #311, revised in place by #320/#322) like the claude.ai Project threads' checkpoints; how to redo it and the template checks it must pass"
metadata:
  node_type: memory
  type: project
  originSessionId: 0599380b-0d32-4e19-b5be-65bdd1017566
  modified: 2026-10-21T02:00:56.415Z
---

Greg, 2026-10-20: "write a similar checkpoint and handoff into the symphony-template repo as the other claude code
projects so all your knowledge can be consolidated likewise". Done as
`OpenSpineConsortium/symphony-template/docs/checkpoints/2026-10-20-claude-code/` (PR #311), revised the same evening in
place (issue #320, PR #322) with the later work, the CI errors explained, and the memory re-exported: handoff.md
(restore the memory, first message, workstreams, open PRs, numbered waiting list, revision section), memory.md (this
MEMORY.md, links into topic-memories/), topic-memories/ (every fact file). Other threads' checkpoints sit beside it
(2026-10-14 ... 2026-10-19).

**How to redo it (a newer dated folder for a new day; the same folder only for the same day):** export the memory
folder with these rules (scratch script export_memory.py did it):
- ASCII + LF (docs/ is under tools/check_docs.py): em/en dash, arrows, x, <=, +/-, sec., Greek letters, accents spelt;
- the banned word renamed out of file names and text (splits-...-and-v3-resplit.md becomes splits-origin-...);
- students' GitHub usernames replaced by [student N] in EVERY file (they occur outside annotator-roster too);
- MEMORY.md links rewritten to `topic-memories/<file>`;
- `tests/test_claim_skill.py` scans every page under docs/: every push command must name remote AND branch (one memory
  said "git push/pull" and failed it; even quoting the two words in backticks without arguments fails), and every
  branch creation (switch -c, checkout -b) must carry --no-track. The filled-copy tests copy the template, checkpoints
  included, and rerun the same tests, so one bad line fails three jobs.
Check locally with `python tools/check_docs.py` and `python -m unittest tests.test_claim_skill tests.test_check_docs`
(about 5 min); never `bash scripts/check.sh` in the clone ([[living-docs-test-mutates-the-clone]]).

The template: internal, only Greg can read it, no automerge workflow but `allow_auto_merge` on; `gh pr merge <N> --auto
--merge` waits for the required checks. Worker label there is the older `account:main` (no worker:<login> label exists).
Everything under docs/checkpoints/ is copied into every repo made from the template; none public as of 2026-10-20.

Related: [[schwingnet-repo-and-registry]], [[symphony-spine-program-adoption]].
