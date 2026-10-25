# The access path of six spine-datasets records

Source: the thread "Unresearched dataset records" in the symphony_2 Project, 2026-10-22, on the owner's ask of 09:33 UTC for more parallel work on the board that Ashley is not doing. Six tasks in OpenSpineConsortium/spine-datasets whose record still said "to confirm on the page" were claimed and read: #23, #24, #30, #32, #35 and #59, none of them among the tasks the owner gave Ashley (ashley-dataset-handoff.md). Each finding went into its record as one dated history entry, by pull requests #141 to #146.

## How the pages were read

The session's network refuses Zenodo, Mendeley, Kaggle and Open-i directly, so each page was read through a fetch tool that summarises a page in answer to a question; Zenodo's API is closed to it by robots.txt, its record pages are not. Kaggle's dataset API (api/v1/datasets/view/OWNER/SLUG) answers through it with the licence field, the size in bytes and the description, which the Kaggle page itself does not show without a browser. The licence lines and sizes were asked for word for word, but nothing here is a manifest: the manifest command (tools/dataset_review.py manifest) reads each source's own API again, so no number of this note reaches the promoter unchecked.

## What each page says

| Task | Set | Licence as read | Host and size | Where it stands |
| --- | --- | --- | --- | --- |
| #30 | PENGWIN Task 2 synthetic X-rays | CC BY 4.0 | Zenodo 10913195, one archive of 35.0 GB; contact Benjamin Killeen | todo, ready for a Zenodo manifest |
| #32 | Canine lateral thoracic radiographs (VHS) | CC BY 4.0 | Mendeley ktx4cj55pn version 1, PNGs with sha256 each; the first 86 files about 282 MB | todo, ready for a Mendeley manifest |
| #23 | Kaggle scoliosis set (salmankey) | MIT in Kaggle's field, CC BY 4.0 in the description; both open | Kaggle, 251,996,951 bytes; Roboflow boxes, augmented copies, origin unstated | needs-owner: the owner's Kaggle login; the AASCE hash check stays |
| #24 | Kaggle fracture multi-region set | PDDL in Kaggle's field, ODC-By 1.0 in the description | Kaggle, 507,724,147 bytes; merged from three other Kaggle uploads | todo: a collaborator reads the three source uploads' terms first |
| #35 | Open-i Indiana chest collection | CC BY-NC-ND 4.0 as two mirrors state; NLM's FAQ was under maintenance | NLM's own archives; the Kaggle mirror is 14.2 GB and resized | needs-owner: the non-commercial, no-derivatives term |
| #59 | VSDFullBody whole-body CT | CC BY-NC-SA 3.0 Switzerland | Zenodo 8270365, 109 archives, 116.3 GB, four of them empty placeholders | needs-owner: the non-commercial, share-alike term |

## What it teaches

- A Kaggle set's open licence field says nothing about where its images came from. One of the two here is a merge of three other uploads, so its own open licence cannot clear it; the other names no origin at all. Kaggle's licence field and its description disagreed in both, which is common enough that a record should quote both.
- "Open, no agreement" on a host's page is about access, not use: Open-i lets anyone download, and its collection still carries a non-commercial, no-derivatives licence by every mirror's account.
- A licence on a Zenodo mirror of an older database is the uploader's statement of the original's terms (VSDFullBody's mirror says it changed nothing), so the record names both the mirror and the original.
- Two of the six (#30, #32) are now one manifest away from the promoter; three (#23, #35, #59) wait on the owner's decision or account, which the pipeline board shows in its needs-owner column.
