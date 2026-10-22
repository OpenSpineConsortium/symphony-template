# Word, OneDrive and Zotero as a new user

Source: the thread "Word, OneDrive and Zotero workflow", 2026-10-22, for task 5 of the owner's
handoff to Ashley (docs/research/ashley-dataset-handoff.md): test revising a Word document with
citations, synced with OneDrive, as a new user would, file each rough spot as an issue and fix
what can be fixed.

## How the walk was done

In a cloud session, with Python 3.12 and LibreOffice and no Word, Zotero or OneDrive: the sample
paper from `docx_review.py sample`, a made-up BibTeX library of an article and a book read with
`notebook.py refs`, two citations written with `docx_cite.py`, the insertions accepted as an
author would, and a revision applied to a cited paragraph. Each copy was checked with the Office
Open XML schemas and the tracked-change checks of Anthropic's docx validator and opened with
LibreOffice.

## What a new user met, and what became of it

- A cited paragraph could not be revised (#351). apply refused any field, link or content
  control, so in a real paper, where most paragraphs cite, the loop revised almost nothing. Now a
  citation, another field, a link or a content control is kept whole: its words stand in the
  text as one character while the words around it are diffed, the sheet lists them as "keep as
  written", and a field whose words the revision leaves out is a tracked deletion. A link or a
  content control must stay, since deleting one as a tracked change is not built. Fixed.
- A cited paragraph could not take another citation (#352). Fixed: docx_cite.py now cites in any
  paragraph apply could revise, after plain words and never inside a citation.
- References lost what a bibliography needs (#353): every book became a journal article or Misc,
  volume, issue, pages and publisher were dropped, {World Health Organization} became a person
  named Organization, and Zotero's CSL JSON export was not read. Fixed: the CSL kind and those
  fields are kept from BibTeX, RIS, CSL JSON and Zotero's web API and written as Word's source
  types and CSL types; a CSL JSON id that is a zotero.org item address is kept as the item's uri,
  which `--form zotero` needs, so a synced library's export may serve with no API key (untested).
- No path through it (#354): the steps were spread over a setup page, two research notes and a
  skill, and the tools' help cut off mid-sentence. Fixed: docs/setup/word-revisions.md gains "Try
  it in five minutes" and "Citations", and the three tools print their whole description and each
  option's meaning.
- Not testable here, and open: Zotero's Refresh on a `--form zotero` copy, Word for the web, and
  what a synced library's CSL JSON export carries (#355); a new user's first OneDrive round trip of
  a real document through the Folders tab (#356). Both need a person's own Word, Zotero and
  OneDrive.
