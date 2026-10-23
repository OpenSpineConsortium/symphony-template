# What the project knows, across its repositories, on 2026-10-23

Source: the thread "Spine knowledge synthesis", 2026-10-23, on the owner's ask of 02:03 UTC to pick up "big picture stuff like knowledge synthesis". Read from this folder's notes (curse-of-coordination-full-run.md, flowbench/README.md, stale-branch-failures.md, claim-waits-in-a-real-copy.md, grid-and-cloud-workers-review.md, running-a-project-through-the-grid-gate.md, fetch-failures-read-behind-the-gate.md, spine-dataset-status-audit.md, handoff-2026-10-23.md) and from spine-datasets' records at main b44ba32. No grid job, fetch or bench run was started for it. SchwingNet's research is confidential, so it is synthesised inside SchwingNet alone (below), and nothing of its method or results is written here.

## Where each synthesis lives

- Symphony and the operations that serve every project: this note.
- The datasets, by the question each can answer, with the paired CT and X-ray breakout: spine-datasets docs/research/datasets-by-question.md (spine-datasets #180, step 4 of its track #175). The generated census is that repository's #178.
- The paired CT and X-ray sets by tier, and the annotation plan: paired-ct-xray-annotation-plan.md, beside this note (the thread "Paired CT and X-ray datasets").
- SchwingNet's research: SchwingNet docs/research/state-of-knowledge.md (SchwingNet #147), confidential, read there.
- The owner's claude.ai artifacts as one book: SchwingNet's artifact-textbook programme (#120).

## 1. Symphony: what coordination has been shown to buy

| Measurement | What it found | Grade |
| --- | --- | --- |
| CooperBench, 43 pairs, five arms (curse-of-coordination-full-run.md) | solo 33, team 33, sdlc 32, coop-git 32, coop 30 passed; no difference significant (sdlc against coop p 0.63); every two-agent arm about twice solo's cost | Measured |
| flowbench pilot, 8 SWE-bench instances, three arms (flowbench/README.md) | symphony 8/8, script 8/8, solo 7/8; symphony used 0.75 of the script's tokens (0.67 to 0.82) | Measured, n = 8 |
| Stale branches in this project's own history (stale-branch-failures.md) | with the up-to-date rule on, 34 % of symphony-template's merged pull requests went stale after green and 35 % of check runs were redone, rising from 8 % of pull requests taking main in alone to 93 % beside six or more | Measured |
| Claim waits in a real copy (claim-waits-in-a-real-copy.md) | 84 s from claim commit to draft, 9.6 min from opening to merge, by median | Measured |

Read together, these say three things:

- Every effect measured so far is on cost and churn, not on whether the work passes. On pass rate, the claim protocol is within noise of solo and of the other two-agent arms on both benchmarks.
- The largest effect measured is a process change, not the protocol: turning off "require branches to be up to date". The claim protocol itself has not been compared under load in this project's own history. Only 8 of 256 merged pull requests came from a claim branch, all from days when few threads ran. The record now keeps whether each pull request is a claim's, so the comparison can be made from the history once claims are the usual route.
- What would change this reading is a benchmark where one agent alone does worse, or many more pairs. Both are runs that spend tokens and wait for the owner's word and the count (coordbench's trial-order.md, flowbench's PLAN.md).

## 2. The grid as a platform

What the notes found by running projects through the gate, as rules that now hold:

- A project never writes placement. Every job goes through hpcworker's `job submit` with a class, and the site profile places it.
- Parsed output is guarded: `apptainer --quiet exec`, redaction filters tested on ordinary text, and a .netrc read as wget reads it.
- The status word says that a job failed and when, and never why. The reason is read on the grid (fetch-failures-read-behind-the-gate.md).
- The grid's workers are behind industry practice on bursts, heartbeats, key lifetime and error causes (grid-and-cloud-workers-review.md). The lost-press fault is fixed. The rest are ranked there.

One consequence the notes record separately and nobody has set side by side yet. The fetch word makes every job it sends wait afterany on every live X-ray fetch. The VinDr-PCXR fetch, 40704982, is tabled and left alone (spine-datasets #17). It moved about 29 MB an hour at 02:05 UTC on 2026-10-23, so its 34.1 GB would take weeks. Nine fetches wait behind it: CADS, NLST, ReXGradient, OL3I, CheXpert Plus, MAGIC-CT, the FluoroSAM weights, the IPCAI 2025 Drive archive and FluoroSeg (handoff-2026-10-23.md, "Picked up"). So while 40704982 runs, those nine do not start. Whether to cancel it, or to send the nine again without the wait, is the owner's call. Under his rule, no session resends a fetch before it has checked with the status word.

## 3. Getting the datasets

What blocks the data is almost never a download. It is one of a short list of things that only the owner can do:

- a licence term: the non-commercial licence that keeps LUMOS out, although the project already holds COBRA and DeepFluoro under such terms; and FluoroSeg's, which the owner accepted;
- a credential: PhysioNet's CITI review for the MIMIC sets, the Kaggle rules for RSPECT, and the RATIC link, which expires on 2026-10-28;
- a signed request: MrOS and SOF through the NIA Aging Research Biobank, and any LevelCheck cohort agreement with Johns Hopkins;
- storage, for Merlin and INSPECT: the volume held 9,605 GB of a 21,991 GB quota on 2026-10-23.

The records drift from what other repositories know. spine-datasets #180 lists five places where a record disagrees with SchwingNet's records. Its track #175 is to make the records the one source that every page is generated from.

## 4. What no note has measured yet

- The claim protocol against no protocol, under the same load, in a real repository.
- Two or more grid workers at once on real nodes, and the queue wait per partition.
- Whether a long Remote Control session survives several job ends whole.
- Why the PadChest and BIMCV COVID-19+ fetches failed. Only the grid's logs hold the reason.
