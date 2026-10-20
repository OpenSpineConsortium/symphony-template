---
name: hf-mirror-is-v10
description: "The PUBLIC CTSpinoPelvic1K (Hugging Face OpenSpineConsortium/CTSpinoPelvic1K, revision 2026-09-23; Zenodo v10 2026-09-07) is still v10 with id 29 present on 2026-09-27 -- v11 (29 dissolved into 26) exists only locally / on the grid; student materials saying \"v10, S1 = 29\" are correct until v11 ships"
metadata:
  node_type: memory
  type: project
  originSessionId: f1bdbd78-151f-470b-b703-dd9af9b3fecc
  modified: 2026-09-27T21:16:06.575Z
---

Checked 2026-09-27 via the HF API: dataset sha 72cd7773..., lastModified 2026-09-23T18:08 (the CT 0533
repair); `dataset_labels.json` on `main` still carries key 29; the README describes the scheme as
v10. Zenodo v10 was published 2026-09-07 (concept DOI 10.5281/zenodo.22139642). CLAUDE.md's "the
release is v11" describes the working tree, not what the public can download.

**Why:** a critic pass flagged Student_Projects (IDEAS.md, templates/CLAUDE.md, get_dataset.sh,
onboard.md) as "pinned to v10 while the release is v11" and I nearly repointed them. That would have
told students to use identifiers that the file they download does not carry.

**How to apply:** Do not change student identifier text to v11 until v11 is on HF and Zenodo. When it
ships: IDEAS.md lines 9-12 and 113, templates/CLAUDE.md lines 52-57, examples/pelvic_width_dimorphism
README line 71, onboard.md line 89, README.md line 49, proposal_example DOI. Anything that gates on 29
goes with it (CLAUDE.md: `select_anchor_cases.py` incident).
Related: [[label-scheme-v4-vs-ostk]], [[s1-carve-changed-spinopelvic]], [[zenodo-deposit]].
