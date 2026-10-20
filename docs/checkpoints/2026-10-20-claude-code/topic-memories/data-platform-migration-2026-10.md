---
name: data-platform-migration-2026-10
description: "The imaging data platform (Greg 2026-10-07): manifest of 212 sources, re-acquisition driver, Ceph layout, migration plan and index DB live in spinesurg-ct-nnunet/data_platform; migration runs as sbatch batches B00-B14 with rename+symlink cut-over; the report is a Claude Doc; students read everything except VinDr and BUU"
metadata:
  node_type: memory
  type: project
  originSessionId: 0599380b-0d32-4e19-b5be-65bdd1017566
  modified: 2026-10-12T00:44:34.435Z
---

Greg, 2026-10-07: "manifest of where all my raw data came from ... programmatic re-acquisition ... move all
X-ray/fluoro/CT data to oschome ... a database indexing by annotation status, modality, position"; 2026-10-08:
"create an artifact of this report, begin moving all of them ... students should be able to see all of this data".

**Where things are.** `spinesurg-ct-nnunet/data_platform/` (branch L6_Class, commit 5811eda, pushed; also copied
to the grid checkout with `git archive | ssh tar` because the grid cannot fetch the private repo):
DATA_MANIFEST.md (212 cards, 929 KB), sources.yaml/json, reacquire/ (driver, refuses the login node),
LAYOUT.md (`/rs/rs_grp_oschome/go2432/data/<source_id>/{raw,converted,derived,labels,meta}` + README.yaml),
MIGRATION_PLAN.md + plan/ (build_plan.py, preflight.sbatch, migrate_batch.sbatch, cutover.sh with FINALIZE and
ROLLBACK, verify_transfer.py, publish_visibility.sh), db/ (SCHEMA.sql, build_index.py), VERIFICATION.md.
The report is the Claude Doc "Imaging data holding: manifest, migration and index"
https://claude.ai/code/artifact/74a2ec52-90e4-4f20-82a5-5c8648668676 (doc node 2fba9a59-8077).

**Procedure per batch (all sbatch, never warrior):** preflight -> migrate_batch (rsync -aH, verify by counts,
sizes, links, hashed sample) -> cutover (rename to `<path>.pre-ceph` + symlink at the old path) -> FINALIZE
(second comparison, then delete the .pre-ceph copy: the only step that frees HOME quota) -> publish_visibility
(o+rX for non-restricted folders; VinDr/BUU and banks with their pixels 0700). State: `plan/runs/<B>/STATUS`.

**Census (jobs 40578909, 40580051, 40580052; `data/inventory/census_2026-10-07/`):** Ceph 7.7 TB apparent
(data/ 5.33 TB; u251 2.2 TB non-imaging); HOME `~/CTSpinoPelvic1K` is 7.7 GB (the 1.9 TB September tree was
reclaimed 2026-09-07), `~/data/CTSpinoPelvic1K` 196 GB is the only HOME copy of the 802 CTs, `~/data` 624 GB,
VerSeFusion 195 GB, ablate 202 GB. Python `sorted()` walks uppercase names first; FluoroCap alone took > 7 h.

**Why:** the plan was built from documents whose sizes were a month stale; the census decides. **How to apply:**
regenerate with `plan/build_plan.py --census <tsv with path,gb>` (my census.tsv has path+gb columns), re-read
`migration_batches.csv`, then continue batches in dependency order (B03 after B02; B05 after B04; B10 after
B02/B04/B06/B07; B11 after B10). B13 (results, 627 GB) and deletions are Greg's calls. Related:
[[grid-access-list-gate]], [[grid-ceph-volume-oschome]], [[no-jobs-on-login-node]].

