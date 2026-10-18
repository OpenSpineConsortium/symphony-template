# A repository that tracks Google Drive or OneDrive files

Source: the thread "Word revisions from OneDrive" in the project symphony2, 2026-10-18,
answering three of the owner's messages that day. The first asked for GitHub connected to
OneDrive, kept in sync, with new comments starting work. The second asked to do the shortcut in
https://startupceo.com/2026/04/ai-shortcut-how-to-collaborate-on-claude-projects-without-a-teams-or-enterprise-license
"way better", given Claude's integration with Google Drive and OneDrive. The third: "I want to
one-click authorize and literally create a repo which tracks certain files/folders from my
onedrive/google drive that i choose in the browser". This note is the design, what this pull
request builds of it, and what waits on the owner's clicks and on other threads. The Word side
is docs/research/word-revisions-from-onedrive.md and docs/setup/word-revisions.md.

## The article's shortcut, and what Symphony already does better

The article (read 2026-10-18) shares one Claude context across separate Pro accounts with no
Teams plan. A shared Drive folder holds three Google Docs (ProjectContext, WorkingConventions,
ChangeLog). Each member's Project instructions tell Claude to read them, and each member connects
the Drive connector. A weekly prompt harvests decisions, a "context owner" pastes them in by hand,
and the article names its own limits: the connector is read-only, nothing is in real time, memory
is not shared, and upkeep is manual.

A Symphony repository is that idea already, without the hand work. CLAUDE.md, docs/project.md and
docs/memory/ are the context every session loads, on any account. A fact lands by pull request,
in the same change as the work it came from, so no harvest or context owner is needed. The board
shows who is doing what in real time, and the workers in Actions write as well as read. What the
article has that Symphony lacked is that the people who never open GitHub work in Drive or
OneDrive. This design brings their folder to the repository and their comments to the board.

## The flow the owner asked for

One page of the control panel, Folders (/symphony/control/folders.html), signed in with GitHub as
every panel page is:

1. Connect Google Drive, or Connect OneDrive: one press, the provider's own consent screen, back
   to the page.
2. Pick: the provider's own picker (Google Picker; OneDrive's File Picker v8) chooses the files
   and folders to track.
3. Create the repository: the page opens GitHub's own "new repository from a template" form,
   https://github.com/new?template_owner=OpenSpineConsortium&template_name=symphony-template,
   named and pressed by the person. That keeps the rule that a new repository's first commit is
   the owner's, and needs no Administration permission for SymphonyBoard, which the decisions
   keep off it. The adoption runs as it does from the front door.
4. Track: the page writes .github/symphony/drive.json (the provider, the folder in the repository,
   the picked items' ids and names) and saves the drive's refresh token as the repository's secret
   SYMPHONY_DRIVE_REFRESH, both through the App. Then it starts the first sync.

From then on .github/workflows/drive-sync.yml keeps the two in step every half hour, and the
page's Sync now button runs it at once. A new comment in a document becomes a task on the board,
a worker answers it as tracked changes, and the revised file goes back to the drive.

## What this pull request builds

- tools/drive_sync.py, standard library only. It reads both providers through their REST APIs,
  with each folder walked to six levels, and decides each file's move from three things: the
  drive's version, the default branch's copy and the last run's record (state.json on the branch
  drive-state). A file that changed only in the drive comes down on the pull request drive/sync,
  which merges by itself once green. One that changed only here goes up in place. One that changed
  on both goes up beside the drive's as "<name> (Symphony revisions)", and the drive's comes down,
  so nothing is lost. A pulled file waits for its merge, so it is neither pulled twice nor pushed
  back. A native Google file comes down exported (Doc as .docx, Sheet as .xlsx, Slides as .pptx).
  It takes no upload, so its revision goes beside it. A Google file's version includes a hash of
  its Drive comments, since a comment on a Google Doc changes no version of the file. A redirect,
  such as Graph's download, is followed without the token. A drive's names are cleaned to single
  path segments.
- .github/workflows/drive-sync.yml. First it queues the comments of what is already on the default
  branch. Then it syncs, opens or updates drive/sync, asks for the check there and arms auto-merge.
  It uses GITHUB_TOKEN alone, as protocol.yml does, and ends at once with no drive connected.
