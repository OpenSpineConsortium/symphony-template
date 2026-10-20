---
name: nhanes-double-inclusion
description: NHANES II enters the allspine banks twice (~/films_drr source nhanes AND ~/nhanes_drr), split independently -- 89 % of NHANES val patients have their copy in training (v2, v6, v7); pooled real-film numbers are inflated for that part
metadata:
  type: project
---

Found 2026-09-22 while sourcing the manuscript's film naming number. `make_context_crops.py` splits per source;
`~/films_drr` (source `nhanes`, patient-grouped) and `~/nhanes_drr` (`NH_00160_c`, same Zenodo pickles,
name-grouped) are two sources of the same 543 films. In v6 and v7, 48 of 54 NHANES validation patients have their
other copy in training; v2 was built the same way (its build log shows both sources). The level-model encoder
was trained on the same split. Record: `spinesurg-ct-nnunet/docs/NHANES_DOUBLE_INCLUSION_2026-09-22.md`.

**Why:** a plausible, finite, wrong number again -- the pooled `real_film` (7,339 vertebrae) counts NHANES twice.
The "99.02 % shortcut-free real-film" figure in [[mixed-length-head-and-sota]] includes it.

**How to apply:** quote real-film naming per source: CSXA and BUU-LSPINE are clean (BUU levels are assigned by
position, not annotated). Never pool NHANES from these banks. A clean bank needs one NHANES directory or a
cross-source patient key. Also: tally a bank's sources with the FULL counter -- `most_common(8)` hid the second
NHANES source once already. Related: [[rsnai-paper-endpoint]], [[no-jobs-on-login-node]].
