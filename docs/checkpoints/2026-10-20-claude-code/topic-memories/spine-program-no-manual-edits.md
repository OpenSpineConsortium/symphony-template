---
name: spine-program-no-manual-edits
description: Greg 2026-10-11 -- never edit OpenSpineConsortium/spine-program by hand; everything there is done by the Symphony GitHub Apps, the marketplace plugin's skills, or connectors (claims + pull requests)
metadata:
  type: feedback
---

Greg, 2026-10-11, on preparing the 13 spine-program projects as Symphony projects: "i dont want you to edit the underlying spine-program repos at all manually, i want it all to be done using the github apps preferably launched through marketplace plugins, or skills, or connectors."

**Why:** the point of the repo is to exercise the Symphony protocol itself (board, claims, PRs, Apps); a hand-written commit on main bypasses what the students are meant to follow, and the push guard / ruleset forbid it anyway.

**How to apply:** adoption = the symphony-start form (Apps). Work items = GitHub issues on the board (Task form: Goal / Acceptance / Files likely touched, label `todo`). Content changes = a session claiming an issue with the committed `/claim` skill (not `/symphony:claim`, whose copies name files this repo lacks), branch claude/<issue>, draft pull request, labels claimed + account:<login>, plan as an issue comment; Greg merges (never auto-merge, never merge from a session: every session acts as Greg's GitHub account and the ruleset requires zero approvals). Headless sessions may run with the extension's claude.exe `-p` from the clone. Opening issues with gh is allowed (it is the board, not the tree). See [[symphony-spine-program-adoption]].

Greg 2026-10-12, same thread: "dont exclude any projects from issues on the board, but also dont pick up and start doing the underlying research, just get it all ready for me to pickup in a claude code project". So: every project's tasks sit in the queue labelled todo; Claude's own headless claims are limited to readiness work (start pages, DATA.md, skills, docs state), and the research issues wait for Greg or a student.
