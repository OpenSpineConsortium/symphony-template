# The drive organizer: a whole drive sorted into projects

Source: the thread "Organize a whole OneDrive" in the project symphony, 2026-10-18, answering
the owner's message that day in the Folders thread: "i want it to be really built out the
revision type functionality where you can share your entire drive and have claude
self-organize it into projects, create tasks, issues, ect and provide suggestions of directions
you could take it, it also should be general to read excels and do data analysis, business
tasks, marketing, accounting, computer science, writing, art, whatever the user has in their one
drive". The same message's panel asks (a file explorer like Windows', opening files in their own
apps, the dependency view in tabs, a tree to drill from an epic to a worker's log) belong to the
Control panel sign-in thread; this note says what that thread can read from here. The sync of
picked files is docs/research/drive-sync.md.

## What it does

The drive sync brings a few picked files into the repository. A whole drive is too big for
that: gigabytes of photographs and archives would bloat git, and most of a drive is not work
anyone will take up. So the organizer reads the whole drive without bringing it in, proposes
projects, and brings in only the folders of a project the owner accepts.

.github/workflows/drive-organize.yml runs three steps, each started by hand from the Actions tab
or the panel, with nothing on a schedule:

1. catalog, no Claude. tools/drive_organize.py walks every folder and file the items in
   drive.json's new "organize" key hold, or its "items" when that is absent. Sharing the drive's
   root is `{"organize": {"items": [{"id": "root", "name": "OneDrive"}]}}`, since both Graph and
   Google Drive take "root" as the id of a drive's top. It writes three files to the branch
   drive-catalog. catalog.json has every folder, with its files, bytes, kinds and newest date
   rolled up, and every file, with its kind, size, date and the drive's own link (OneDrive's
   webUrl, Google's webViewLink). TREE.md is the folders to four levels with the names of each
   one's newest files. digests.jsonl says what a sample of files hold. The walk stops at 20,000
   entries and sixteen levels and says so. A folder the drive will not list is named, and the
   rest is still walked.
2. organize, Claude on the repository's token. Claude reads the catalog with Read, Glob and Grep
   alone and returns JSON: projects, each with a slug, a title, one of fifteen domains (data
   analysis, accounting, finance, business, marketing, sales, software, research, writing,
   teaching, design and art, media, operations, personal, other), a summary, its folders and
   files, two to six directions it could take, a plan and its tasks. The tasks use the
   coordinator's own shape (team.plan_schema), so the clerk's code writes them. Then
   `drive_organize.py open` opens each new project as an epic labelled epic, proposed, drive and
   project:<slug>, with its tasks as sub-issues labelled proposed, with no todo and with
   "Project: #N" where the coordinator's tasks say "Epic: #N". It also opens or rewrites one
   index issue, "Your drive, organized": the projects, what fits none, and the directions across
   the drive.
3. accept, no Claude, given a project's number. The project is labelled tracking in place of
   proposed, and a pull request from drive/track-<number> adds its folders to drive.json's items,
   with auto-merge armed. Once the sync has brought those folders in, `drive_organize.py ready`,
   which the sync's own run calls every half hour, starts the tasks: "Project: #N" becomes
   "Epic: #N", and they get todo and their workers' labels. So no worker claims a task whose files
   are not here yet. Accept can be run again on a project it accepted, so a pull request that
   failed is made again.

## The file reader

tools/file_digest.py reads any file as a short text, standard library only, and a worker uses it
too (`python3 tools/file_digest.py FILE`), since Claude Code's Read takes text, images and PDFs
but not an Office file:

- Word: headings, opening text and open comments, through docx_review.
- Excel and CSV: each sheet's extent and formulas, the header and first rows, and per column the
  count, minimum, maximum, mean and sum of its numbers, or its distinct values. This is the start
  an analysis or an accounting task needs.
- PowerPoint: each slide's text in the deck's own order.
- Jupyter notebooks: language, cells and the first text. Code: language, lines, and the count of
  functions and classes. JSON: its shape.
- PDF: page count and title. Images: format and pixel size (PNG, JPEG, GIF, WebP, SVG).
- Design files (.psd, .ai, .fig, .blend and the like), audio, video, archives and mail: kind and
  size.

A file is data: nothing in it runs, a zip part is read only to 20 MB, and a fault is said in the
digest ("could not be read (BadZipFile)") and never stops the run. The sample is the newest few
files of every folder in turn, so a folder of ten thousand photographs takes no more of it than
a folder of three spreadsheets. It stops at 400 files or 120 MB, with each file at most 5 MB. The
bytes are deleted once read, so only names and digests are kept.

