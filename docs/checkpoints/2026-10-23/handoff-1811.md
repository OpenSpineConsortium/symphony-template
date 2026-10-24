# Handoff of 2026-10-23 at 18:11 UTC, for another account

Source: the thread "Dataset census and roadmap", written with tools/handoff.py because the owner,
at 92 percent of the weekly limit at 18:10 UTC, asked every thread to hand off. A session on the
next account reads this page first (the session-start hook names it), then the board. No secret,
token or e-mail is written here.

## Where this session stands

- Updated 2026-10-24 at 02:45 UTC by the same thread, which carried on after this page was
  written: the MTDDH fetch and the Harms Study Group letter are done, as the sections below now
  say. The branch claude/project-thread-tn9lgv stands at origin/main in both repositories and
  holds nothing of its own; no file is changed and not committed.
- The pull requests this thread opened, all merged: symphony-template #422 (the OpenDataLab
  search for CM Spine), #423 (the Chinese dataset hosts) and #425 (section 9 of the Chinese hosts
  note, and this page); spine-datasets #223 (the MTDDH record), #224 (the Bournemouth group's OSF
  deposit and MTDDH's no-login download, both records), #226 (the owner's reply to Uneri
  recorded), #228 (the MTDDH manifest, and Science Data Bank as a host the promoter knows), #230
  (the Harms Study Group request recorded as sent) and #231 (the promoter's own record of MTDDH on
  the grid).
- Nothing of this thread lives only in the cloud session. The research is in
  docs/research/spine-datasets-on-chinese-hosts.md (section 2 says what was searched and how,
  section 9 what the owner's pages and computer answered, with every endpoint used) and
  docs/research/cm-spine-dataset-provenance.md; the records are in spine-datasets. The raw
  answers of the two Remote Control runs are on the owner's computer, in the Desktop folders
  opendatalab-search-2 and dataset-links, outside any repository; the notes carry what matters.

## Open work

- MTDDH is on the grid: done. The owner gave the word for one set of 4.05 GB at 19:54 UTC on
  2026-10-23; spine-datasets #228 brought the manifest and the host entry; the owner's restart word
  reached the grid at 01:49 UTC on 2026-10-24 (logs/job-promoter-restart.json on the branch grid,
  promoter job 40754479); the promoter fetched the three files, 4,053,482,052 bytes, installed them
  at /rs/rs_grp_oschome/shared/datasets/scidb_mtddh/raw, froze the set (frozen/scidb_mtddh.json)
  and opened #231, merged at 02:38 UTC. The record datasets/scidb_mtddh.json says fetched with its
  grid path and measured block. Nothing is open.
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
  Daradia (daradia_vertebroplasty, requested; one follow-up if nothing by 2026-11-04), the Harms
  Study Group (hsg_ais_registry, requested: Uneri introduced the owner to Michelle Marks,
  Executive/Research Director of Setting Scoliosis Straight, on 2026-10-23, and the letter
  letters/hsg_ais_registry.md went to her at 20:24 UTC as the owner's reply-all with Uneri in copy,
  #230; her review is awaited, and the owner follows up in the same thread if nothing has come by
  2026-11-06; levelcheck_jhu stays refused), and Wasserthal (the three zenodo_ts_task records, held:
  the owner sends the drafted follow-up, which waits in the owner's Outlook Drafts folder, unsent,
  since a send needs the owner's word). Radiopaedia's licence application is the owner's own, and
  the site is never fetched by script.

## Durable facts for the next checkpoint

The checkpoint files (.claude/session.md and the marked block of CLAUDE.md) were left untouched,
since several threads hand off at once and each would edit the same lines; the next account
carries these into them:

- Decision (the owner, 2026-10-23): Dr Branney is not chased by e-mail; the OSF deposit's terms
  are asked when he answers.
- Decision (the owner, 2026-10-23, standing): every fetch waits for the owner's word and its
  count; MTDDH's word was given at 19:54 UTC on 2026-10-23 for one set of 4.05 GB, and the set is
  on the grid since 2026-10-24.
- Constraint: the cloud container cannot reach osf.io, api.osf.io, www.scidb.cn or
  download.scidb.cn (the proxy refuses the CONNECT), and both sites' pages are JavaScript shells
  to WebFetch; the owner's computer reads them through Remote Control, OSF by
  api.osf.io/v2/nodes/ID/files/osfstorage/ and Science Data Bank by the public file-list
  endpoints named in section 9 of the Chinese hosts note.
- Constraint: the promoter's DOWNLOAD_HOSTS knows figshare, Mendeley, Zenodo and, since #228,
  Science Data Bank (download.scidb.cn); a host that serves files from a name other than the
  record's link needs an entry there and the gate word promoter-restart after the merge, since the
  promoter takes a session's commit only through that word.
- Constraint: grid-accounts.yml's action input defaults to list, so a run with promoter-restart in
  the job field and the action left on list only lists the accounts (the owner's run of 01:35 UTC
  on 2026-10-24 did); the action must be set to job. A session may send the job word itself once
  the owner has given it (the owner's choice of 2026-10-21), as this thread did at 01:49 UTC.

## Waiting on the owner

1. Nothing for MTDDH, which is on the grid, nor for the Harms Study Group, whose answer is
   awaited.
2. Nothing to send to Bournemouth: the next step is Dr Branney's.
3. The Wasserthal follow-up: open Outlook's Drafts folder, read it and press Send, or say the word
   and a session sends it. The Uneri reply went on 2026-10-23 at 16:56 UTC.

## Resume

1. Open a session on this repository with the next account (a Project of its own on claude.ai, or a grid worker moved to it).
2. Read this page and the research notes it names; then fetch and read the board.
3. Take the open work above in its order; a claim still held by this session's worker name is carried on in its own branch.
