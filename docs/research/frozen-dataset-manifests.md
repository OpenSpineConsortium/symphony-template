# Frozen dataset manifests

Source: the thread "Frozen dataset manifests", 2026-10-23, from the owner's question of that day:
if every dataset put on the grid came with a metadata file that froze its directory, hashed it so
the copy is shown identical, and held its files, its structure and its size, could those numbers
be read nearly at once and in detail. Built in OpenSpineConsortium/spine-datasets (tools/freeze.py,
frozen/, grid/freeze.sh; spine-datasets #215).

## The answer

Yes, once each set is read one time. Hashing every byte is the only way to show a copy identical,
and it costs one full read of the data; after that the totals, the outline and any folder's size
come from a small file in milliseconds, and a quick check that nothing moved needs only a
directory walk.

Size and file counts alone were already instant: CephFS keeps a folder's recursive bytes and file
count as extended attributes (ceph.dir.rbytes, ceph.dir.rfiles), read with getfattr and no scan.
SchwingNet #161 reads the quota the same way. What the freeze adds is what CephFS does not keep:
the identity of every file and of the whole tree, an outline that GitHub can show to anyone with
no grid access, and a record in the census.

## The design

- One freeze per set, written beside the data: FROZEN.files.tsv.gz holds one line per file
  (sha256, bytes, path), sorted by the path's bytes, and FROZEN.json holds the totals, the tree's
  sha256 (the sha256 of that list uncompressed, so one hash covers every name and every byte),
  each folder to two levels with its own totals and hash, the outline by depth, the counts by
  extension and the largest files. A folder's hash takes paths from that folder, so a subtree
  copied or moved keeps its hash. Links are listed, never followed.
- A public copy, frozen/<id>.json, in spine-datasets. That repository is public, and a set held
  under an agreement may name its subjects in its paths, so the copy keeps no file name, nothing
  below the top, the top folders only where a set has at most twelve (a set with more most likely
  keeps one per subject), and only known extensions, the rest counted as (other), since "Jane.Doe"
  would show ".doe"; the check refuses a copy that names more. The review found both of the last
  two leaks in the first draft.
- The record's measured block takes bytes, files, tree_sha256 and the date from the freeze, and
  the check fails when the copy and the record disagree. The census counts the sets frozen and
  lists each set on the grid that is not.
- The promoter freezes each set it installs from the sha256 it has just checked, so no byte is
  read twice, and its record update brings frozen/<id>.json with it. The review lets the
  promoter's branch change that file beside the record, and the freeze's code joins the code that
  only an owner's own pull request may change, since it runs as the owner.
- It runs on the grid's python3 as old as 3.6, standard library only. A long freeze survives its
  wall time: each hashed file goes into a checkpoint, and a requeued job reuses it while the
  file's size and modification time are unchanged. Hashing runs N files at once, since a network
  filesystem gives several readers more than one.
- Where it fits the rest: a fetch's exact size before it starts is still the manifest's
  bytes_total (the all-or-nothing rule against the 22 TB quota); a landed set's size is its
  freeze's bytes. A training run's PROVENANCE.json (SchwingNet #157) could name each source's
  tree_sha256, so a run says which exact bytes it read; that is a follow-up in SchwingNet.

## What it would take for the sets already on the grid

`tools/freeze.py plan` lists 101 sets on the grid with no freeze on 2026-10-23: 50 under the
owner's data root, 39 IDC collections, 7 in the shared tree and 5 elsewhere, with 3 whose
grid_path names more than one folder, frozen by hand. The records state 3.9 TB for 81 of them;
the coordinator's figure for the whole is about 10 TB, and getfattr gives the exact number.

The cost is reading the bytes, not hashing them. Python's sha256 ran at 1.4 GB/s on one core of
the cloud container, with the CPU's SHA instructions; an older grid node without them is nearer
0.3 to 0.5 GB/s a core, so 8 workers hash faster than one CephFS client reads. Taking a client's
read at 0.25 to 1 GB/s for large files, and about 3 ms of metadata per small file for the IDC and
other DICOM sets (on the order of 7 million slices across about 25,000 CT volumes, spread over
the workers):

| Plan | Wall time for 10 TB | CPU time |
|---|---|---|
| 1 job, 8 CPUs | about 3 to 11 hours, inside two 12-hour wall times at worst | up to about 90 core-hours |
| 4 jobs, 8 CPUs each, shares of equal stated size (1.3 to 1.4 TB stated each) | about 1 to 4 hours, if the pool gives four clients their rate | about the same core-hours, spread |

These are estimates from stated rates, not measurements on the grid. The recommended order is a
pilot of 1 job on one set of about 100 GB (amos22, 102.6 GB stated), which measures the real read
rate in 5 to 15 minutes, then the remaining sets as 4 jobs. No job was sent; each needs the
owner's word and the count, by the project's rule, and grid/freeze.sh has no gate word yet.

## Handoff, 2026-10-23 18:15 UTC (the owner at 92 percent of the weekly limit)

Where the work stopped, so the next session picks it up exactly here. Nothing of it lives only in a cloud session: every change is merged or pushed, and the frozen data sits on the grid.

Done and merged: tools/freeze.py with census and promoter wiring (spine-datasets #215, #216), the report route back (spine-datasets #219: `freeze.sh report` and `freeze.py bundle` and `apply`), the gate words freeze status, pilot and start (hpcworker #37, symphony-template #413) and the grid-accounts word freeze-report (symphony-template #418). The owner approved a one-job pilot and then four jobs ("yes you have my word"); the pilot froze amos22 (102.6 GB, 3,067 files, job 40744799, under 16 minutes) and the four jobs 40745721 to 40745724 were queued at 13:31 UTC on the other 97 sets of grid/freeze-plan.tsv; at 14:31 UTC 26 of 98 were frozen. The copies are kept under the lab root's spine-datasets-freeze/frozen and measured on the grid.

Open: hpcworker #39 (the gate word `freeze report`), green but in conflict with hpcworker main again after #38's neighbour changes; merge main into its branch claude/project-thread-ajmjdi-freeze-report (keep both words in JOBS_RE and the refusal list), push, merge once green.

Next steps, in order, none of them a new grid job:
1. Merge hpcworker #39, then send grid-accounts.yml with action job, job update, so the gate's clone carries the word.
2. Send job freeze-status and read logs/job-freeze-status.json on symphony-template's branch grid: the four jobs done, how many of 98 frozen, any set that logged "not frozen".
3. Send job freeze-report; it sets spine-datasets' branch freeze-report to one parentless commit of frozen/<id>.json.
4. In a spine-datasets checkout: `git fetch origin freeze-report`, extract its frozen/ to a scratch folder, run `python3 tools/freeze.py apply <scratch>/frozen`, `bash scripts/check.sh`, and open the pull request (with its Adversarial review section) that adds frozen/<id>.json and each record's measured block; the census then shows frozen sizes, file counts and tree hashes.
5. Freeze by hand the three sets whose grid_path names several folders (aasce, deepfluoro, totalsegmentator), only on the owner's word with the count of jobs.
6. A set that failed in a job is retried only with the owner's word: `freeze-start` again queues only the unfrozen sets, as new jobs.
