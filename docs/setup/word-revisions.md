# Revising Word documents with Symphony

A paper or any other Word document kept in this repository is revised the way
code is: each document with open review comments becomes a task on the board,
a worker claims it, answers the comments and opens a pull request, and the
author reviews the result in Word as tracked changes, accepting or rejecting
each one. tools/docx_review.py is the bridge, since Claude cannot read a .docx
file, a zip of XML, by itself; it uses Python's standard library alone. The
research behind it, with the ways a OneDrive folder reaches the repository, is
docs/research/word-revisions-from-onedrive.md.

## The folder

Keep the documents in one folder, papers/ unless the project says otherwise,
one .docx per document, with comments made in Word's Review tab. Beside each,
the tool writes and the worker updates:

- `<name>.review.md`, the review sheet: every paragraph numbered, the open
  comments under the paragraph each ends in, with the words it marks. It is
  what a worker reads and what a pull request shows as a diff, since git shows
  nothing of a .docx file's own change. Comments marked done in Word are left
  out.
- `<name>.revisions.json`, the worker's answer: one entry per paragraph it
  changes, `{"paragraph": 12, "old": "...", "text": "...", "comment": "3",
  "why": "..."}`. "old" is the paragraph exactly as the sheet shows it, so a
  revision never lands on a paragraph that moved; "why" becomes a comment of
  Claude's on the paragraph, and an entry whose text equals its old text
  changes nothing and only answers the comment, for a comment that needs the
  author (new data, a figure, a judgement).

## The loop

1. `python3 tools/docx_review.py sheet papers/*.docx` writes the sheets.
2. `python3 tools/docx_review.py tasks papers` prints one task per document
   with open comments, in the Task form's shape (Goal, Acceptance, Files
   likely touched); `--gh` opens or updates them as watch does, below. One
   task per document, never per comment, since two workers rewriting one
   .docx file would meet in it, and the board's Overlaps would only order
   them.
3. A worker claims the task as for any issue (docs/agents/PROTOCOL.md): a
   person's session, a routine, a worker in Actions (workers.yml, which an
   issue labelled todo wakes when one is registered), or @claude on the issue
   (claude.yml). It writes the revisions file, runs
   `python3 tools/docx_review.py apply papers/<name>.docx papers/<name>.revisions.json`
   and the sheet again, and commits the three files. The workers' allowed
   tools already take `python3`.
4. The author opens the pull request's .docx in Word, or merges and opens it,
   and walks the tracked changes with Review, Next, Accept or Reject; each
   change is Claude's, dated, and each "why" sits beside its paragraph.

A document's task is one issue for good. .github/workflows/papers.yml runs
`python3 tools/docx_review.py watch` on each document a push brings to the
default branch: new comments are told on the issue, which is reopened or
queued again, and the workers are woken. A comment is known by its author,
date and words, since Word renumbers comments on every save, and Claude's own
comments, the answers, queue nothing. A connected Google Drive or OneDrive
brings documents in and takes revisions back by itself
(docs/research/drive-sync.md).

## Try it in five minutes

Every command below runs in a clone with Python 3.12 and nothing else, on a
made-up paper, so a new person sees the whole loop before touching a real
document. Each tool also explains itself with `--help`.

    python3 tools/docx_review.py sample papers/sample.docx
    python3 tools/docx_review.py sheet papers/sample.docx
    # read papers/sample.review.md, then write papers/sample.revisions.json:
    # [{"paragraph": 2, "old": "<paragraph 2 exactly as the sheet shows it>",
    #   "text": "<the new text>", "comment": "1", "why": "<one line>"}]
    python3 tools/docx_review.py apply papers/sample.docx papers/sample.revisions.json --out papers/sample-revised.docx

Open papers/sample-revised.docx in Word and walk the changes with Review,
Next. Citations follow the same way (Citations, below): export a few
references from Zotero, Mendeley or EndNote, run `refs`, write a cites file
and run docx_cite.py.

## Citations

A paper's paragraphs mostly hold citations, and a revision keeps them:

- Revising around a citation. A citation, whichever manager put it there
  (Word's own, Zotero's or EndNote's field, Mendeley Cite's content
  control), and a hyperlink or another field, is kept whole. The sheet lists
  its words under the paragraph as "keep as written"; a revision keeps those
  words as they are and changes the words around them. Leaving a field's
  words out of the new text deletes that field as a tracked deletion the
  author can reject; a link or a content control must stay.
- Adding citations. `python3 tools/notebook.py refs --export library.bib
  --out references.json` reads a BibTeX, RIS or CSL JSON export (Zotero:
  File, Export Library, or right-click a collection; Mendeley: File, Export;
  EndNote: File, Export, RIS), keeping each reference's kind, venue, volume,
  issue, pages and publisher. A cites file names where each goes,
  `[{"paragraph": 3, "after": "Table 1", "refs": ["smith2020"]}]`, numbered as
  the sheet numbers paragraphs, and
  `python3 tools/docx_cite.py papers/paper.docx --refs references.json
  --cite cites.json --out papers/paper-cited.docx` writes them as tracked
  insertions in a copy. The default form is Word's own citations, which any
  Word fills in with no add-in (References, Bibliography, Insert
  Bibliography; Update Field on a citation); `--form zotero` writes Zotero's
  field instead, for a paper cited with Zotero, which needs each item's
  library address and so a library read through Zotero's web API, or a CSL
  JSON export of a synced library (docs/research/notebooks.md). A paragraph
  takes another citation once the earlier ones are accepted.
- OneDrive. A document in a tracked OneDrive folder comes into the
  repository and its revisions go back beside it by themselves
  (docs/research/drive-sync.md), once the folder is picked on the control
  panel's Folders tab.

## What apply refuses

A paragraph that holds a picture, an equation, a run of something other
than text, or a tracked change already there is refused with its number,
and the review sheet says so under the paragraph, since rewriting it could
lose what it holds: the author revises it by hand, or accepts the earlier
changes first. Citations, fields, links and content controls are kept whole
(Citations, above); a field that runs on past its paragraph, or a revision
that drops a link's or a content control's words, is refused. A revision whose "old" no
longer matches is refused too, as are two entries for one paragraph, a new
text holding a line break (a paragraph's text is one line; tabs are kept), a
tracked format change still waiting in the paragraph, and a "why" in a
document that has no comments part yet (add one comment in Word first). Each changed run keeps its formatting; an
inserted word takes the formatting of the word before it.
