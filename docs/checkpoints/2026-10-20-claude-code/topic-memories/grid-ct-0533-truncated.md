---
name: grid-ct-0533-truncated
description: "CTSpinoPelvic1K CT 0533 (COLONOG_378): truncation repaired everywhere 2026-09-23 -- grid rebuilt from TCIA AND the HuggingFace release replaced (LFS sha 478a74e9..., verified via the API); only KNOWN_ISSUES/Zenodo notes remain"
metadata: 
  node_type: memory
  type: project
  originSessionId: f1bdbd78-151f-470b-b703-dd9af9b3fecc
  modified: 2026-09-23T07:06:36.819Z
---

`ct/0533_ct.nii.gz` was 17,301,504 bytes -- exactly 16.5 MiB -- sha256
`20e673dc6c2acd1e9aabc32b18d5f3eb47f877893eca0640cb3cfdd3960d6e23`, failing `gzip -t`, against about 260 MB for its
neighbours. Dataset813 links `COLONOG_378_0000.nii.gz` to it, so every CT-derived bank held 801 of 802 and SPINEPS
skipped the case.

**It was NOT a local download defect.** This note said so for a day and that was wrong. The HuggingFace release
carries the same object: the LFS identifier equals the grid file's sha256, so every public consumer gets the
truncation, and a re-download returns the identical file. The grid file (25 June 2026) predates the 7 September push,
so the mirror was uploaded from it.

**Repaired 2026-09-23** (job 40416624, `slurm/ctsp0533_repair.sh`): rebuilt from TCIA with the release's own
`fetch_from_tcia.py` -- the SeriesInstanceUID `manifest.json` names, 577 slices, dcm2niix, resampled onto the label's
grid -- now **250,067,995 B, sha256 `478a74e909956ff98df9fb5ccb4cced3671bf870935f4a29163d1ce9dfa164d5`**, shape
(512, 577, 512), PIR, affine identical to the label. `~/data/CTSpinoPelvic1K/ct` holds 802 and all pass `gzip -t`.
The truncated file is kept at `/rs/rs_grp_oschome/go2432/data/ctsp0533_repair/0533_ct.TRUNCATED.20e673dc6c2a.nii.gz`.

**`spine_bone_pct` is measured over the VERTEBRA identifiers only.** Nothing says so, and the rebuild reads 75.7% over
all labels against the manifest's 85.1 -- a 9-point gap that looks exactly like the wrong acquisition of the same
patient. Ten intact records measured the same way (job 40416604) sit 2-5 points below their own recorded value over
all labels and reproduce it to +0.12 to +0.27 over the vertebrae; 0533 rebuilt is 85.32 vs 85.1, delta +0.22.
`manifest.n_voxels_fg` is separately broken (0 in 340 of 802; 2,094,598 for 0533 against 3,167,246 in the mask).

**The HuggingFace object is REPLACED (2026-09-23).** The first push (job 40418393) failed rc=1 -- `huggingface-cli`
is deprecated on the grid env and prints help instead of uploading; job 40419665 used `hf upload` and landed. Verified
independently against the API (`paths-info/main`): `ct/0533_ct.nii.gz` now 250,067,995 B, LFS sha `478a74e9...`, commit
"Replace the truncated ct/0533_ct.nii.gz..." 2026-09-23T18:08Z. Public consumers now get the rebuild. Still open:
`KNOWN_ISSUES.md` section 10 (written in `data/zenodo_deposit/KNOWN_ISSUES.md`, not yet pushed with the release) and
the same note on the Zenodo deposit.

**How to apply:** banks rebuilt after 2026-09-23 03:03 EDT hold 802; pin "801" in any claim already published, and say
which. Related: [[rsnai-paper-endpoint]], [[dataset813-image-links-are-container-paths]].
