# Finishing the nearly-done spine-datasets work

Source: the thread "Dataset finalization", 2026-10-23, in the project symphony_3. Read from OpenSpineConsortium/spine-datasets' open pull requests and issues, its board at main b44ba32, its records under datasets/ at main 4b2c993, and the status word's reading of 02:05 UTC on symphony-template's branch grid (26f3bde, logs/job-schwingnet-status.json). No grid job, fetch or resend was made.

## What was merged

Twelve pull requests that were finished and green went in, each squashed, and `bash scripts/check.sh` passed on main after the first eleven (1,310 tests).

- The promoter's four records of Zenodo CT sets it had fetched, sha256-checked and installed read-only under the shared tree: #164 zenodo_lumvbcanseg, #165 zenodo_medpelvis3d, #166 zenodo_tmtv_benchmark, #169 zenodo_unitochest. Each now reads fetched with its grid path and promoter job.
- Ashley's seven licence records, each marked ready since 2026-10-22 with the owner asked for review: #122 LUMOS (CC BY-NC 4.0), #123 IPCAI 2025 paired X-ray and CT (research only), #124 VerSe 2D projections (no stated licence), #125 Veriserum (In Copyright, non-commercial), #126 Guide3D (CC BY-NC 4.0), #127 CathAction (CC BY-NC-SA 4.0 behind a form), #128 VFSS2022 (not released; a letter is next). Each record now says needs-owner, or for VFSS2022 the letter, with the licence line quoted; the merge closed its issue.
- #130, the Mendeley manifest command: it takes a page address, a DOI or a bare id, the latest version unless one is named, several datasets for one record under raw/<id>/, readies the record's licence, status and history in the same step, and checks the result against the promoter's rules. Its tests passed on main before the merge. It closed #129.

None of the merges started a fetch: a record's status changes on main, and the promoter acts only on a merged manifest.

## What is left, and why it waits

- The Kaggle sets #23 (#167) and #24 (#168). #24's archive came down (job 40712010) but its bank job failed by design, since SchwingNet's recipe grid/banks/kaggle_fracture_multiregion.json still has four fields to confirm, which only a listing of raw/ on the grid settles. #23 holds only its claim. Both need the owner's word for a grid job.
- CADS #86 (#159) waits on job 40710713, queued behind 40704982; BIMCV COVID-19+ #111 (#147) failed its fetch 40732922. The thread "Handoff merges and grid checks" holds both.
- RATIC #87 and RSPECT #88 (#158, #160) and the eleven "owner's step" drafts (#147 to #157) wait on the owner's paperwork (owner-paperwork-sitting.md).
- The census, #178 and #179, belongs to the thread "Dataset census and roadmap".

## Records behind the grid

Set beside the status word's folder list, 21 records that do not say fetched have a folder of the same name, or a near one, in the owner's data tree. The data is there; the records were not brought along.

- todo: aariz_cephalograms (folder aariz), aws_stoic2021, idc_cptac_lscc, idc_cptac_luad, idc_ldct_and_projection_data, idc_midrc_ricord_1b, idc_nsclc_radiogenomics, idc_nsclc_radiomics, idc_spinal_multiple_myeloma_seg, idc_spine_mets_ct_seg, kub_stonex, nih_chestxray14, pengwin_task2_xrays.
- requested: zenodo_ts_task_hip_implant, zenodo_ts_task_liver_lesions, zenodo_ts_task_pleural_effusion.
- needs-owner: cathaction, ipcai2025_xray_ct, lumos (folder zenodo_lumos), verse_2d_projections, zenodo_vsd_fullbody.

idc_lidc_idri, idc_nlst (full) and idc_prostate_anatomical_edge_cases have no folder of their own; they may sit inside the folder idc, which a listing would show.

Two things follow. First, the open issues #25, #26, #30, #36 to #37, #44 to #54 and the TotalSegmentator task issues ask to obtain data the grid already holds, so their honest next step is to record it, not fetch it. The census (#179) adds a status held for data on the grid by the owner's own chain rather than the promoter, with a held history entry and a grid_path, and moves aariz_cephalograms to it; this thread reconciles the rest once #179 is on main, held where the status word's size matches the record and fetching with a note where the folder may be a partial fetch. Second, for the five needs-owner records the files are on the grid while the owner's decision on a non-commercial or research-only licence is still open: whether that decision allows the data's use is the owner's question, and the records should say the data is held while the decision waits.

## Outcome of the reconciliation

spine-datasets #209 (closing #202) moved 18 of those records to held, each against the 02:05 UTC listing. aariz_cephalograms and ipcai2025_xray_ct were already held by the census (#179), and zenodo_vsd_fullbody waits for job 40697705 to end. No folder was smaller than its record's stated size, and every job the listing names for them ended COMPLETED. The held review then turned up three records that had been todo with no obstacle, though their licence is non-commercial: aws_stoic2021 (CC BY-NC 4.0), idc_midrc_ricord_1b (CC BY-NC 4.0) and idc_nsclc_radiomics (CC BY-NC 3.0). Each now names the owner's decision as its obstacle, as cathaction, lumos and verse_2d_projections already did. The data is on the grid, but whether it may be used is still the owner's call for those six.
