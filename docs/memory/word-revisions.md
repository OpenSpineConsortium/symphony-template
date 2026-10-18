Word documents are revised as tasks: tools/docx_review.py turns comments into a review sheet and one task per document, and writes revisions back as tracked changes.

A .docx file is a zip of XML that Claude cannot read by itself, so
tools/docx_review.py, standard library only, writes <name>.review.md beside
each document (paragraphs numbered, open comments under them), makes one task
per document (never per comment, since two workers in one .docx would meet),
and applies the worker's <name>.revisions.json as word-level tracked changes
with a comment of Claude's for each "why"; each entry carries the paragraph's
exact old text, and a paragraph with a field, picture, hyperlink or earlier
tracked change is refused. The procedure is docs/setup/word-revisions.md and
the research, with the OneDrive routes, docs/research/word-revisions-from-onedrive.md:
the owner's own computer through the folder tools is the recommended sync,
with no credential; Microsoft Graph in Actions would store one and is the
owner's call.
