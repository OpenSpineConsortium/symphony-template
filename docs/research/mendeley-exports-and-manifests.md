# Mendeley exports and manifests: what was rough, what changed

Source: the thread "Mendeley integration", 2026-10-22, for task 6 of the owner's handoff
(docs/research/ashley-dataset-handoff.md): make Mendeley seamless for references, a library export
into references.json, and for dataset manifests, spine-datasets' `tools/dataset_review.py manifest
--mendeley`. Issues: symphony-template#357 and OpenSpineConsortium/spine-datasets#129. The cloud
session's proxy refuses data.mendeley.com and api.mendeley.com, so the exports were written by hand
in the shapes Mendeley Desktop and Mendeley Reference Manager write, and the Mendeley Data answers
in the shape the existing manifests (fraiwan_spine_xray, cadica) were built from.

## References

Running `tools/notebook.py refs` on such exports found four things wrong. Mendeley Desktop escapes
`_ & % $ # { }` in BibTeX as `{\_}`, `{\&}` and so on, and the backslashes stayed in titles, links
and DOIs; a DOI given as a doi.org link stayed a link; two references with one key (Mendeley writes
Smith2021 twice) both kept it, so docx_cite's lookup by key quietly took one; and Mendeley's RIS
carries no ID, so references were keyed ref1, ref2 by position, and every key moved when the
library grew and was exported again, pointing the citations already written at other works.

refs now undoes the escapes, cuts a DOI link to the DOI, makes every key unique the way citation
managers do (Smith2021a), keys a reference that came with none by its first author and year, and,
run onto an existing references.json, keeps each reference's earlier key, matched by DOI or by
title and year, printing how many kept theirs. The export stays the way in: no Mendeley account,
key or app is needed, and the API import planned in mendeley-sign-in.md still waits on the owner.

## Manifests

The manifest command took only a bare dataset id, with a version that defaulted to 1, so a set
updated since was read at its first version without a word; one dataset per run, so a record that
gathers two (mendeley_ddh_hips) could not be written; it crashed on an entry with no download link
and printed tracebacks for a 403, a 404 or a Mac's certificate failure; and it left the record's
licence, status, history and next to be edited by hand, so the first push often failed the check.

It now takes the page's address, the bare id or the DOI, the latest version where none is named,
`--mendeley` once per dataset with each one's files under raw/<dataset>/, `--licence` for the line
read on the page, readies the record, holds the result to the promoter's rules and says what is
still to do, in one line per refusal.

## Not yet known

Whether Mendeley Data's public API names a dataset's latest version at
public-api/datasets/<id> (the command asks for `--version` where it does not), and how its file
list shows a dataset's folders: the list read is the top level only, and the command stops on an
entry with no download link rather than leave it out. Both are read on a machine that reaches
Mendeley before they are relied on.
