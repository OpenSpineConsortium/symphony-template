# Three Hugging Face fetches ended COMPLETED with nothing fetched

Source: the thread "Paired CT and X-ray datasets", 2026-10-23. The measurement is the answer of the gate word status at 09:29 UTC (job schwingnet-status through .github/workflows/grid-accounts.yml, kept on this repository's branch `grid` as logs/job-schwingnet-status.json at commit 1c8246b). It is read beside SchwingNet's grid/run-platform-fetch.sh and grid/platform-fetch.sbatch at 6e93909, and spinesurg-ct-nnunet's data_platform/reacquire/reacquire.py at bf1432f. No Claude Doc or artifact.

## The question

The owner asked why the fetches of the night before ended in seconds. Five sources he had approved were each sent as one job, and they waited afterany behind the VinDr-PCXR fetch. That fetch was tabled and cancelled, and then the five ran. The status word lists each as COMPLETED, exit 0:

| job | what | ran |
| --- | --- | --- |
| 40710713 | dp_hf_cads_unique | 1 h 43 min 40 s |
| 40712197 | dp_hf_rexgradient_160k | 6 s |
| 40731148 | dp_fluorosam_weights_drive | 19 s |
| 40731313 | dp_ipcai2025_robotic_xray_drive | 11 s |
| 40731321 | dp_hf_fluoroseg | 20 s |

The answer cannot show whether anything landed. It includes the log only of a job that failed or was cancelled, and its space list stops at the 80 largest sets, the smallest of which was 4 GB. None of the five landings is in that list.

## Why the three Hugging Face fetches fetched nothing

The hf-token route runs reacquire.py hf-get. hf-get hands `--include` to huggingface_hub's snapshot_download as allow_patterns, and to fnmatch when it checks each file of the repository's tree, so it reads `--include` as a glob. The acq route's acquisition_fetch.py and the zenodo-get helper read their `--include` as a regular expression instead, where `.` means any file. hf-get also returns 0 when it checked no file: it writes files 0, failed 0, all_verified false, and exits 0 because nothing failed.

- ReXGradient-160K and FluoroSeg: the lines gave `--include .`, the regular expression's "anything". As a glob, `.` matches only a path that is exactly `.`. Nothing was downloaded, and the job's few seconds went on listing the repository.
- CADS: the line gave `--include CT-TRI/*`, which is a glob. But the Hugging Face tree of 2026-09-23 (spinesurg-ct-nnunet's data_platform/sources.json) names the CT-TRI part's folder `0043_new_ct_tri`, and fnmatch is case sensitive on Linux, so it matched nothing either. The 1 h 43 min fits hf-get's check, a file-by-file listing of a repository of many thousands of files, rather than a download. The landing is also missing from the list of the 80 largest sets, though CT-TRI alone is 83.4 GB.

The fault was in the fetch list, not in the helper. The same list uses `--include .` correctly for the zenodo and acq routes, and the hf-token lines copied it.

## The two Google Drive fetches most likely landed

gdown exits non-zero when it cannot fetch (a file it may not read, or a quota page), and the job returns gdown's code. Both exited 0, in times that fit their sizes: 0.85 GB in 11 s and 1.0 GB in 19 s. Both are under the 4 GB cut, so the status word cannot confirm them. On the grid, the check is meta/file_report.txt in each landing, which file(1) writes.

## What was done

- SchwingNet #158, fixed by #159:
  - The sources the owner chose whole (FluoroSeg, ReXGradient-160K, CT-RATE) take no `--include`.
  - CADS takes `*0043_new_ct_tri/*`, and its VISCERAL note `*000[12]_visceral*`.
  - The hf-token route keeps the pattern away from the shell's own globbing.
  - When hf-get's summary checked no file, the route fails with exit 3, in a line that grid/log-shapes.awk keeps, so the status word shows why.
  - Tests hold each of these, and each test fails when its fix is undone.
- spine-datasets #86 (CADS), #11 (ReXGradient-160K) and #171 (FluoroSeg) each carry a comment that their job fetched nothing, so no record moves to fetched on a COMPLETED state.
- The census thread was told to count the three as not held.

## What waits

- The resend is three gate words, each on the owner's word and count, after #159 merges and after a status check:
  - `fetch hf_fluoroseg`: about 2,650 GB.
  - `fetch hf_rexgradient_160k`: 156 GB.
  - `fetch hf_cads_unique`: 123.3 GB stated in the line, 83.4 GB of it CT-TRI.
  The submit script refuses any set beyond the volume's free space minus 5 TB.
- CADS's VISCERAL part has no line of its own, so no gate word fetches it yet.
- hf-get itself still returns 0 when its pattern matches nothing. It lives in spinesurg-ct-nnunet, which SchwingNet reads and never changes, so the check sits in SchwingNet's job script.
- Not asked for, but it would have caught this a day sooner: the status word could show each ended fetch's landing, its files and size from the CephFS attributes, as it already does for a live X-ray fetch. A COMPLETED job with an empty landing would then read as one.
