# The spine data census, and the roadmap of the dataset work that remains

Source: the thread "Dataset census and roadmap", 2026-10-23, on OpenSpineConsortium/spine-datasets.
The work is spine-datasets #179 (issue #178, merged as 6856c4b), the tracks #174 to #177 and the
tasks #181 to #208; another thread's #209 (merged as 90c4c92) then moved 18 more records to `held`.
The CT part is spine-datasets #213 (issue #181, merged as 62068b2) and #214 (merged as b6fe73f).
The artifact "Spine Data Census" (https://claude.ai/artifact/PJrXJCBK8S4m8igHf5Q3MU) is a copy of
the page the census wrote on the branch `census` at aa67051, and the artifact "Spine CT Census"
(https://claude.ai/artifact/2LDmxK2rfnmcVNyWURpabv) a copy of the CT page beside it.

## The question

On 2026-10-23 the owner asked for four things. The first was a task for all the dataset work that
remains. The second was tracks for the big-picture work: knowledge synthesis, workflow development,
and workflows whose datasets grow without a restart. The third was a start on planning the
annotation of the paired CT and X-ray data. The fourth was a census artifact that is accurate and
breaks the pairs out. He then asked for the census to keep itself up to date: one formatted metadata
file per dataset, and a script that folds new and changed files into the census so that it
accumulates.

## What was built

Every dataset is one record, `datasets/<id>.json`, in spine-datasets. `tools/census.py` folds the
records into the census. A row whose record has not changed (by its sha256) is carried, a new or
changed record is derived afresh, and a dated log says what moved. The rules a row is derived by are
a hash of `tools/census.py` and `tools/pipeline.py`, so a change to either derives every row again.
Each record keeps the date the census first saw it, and that date survives the record being removed
and written again.

`.github/workflows/census.yml` runs the census on every merge that touches the records or the
census code, on issue events, and once a day. It writes `CENSUS.md`, `census.html` and `census.json`
to the branch `census`, and a quiet day pushes nothing. The docs site renders `census.html`.

- **Counts.** Subjects, still X-ray images, X-ray videos and sweeps, the frames inside those, CT
  volumes and bytes, each under one standard key. The older names are read as aliases by the kind of
  set, so a frame inside a video or a CBCT sweep is never counted as a still image.
- **Pairs.** A real X-ray set with the same subject's CT carries a `pairing` block. Its tier follows
  the record's status by itself: A on the grid, B open or granted, C behind a letter, an agreement
  or the owner's hand, D refused or embargoed, E a pair of something other than the spine. A task whose body names
  `Record: datasets/<id>.json`, with no such file yet, is listed as pending, among the pairs when it
  carries the label `paired`.
- **Checks.** `census.py check` runs in the required check. It refuses a field the page shows that is
  missing or not text, a link that is not a web address, two records with one id, and an id that is
  not its file's name. `tools/dataset_review.py` fails a move to `held` whose path is outside the
  owner's data root and the shared tree, and flags every other move to `held` for whoever merges, to
  check against a status listing.

## What the adversarial review found, as lessons for any folded census

A separate reviewer ran the tests, the checks and scenarios on a throwaway clone, and made nine
findings. All were fixed, except the two left as stated below.

1. A carried row is only as fresh as the code that derived it. The rules number lived in the census
   while the stage came from the pipeline's code, so a change there left old stages in place. The
   fix is to hash the deriving code into the rules.
2. An id is a key. Two records with one id made every run look changed and push a commit.
3. Every field the page reads must be checked by the checker. A null licence passed both checks and
   then crashed the render, which would have stopped the docs site.
4. What is counted must follow the kind of record. COBRA's 375,618 CBCT projections had been 89 % of
   the "X-ray images on the grid" until frames inside sweeps got a count of their own.
5. A change to the page code alone must still reach the branch. Writing the rules hash into the data
   file does that.
6. Arithmetic finds records that contradict themselves: an NHANES II count off by one, a femur set
   described as a spine set, and a cohort's second paper left out of the counts.
7. A status the census trusts must be reviewed, so a move to `held` is now checked.
8. Dates. A rules change must not move a record's last-changed date. Left as it is: the log of what
   moved is not trimmed, since it is the record and grows by a few lines a day.
9. Smaller points: sizes are rounded, not truncated, and a licence's open reading counts only outside
   parentheses. Left as it is: one mirror's path keeps its uploader's public handle, since that is the
   folder's real name.

One more problem turned up after the review. A copy of one set lies in a project folder of the
owner's grid home, and the folder's name trips spine-datasets' confidentiality word rule. The
required check caught it, so that record no longer names the path and waits as `needs-owner` for a
grid job that lists the copy and moves it.

## How the held paths were checked

The 22 held paths of #179 were each read against the grid's status listing of 2026-10-23 02:05 UTC
(`logs/job-schwingnet-status.json` on this repository's branch `grid`, 26f3bde), and the 18 that
#209 moved are records #202 took from the same listing's folders. The listing gives
the data root's folder sizes down to 4 GB and the shared tree's folders. Its sample report of
2026-10-22 covers the smaller folders, read at the paths the records give. Its job list shows only
the newest jobs, so an older fetch is judged by its folder's size against the size the source states.

## The data in numbers, from the census of 2026-10-23 at c8ee645

A snapshot, taken after #209 moved 18 more records to `held` for #202.

- 109 records. 46 sets are on the grid: 40 held by the owner's own chain and 6 fetched by the
  promoter.
- The sizes, where the records give them: 1.9 TB over 28 of the 46 sets. 160,879 still X-ray
  images over 16 sets. 694 videos and sweeps holding 376,220 frames. 8,217 CT volumes over 16 sets.
- Stages: 9 downloadable now, 9 to ask, 27 asked and waiting, 5 granted with the fetch pending, 6
  on the grid in the shared tree, 40 held, 11 needing the owner, 1 refused and 1 later.
- Paired CT and X-ray, by tier:
  - A, on the grid: 5 sets with 1,651 subjects (C-ArmLSpine 149, COBRA2026 692, DeepFluoro 6,
    Ljubljana 1, LUMOS 803). LUMOS's 803 are its record's count; whether its films and its CTs
    are the same patients is #207's question, so they are pairs only once #207 says so.
  - B, open or granted: none.
  - C, behind a letter, an agreement or the owner's hand: 3 (Huashan, LevelCheck, NIT Warangal).
  - D, refused or embargoed: 2 (Balgrist, COBRA's embargoed cases).
  - E, pairs of something other than the spine: 4 (the Geneva hip phantom, the IPCAI 2025 femur
    set, Veriserum, the pig set).
  - Pending: 19 pair leads, as tasks.
- Before #209, at 86f4190: 28 sets on the grid (22 held), 1.4 TB over 14, 44,569 still images over
  13, 7,837 CT volumes over 14, and tier A 4 sets with 848 subjects, LUMOS then in C.
- Left out on purpose:
  - Synthetic renders, which measure nothing about real images.
  - Two held collections whose use is the owner's call.
  - The anomaly harvest's 55 CT releases, which got their records by #181 (below).

## CT and its masks, from the census of 2026-10-23 at aa67051

The owner then asked whether the census left CT out on purpose, and for a CT census with each set's
segmentations. It had not left CT out, but it counted CT volumes and nothing more: no record said
which regions a CT covers or which masks a set has. #213 wrote records for the 54 releases of the
anomaly harvest already on the grid: the 39 IDC collections its pooled route fetched, and 15
releases from Zenodo, Hugging Face, NBIA and IDC. The issue had counted 55 releases. The 55th, a
list of 70 links into TotalSegmentator's CTs, gets no record, since TotalSegmentator's own record
counts those CTs; nor does the pooled route, whose CTs are the 39 collections'. #214 then gave
every CT record two fields and the census a CT page:

- `regions`: the body regions in the field of view, in seven words (head and neck, chest, abdomen,
  pelvis, spine, whole body, other). They come from the data platform's anatomy for the manifest
  records the registry's map ties the record to, else from the record's own text.
- `segmentations`: one entry per kind of mask. Each says whether the masks are the source's own or
  made on the grid, what they are, whether they name the vertebrae by level, who made them and how,
  the CT volumes they cover and the grid folder that holds them. The evidence is the data
  platform's manifest, IDC v24's own index (idc-index-data 24.2.2, its seg_index and
  rtstruct_index), the sample report's file counts and what another thread found on disk.

What the survey found, over the 163 records then written:

- 105 records hold CT, and 88 of them are on the grid: 24,959 CT volumes over the 70 that give a
  count, 25,991 subjects over 80 and 3.8 TB over 78. The whole census counts 101 sets on the grid.
- The source's own vertebra masks by level, on the grid: 4,208 CT volumes in 6 sets. They are
  TotalSegmentator 1,935, CTSpine1K 1,005, CTSpinoPelvic1K 802, VerSe 374, RSNA 2022's cervical
  spine 87 (inside its zip, not unpacked) and Ljubljana 5.
- Four more sets ship such masks in IDC, and the grid holds none of them: NLST, the NLST pilot,
  Spine-Mets-CT-SEG and Spinal-Multiple-Myeloma-SEG. IDC's fetch took the CT series alone, so no
  IDC mask is on the grid: Spine-Mets-CT-SEG's copy holds 35,527 DICOM files, IDC v24's count for
  its 55 CT series. A fetch of the SEG and RTSTRUCT series would bring them in, and it is a grid
  job.
- Masks made on the grid: 64 sets. The anomaly harvest made them for 61 (TotalSegmentator and
  SPINEPS with VERIDAH, the level called from the two together) and the owner's own runs for 7.
  Both are automatic and no radiologist has read them. The 20 of the 62 with a grid folder that
  give a count cover 15,753 CT volumes; the pooled IDC harvest counts 3,499 usable CTs over its 39
  collections together, not per collection.
- Still open: the source ships no masks for 35 sets, and for 33 nothing recorded says what it
  ships. 21 of those 33 are on the grid. For 7 of them the fetch took the images alone, as with
  AbdomenAtlas 3.0 Mini's image_only folder and PANORAMA's four image batches; for 9 any masks
  are inside archives fetched whole and not yet opened; 5 are to confirm on the source's page.

What it taught, for any census of masks:

1. Keep the source's masks apart from masks made on the grid. Automatic masks by level are not
   level truth, and a figure that summed both would read 15,753 automatic masks as labelled data.
2. "None", "not recorded" and no field at all are three answers: the source ships none, nobody here
   knows, nobody has looked. The check refuses an entry that says none and names a folder.
3. A fetch that takes the images alone leaves the release's masks behind, and an archive fetched
   whole hides them until it is opened; nothing on the grid shows either. The census can only list
   such a set as a gap until someone confirms the source's page, opens the archive or fetches the
   masks.
4. Count a set's CTs once however many of its entries cover them; the census takes the largest
   count among them.
5. A sum over records counts a CT twice where two records hold it (AbdomenAtlas 3.0 Mini holds
   PANORAMA's 274 cases), so the page says so in place of folding them.

## The roadmap

The tracks and their tasks, all in spine-datasets:

- **#174, planning the annotation of the paired data.** #170 (the digital-twin cadaver), the pair
  leads #182 to #201 (one per dataset, each naming its record line, all labelled `paired` but MINTOS,
  whose CT is unconfirmed), and #207 (whether LUMOS's film n and CT n are one patient). The plan
  itself is this repository's docs/research/paired-ct-xray-annotation-plan.md.
- **#175, one knowledge synthesis generated from the records.** #178 (the census, done), #181
  (records for the harvest's releases, done by #213, with the CT page of #214 after it), #203
  (counts and licence lines the census cannot read yet) and #208 (every real-data row of the
  Fluoroscopy Data Atlas mapped to a record, a task or a reason; a first automatic match left about
  50 real rows with neither).
- **#176, the data workflow from request to a verified set.** #202 (19 records whose folders the
  listing shows, to say `held`; #209 moved 18 and left zenodo_vsd_fullbody for its running fetch)
  and #204 (a landing pass that writes each held set's bytes, file count and SHA256SUMS into its
  record). The held review in #209 found three sets under non-commercial licences that had no
  obstacle before, aws_stoic2021, idc_midrc_ricord_1b and idc_nsclc_radiomics, so each now waits on
  the owner's licence decision.
- **#177, datasets that grow without a restart.** #205 (an append-only case index and annotation
  layout beside raw/, with splits fixed per person) and #206 (the promoter appending to the index).

What waits on the owner:

- every grid job (a fetch, a listing, the landing pass), which needs his word and its count;
- every non-commercial or no-derivatives licence;
- every registration and agreement (MIDRC among them);
- the copy in his grid home;
- the promoter's code, which only his pull requests change.

Letters go out on his word, or from a collaborator's own mailbox under spine-datasets' rules.
