# Automatic run reports: reporting checklists answered by code, and licences carried with the run

Source: the thread "Automatic report generation", 2026-10-23, from the owner's ask of that day that a training workflow build, before training starts, a record of every run that shows complete CLAIM and REFORMS compliance and maps the datasets it trained on to their licences, so that a network meant for commercial use can be told from one that needs non-commercial terms. The build is in OpenSpineConsortium/SchwingNet, issue #153 and pull request #154; this note keeps the method only, since SchwingNet's research and numbers stay in SchwingNet.

## What was already there

- A run record written before the first step (the commit, a clean-tree refusal, the catalog's sha256, the split check, the jobs with what they cost), and results rows stamped with the run id and a Wilson interval. These answer most of the methods and results items of both checklists without a person.
- A REFORMS checklist artifact from 2026-10-03 that tied all 32 items to a gate and split them into 20 a program can check and 12 a person must write, the code checking only that the writing is there.
- No CLAIM list, no report a run wrote of itself, and licences only as free text in each dataset record.

## The design

1. The items are data, not code: one JSON file lists CLAIM 2024's 44 items (Tejani et al., Radiology: Artificial Intelligence 2024, doi 10.1148/ryai.240300) and REFORMS's 32 (Kapoor et al., arXiv 2308.07832), each with the one fact that answers it and whether code or a person gives that fact. Items that ask for the same thing share a fact, so one answer serves both lists (76 items over 64 facts).
2. Four states, never inferred: met (code found it, and the evidence quotes the file), declared (a person's sentence in one study file), not applicable (a declared sentence that starts so, with its reason), missing. A dirty tree, a leaking split or a file the run does not hold is never met.
3. A gap names its work: a missing code item says which file or step would answer it, so the report doubles as the list of what to build next (in the first report: the excluded samples, missing data per class, the characteristics of each part, and the licence record).
4. The study file starts empty, on purpose: the declared items are the owner's claims, and a session writing them would be the report vouching for itself.
5. Licences are read, never worked out: the licence work writes one provenance file per run (each source's licence, class, commercial answer, whether the owner reviewed the class, frames by part, the run's least permissive class, the recipe the catalog was cut by), and the report renders it. One owner of the rule means the report and a recipe can never disagree.
6. Written by the flow, held by the check: the training flow writes the report after its last step and copies it with the run's small files; the required check rewrites every recorded run's report in memory and fails when the committed one differs, so a changed study answer or a hand edit is caught. A stricter mode fails while any item is missing and is the gate before a number is published, not before a run, since a training run should not stop for a missing manuscript sentence.
7. Standard library only, like the evaluation page it sits beside, so the required check runs it without the locked environment.

## What to carry elsewhere

The pattern fits any repository whose runs leave a record: a JSON list of a reporting standard's items keyed to facts, a function per code fact over the run's files, a study file for the rest, and a check that the committed report is what the files give. Other standards (TRIPOD+AI, STARD-AI, a model card) are another list in the same file.

## Not measured or not yet checked

- The CLAIM item texts were read through a summarising fetch of the eScholarship copy of the paper, since the session's proxy refused the journal and the PDF; they should be checked once against the published checklist table.
- No real run has written a report yet: the two recorded runs are dry runs, and no grid job ran for this work.
