---
name: zenodo-deposit
description: "Zenodo token/DOIs/scripts for the CTSpinoPelvic1K deposit; v10 = 10.5281/zenodo.22642578 published 2026-09-07 (13 ribs per side, contiguous 0-68); concept 10.5281/zenodo.22139642; earlier versions cannot be deleted (only support can withdraw them)"
metadata: 
  node_type: memory
  type: project
  originSessionId: e44eca96-f48c-494d-ba1f-7dae68bdf06d
  modified: 2026-09-07T18:30:12.950Z
---

Token at `~/.zenodo_token` (WSL home; network work runs in WSL). Concept DOI
10.5281/zenodo.22139642. **Current version: v10 = 10.5281/zenodo.22642578, published
2026-09-07** (thirteen ribs per side, lumbar ribs 60/61, hardware 62-68; labels.zip
1,074,544,275 bytes). Earlier: v9 22639598 (contiguous 0-66), v8 22293878, v7 22242745,
v6 22139643. Greg wanted earlier versions erased; Zenodo uploaders cannot delete published
records, support can withdraw (tombstone) on request.

New version recipe: `scripts/renumber_labels.py --map vN` (parallel remap, presence json),
`zenodo/finalize_v9.py --new labels_vN --old labels_vM_old --max-id 68` (swap, labels.zip,
SHA256SUMS), `python3 zenodo/new_version.py --record <latest> --version vN --dir
data/zenodo_deposit --replace <files>` (draft; `--draft <id>` resumes), then
`python3 zenodo/upload.py --publish <id>`. Then set `\datasetversion` and the DOI in
main.tex, title_page.tex, cover_letter.md. `hf/push_v9.py --repo ... --card <card>` mirrors
labels + metadata to both HF repos (never the deposit README as the card).

**Build archive (separate record, not a dataset version): PUBLISHED 2026-09-07 as
10.5281/zenodo.22647933** (13 files, 6.24 GB, verified by size+md5 with
`zenodo/check_draft.py`); metadata `zenodo/build_archive.json`, chain in
`docs/BUILD_CHAIN.md`, code state tagged `v10-build-archive`. Chain check: v7 -> v9 -> v10
regenerates all 802 released volumes voxel-identically. Grid cleanup phases A and B ran the
same day; the grid keeps only `~/data/CTSpinoPelvic1K` (v10 + CTs) for the dataset. The
title page cites it via `\buildarchivedoi`.

**Why:** three versions in four days (v8 Castellvi consensus, v9 gap closed, v10 rib 13);
each was a Greg request, and each needs a new Zenodo version because files cannot change.
**How to apply:** cite only the concept DOI and the current version in the paper. See
[[scheme-bone-hardware-only]].
