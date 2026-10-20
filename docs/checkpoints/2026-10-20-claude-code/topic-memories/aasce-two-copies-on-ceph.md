---
name: aasce-two-copies-on-ceph
description: "AASCE \"609 vs 579\" explained -- release = 609 labelled (481 BoostNet train + 128 test) + 98 challenge-test without landmarks; two Ceph copies (mirror 707; old request-form copy 579 without the 128); HOME path is a symlink since 2026-10-10"
metadata:
  node_type: memory
  type: project
  originSessionId: 0599380b-0d32-4e19-b5be-65bdd1017566
  modified: 2026-10-20T22:21:56.266Z
---

Grid listing 2026-10-20:
- **Mirror** (GitHub zlinzju/ke30_u7_AASCE2019, MIT repo, fetched 2026-09-22 01:06):
  `/rs/rs_grp_oschome/go2432/data/thoracic_xr/mirror_zlinzju_ke30_u7_AASCE2019/unpacked/ke30_u7_AASCE2019-master/`
  boostnet_labeldata/data/training 481 + data/test 128 = **609 labelled**, plus test/ 98 challenge films (and test/resized).
- **Old request-form copy**: `/rs/rs_grp_oschome/go2432/data/aasce2019_boostnet/raw/aasce` train 481 + test 98 = **579**;
  lacks the 128 labelled test films. `~/spine-detector/data/raw/aasce` is a symlink to it since 2026-10-10 (so "HOME"
  is not a third copy). grid_copy_md5.json: identical 962, differing 98 (the 01-July-2019-* challenge set), only in
  mirror 35.
- **Thoracic test prep** `data/thoracic_xr/aasce/` (summary.json): films_labelled 609, written **608** (1 degenerate box),
  label_order_not_monotonic 28. 457 = 481 minus 24 converter geometry skips (unsorted-landmark artefact) in the deleted
  v4/v5/v5c banks; the 128 never reached aasce_drr. Training-vs-test use of AASCE is still undecided (audit row).

Sources: spine-program 10_data_platform_grid/docs/DATA_COMPLETENESS_AUDIT.md AASCE rows; spinesurg-ct-nnunet
data_platform/sources.json `aasce2019_boostnet`.

Related: [[schwingnet-repo-and-registry]], [[data-platform-migration-2026-10]].
