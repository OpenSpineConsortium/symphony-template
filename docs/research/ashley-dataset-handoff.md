# Handoff for Ashley: the dataset collection, and work beside the owner's aims

Source: the thread "Ashley's handoff and parallel work" in the symphony_2 Project, 2026-10-22, on the owner's ask of 02:12 UTC for a handoff Ashley Schehr (GitHub aschehr) can pick up to continue the dataset collection in OpenSpineConsortium/spine-datasets, and for other work she can do beside his aims. Written from spine-datasets' main at 9912438 (the records under datasets/, tasks/TASKS.md, manifests/README.md, docs/ONBOARDING.md), its open issues and its pull requests #99 and #119 to #121, part 6 of docs/checkpoints/2026-10-22/handoff.md, and the Project memory on spine-datasets and the dataset promoter. The owner's Outlook was searched at 02:15 UTC for answers to the three letters of 2026-10-21; none had come.

Part 6 is the work the owner approved for her on 2026-10-22 at 02:23 UTC: tasks A, B, E and F. C, D and G were proposed and left for later.

## 1. Where to start

1. docs/ONBOARDING.md in spine-datasets, then CONTRIBUTING.md and manifests/README.md.
2. The pipeline board: PIPELINE.md on the branch `pipeline` (and pipeline.html on the repository's docs site), every dataset's stage, obstacles and next step.
3. The Board: `/board` in a thread of her own Project on spine-datasets. The tasks are the "Obtain <dataset>" issues, #7 to #92 and #108 to #111; take one by the claim skill, one issue, one branch `claude/<issue>`, one pull request.

## 2. The rules that do not bend

- Anything binding is the owner's hand alone: a data use agreement, a fee, an attestation, a licence box, an account opened in his name. A task that reaches one stops there and says so on the issue, with the label needs-owner.
- A letter goes from her own mailbox, with go2432@wayne.edu in copy, from letters/TEMPLATE.md.
- Confidentiality: no text anywhere, a letter, a record, a pull request, a commit, says or implies that a model, a neural network, machine learning, AI or training is built or used. The required check fails a pull request whose added lines carry those words (tools/dataset_review.py).
- X-ray first: fluoroscopy, video, projections and films before any CT set.
- Her grid account is hy9698, which cannot write /rs/rs_grp_oschome/shared/datasets, by design. She never fetches into the shared tree herself and never asks for, or runs, setfacl. She contributes a manifest; the owner's merge and the promoter do the rest (section 4).
- No grid job, Claude run or training that spends without the owner's word.

## 3. State on 2026-10-22, 02:15 UTC

90 records: 3 on the grid (CADICA, the Fraiwan spine X-rays she started in #99, the DysphagiaBank swallow videos), 1 fetching, 4 granted (all CT), 29 asked and waiting, 5 needing the owner's hand, 1 refused (Balgrist), and 47 still to do, 35 of them plain downloads.

- VinDr-PCXR (#17): granted under the owner's PhysioNet agreement and fetching since 2026-10-21 21:35 UTC (Slurm 40697734, then 40697735 and 40697736), about 30 GB to /rs/rs_grp_oschome/go2432/data/vindr_pcxr/raw. It is marked fetched only once the files match the project's SHA256SUMS.txt; the owner's threads check and record it, since the files sit in his own tree.
- Letters sent from the owner's mailbox on 2026-10-21 at 19:54 and 19:56 UTC: IRI-VFI, Chongqing (#21), TVGH-SpineXR (#14) and the TVGH ankylosing spondylitis films (#108). No answer yet. The answers come to the owner's mailbox, so his threads record them; she does not chase them.
- MIMIC-CXR, MIMIC-CXR-JPG (#15) and VinDr-CXR (#16) wait on PhysioNet's review of the owner's CITI record.
- The owner's hand: MAGIC-CT (#7), BRAX (#110), BIMCV with its IEEE login and a space decision (#111), Stanford AIMI Merlin and INSPECT (#18, #19, held for storage).

What she fixed on 2026-10-21, now merged:

- #119: the manifest command sends a User-Agent, since Mendeley's API turns Python's default away with 403 (her finding and her header), and manifests/README.md tells a Mac with python.org's Python to run `SSL_CERT_FILE=/etc/ssl/cert.pem python3 tools/...` or Install Certificates.command once.
- #120: the Economics test that broke under her Python 3.14 now nests 200,000 deep, which 3.12 and 3.14 both refuse.
- Still open from her run: five failures in TheUnblock (tests/test_workers_steps.py). They pass on Linux under 3.14.6; the tests run a coordinator.yml shell step written for the Ubuntu runner, so a Mac's own shell tools are the likelier cause (task E below).

## 4. The promoter, and what it means for her pull requests

Her pull request carries the record at status `fetching` and manifests/<id>.json; the required check reviews it; the owner merges; the promoter, a Slurm chain under the owner's grid account, downloads every file, checks bytes and checksum, installs it read-only under /rs/rs_grp_oschome/shared/datasets/<id>/raw and opens the record's update to fetched by itself. CADICA and Fraiwan went that way on 2026-10-21.

#121 moved the chain's jobs onto hpcworker's `job submit`, but the running chain keeps its old code, since it updates itself only from the owner's own commits; it is restarted by a gate word, promoter-restart, which the owner's Beethoven grid thread is building. Until then a merged manifest may wait for the promoter longer than the ten minutes it used to; she writes and opens manifests as before and does nothing on the grid about it.

## 5. The dataset work, in order

1. Open-licence X-ray downloads, by manifest (manifests/README.md, "Writing one"), each a claim and a pull request: Mendeley DDH hips (#33, `--mendeley`), VertXNet labels for NHANES II (#28, Zenodo, the record number to confirm on the page first), IPCAI 2025 paired X-ray and CT (#34, `--zenodo 15753063`), VerSe 2D projections (#29, `--zenodo 8115942`), LUMOS (#27); then the figshare ones written by hand from figshare's public API, which gives each file's size and md5: Aariz (#25), KUB-StoneX (#26), FracAtlas (#36). Where a task says "the owner's hand: the licence line read on the page", she quotes the licence line exactly in the record and the pull request; the owner's merge is the acceptance.
2. Video and fluoroscopy downloads, the same way: VFSS2022 (#42), Veriserum (#41), Guide3D (#40), CathAction (#39), the coronary sets beyond CADICA (#38).
3. Open-i (#35) and NIH ChestX-ray14 (#37) are large chest sets; ask the owner for the size first.
4. CT downloads (#44 to #59) only after the X-ray ones.

## 6. Work beside the owner's aims (approved: A, B, E and F)

Chosen so that nothing touches what the owner's open threads hold: the SchwingNet video demo, latency and ONNX, the 3D CT priors (all confidential SchwingNet work, which she is not given), the Beethoven grid and the promoter restart, and the button home screen (site #136, symphony-app #89, symphony-template #344).

- A. The section 5 manifests. The collection itself; spine-datasets only.
- B. Neurosurgical Focus: Video (#43): screen the CC BY articles in a browser for live fluoroscopy and list the ones worth a download in the record. Browser work only, since a proof-of-work gate stops scripts.
- E. Symphony on a Mac: make the five TheUnblock tests pass on macOS (BSD shell tools) as well as on Linux, in symphony-template, the source the copies take it from. No thread holds it.
- F. Symphony's proof, as the second person: her claims and pull requests in spine-datasets are the field metrics' several-people setting, the case the coordination measurement needs; and she walks docs/ONBOARDING.md as a fresh user on her Mac, filing every point of friction as an issue in symphony-template, as her three findings of 2026-10-21 already were.

Left for later, on the owner's choice: reading the five forms (#9 to #13) field by field, a figshare source for the manifest command, and a no-scroll audit of the control panel's tabs once site #136 merges.
