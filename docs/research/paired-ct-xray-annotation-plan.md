# Paired CT and X-ray data: what is held, what is coming, and the annotation plan

Source: the thread "Paired CT and X-ray datasets", 2026-10-23, from the owner's ask of 02:03 UTC ("start planning the annotation of paired ct-xray data so make sure the artefact which has all the data census is accurate and breaks that out") and of 02:36 UTC (threads only for knowledge, finishing and the paired CT and X-ray datasets). Read from spine-datasets' records under datasets/ at b44ba32, SchwingNet's registry under data/sources/ at caa5641, SchwingNet #127 with its three comments, and spine-datasets #170 and #174 on 2026-10-23. It answers the five questions of spine-datasets #174, the data side of SchwingNet #127; the methods stay in SchwingNet, which is confidential, so this note names datasets, counts, folders and people, never a method beyond what #174 already says. The census itself is the census thread's (spine-datasets #178 and its draft pull request #179), which this note feeds and does not edit. Nothing here was fetched or run on the grid.

## 1. Every pair, by tier

The tiers are #179's: A on the grid, B open and not fetched, C behind a request, D refused or embargoed, E a real pair of something other than the spine. "Frames" are real X-ray images of a subject whose CT is in the same set.

| Tier | Set | Region | Subjects with a CT | Real frames | Pose | Masks shipped | Licence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A | C-ArmLSpine | lumbar | 149 CBCT | 299 spot frames; 2 rotational sweeps of 301 frames | the project's own registrations, quality not measured | level names on 814 of 910 bodies, no body masks | CC BY 4.0 |
| A | COBRA2026 (Elekta 467 + Varian 225) | lumbosacral, pelvis | 692 planning CTs | 375,618 kV projections | stored geometry | none for vertebrae | CC BY-NC 4.0 |
| A | DeepFluoro | pelvis, low lumbar | 6 specimens: 6 CTs with the H5 set, 19 CTs in the vendor deposit | 366 H5 frames; 2,659 vendor frames | released for the H5 frames | 7 classes, the vertebrae as one | CC BY-NC-SA 4.0 |
| A | Ljubljana 2D/3D gold standard | L1 to L5 | 1 cadaver | 18 | stored | none | ND, read-only |
| B | Digital-twin cadaver (spine-datasets #170) | mid-femur to T2 | 1 cadaver, 4 CTs | 80 (46 viewpoints) | navigation, to confirm on unzip | to confirm on unzip | not stated |
| B | LUMOS (spine-datasets #27) | lumbar, diagnostic films | 280 of 803 patients | the films of those 280, out of 1,620 | none: registration needed | to confirm | CC BY-NC 4.0 per SchwingNet; the record still says to confirm |
| C | LevelCheck (Johns Hopkins, #60) | cervical to lumbar (De Silva 2016); thoracolumbar (Ketcha 2017) | 178 patients, plus 24 | 398 radiographs, plus 61 | registration to the labelled CT | level per vertebra | a data use agreement |
| C | Huashan, Fudan (#61) | L1 to L5 | 140 patients | AP and lateral films of each | none stated | none stated | a data use agreement |
| C | NIT Warangal and NIMS | L1 to L5 | 9 patients | at most 49 unique C-arm frames | none; level-named centroids from the CT | centroids public, CT by request | not recorded |
| D | Balgrist ex-vivo lumbar | lumbar | - | - | - | - | refused 2026-10-21 (proprietary) |
| D | COBRA held-back cases | pelvis | 175 | - | - | - | embargoed to 2032-03-01 |
| E | Geneva hip phantom | pelvis | 1 phantom CT | 116 | gold rigid transforms | boxes | not recorded; the unseen-device test, never tuned on |
| E | IPCAI 2025 femur set (Zenodo 15753063) | distal femur | 5 | 50 | stored | contour masks, bone models | research-only |
| E | Pig lower limb (IEEE DataPort) | pig limb | 1 CT, 2 CBCT | 7 per condition | matrices | none | open access |
| E | Veriserum | knee implants | implant models | about 110,000 | 200 manually registered | implant poses | to confirm |

Two corrections the census needs, both already settled in SchwingNet's registry and still stale in spine-datasets' records: ipcai2025_xray_ct is the distal femur, not pelvis or spine, and is held (fetched on 2026-10-21, still zipped); veterinary_pig_levelcheck is a pig lower limb from Goswami 2020, not the LevelCheck pig study, and names no level. Both are tier E. And COBRA's two counts agree: 692 is Elekta's 467 and Varian's 225, which the registry keeps as two records.

Not in a tier because no reader is needed: the synthetic pairs, PENGWIN task 2 (50,000 renders of 100 pelvic CTs at real C-arm poses, CC BY 4.0, todo) and FluoroSeg (spine-datasets #171, gated), whose labels are exact by construction. The held CTs that make renders (DRRs) with exact labels are VerSe (374 series), CTSpinoPelvic1K (802), TotalSegmentator (1,228 and 1,935), CTSpine1K (1,005) and RSNA 2022 cervical (2,019, the C1, C2 and C7 anchors); SchwingNet already holds 12,929 rare-anatomy renders from them.

What is missing everywhere: no cervical pair, and one thoracic pair (the digital-twin cadaver, one specimen, so a test only). LevelCheck is the one candidate that would add living cervical, thoracic and lumbar pairs at scale; it waits on the Johns Hopkins answer.

## 2. Which sets, in what order

The order runs from what is in hand with a pose to what needs a fetch or a registration first, and each step gives a number the next one needs.

1. C-ArmLSpine, all 149. Everything is in one case folder and on the grid; the first five cases give the owner's minutes per case, which sizes every later step.
2. DeepFluoro, the 6 H5 CTs. The work is splitting one vertebrae class into named bodies on six volumes, not drawing, and it checks the split against the shipped class.
3. Ljubljana, one CT, five bodies. Masks kept in the owner's own tree beside the read-only set, never in the shared one, under its ND licence.
4. The digital-twin cadaver, once fetched (#170) and unzipped: four CTs of one specimen. A test set for the thoracic levels, never trained on.
5. COBRA, starting with the 145 Elekta cases already banked, then the rest by the per-case time from step 1. 692 CTs is the bulk of the reading, so its count is the owner's to set.
6. LUMOS, after its fetch (the owner's word and count) and after its pair key is shown (section 3).
7. The C tier, each as it is granted: LevelCheck first (living patients, thoracolumbar, the largest), then Huashan, then NIT Warangal.

## 3. The pair key of each set

| Set | Key | How sure |
| --- | --- | --- |
| C-ArmLSpine | the case folder: its CBCT and its spot frames | certain; one device, one session |
| COBRA | the case id: planning CT and projections | certain; the CT is registered to the reconstruction |
| DeepFluoro | specimen id; for the H5 frames, the frame's own CT | certain for H5; the vendor deposit's frame-to-CT map is to read |
| Ljubljana | one cadaver | certain |
| Digital twin | one cadaver; which of the 4 CTs covers each frame | to read on unzip |
| LUMOS | CT id and film id | not shown: that CT n and film n are one patient is a hypothesis until the record's metadata or a check of patient age and sex across the pair says so |
| LevelCheck, Huashan, NIT | patient id in the agreement's export | as the holder states it |

Each set gets one pairs file, `pairs.csv`, with a row per frame: the pair key, the CT's path relative to the set's raw/, the frame's path, where the pose comes from (stored, released, project registration, none) and how sure the pairing is (certain, stated, inferred). It is the census's `pair_key` made concrete, and the list every later step reads, so a set grows by adding rows.

## 4. Where the annotation lives, so a set can grow without a restart

Every set lands read-only at /rs/rs_grp_oschome/shared/datasets/<id>/raw, written only by the promoter (spine-datasets grid/README.md). Annotation sits beside it, never inside, so a fetch again or a new release never touches a reader's work:

```
/rs/rs_grp_oschome/shared/datasets/<id>/
  raw/                      the promoter's, read-only
  pairs/pairs.csv           section 3
  annotation/<case>/
    auto/                   the automatic first pass, one file per CT, with its tool and version
    corrected/              the owner's edit, one file per CT
    review.csv              one row per body: reader, date, verdict (verified or returned), note
  annotation/STATUS.csv     one row per case: which layers exist, gold or silver, split (test or train)
```

The editor's name and the date go in a sidecar or in review.csv, never in the mask file. Ljubljana's folder is the same shape under the owner's own tree, not the shared one.

Growing without a restart follows from three rules: every step reads pairs.csv and STATUS.csv and works only on cases missing its layer, so a new case is picked up by the next run with nothing redone; a case's split is written once, on its first row, and never changes; and a new set is a new folder of the same shape, which the census picks up from its record. The automatic pass is then one grid array job whose size is the number of cases without auto/, which the owner approves by that number.

## 5. The reader budget and who reads

- First reader, correcting: the owner, in ITK-SNAP, on the automatic pass. TotalSegmentator has no L6 class, so every sixth lumbar body is the owner's to draw and flag, and on a lumbarised spine its labels can shift by one level, so the correction concentrates on transitional spines.
- Second reader, verifying: Dr Tech, marking each body verified or returned in review.csv.
- A third reader for disagreements is not named yet: the owner's choice (Ashley, who already takes spine-datasets tasks, is one possibility, if the owner wants it).

The counts are the owner's. What the numbers say: 30 verified cases give about plus or minus 10 points on a per-body rate near 90 %; C-ArmLSpine's 149 at five or six lumbar bodies each is about 800 to 900 bodies. Everything in tiers A and B with a spine is about 1,130 CTs (149 + 692 + 6 + 1 + 4 + 280 = 1,132, counting DeepFluoro's H5 CTs only), so reading all of it is weeks of the owner's time at any plausible rate; the first five cases' timing turns that into a number before anyone asks.

## 6. Gold, silver, and the test rule

- Silver: the automatic pass, unread. Usable for training, never reported as truth.
- Corrected: edited by the owner, not yet verified. Still silver for reporting.
- Gold: verified by the second reader. The only layer a reported number rests on; the two-reader agreement is reported with it.
- Every mask and every label map made from one carries its layer, so a later result says which it rests on.
- A case marked test is read for the test alone and stays out of every training shard; the digital-twin cadaver and the Geneva phantom are test only from the start.

## 7. What waits on the owner

- The word and count for the automatic pass on the tier A spine CTs (149 + 692 + 6 + 1 = 848 CTs, or a smaller first batch such as C-ArmLSpine's 149).
- The non-commercial licence decision for LUMOS (CC BY-NC 4.0, as COBRA and DeepFluoro already are), then the word and count for its fetch (46.4 GB) and, after #170's fetch, the unzip check.
- How many C-ArmLSpine cases the owner and Dr Tech read before the talk on 2 November, and whether a third reader is named.
