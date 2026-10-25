# Handoff of 2026-10-23 at 18:11 UTC, for another account

Source: the thread "Dataset census and roadmap", written with tools/handoff.py because the owner,
at 92 percent of the weekly limit at 18:10 UTC, asked every thread to hand off. A session on the
next account reads this page first (the session-start hook names it), then the board. No secret,
token or e-mail is written here.

## Where this session stands

- Updated 2026-10-24 at 06:15 UTC by the same thread, when the owner asked every thread to stop,
  checkpoint and push. Since the update of 02:45 UTC the thread sent three letters on the owner's
  word and recorded them, and found ReXGradient-160K already on the grid. The branch
  claude/project-thread-tn9lgv stands at origin/main in spine-datasets (5314bfd) and holds
  nothing of its own; in symphony-template it holds only this page's update, in a draft pull
  request. No file is changed and not committed in either checkout.
- The pull requests this thread opened, all merged but the last: symphony-template #422 (the
  OpenDataLab search for CM Spine), #423 (the Chinese dataset hosts), #425 (section 9 of the
  Chinese hosts note, and this page) and #437 (this page's update of 02:45 UTC); spine-datasets
  #223 (the MTDDH record), #224 (the Bournemouth group's OSF deposit and MTDDH's no-login
  download), #226 (the owner's reply to Uneri recorded), #228 (the MTDDH manifest, and Science
  Data Bank as a host the promoter knows), #230 (the Harms Study Group request recorded as sent),
  #231 (the promoter's own record of MTDDH on the grid), #232 (the Branney and Wasserthal sends of
  2026-10-24 recorded) and #233 (ReXGradient-160K held, with the released claim's history and the
  note to Dr Zhang); and the draft pull request that carries this update, left unmerged because
  the owner asked the thread to stop once it was pushed.
