---
name: dataset813-image-links-are-container-paths
description: "Dataset813 imagesTr symlinks point at /data/hf_export/ct/... which only resolves inside Singularity; never \"repair\" them on the host -- the fix is HF_EXPORT_DIR"
metadata: 
  node_type: memory
  type: project
  originSessionId: e44eca96-f48c-494d-ba1f-7dae68bdf06d
  modified: 2026-09-13T02:51:20.807Z
---

All 802 `imagesTr` symlinks in `~/spinesurg-ct-nnunet/nnunet/raw/Dataset813_*` look dangling
from the host (`/data/hf_export/ct/<n>_ct.nii.gz`). They are container bind paths, and
`slurm/spine_prep.sh` warns in its header that an earlier host-side cleanup "wiped the whole
dataset on every resume run". On 2026-09-12 I repaired them anyway, then reverted with
`tools/restore_container_links.py`.

**Why:** nnU-Net trains from `preprocessed/`, so a corpus whose raw images are all unreadable
still trains with healthy metrics -- nothing downstream notices. The `hf_export` bind source is
also genuinely absent on the grid now; the surviving CT copy is `~/data/CTSpinoPelvic1K/ct/`.

**How to apply:** run preprocessing with `HF_EXPORT_DIR=$HOME/data/CTSpinoPelvic1K` (it needs a
`ct/` subdir) so the bind resolves; any tool that must read the CT from the host should take the
link's basename and look it up under that root (see `make_drr_dataset.py --ct-root`). Never
rewrite the links. Related: [[grid-access]], [[never-reorient-when-writing-labels]].