**2026-10-08 later.** Batches B00, B01, B02, B03, B08 cut over (symlinks at the old home paths, .pre-ceph originals kept
until FINALIZE); B06 (VerSe, 14 items) verified and cutting over; B04/B07/B09 copying; B14 = the fifteen "unknown"
home entries, identified from their own files: spondy_landmark = Mendeley 5jdfdgp762 (url.txt); s1v11 = the CTSP v11
build workspace (irreplaceable); pitest/pdwtest = the 2026-09-10 pelvic-incidence and pedicle-width test copies
(companions ~/pi_ostk2.csv, ~/pdw_why.py, ~/ostk_level_morphometry.csv move with them); dis_renders = 5 BUU renders;
qc.tar.gz = June CTSP QC PNGs; Multi-View-Vertebra = cloned MICCAI 2023 code; ~/docs = Feb 2026 weak-label docs;
3, 6, ada, output, v = GOMC/CHARMM chemistry; morphdef = empty scaffold; **~/github = a plain-text GitHub PAT**
(set 0600 on 2026-10-08; Greg to rotate and delete; never copy it). Students read every Ceph source folder except
VinDr, BUU, the banks with their pixels, and build_archive_private (publish_visibility.sh). The one-installation
rule on the access service is Off since 2026-10-03 00:13Z. **The Claude Docs below were created under Greg's PREVIOUS
Claude account (he switched accounts on 2026-10-08 ~20:00 when his usage ran out); they are private to that account and
unreachable from the new one unless shared or recreated from the committed HANDOFF files.** The Claude Docs: data report 74a2ec52..., handoff
c3c7acfd..., literature state 3b03e849... (all six sections filled 2026-10-08 midday from HANDOFF/LITERATURE_STATE.md,
committed on L6_Class), **research directions 93705038-d1f9-46df-a267-da8f2c2e2d17** (filled 2026-10-08 16:15 from
HANDOFF/RESEARCH_DIRECTIONS.md, commit e4c3e88: 16 ranked projects; PAR-1 ratio-only 3-D target first, PAR-2 projected
morphometry on the 802 v11 volumes second, FLU-1 the 63-volume reader queue third; parity = 5-point non-inferiority on
one label set; one open comment to Greg on that margin). **HANDOFF/ committed 097933a (2026-10-08 ~16:45)**: README,
RESULTS_CATALOG, RECIPES, DATASET_USAGE, LEAKAGE, MANUSCRIPTS, INFRASTRUCTURE, CONTEXT_EXPORT + context/ (141 redacted
memory copies, INDEX.md with LEAKED/SUPERSEDED statuses), GLOSSARY, OPEN_QUESTIONS, working_notes/builders; the handoff
Claude Doc c3c7acfd filled the same evening. **HANDOFF/GREG_ONLY/ is deliberately untracked** (credential locations,
commercial stance, withheld contacts, student usernames, Greg's personal e-mail) until Greg decides whether it enters
the private repo; the reader split (OPEN_QUESTIONS A29) is unconfirmed, so the whole folder is Greg-only for now.
Before any handover re-run `HANDOFF/working_notes/builders/refresh_context.py` then `build_context_index.py`.

**VinDr-SpineXR IRB: HPR 2026-330, notice 2026-09-29, Not Human Participant Research, supplement to 2026-269** (PDF at
ctsp root, untracked and now gitignored; copy in spine-program/01_carm_level_detection/regulatory/). PhysioNet
credentialing approved 2026-10 (CITI done); the VinDr DUA still has to be signed on the project page. Recorded 2026-10-10
in main.tex (placeholder filled), statements.md, DATA_MANIFEST/sources, OPEN_QUESTIONS A5.

**2026-10-10 15:40 (Greg: "do all of this and if finalize should be done in your opinion, do it").** B04 (27/27), B07
(5/5), B09 (7/7) copies finished 2026-10-09/10; census done; B03 had nothing to move (both sources absent). Chain
submitted from plan/: cutover B04 40595231, B07 40595232, B09 40595233 -> visibility 40595234 (FOLDERS = the 16 folders of
those batches; publish_visibility now also closes mendeley_5jdfdgp762 and spine_detector_corpus, both BUU-derived) ->
dedup_hash 40595235 (GROUP_IDS A05 A06 A11-A16; came back all not_ready because its batch-busy gate counts ANY pending
dp_cutover job, and the nine FINALIZE jobs were already queued: schedule the hash only after every cut-over or finalize
job has left the queue; resubmitted as 40595263 afterany the last wave. **The same gate is in dedup_apply.sbatch:
never queue a dp_migrate or dp_cutover job, even one that depends on the apply, while the apply is pending or running;
run the apply alone, then submit the rest with no dependency**) -> FINALIZE waves: B00/B01/B08 40595236-38, then B02/B14/B04
40595239-41, then B06/B07/B09 40595242-44 (afterany chains). FINALIZE deletes the .pre-ceph originals after re-comparison;
refusals print REFUSED_* in logs/dp_cutover_<job>.out. After it: HOME should drop well below the 4,295 GB soft limit;
dedup_apply (A01 185 VerSe'19 files, A07 after Greg reads s1v11) becomes possible; B10/B11 (banks) and B13 (results)
remain unstarted.

**2026-10-11 21:00, Greg: push spine-program to ONE repo, https://github.com/OpenSpineConsortium/spine-program (exists;
he splits per project later). Pushed from WSL after an unauthenticated API check that it is not public (it holds
SchwingNet). The Symphony conversion (workflow wf_b7c8a2ff-5d4: SYMPHONY.md, DATA.md, Recipe skeleton, student-safe
cuts, REPOS.md and tools/split_and_push.sh per folder) is committed and pushed to the same repo when it finishes; "Symphony"
is Greg's name for the student protocol = Lab Recipe + Beethoven + CLAUDE.md, undefined elsewhere on 2026-10-11.**

**2026-10-11 20:15, Greg: "yes do everything, finish this" and "all the students also have credentials for these"
(the BUU and VinDr agreements).** So: the five closed folders (vindr_spinexr, buu_lspine_3600, buu_lspine_v1_smoke,
mendeley_5jdfdgp762, spine_detector_corpus) open to the approved-student gate (publish_visibility FIXED_RESTRICTED now
empty, with Greg's statement quoted in the script); dedup_apply submitted for A01 A05 A06 A11 A14 A15; the remaining
batches B05, B10, B11, B13 run as one chain after the apply (migrate -> cutover -> finalize -> visibility); the
unconditional deletion candidates (release zips beside verified unpacked trees) are deleted in a guarded job; the
conditional ones (vendor zips pending unzip -l, VerSe canonical/, build archives, superseded banks) are listed for Greg.

**dedup_apply 40598719 ran 2026-10-11 20:40 (23 min): linked A01 185 files (8.4 GB), A05 1,226 (22.5 GB), A06 3, A11 77,
A15 965; A14 partial (1 linked, 1,412 refused: the read-only Mendeley modes again, fix with chmod u+w on the Ceph
duplicate then rerun GROUP_IDS=A14 when nothing else is queued). Ledgers in dedup/applied/ and $RS/dedup_ledgers/.
dedup_guard.sh must pass before any deletion.** The remaining-batch chain (B05, B10->B11->B13 migrate -> cutover ->
finalize -> visibility; plus the guarded deletion job for the TS zips and NHANES extracted pickles) was submitted right
after the apply with no dependency.

**MIGRATION FINALIZED 2026-10-11 20:00.** Every batch with data is copied, verified, cut over and FINALIZED with the
.pre-ceph originals deleted after full comparison: B00, B01, B02 (5), B04 (27), B06 (14), B07 (5), B08, B09 (7, FluoroCap
316 GB took 11 h to hash both sides), B14 (9); B03 had nothing to move. Three finalize refusals, all benign and fixed:
two read-only Mendeley copies (chmod -R u+w in a job, then re-finalize) and one stray symlink inside
build_archive_stage.pre-ceph (unlinked in a job). **HOME 4,051 -> 1,902 GB of the 4,295 GB soft limit.** Dedup hash run 3
(40595263): A05 TotalSegmentator v2 = v3 for 1,226 CTs (22.5 GB linkable), A06 3, A11 77, A13 10, A14 1,413 (89 MB),
A15 965 (59 MB) identical; A16 fluorocap_pack different (1 size differs, 1,501 unpaired: not a copy); A12 not_ready
(buu_lspine_2000 is batch B05, never run). Still unstarted: B05 (BUU 2000), B10/B11 (banks), B13 (results, Greg's call).
dedup_apply can now run (every covered batch is FINALIZED) for A01, A05, A06, A11, A13, A14, A15 once Greg says so;
A04/A13 removals and A07 wait on Greg. Visibility: 11 folders opened 2026-10-10, 5 closed (BUU, BUU smoke, Mendeley,
spine_detector_corpus, VinDr).

**2026-10-08 evening: the spine-program seed (Greg: "a folder I can push to GitHub ... logical set of projects, triaged,
C-arm detection first ... self-contained with memory, description, goal").** Workflow wf_e27ebb09-038, script
`workflows/scripts/spine-program-seed-wf_e27ebb09-038.js` (resume: `Workflow({scriptPath, resumeFromRunId:
'wf_e27ebb09-038', args:{date:'2026-10-08'}})`; completed agents replay from `subagents/workflows/wf_e27ebb09-038/journal.jsonl`).
Target `Desktop/spine-program/` (13 project folders + _plan/; not yet git-initialised). State at 20:30: 7 inventories, 2
proposals, the plan and 12 of 13 builds cached; builder `01_carm_level_detection` and the critic and 12 verify/fix calls
failed on the account's session limit (resets 01:00 ET) and rerun on resume; the builder prompt continues from disk.
Order: 01_carm_level_detection, 02_transitional_naming_truth, 03_ctspinopelvic1k_dataset, 04_openspinetoolkit,
05_ct_morphometry_parity, 06_transitional_ct_census, 07_plain_film_level_id, 08_render_devices,
09_wrong_level_clinical_qi, 10_data_platform_grid, 11_students_grid_access, 12_website_pacs_demo, 99_archive.
**Finished 2026-10-08 23:30** by a continuation run (wf_c8c213d2-3d6) that took the cached results as inputs
(`_plan/CACHED_RESULTS_2026-10-08.json`) because `resumeFromRunId` replays only an unbroken prefix of unchanged calls and
the failed first builder broke it (lesson: never edit a prompt before resuming; cache = journal, keyed on prompt + order).
Tree: 13 folders, 6,880 files, 762 MB (01 is 302 MB: figures, two packet PDFs, the CNS v10 deck, 1,100 small results);
no secrets, no banned word, no file over 25 MB; institutional e-mails only. Critic checked 19,455 items, salvaged 6
left-behind items, 8 cross-project defects fixed by the root writer. Greg decides: author lists in manuscript sources and
CNS decks; the 58 preview PNGs in 02; the withheld HF handle; the size of 01. Git initialised and committed locally by the
session; Greg pushes to a PRIVATE GitHub repo.

**2026-10-08 midday.** B06 (VerSe: VerSeFusion/data, vf_813, implant_verse, ctsp_drr_obl ...) and B14 cut over, .pre-ceph
kept; B04/B07/B09 still copying; TotalSegmentator v2.0.1, BUU, FluoroCap and the banks are NOT on Ceph yet. HOME is
4,051 of 4,295 GB: only FINALIZE (deletes .pre-ceph) frees it, and that is Greg's call. **The handoff workflow
(wf_78420abb-db7) was interrupted at 09:42 before writing anything; HANDOFF/ held only LITERATURE_STATE.md until it was
resumed at 11:45** (readers, author, three verifiers, fixer; output HANDOFF/README, RESULTS_CATALOG, RECIPES,
DATASET_USAGE, LEAKAGE, MANUSCRIPTS, INFRASTRUCTURE, CONTEXT_EXPORT, GLOSSARY, OPEN_QUESTIONS). Dedup plan written by
workflow wf_f61cc81c-91a into data_platform/dedup/ (DEDUP_PLAN.md: 46 groups; at most 97.7 GB linkable byte-identical;
482.9 GB deletion candidates for Greg; 1,659 index alias rows); its hash job `dedup_hash.sbatch` is read-only and gates on
VERIFIED + cut over + no running batch job; `dedup_apply.sbatch` also requires FINALIZED. Nothing of dedup is on the grid
yet: copy the folder (git archive | ssh tar), then `sbatch -D "$PWD" dedup_hash.sbatch` from
~/spinesurg-ct-nnunet/data_platform/dedup after the B06 cut-over job ends (B06 and its visibility pass finished 12:35;
dedup committed 9bc7303 and shipped; hash job 40581845 submitted 12:44, results in dedup/hash_results/<gid>.json;
groups whose batch is still copying (B04 BUU/AASCE/Mendeley_716, B07 TotalSegmentator v2, B09 FluoroCap, B10/B11
banks) come back not_ready and are rerun with GROUP_IDS later). **Hash verdicts 13:03:** A01 VerSe'19 = VerSe'20 for
185 files, 8.42 GB (identical, linkable after FINALIZE); A02 canonical/ has 224 links and no byte copy; A03 the HF
staging trees are NOT hard links (27 same inode, 2,753 files with no byte twin: 56 GB of distinct bytes, a kind-(b)
candidate for Greg, not a link); A07 s1v11 build labels = release labels, 802 files 1.19 GB (hold greg_review); A09
0533 repair = release; A08/A10 no twins (ctsp_april shares no CT bytes with the release); A04 came back "missing"
because **the grid's bash 4.2.46 keeps the quotes of a quoted replacement in `${var/pat/"$new"}`** (WSL bash 5.2 does
not; the 106-check suite missed it); fixed, rerun as job 40581924: 357 renders identical, the 13 `ann/glgl*.json`
differ only by the embedded name, hold `removal_preferred` stands. Summary in dedup/HASH_RESULTS.md. **The TCIA CT Colonography raw DICOM (721 GB) and tcia_nifti (336 GB) are on
neither HOME nor Ceph** (dedup readers, 2026-10-08 census); nothing records what removed them beyond the 2026-09-07
reclaim; the manifest card says on_disk_state_unknown and the re-acquisition route is `tcia_ctsp_download`.

**2026-10-12 03:30 EDT, remaining-batch chain.** Migrate: B05 40598777 3/3 VERIFY_OK (BUU-LSPINE 2000 8,001 files 4.07 GB; xrsp1k 32,092 files 4.64 GB), B10 40598778 64/64, B11 40598779 64/64, B13 40598780 still RUNNING (2 items verified: nnunet results 299 GB, ablate 202 GB). Cutover/finalize: B05 cut 40598781 + finalized 40598782; B10 cut 40598783 + finalized 40598784 (64 FINALIZED); B11 cut 40598785, finalize 40598786 RUNNING (18 finalized so far); B13 cutover 40598787 and finalize 40598788 PENDING; visibility 40598789 PENDING. No REFUSED line anywhere. HOME 1,902 -> 1,334 GB (pan_quota); Ceph oschome 9 TB of 20 used (46.8 %).
**dedup_delete 40598790 "REFUSED by dedup_guard" was NOT a guard refusal:** the job did `cd "$(dirname "$0")"`, and sbatch runs a spool copy of the script, so the cd landed in /var/spool/slurmd and `bash dedup_guard.sh` was not found -> non-zero -> refused; nothing deleted. Fixed on the grid (cd to the dedup dir by absolute path) and requeued afterany the visibility job: dedup_delete 40599718, dedup_chmod 40599719 (chmod -R u+w Ceph mendeley_5jdfdgp762/raw/spondy_landmark), dedup_apply GROUP_IDS=A14 40599720 afterany the chmod. Lesson: never `cd "$(dirname "$0")"` in an sbatch script; use the absolute folder or rely on `-D`. Follow-up check scheduled 2026-10-12 06:37 (session cron ba54d08c).

**2026-10-12 06:37 EDT check.** B13 migrate 40598780 COMPLETED, STATUS 3/3 VERIFY_OK. B11 finalize 40598786 COMPLETED: 64 FINALIZED, 0 REFUSED. B13 cutover 40598787 COMPLETED (5 CUT lines, 0 refused). B13 finalize 40598788 RUNNING (1 of 3 finalized: nnunet/results.pre-ceph deleted after full compare). Old visibility 40598789 CANCELLED (replaced by 40599867 on the fixed script, d9b388d); 40599867, dedup_delete 40599718, dedup_chmod 40599719, dedup_apply A14 40599720 all PENDING behind 40598788. Earlier on 2026-10-12: visibility 40599886 opened the VinDr/BUU items of vindr_spinexr, buu_lspine_3600, buu_lspine_v1_smoke, spine_detector_corpus, mendeley_5jdfdgp762, buu_lspine_2000, xrspinopelvic1k (opened 7, closed 0); multisource_banks VinDr/BUU banks still drwx--S--- until 40599867. HOME 818 GB of 4,295 (from 4,051 on 2026-10-08). Next check scheduled 08:41 (session cron).

**MIGRATION CHAIN COMPLETE 2026-10-12 08:41 EDT.** Every batch with data is copied, verified, cut over and FINALIZED; B13 finalize 40598788 COMPLETED (3/3 FINALIZED, 0 refused); no REFUSED line in any cutover/finalize log of the chain. Visibility 40599867 (fixed script d9b388d) opened 20 folders and closed exactly 2 items (build_archive_private, s1v11): multisource_banks VinDr/BUU banks now drwx--Sr-x (others r-x); s1v11 drwx--S---. dedup_delete 40599718: guard OK; DELETED TotalSegmentator v3.0.0 zip (37.4 GB) and NHANES extracted pickles (159 GB, zip intact first); KEPT the v2.0.1 zip (23.58 GB) only because the script looked for cases in raw/TotalSegmentator/Totalsegmentator_dataset_v201, while the 1,228 cases sit directly under raw/TotalSegmentator/ (s0000 ... s1055); the zip is at raw/TotalSegmentator/Totalsegmentator_dataset_v201.zip and is safe to delete on Greg's word (Zenodo re-downloads it). dedup_chmod 40599719 done; dedup_apply A14 40599720: linked 1,413 files, refused 0. HOME 520 GB of 4,295 (was 4,051 on 2026-10-08); Ceph oschome 9 of 20 TB (46.0 %). Nothing of the chain is queued.

**2026-10-12 evening, Greg: "anyone can read anything, dont worry about tokens ... delet those last zips".** spinesurg-ct-nnunet 0ab783f (pushed): s1v11 opened without the token check (visibility 40602925); build_archive_private stays owner-only because its one file is annotator_map.json (students' identities). Job 40602926 opened envs/spineps212 (963 owner-only entries -> 0) and results/ (already open). Job 40602927 DELETED the TotalSegmentator v2.0.1 zip (23,581,218,285 B; guard OK; 1,228 cases unpacked beside it). Greg's HOME stays closed. Answers posted on spine-program #68-#72; claim of #68 records them.
