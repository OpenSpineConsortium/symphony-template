# Training data licence provenance

Source: the thread "Training data licence provenance", 2026-10-23, on the owner's ask of that day that a project's training workflow record which datasets every run used under which licence, so that networks for commercial use are built only from data that allows it and the possible recipes can be seen before anything runs. The work landed in the private repository it serves (OpenSpineConsortium/SchwingNet, pull request 157); this note keeps the method, which any Symphony project that trains on other people's data can reuse, and none of that repository's research.

## The method

1. One licence entry per dataset, in a file beside the dataset records, that copies the record's licence line word for word. A line that changes then fails the required check until it is classified again, so a class never outlives the words it was read from.
2. Six classes, from the most permissive: open (commercial use and derivatives, at most attribution), share-alike, non-commercial, agreement (a DUA, a credentialed licence, a request form, competition rules, research-only), no-derivatives and unknown. A rule proposes the class by the strictest reading any phrase of the line gives, restrictions counted even inside notes, permissive words only outside them, and doubt ("to confirm", "mixed", "open access", a bare "open", an unstated origin) read as unknown. Only the owner's own reading, recorded with a date, may give a class looser than the rule's.
3. Recipes are small files naming the classes they take; no recipe takes unknown, and the commercial ones take owner-reviewed entries only. A tool cuts a catalog to a recipe and writes the recipe and the parent catalog's sha256 into the copy, so a derived catalog says what it was cut from.
4. Every training run writes a provenance record (JSON and Markdown) before its first step: each source, its licence and class, its frames and persons in each split, the recipes it fits, and the run's own class, the strictest among the sources it trained or selected on; a test-only source is listed but does not set the class. A run that names a recipe is refused, before anything is written, when its catalog holds a source the recipe does not take. The ledger row names the run's class, and the per-run report reads the record rather than recomputing it.

## What it found

Classifying the free-text licence lines by the strict rule left about two fifths of the datasets unknown, most because a line still said "to confirm", and no source in the commercial recipe until the owner confirms the open classes: the record makes that gap visible rather than letting a run assume a licence. Where two repositories each hold a copy of a dataset's record, the later reading in one does not reach the other by itself, so the licence lines need one owner or a sync.

## What it does not settle

A class says what the licence's words say. Whether a trained network is an adaptation under share-alike or no-derivatives terms, and what an agreement's research-use clause allows a spin-out, are questions for counsel and the university's technology transfer office; the record keeps the facts they would ask for.