- Nothing of this thread lives only in the cloud session. The research is in
  docs/research/spine-datasets-on-chinese-hosts.md and docs/research/cm-spine-dataset-provenance.md;
  the records and the letters are in spine-datasets, and each record's next field is the source
  of truth for what waits (the list made from them at 02:55 UTC, dataset-census/waiting-on-2026-10-24.md
  in the Project's files, predates the three sends below). The raw answers of the two Remote
  Control runs are on the owner's computer, in the Desktop folders opendatalab-search-2 and
  dataset-links, outside any repository; the notes carry what matters.

- Resumed 2026-10-24 at 07:52 UTC on the owner's word, by a new session on the same thread
  title: it checked that spine-datasets #232 and #233 are on main (5314bfd), closed the released
  draft #157, and merged this page. No answer from Branney, Wasserthal or Dr Zhang is recorded
  yet; a session cannot read the owner's mailbox, so each answer reaches the records when the
  owner forwards it or says so.

## Open work

- ReXGradient-160K (spine-datasets, datasets/rexgradient_160k.json, status held; issue #11 still
  open and labelled todo). The owner's chain fetched the whole set, 156 GB, on 2026-10-23 (job
  40743347) into /rs/rs_grp_oschome/go2432/data/hf_rexgradient_160k. Clause A.5 of the agreement
  allows only the part a project needs, so on 2026-10-24 at 03:24 UTC the owner sent the
  corresponding author, Dr Xiaoman Zhang, the note drafted on 2026-10-22, asking leave for all ten
  image parts and promising to keep only the studies the work uses; its text is the last section
  of letters/rexgradient_160k.md.
  1. When Dr Zhang answers (the mail thread in the owner's mailbox), record the answer in the
     record's history.
  2. Read the view-position metadata and keep only the lateral studies, deleting the rest, as the
     note promised; that is a grid job and waits for the owner's word and count.
  3. The landing pass checks the files kept, and a freeze follows on the owner's word.
  4. Tidy: the released claim's draft #157 was closed on 2026-10-24 at 07:58 UTC, its history
     being in the record and its branch renamed to released/11-27c16cf. SchwingNet's own
     data/sources/rexgradient_160k.json still says not fetched, which is the SchwingNet thread's
     to correct.
- The Bournemouth lumbar cine (datasets/bournemouth_lumbar_qf.json, requested; the cervical set
  datasets/bournemouth_cervical_qf.json rides in the same thread). The group's public OSF deposit
  z2jby holds preproc_224_wb_flex.zip (1,492,963,815 bytes, sha256 in the record,
  https://osf.io/download/xjt4f/) with no licence stated. Dr Branney answered the first letter on
  2026-10-22 and is checking with his research department. On the owner's word of 2026-10-24
  03:03 UTC, the owner's reply-all of 03:08 UTC in his thread, with the original copy list, asked
  whether the deposit may be used meanwhile and on what terms, and whether it is drawn from the
  whole L2-S1 database or a subset (#232).
  1. When Branney answers, record it in both Bournemouth records; the owner signs any
     data-sharing agreement.
  2. A yes on the deposit is a granted step; then the manifest with the one file (its bytes and
     sha256 checked against OSF's file API), status fetching, and the promoter fetches. Before
     that, check that tools/promote.py follows the 302 from osf.io/download to files.de-1.osf.io.
- The three TotalSegmentator task sets (zenodo_ts_task_hip_implant, zenodo_ts_task_liver_lesions
  and zenodo_ts_task_pleural_effusion, held). The owner's one-line follow-up to Wasserthal went on
  2026-10-24 at 03:05 UTC, asking whether the task sets' subjects are among the v2 and v3
  subjects with the same identifiers or new people (#232). When he answers, record it on the
  three records and letters/totalsegmentator_tasks.md; the landing pass (#204) checks the files.
- The letters still out, each a record in spine-datasets with its dates: James Coyle
  (pittsburgh_swallow, requested; the owner sends one short follow-up if nothing by 2026-10-28),
  Daradia (daradia_vertebroplasty, requested; one follow-up if nothing by 2026-11-04) and the
  Harms Study Group (hsg_ais_registry, requested: the letter went to Michelle Marks of Setting
  Scoliosis Straight on 2026-10-23 at 20:24 UTC with Uneri in copy, #230; the owner follows up in
  the same thread if nothing by 2026-11-06; levelcheck_jhu stays refused). Radiopaedia's licence
  application is the owner's own, and the site is never fetched by script.
- MTDDH is on the grid, frozen by the promoter (spine-datasets #231); nothing of it is open.

## Durable facts for the next checkpoint

The checkpoint files (.claude/session.md and the marked block of CLAUDE.md) were again left
untouched, since every thread hands off at once and each would edit the same lines; the next
account carries these into them:

- Decision (the owner, 2026-10-23): Dr Branney is not chased by e-mail; on 2026-10-24 the owner
  made one exception, the question on the OSF deposit sent at 03:08 UTC, and nothing more goes
  until he answers.
- Decision (the owner, 2026-10-23, standing): every fetch and grid job waits for the owner's word
  and its count.
- Constraint: Microsoft 365's send refuses a draft with attachments, and a reply or reply-all
  draft made on a received message that carries inline signature images inherits them; reply to
  the owner's own sent message in the same conversation instead, which has none.
- Constraint: a released claim's draft pull request can stay open after the board renames its
  branch (spine-datasets #157), and the board's overlap comments keep naming it as work to land
  first; check with git ls-remote that claude/<n> still exists, carry what is still true from
  released/<n>-<sha> into your own pull request, and land in the protocol's order.
- Constraint: the cloud container cannot reach osf.io, api.osf.io, www.scidb.cn or
  download.scidb.cn, and both sites' pages are JavaScript shells to WebFetch; the owner's
  computer reads them through Remote Control (section 9 of the Chinese hosts note).
- Constraint: the promoter's DOWNLOAD_HOSTS knows figshare, Mendeley, Zenodo and Science Data
  Bank (download.scidb.cn); a host that serves files from a name other than the record's link
  needs an entry there and the gate word promoter-restart after the merge.
- Constraint: grid-accounts.yml's action input defaults to list, so a job word needs the action
  set to job; a session may send the job word itself once the owner has given it (the owner's
  choice of 2026-10-21).

## Waiting on the owner

1. Nothing to send now: the letters to Branney, Wasserthal and Dr Zhang went on 2026-10-24
   between 03:05 and 03:24 UTC, and each answer is awaited.
2. The dated follow-ups, only if nothing has come: Coyle on 2026-10-28, Daradia on 2026-11-04,
   Marks on 2026-11-06.
3. This page's draft pull request in symphony-template: merge it once its check is green, or let
   the next session do so, so that the session-start hook finds the update on main.

## Resume

1. Open a session on this repository with the next account (a Project of its own on claude.ai, or a grid worker moved to it).
2. Read this page and the research notes it names; then fetch and read the board.
3. Take the open work above in its order; a claim still held by this session's worker name is carried on in its own branch.
