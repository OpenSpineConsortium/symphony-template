---
name: schwingnet-repo-and-registry
description: "OpenSpineConsortium/SchwingNet (private, from symphony-template 2026-10-20) -- automerge on ready; registry data/sources/ -> datasets-inventory.md (PR #24, fixed in #27); REPRODUCTION KIT data/reproduce/ (manifest + reacquire code at spinesurg bf1432f, SHA256SUMS, map.json) -> datasets-reproduce.md via tools/reproduce_table.py, checked by scripts/check.sh (PR #32)"
metadata:
  node_type: memory
  type: project
  originSessionId: 0599380b-0d32-4e19-b5be-65bdd1017566
  modified: 2026-10-21T02:04:27.692Z
---

OpenSpineConsortium/SchwingNet: private, created 2026-10-20 from symphony-template (so it carries the template's
docs/checkpoints/ and its own docs/memory/). Local clone: `C:\Users\grego\OneDrive\Desktop\SchwingNet` (made 2026-10-20).
docs/project.md: confidential, provisional patent in preparation, nothing copied to a public place.

- **Landing:** `.github/workflows/automerge.yml` arms GitHub auto-merge on every PR opened or marked ready; it lands when
  the required checks pass ("whether a change lands is decided by the tests"). Marking ready IS the merge decision.
  After a later push the arming survives, but a PR that is behind main or conflicting is "dirty"/"blocked": merge
  origin/main in, re-render, push, and `gh pr merge <N> --auto --merge` if auto is off. An automerge does NOT close the
  linked issue here (#23 after #24, #26 after #27): close it by hand with a comment.
- **Dataset registry (PR #24, issue #23):** one JSON per source in `data/sources/` (60), pydantic model in
  `src/schwingnet/sources.py`, renderer `tools/sources.py render|check` writes docs/research/datasets-inventory.md; the
  check fails when page and records differ. `tools/check_docs.py` holds `data/sources/`, `data/registry/`, `data/splits/`
  to ASCII+LF (PLAIN_TEXT_FOLDERS).
- **PR #27 (issue #26, merged 2026-10-20):** AASCE = 609 labelled (481+128) + 98 challenge-test, both Ceph copies (see
  [[aasce-two-copies-on-ceph]]); VinDr held under HPR 2026-330 (see [[vindr-covered-by-hpr-2026-330]]); every count in
  the closing prose read from a record (C-ArmLSpine record gained `l6_cases: 3`).
- **Reproduction kit (issue #31, PR #32, merged by automerge 2026-10-21 02:03 UTC; Greg: "make sure we have all the manifest and direct
  links and code that could reproduce this dataset and all the links they came from").** `data/reproduce/`:
  sources.json (211 sources), reacquire/reacquire.py + reacquire.sbatch, byte-for-byte from spinesurg-ct-nnunet
  data_platform at bf1432f (cmp-verified), SHA256SUMS (written by Python; Git Bash sha256sum prefixes names with `*`);
  map.json = 60 registry ids -> manifest ids (55 -> 59 records; anomaly_harvest_b -> family B = 144; 4 none:
  coronary_angiography, pediatric_iri, veterinary_pig_levelcheck, cervical_thoracic_intraop). `tools/reproduce_table.py
  render|check` -> docs/research/datasets-reproduce.md (ASCII; a SPELT table maps the manifest's non-ASCII, an unknown
  character is a SystemExit); `check` also verifies SHA256SUMS and the map's completeness; wired into scripts/check.sh.
  Verified 2026-10-20 in the SOURCE repo: `reacquire.py --list` 211, `--grid --all` dry run 2,171 lines exit 0,
  `test_reacquire.py` 28 OK (the suite is not copied: it expects the source layout). To update: recopy the 3 files,
  rewrite SHA256SUMS, name the commit in data/reproduce/README.md, render.
- **Another session the same evening:** the frame catalog (#30: data/registry/, data/splits/, tools/catalog.py,
  docs/research/data-catalog.md); merged into #32 (the two index files: keep both sides' lines).

**Write-tool trap (2026-10-20):** backslash-u escapes typed into a Write call land as literal characters, so a tools/
file then fails the ASCII rule; fix with a script FILE that re-escapes them (never a heredoc: backslashes collapse).

Greg's rule for review follow-ups, 2026-10-20: resolve findings from the history; where a review leaves things half
consistent, "consistency should be chosen unless there is good reason".

Related: [[living-docs-test-mutates-the-clone]], [[provisional-patent-materials]], [[checkpoint-in-symphony-template]].