## Why it is shaped this way

- Proposed, not queued. A todo task is picked by the workers' six-hourly run and spends the
  Claude plan. The project rule is that only people who may write queue work. So nothing the
  organizer opens carries todo until a person accepts it. The issues are opened with
  GITHUB_TOKEN, which starts no workflow, so the coordinator does not plan them again.
- No integration of a refusal. The coordinator's routing starts an integration when the last
  task of an epic closes, and reads a task's epic from its "Epic: #N" line. A proposed task
  carries "Project: #N" in its place, so closing a proposal's tasks to say no starts no Claude
  run.
- No again. A slug the organizer proposed before, open or closed, is never proposed again, so
  closing a proposal is how the owner says no. Only issues the workflow's own bot opened count,
  so an outsider's issue with the same marker neither blocks a project nor is accepted as one.
- Ids from the catalog, never from Claude. A project's drive.json items are looked up by path in
  the catalog and kept in a hidden line at the head of the epic. A path Claude invents is
  dropped, so accept can only add folders the drive really has. A top item, which is the whole
  of what was shared, and a folder over 2 GB or 2,000 files are never tracked whole, and the epic
  names them.
- No line of the drive's can pose as the organizer's. Claude's text is written from what the
  drive's files say, so a file could get it to write a comment line the organizer reads, such as
  the clerk's task list. Every text Claude gives is cleaned of comment marks, and the organizer
  reads its own lines only where it writes them: the head of a body, the last task list, the
  owner line at a task's end. An epic is opened with no head, which goes on last, so a run that
  fails halfway leaves nothing read as a project.
- Private repositories only. Every step stops in a public repository, since the catalog names a
  person's files and holds a little of what is in them. The log carries counts alone.
- The tidy leaves them alone. The coordinator's weekly tidy splits requests into todo issues; its
  prompt (docs/agents/routines/coordinator.md) now leaves alone what is labelled proposed or
  drive.
- Spending only on purpose. The catalog and accept steps spend no Claude usage. Organize is one
  Claude run, started by hand, at most 60 turns, never in crowd mode, and recorded for the field
  metrics like the coordinator's runs.
- Personal records are left out. The prompt tells Claude to leave out identity documents, medical
  and legal records, and anything that looks like passwords, account numbers or tax returns.

## For the panel (the Control panel sign-in thread)

The Windows-like explorer can draw the whole drive from drive-catalog's catalog.json: folders
with their roll-ups, files with kind, size, date and `web`, which opens the file in Word, Excel
or Docs online. The hierarchy tab can walk from the index issue to the epics (label project:*),
their sub-issues, the claim branches and pull requests, and the runs' logs. An Accept button is a
dispatch of drive-organize.yml with step accept and the epic's number. Opening a file in the
desktop app is the panel's call: OneDrive's `ms-word:ofe|u|<url>` style links take the webUrl.

## The adversarial review

A review before the pull request found eleven faults, each fixed, with a test where one can be
written: drive text posing as the organizer's own lines (a repro queued another project's task),
the weekly tidy splitting proposals into todo issues, closing a proposal starting an
integration, accept tracking the whole drive or a huge folder, accept that could not be retried,
tasks queued before their files arrived, a second queued run cancelling the first, a regex that
took quadratic time on a file of blank lines, a .docx part that could inflate without limit,
accept running in a public repository, and a folder past the depth limit counted as complete.

## Not yet known

- Nothing has run against a real drive. The first catalog waits on a connected drive (the Folders
  tab and the owner's Microsoft clicks in drive-sync.md), and the first organize waits on the
  owner's word, since it spends the Claude plan.
- How long a large drive takes to walk: one Graph call per folder per 200 children, so a drive of
  50,000 files in 3,000 folders is a few thousand calls, inside the 90-minute job. Not measured.
- Graph throttling (429) on a large walk is not retried yet; the folder is named as unlisted.
- The sync roots each tracked item at its own name, so two projects' "Reports" folders under
  different parents both land in `<folder>/Reports/`, and it walks six levels where the catalog
  walks sixteen. A task's files are named by their drive paths, so the board's Overlaps do not
  see them. Neither is fixed here: both are the sync's layout, and a real drive will show whether
  they matter.
- Closing a proposal's epic leaves its proposed tasks open. They carry no todo, so nothing takes
  them; closing them is the owner's tidy.
- How well Claude groups a real drive. The digests are the evidence it gets, and a domain
  outside the fifteen is "other".