- .github/workflows/papers.yml and `tools/docx_review.py watch`. A document is one task for good,
  found by a marker in the issue body, which also lists the comments seen so far. Each comment is
  keyed by its author, date and words, since Word renumbers comment ids on every save. New comments
  are told on the issue, which is reopened or labelled todo again, and the workers are woken.
  Claude's own comments, the answers, queue nothing.
- An adversarial review before the pull request found ten faults, each fixed with a test where
  one can be written:
  - a drive/sync pull request left open after the drive moved on, which merged late and was then
    pushed back over the drive (now every run rebuilds or closes it, and a copy the sync once
    staged is never taken for a revision);
  - files kept by path, so a rename or two files of one name mixed them up (now by the drive's id);
  - a reopened task still labelled in-review;
  - an outsider's issue taken for a document's task (now only the workflows' own, or a writer's);
  - a removed comments marker spamming the issue;
  - one unreadable document stopping the sync;
  - a failed pull request never retried;
  - a 4 MB conflict that stalled a file;
  - a network error that lost the state;
  - the two workflows racing.
- Tests: tests/test_drive_sync.py (each decision, a round trip against a drive in memory, both
  providers' calls) and tests/test_docx_review.py (watch, renumbering).

## What other threads build, and the owner's clicks

The sign-in service (symphony-app/signin, the Control panel sign-in thread's) takes two routes. Both
keep nothing, as its GitHub sign-in does:

- POST /drive/connect, {provider, code, code_verifier, redirect_uri}: exchanges the consent code,
  with the client secret it holds, and returns the refresh token to the page, which seals it
  straight into the repository's secret.
- POST /drive/token, {provider, refresh_token}: returns an access token for the run. The client
  secrets stay in Cloudflare, so no repository holds one.

The panel's Folders page is the site's and the same thread's. Every page that signs in is a
SymphonyBoard Callback URL, which is the owner's click. Saving a repository secret needs
SymphonyBoard's Secrets permission, the grant already waiting on the owner for the Tokens page.
The Apps' privacy statement gains what the page and the service handle before either ships
(version 11 is the grid thread's, so this is the next).

The owner's one-time clicks, given with their links when the page is built:

- Google: a Cloud project with the Drive API and the Picker API on. An OAuth client of type "Web
  application", whose redirect URI is the Folders page. A browser API key restricted to
  openspineconsortium.com, which is public by design and no secret. The consent screen published
  "In production": the one scope, drive.file, is non-sensitive, so no verification is due, and in
  Testing a refresh token lapses after seven days.
- Microsoft: an app registration for "Accounts in any organizational directory and personal
  Microsoft accounts", a web redirect URI of the Folders page, a client secret into Cloudflare,
  and the delegated scopes Files.ReadWrite and offline_access.

## Limits and what is not yet known

- OneDrive at WSU: a university tenant often lets users consent only to apps from a verified
  publisher, so the owner's WSU account may need IT's consent or a verified publisher (a free
  Microsoft partner ID). Not tried. A personal Microsoft account has no such gate. Where neither
  goes, the owner's own computer is the fallback (word-revisions-from-onedrive.md), with no stored
  login.
- Files.ReadWrite reaches all of the person's files, though the run reads only the picked items.
  Graph's Files.ReadWrite.Selected grants only "several hours" after each selection (Graph's
  permission reference, read 2026-10-18), too short for a sync.
- A Microsoft refresh token lasts 90 days. The run cannot write a secret, so it cannot keep the
  rotated one, and the person presses Connect again about every 90 days. The page shows when.
  Google's lasts until it goes unused for six months.
- drive.file grants what the person picks. Whether picking a folder grants the files inside it is
  not settled by Google's picker guide (read 2026-10-18). The first real connection tests it, and
  if it does not, the person picks the files themselves.
- Comments: a native Google Doc's comments are expected in its .docx export, which is not yet
  checked. Comments made in Drive's preview of a .docx file stay outside the file, so the tasks see
  only comments made in Word or in Docs' Office editing.
- Graph's simple upload takes 4 MB. A larger file stays in the repository and is named in the
  run's summary until an upload session is built. A file the drive drops stays in the repository.
- Every half hour costs a private repository about 1,440 Actions minutes a month. A public one is
  free. A push from the drive itself would need the service to take Google's or Graph's change
  notifications and dispatch the run, which it cannot do without holding a GitHub token, so the
  schedule is the fallback and Sync now the button.
- Nothing has run against a real drive yet: the first connection is the test, and it waits on the
  clicks above.
