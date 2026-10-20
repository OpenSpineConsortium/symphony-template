---
name: schwingnet-repo-and-registry
description: "OpenSpineConsortium/SchwingNet (private, made from symphony-template 2026-10-20) -- automerge on ready, the dataset registry data/sources/ rendered to docs/research/datasets-inventory.md; AASCE and VinDr records corrected in PR #27"
metadata:
  node_type: memory
  type: project
  originSessionId: 0599380b-0d32-4e19-b5be-65bdd1017566
  modified: 2026-10-20T22:21:40.927Z
---

OpenSpineConsortium/SchwingNet: private, created 2026-10-20 from symphony-template (so it carries the template's
docs/checkpoints/ and its own docs/memory/). Local clone: `C:\Users\grego\OneDrive\Desktop\SchwingNet` (made 2026-10-20).
docs/project.md: confidential, provisional patent in preparation, nothing copied to a public place.

- **Landing:** `.github/workflows/automerge.yml` arms GitHub auto-merge on every PR opened or marked ready; it lands when
  the required checks pass ("whether a change lands is decided by the tests"). Marking ready IS the merge decision.
  The protocol is the vendored symphony-protocol (claims, worker:<login> labels, board branch).
- **Dataset registry (PR #24, issue #23):** one JSON per source in `data/sources/` (60), pydantic model in
  `src/schwingnet/sources.py`, renderer `tools/sources.py render|check` writes docs/research/datasets-inventory.md; the
  check fails when page and records differ. Records must be ASCII+LF: since PR #27, `tools/check_docs.py` holds
  `data/sources/` (PLAIN_TEXT_FOLDERS), not a test.
- **PR #27 (issue #26, Greg 2026-10-20):** AASCE = 609 labelled (481+128) + 98 challenge-test, both Ceph copies (see
  [[aasce-two-copies-on-ceph]]); VinDr held under HPR 2026-330 (see [[vindr-covered-by-hpr-2026-330]]); every count in
  the closing prose read from a record (C-ArmLSpine record gained `l6_cases: 3`).

Greg's rule for review follow-ups, 2026-10-20: resolve findings from the history; where a review leaves things half
consistent, "consistency should be chosen unless there is good reason".

Related: [[living-docs-test-mutates-the-clone]], [[provisional-patent-materials]].
