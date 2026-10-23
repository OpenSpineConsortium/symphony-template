# The spine data census, and the roadmap of the dataset work that remains

Source: the thread "Dataset census and roadmap", 2026-10-23, on OpenSpineConsortium/spine-datasets.
The work is spine-datasets #179 (issue #178, merged as 6856c4b), the tracks #174 to #177 and the
tasks #181 to #208; another thread's #209 (merged as 90c4c92) then moved 18 more records to `held`.
The artifact "Spine Data Census" (https://claude.ai/artifact/PJrXJCBK8S4m8igHf5Q3MU) is a copy of
the page the census wrote from the branch `census` at c8ee645.

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
  - The anomaly harvest's 55 CT releases, which get their records by #181.

## The roadmap

The tracks and their tasks, all in spine-datasets:

- **#174, planning the annotation of the paired data.** #170 (the digital-twin cadaver), the pair
  leads #182 to #201 (one per dataset, each naming its record line, all labelled `paired` but MINTOS,
  whose CT is unconfirmed), and #207 (whether LUMOS's film n and CT n are one patient). The plan
  itself is this repository's docs/research/paired-ct-xray-annotation-plan.md.
- **#175, one knowledge synthesis generated from the records.** #178 (the census, done), #181
  (records for the harvest's releases), #203 (counts and licence lines the census cannot read yet)
  and #208 (every real-data row of the Fluoroscopy Data Atlas mapped to a record, a task or a
  reason; a first automatic match left about 50 real rows with neither).
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
