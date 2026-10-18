The drive organizer sorts a whole drive into proposed projects: catalog, organize (one Claude run), accept, each started by hand in a private repository.

.github/workflows/drive-organize.yml and tools/drive_organize.py read every folder and file
that drive.json's "organize" items hold (the drive's root id "root" for all of it) into
catalog.json, TREE.md and digests.jsonl on the branch drive-catalog, with no Claude. The
organize step has Claude return projects as JSON, opened as epics labelled epic, proposed,
drive and project:<slug>, with tasks labelled proposed, never todo, under "Project: #N" in
place of "Epic: #N", so no worker spends and no integration starts until the owner runs
accept, which labels the epic tracking and adds its folders to drive.json by a pull request;
drive-sync.yml's run then calls `drive_organize.py ready`, which gives the tasks todo and
their workers' labels once the folders are in the repository. Claude's text is cleaned of
comment marks, since the organizer reads its own hidden lines. A slug proposed before is never
proposed again, so closing a proposal says no. tools/file_digest.py reads Word, Excel, CSV,
PowerPoint, notebooks, code, PDFs and images as text for Claude and for workers. The design
is docs/research/drive-organizer.md.
