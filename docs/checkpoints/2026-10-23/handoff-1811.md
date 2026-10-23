# Handoff of 2026-10-23 at 18:11 UTC, for another account

Source: the thread "Dataset census and roadmap", written with tools/handoff.py because the owner,
at 92 percent of the weekly limit at 18:10 UTC, asked every thread to hand off. A session on the
next account reads this page first (the session-start hook names it), then the board. No secret,
token or e-mail is written here.

## Where this session stands

- Branch claude/project-thread-tn9lgv at 7e3f261 plus the commit that adds this page; nothing is
  on this branch that is not on origin.
- No file changed and not committed, here or in spine-datasets, whose branch of the same name was
  recreated from main at 2d18c10 after #224 merged and holds nothing of its own.
- The pull requests this thread opened today: symphony-template #422 (the OpenDataLab search for
  CM Spine) and #423 (the Chinese dataset hosts), merged; spine-datasets #223 (the MTDDH record)
  and #224 (the Bournemouth group's OSF deposit and MTDDH's no-login download, both records),
  merged; symphony-template #425 (section 9 of the Chinese hosts note, and this page), ready and
  merging once its check is green on the owner's standing permission.
- Nothing of this thread lives only in the cloud session. The research is in
  docs/research/spine-datasets-on-chinese-hosts.md (section 2 says what was searched and how,
  section 9 what the owner's pages and computer answered, with every endpoint used) and
  docs/research/cm-spine-dataset-provenance.md; the records are in spine-datasets. The raw
  answers of the two Remote Control runs are on the owner's computer, in the Desktop folders
  opendatalab-search-2 and dataset-links, outside any repository; the notes carry what matters.

## Open work

- MTDDH onto the grid (spine-datasets, datasets/scidb_mtddh.json, status todo, route download).
  The three Science Data Bank files download with no account: JPG_DICOM.rar, 1,165,024,411 bytes,
  md5 2029b761e5077e61280f4a5fb9308a32; MTDDH.zip, 1,872,032,279 bytes, md5
  1508164e97c35b7063a163726bf4ef05; code.zip, 1,016,425,362 bytes, md5
  a91952a0f1b6fc0989e8a1d53cd0432e; 4,053,482,052 bytes in all, each at
  https://download.scidb.cn/download?fileId=ID&path=/V1/NAME&fileName=NAME, the whole links in
  the record's how_to_get; licence CC BY 4.0. Nothing is fetched yet, since no fetch runs without
  the owner's word and count.
  1. On the owner's word: write manifests/scidb_mtddh.json on the shape manifests/README.md gives
     (source the record's link, licence the record's line word for word, the three files as
     raw/NAME with url, bytes, md5 and verified_against naming Science Data Bank's file-list API
     of 2026-10-23), set the record's status to fetching with the history entry "manifest ready;
     the promoter fetches after merge" and next "the promoter installs it after merge", and run
     python3 tools/census.py check, python3 tools/pipeline.py check and
     python3 tools/dataset_review.py diff --base origin/main.
  2. In the same pull request add "scidb.cn": ("download.scidb.cn",) to DOWNLOAD_HOSTS in
     tools/promote.py, since same_site otherwise refuses download.scidb.cn beside the record's
     www.scidb.cn link, and a line in tests/test_promote.py's class Hosts asserting
     same_site("download.scidb.cn", "scidb.cn"); tools/dataset_review.py marks a change to
     promote.py in a pull request opened as the owner as a NOTE, not a failure. Run
     bash scripts/check.sh and merge once green.
  3. The promoter on the grid does not take that code by itself, since the pull request's commits
     carry a session's Claude-Session trailer: the owner sends the gate word promoter-restart
     (below), which installs main's copy; the next pass fetches the manifest within about ten
     minutes, installs it at /rs/rs_grp_oschome/shared/datasets/scidb_mtddh/raw and opens the
     record's fetched pull request from promote/scidb_mtddh; merge it.
  4. If Science Data Bank refuses the grid, the fallback is the authors' older figshare copy
     (MTDDH.rar, 1,871,869,324 bytes, md5 697c3c29b6a1faf69a2032e22486400e, CC BY 4.0, served
     from ndownloader.figshare.com, a host the promoter already knows), a smaller earlier version
     named in the same how_to_get.
- The Bournemouth lumbar cine (spine-datasets, datasets/bournemouth_lumbar_qf.json, status
  requested). The group's public OSF deposit z2jby holds preproc_224_wb_flex.zip (1,492,963,815
  bytes, sha256 in the record, https://osf.io/download/xjt4f/) with no licence stated, so the
  promoter's rule needs Bournemouth's grant first. Dr Branney answered the letter on 2026-10-22
  and is checking with his research department; the owner chose on 2026-10-23 not to chase him,
  and the reply draft to him was deleted unsent.
  1. When Branney answers (the mail thread with him in the owner's mailbox), ask in that reply
     whether the OSF deposit may be used under the arrangement and whether it is the whole L2-S1
     set or only the weight-bearing flexion part; the owner signs any data-sharing agreement.
  2. A yes is recorded as a granted step in the record's history; then the manifest with the one
     image file (the osf.io/download link, its bytes and sha256, verified against OSF's file API),
     status fetching, and the promoter fetches. Before that, check that tools/promote.py follows
     the 302 from osf.io/download to files.de-1.osf.io, which that link form needs.
- The letters and replies still out, each a record in spine-datasets with its dates: James Coyle
  (pittsburgh_swallow, requested; the owner sends one short follow-up if nothing by 2026-10-28),
  Daradia (daradia_vertebroplasty, requested; one follow-up if nothing by 2026-11-04), Uneri's
  introduction to the Harms Study Group (hsg_ais_registry todo and levelcheck_jhu refused: the
  owner sends the drafted reply accepting it), and Wasserthal (the three zenodo_ts_task records,
  held: the owner sends the drafted follow-up). The reply drafts to Uneri and Wasserthal wait in
  the owner's Outlook Drafts folder, unsent, since a send needs the owner's word. Radiopaedia's
  licence application is the owner's own, and the site is never fetched by script.
- symphony-template #425: nothing left but the merge; if it is still open, merge it once green.

## Durable facts for the next checkpoint

The checkpoint files (.claude/session.md and the marked block of CLAUDE.md) were left untouched,
since several threads hand off at once and each would edit the same lines; the next account
carries these into them:

- Decision (the owner, 2026-10-23): Dr Branney is not chased by e-mail; the OSF deposit's terms
  are asked when he answers.
- Decision (the owner, 2026-10-23, standing): every fetch waits for the owner's word and its
  count; MTDDH's word has not been given.
- Constraint: the cloud container cannot reach osf.io, api.osf.io, www.scidb.cn or
  download.scidb.cn (the proxy refuses the CONNECT), and both sites' pages are JavaScript shells
  to WebFetch; the owner's computer reads them through Remote Control, OSF by
  api.osf.io/v2/nodes/ID/files/osfstorage/ and Science Data Bank by the public file-list
  endpoints named in section 9 of the Chinese hosts note.
- Constraint: the promoter's DOWNLOAD_HOSTS knows figshare, Mendeley and Zenodo only; a host that
  serves files from a name other than the record's link needs an entry there and the gate word
  promoter-restart after the merge.

## Waiting on the owner

1. The MTDDH fetch: say the word and the count (one set, 4.05 GB) in the thread "Dataset census
   and roadmap" or to the next account, which then does steps 1 and 2 above.
2. After that pull request merges: open
   https://github.com/OpenSpineConsortium/symphony-template/actions/workflows/grid-accounts.yml,
   press "Run workflow", choose the action "job", type promoter-restart in the job field and press
   "Run workflow"; the answer lands on the branch grid as logs/job-promoter-restart.json.
3. Nothing to send to Bournemouth: the next step is Dr Branney's.
4. The Uneri and Wasserthal replies: open Outlook's Drafts folder, read each and press Send, or
   say the word and a session sends them.

## Resume

1. Open a session on this repository with the next account (a Project of its own on claude.ai, or a grid worker moved to it).
2. Read this page and the research notes it names; then fetch and read the board.
3. Take the open work above in its order; a claim still held by this session's worker name is carried on in its own branch.
