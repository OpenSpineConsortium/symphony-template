# Restart kit of 2026-10-27: the new project's goal, instructions, repositories and first prompt

Source: the thread "Write restart kit for the new account" in the claude.ai project symphony (https://claude.ai/code/project/chan_014WUU19NHgHPhf7QetT9cbS), written from 06:46 UTC on 2026-10-27 on the owner's ask of 06:45 UTC, "instructions on restarting in a new project on a new account, including updating the goal, instructions, which repos to add, and what the first prompt should be", with the project's memory and every finding compacted for the next project. It is built from handoff-2026-10-27-checkpoint-4.md (section 0 above all), handoff-2026-10-25.md (sections 0, 2 and 11), the instructions the project symphony ran under, bordercall's README.md and TODO.md at 7015802, and SchwingNet's docs/checkpoints/2026-10-27-morning/. No secret, token or credential is written here, and no career material.

This page gives the texts to paste and the steps. It does not replace handoff-2026-10-27-checkpoint-4.md: that page's section 0, the owner's priority of 05:48 UTC, still holds over everything, and its sections 2 to 6 stay the record each paused thread restarts from. Where this page's first prompt and that page's section 1 differ, this page holds. The compacted memory and the research findings are confidential and live in the private OpenSpineConsortium/SchwingNet, at docs/checkpoints/2026-10-27-restart-kit/ (section 7); nothing of them is copied here.

## 0. The checkpoint of 2026-10-27, 11:33 UTC: the state the next project starts from

Written at the owner's words of 11:33 UTC in the thread "Flesh out Panjabi, rewrite in PyMC" ("Restart none of the paused threads and start nothing else until I say so. When I name the next item, it is gold tier 1, 2 and 3 data, bordercall TODO.md item 5, which takes over the tiers thread's drafts. Send nothing to the grid until I say otherwise. When I answer idk, take the option you recommend. Do not copy anything from SchwingNet or bordercall into a public place, and put no career material in git., literally just update the handoff and push i have like no tokens left, if you have to make issues or something u can do that") and of 11:42 UTC ("continue the checkpoint, workpush, handoff update"). Those standing words hold over sections 1, 2 and 5 below.

What changed since this page was written, all of it in the private repositories: item P was widened at 08:10 UTC to four papers and five steps a to e (bordercall TODO.md as pull request 3 merged it); steps a and b are merged (bordercall pull requests 3, 4 and 5); step c is bordercall pull request 6, merged as it stood at 13:33 UTC and unfinished, whose body lists what is left; the owner's queue of 09:44 UTC follows step e. The state and the owner's words are the first section of SchwingNet's docs/checkpoints/2026-10-27-restart-kit/README.md and memory/priority-panjabi-first.md beside it. The first prompt of section 5 is sent with these changes:

- Its item 3 reads: Start one thread, and only one, titled "Flesh out Panjabi, rewrite in PyMC": it reads the first section of SchwingNet's docs/checkpoints/2026-10-27-restart-kit/README.md, then bordercall's README.md and TODO.md, item P as widened, and continues item P from bordercall pull request 6's body on main (step c's rest, then steps d and e, each a pull request in bordercall merged once green, then the queue of 09:44 UTC in its order); it keeps every finding in bordercall, tells me in one line with the link as each step merges, and stops when the queue is done.
- Where section 1's goal and section 2's instructions name Panjabi's three papers, read four, the articular facets paper of 1993 added, and the steps a to e.

## 1. The project's goal

What the new project is for, to paste where claude.ai asks for it when the project is made:

```
Goal: name every vertebra in a limited field of view correctly, on real held-out fluoroscopy and X-rays or on synthetic images no test can tell from real ones, for the normal spine and every anomaly class. This project continues the project symphony (once symphony_3) on a new account; everything it needs is in git.

Now, and alone until I say otherwise: flesh out Panjabi. In OpenSpineConsortium/bordercall, TODO.md item P: transcribe every remaining table and measure of Panjabi's three papers (cervical 1991, thoracic 1991, lumbar 1992), past what a SPINEPS segmentation measures easily, and score how much the added measures raise naming accuracy, at 1, 3 and 9 bodies and per phenotype. The findings stay in bordercall; report to me and stop when the work has merged.

Next, only when I say so: gold tier 1, 2 and 3 data (bordercall TODO.md item 5), to test the naming rule on segmentations of real spines counted from C2.

Later, each only on my word:
1. Finish the paused work: textbook chapter 36 and the CNS junction slides, the gold and silver tier census, the DRR comparison, the shared textbook door.
2. SchwingNet issue #391: the full FleXray audit with my fork OpenSpineConsortium/FleXray, the test flexray+optimal_window_width_count_from_anchor, FleXray's integration (rendering, inference, fine-tuning, rare-variant classes) and its limits, resolution first; then the state of the art on full-spine panoramas, my anchor-counting protocol, the results explorer and the figures. The licence and patent question is mine.
3. Flux realism: a reproducible fine-tuned FLUX.2 klein edit, built as blocks, that matches FluXray numerically; then held-out gold paired CT and fluoroscopy with SPINEPS labels, until a statistical test cannot tell synthetic from real; then rare-class augmentation of anomalous full spines, found where there is no ground truth by counting between the transition points and the anchors with bordercall's separator.
4. Last: SPINEPS segmentations, enhanced DRRs of the rare anomalies and my anchor-counting algorithm together, for 100% accurate limited-field naming on real held-out fluoroscopy, normal and every anomaly class.
```

## 2. The project's instructions

The instructions the project symphony ran under, brought up to the owner's priority (section 3 lists every change). The coordinator writes them from this section if the field is left empty (section 5, step 1):

```
Priority, in force until I say otherwise: work on nothing but fleshing out Panjabi in OpenSpineConsortium/bordercall, TODO.md item P (every remaining table and measure of Panjabi's three papers, scored for how much more measurement raises naming accuracy), in one thread, with its findings kept in bordercall. Then, only when I say so, gold tier 1, 2 and 3 data (bordercall TODO.md item 5). Nothing goes to the grid until I say otherwise. Section 0 of symphony-template's docs/research/handoff-2026-10-27-checkpoint-4.md and SchwingNet's docs/checkpoints/2026-10-27-restart-kit/ say the rest.

Waits behind the priority until I say otherwise: SchwingNet issue #391. Its full audit of FleXray comes first, with my fork OpenSpineConsortium/FleXray, the test flexray+optimal_window_width_count_from_anchor and FleXray's full integration into the workflow (rendering, inference, fine-tuning, rare-variant classes); the licence and patent question is mine to decide. Then the state of the art on full spine panoramas, my anchor-counting protocol, the results explorer and the figures. Only tasks the audit needs in order to work come before it.

Repos: symphony-template, SchwingNet and bordercall are attached. When a task needs another, add it with add_repo (owner OpenSpineConsortium): FleXray, PlotNeuralNet, spine-datasets, spine-program, hpcworker, symphony-protocol-canary, symphony-app, symphony-start, symphony-marketplace, symphony-extension, coordbench, flowbench, openspineconsortium.github.io, beethoven-*, Onedrive; and Gregory-Schwing-MD-PhD/spinesurg-ct-nnunet.

Rules:
- One thread only, on the priority above, until I say otherwise. When I widen it, extra threads should be knowledge synthesis, finalizing work, or paired CT/X-ray datasets.
- One PR per change, from the thread's own branch. Run bash scripts/check.sh first where it exists. Merge once green on my standing permission; if the org approval rule blocks it, tell me to tick the bypass box.
- Never approve, publish or change a symphony-protocol release or its gate without my own words. Never push to or force-push a default branch. Flat-rate subscriptions come first. Every feature runs entirely on flat-rate subscription accounts, and none needs an API key. Where a key is allowed, one per purpose and listed in docs/setup/keys.md with its owner and location, the subscription takes priority by default and a setting may change the order. No key is ever pasted. A key that a service can make at sign-in is made by a one-click sign-in that the owner's own app completes, and stays on the machine that uses it; a value no sign-in can make is kept as an encrypted GitHub secret, under secret scanning and push protection, and reaches that machine by the key route. No credential is ever in git, an issue, a log, a URL or browser code, and contributors' credentials are never held. Dataset tokens (Kaggle etc.) may be handled in development but never in repos or public logs.
- Grid: check jobs with the status word (schwingnet-status via grid-accounts.yml, action=job) before any resend. No fetch, grid job or training without my word and the count. Every fetch must know its exact size first and is refused if it would pass the 22 TB oschome quota.
- SchwingNet's and bordercall's research notes are confidential and never leave them; bordercall stays private until the provisional is filed.
- Commit findings under docs/research/ in symphony-template with a line in its README.md, by PR, before you stop; SchwingNet's and bordercall's findings stay in their own repositories instead.
- Every manual step for me: numbered, in the reply text, with exact link and what to click.
- If something you need is missing, say exactly what and stop.
- Docs (docs.yml) in SchwingNet and symphony-template builds only when I start it; never start it or give it another trigger. Cut Actions minutes wherever a job re-proves what nothing changed.
- Personal career material (CV, cover letters) never goes in git.
- When I say checkpoint: every thread pushes, opens a draft PR for unfinished work, writes a handoff, and stops.

Standing rules from my words:
- When I answer idk, take the option you recommend. Ask only where a rule needs my own word or count, once, as a decision card, and keep working meanwhile. Never give me a step that only moves or edits text.
- Truth for a level name comes only from full spines countable from C2 to the pelvis; nothing is reported on the 802 CTSpinoPelvic1K columns.
- SPINEPS for production segmentations, reusing the masks already on the grid, never re-run and never TotalSegmentator; MOOSE only to replicate FleXray's dataset; the segmenter is a configurable block, and the label schemes are mapped correctly everywhere.
- No arbitrary constraints on the naming problem: build a series of solutions and report each one's accuracy per phenotype.
- Figures look like Benzel's, drawn by committed code from recorded inputs; in a deck, 3D renders rather than sideways bar charts. No uploads to OneDrive; figures stay in the repositories.
- Evidence tiers: gold shows C2 to the sacrum in one study, silver is partial; 1 is a real CT paired with a real X-ray of the same person with human annotation, 2 the pair without, 3 one modality with human annotation, 4 without; machine masks and synthetic images never raise a tier; experiment power comes from gold data where possible.
- Results may be shown, the method may not, until the provisional is filed and the technology transfer office has read the decks. My text wins in my white paper; corrections go in only as narrow, checked edits. My uploaded papers are read, never committed.
- The textbook needs no step from me: readers load the repository live, never a staged copy.
```

## 3. What changed from the instructions the project symphony ran under, and why

Every rule is kept word for word except these:

1. The first line, the goal of #391 ("Goal first, the lab's objective from now on: ..."), now waits behind a new first paragraph, the owner's priority of 05:48 UTC on 2026-10-27 (handoff-2026-10-27-checkpoint-4.md, section 0). Its own words are kept after "Waits behind the priority until I say otherwise:".
2. Repos: bordercall (OpenSpineConsortium/bordercall, private) is attached from the start, since the priority's work is there; the on-demand list is unchanged.
3. "No fixed thread cap; ..." becomes "One thread only, on the priority above, until I say otherwise", the owner's gate of section 0, with the old line's guidance kept for when the owner widens it.
4. "SchwingNet research notes are confidential and never leave SchwingNet" names bordercall too, which is under the same rule until the filing.
5. "Commit findings under docs/research/ in symphony-template ..." gains the exception the confidentiality rule already implied, so that item P's findings stay in bordercall as section 0 says.
6. "Standing rules from my words" is new: the owner's standing rules since 2026-10-25 (handoff-2026-10-27-checkpoint-4.md, section 4, without its one-off decisions of 2026-10-27), which the project symphony held only in its memory and the checkpoint pages. Instructions load into every thread; memory is read only when a thread looks.

## 4. Repositories

Attach these three when the project is made:

- OpenSpineConsortium/bordercall (private): https://github.com/OpenSpineConsortium/bordercall, where the priority's work is.
- OpenSpineConsortium/SchwingNet (private): https://github.com/OpenSpineConsortium/SchwingNet, the confidential memory, findings and handoffs.
- OpenSpineConsortium/symphony-template: https://github.com/OpenSpineConsortium/symphony-template, the restart pages and grid-accounts.yml, through which every grid word goes.

The rest come on demand, by add_repo, as the instructions' Repos line lists them: FleXray, hpcworker and openspineconsortium.github.io first when the paused threads come back (the anomaly route and Flux realism need hpcworker's gate, the shared door the site), spine-datasets for the tiers census, PlotNeuralNet for the figures of #391.

## 5. The first prompt

Rewritten at 07:55 UTC on the owner's ask of that time: "can you literally do nothing else besides rewrite the first prompt to also account for panjabis fourth paper, articular facet 3d morphometry, expose how you are getting teh numbers out of the panjabi paper so they can be verified as true, and then refactor the code to be able to use scalable, meaning datastructures/formats that are optimized to work with pyMC, and then rewrite this in pyMC". Sections 1 and 2 are left as they were, still naming three papers; the prompt has the coordinator widen them, and holds over them where they differ. The facet paper's PDF is in none of the project's repositories, so the owner attaches it (section 6, step 6).

Sent as the first message in the new project's chat, or after the earlier first prompt where that was sent already:

```
You are picking up the project symphony from an earlier project on another Claude account; everything it needs is in git. Read, in order: OpenSpineConsortium/symphony-template docs/research/restart-kit-2026-10-27.md on main; section 0 of docs/research/handoff-2026-10-27-checkpoint-4.md beside it; then OpenSpineConsortium/SchwingNet docs/checkpoints/2026-10-27-restart-kit/README.md on main. Where they and this message differ, this message holds: it widens the Panjabi priority from three papers to four and adds the steps of item 3 below. Then:
1. If this project's instructions are empty or differ from section 2 of the restart-kit page, write them from that section verbatim, except that where it names Panjabi's three papers you write four, the articular facets paper of 1993 added, and you add the steps of item 3 to the priority. Change the goal the same way if you can edit it; if you cannot, this message stands over it.
2. Write every file of SchwingNet's docs/checkpoints/2026-10-27-restart-kit/memory/ into this project's memory as it stands, its MEMORY.md as the index, except that priority-panjabi-first is widened the same way. FINDINGS.md beside that folder is the research record those files point to; read it when a thread needs it, and do not copy it into memory.
3. Start one thread, and only one, titled "Flesh out Panjabi, rewrite in PyMC"; if this project already has a thread on bordercall's item P, send it this item instead of starting a second. The thread reads section 0 of the checkpoint-4 page and of SchwingNet's docs/checkpoints/2026-10-27-morning/README.md, then bordercall's README.md and TODO.md, and does bordercall TODO.md item P widened as below, in this order, each step a pull request in bordercall merged once green, the first of them writing this widened item P into TODO.md:
   a. Four papers. The fourth is Panjabi MM, Oxland T, Takata K, Goel V, Duranceau J, Krag M, "Articular facets of the human spine: quantitative three-dimensional anatomy", Spine 1993;18(10):1298-1310 (take the citation from the PDF's own first page). Its PDF is not in bordercall yet: I attach it to this message or send it later, and the thread commits it to archive/bordercall/reference/papers/ beside the other three and adds it to papers/README.md's table map. Until it is there, the thread does every other step and says once that the facet tables wait for the PDF.
   b. Show where every number comes from, so I can check that it is true. One provenance file, one row per printed value of the four papers, every value already in the reference CSVs included: the paper's file and its sha256, the PDF page and the printed page, the table, the row and column labels, mean or standard error, the string exactly as printed, the value and its units, the cell's box on the page as rendered at a stated dpi by a committed command, and what each of two independent reading passes read. A Markdown page in bordercall, which GitHub shows with its images, sets every value beside the image of the cell it was read from and says plainly how the numbers were read: rendered pages read by eye by Claude, twice, never by text extraction. Tests fail when the two passes disagree, when a value the papers also state in prose disagrees, or when a CSV holds a value the provenance file does not. List every existing value that changes.
   c. Refactor for PyMC and for scale. Build bordercall TODO.md items 1 and 2 (the package schwingcheck/ and one object per measure) on data shaped for PyMC: the checked table as one long CSV, one row per value with its kind (length, area or angle) and its planes, loaded into an xarray Dataset with named dimensions (level, measure, side); columns, synthetic or real, as arrays (column, body, measure) with NaN for a missing value and integer offsets for gaps; results as ArviZ InferenceData in NetCDF, with the command, the seeds and the digests in its attributes; the code vectorised, with no loop per body or per field, so one call names thousands of fields and the measures can grow past twenty. The archive's 222 tests still pass.
   d. Rewrite the naming rule and the column generator in PyMC. PyMC and the packages it brings (PyTensor, ArviZ, xarray and theirs) are allowed as new dependencies of bordercall by my word of 2026-10-27, pinned to exact versions; nothing else new. The current NumPy code stays as the reference, and tests prove the rewrite before anything new is scored with it: on the seven measures and the same fields the PyMC rule gives every field the same answer as the current code (to 1e-6 where it integrates the same way, within Monte Carlo error where it samples); the PyMC generator's columns match the current generator's in distribution, within Monte Carlo error; and rescoring seed 97's 2,000 columns reproduces the record's rates at 1, 3 and 9 bodies (archive/records/exact-2026-10-26/exact.json).
   e. Only then add the new measures, the facets' among them, to the PyMC model, each kind as item P step 4 says, and score them as item P step 5 says, at 1, 3 and 9 bodies and per phenotype.
   The thread keeps every finding in bordercall, tells me in one line with its link as each step merges, and stops after step e.
4. Restart none of the paused threads and start nothing else until I say so. When I name the next item, it is gold tier 1, 2 and 3 data, bordercall TODO.md item 5, which takes over the tiers thread's drafts.
Send nothing to the grid until I say otherwise. When I answer idk, take the option you recommend. Do not copy anything from SchwingNet or bordercall into a public place, and put no career material in git.
```

## 6. The owner's steps

1. Only if the new project is on another Claude account: open https://claude.ai/connect-github, click Connect, sign in to GitHub as Gregory-Schwing-MD-PhD and click Authorize. The Claude GitHub App is already on every repository of the organization.
2. Open https://claude.ai/code, click Projects in the sidebar and make a new project named symphony. Where it asks what the project is for, paste the goal of section 1.
3. When it asks for repositories, pick OpenSpineConsortium/bordercall, OpenSpineConsortium/SchwingNet and OpenSpineConsortium/symphony-template (section 4). If bordercall is not offered, open https://github.com/organizations/OpenSpineConsortium/settings/installations, click Configure beside Claude, make sure bordercall is covered (All repositories, or tick it under Only select repositories), click Save, and pick it again.
4. Leave the instructions empty: the first prompt has the coordinator write them from section 2. Paste section 2 into the instructions yourself only if you would rather.
5. In the project's chat, send the first prompt of section 5 as it stands. If the earlier first prompt was sent already, send this one too: it widens the thread that is running instead of starting a second.
6. Attach the facet paper's PDF to that message with the paperclip beside the message box. If you do not have it, open https://wayne.illiad.oclc.org/illiad/logon.html, log in with your AccessID, click New Request, choose Article and enter the citation of the prompt's step a; when the PDF arrives, attach it to any message in the new project's chat. The thread does every other step meanwhile.

Not needed for the priority, and still open from handoff-2026-10-27-checkpoint-4.md, section 5: the Microsoft 365 connector on a new account (https://claude.ai/customize/connectors, click Microsoft 365, click Connect, sign in with the Wayne State account) before any mail work; the owner's own textbook door; the FLUX.2 klein 9B licence; the technology transfer office's read of the decks; the Outlook draft to the scoliosis registry; the steps of handoff-2026-10-25-checkpoint-2.md, section 4. Each waits until the work that needs it comes back.

## 7. Where the memory and the findings are

In the private OpenSpineConsortium/SchwingNet, docs/checkpoints/2026-10-27-restart-kit/, which stays there:

- README.md: what the folder holds and how the new coordinator loads it.
- memory/: the project's memory compacted into one file per subject, with MEMORY.md as the index, written in the shape a claude.ai project's memory takes so the coordinator copies each file as it stands. The superseded checkpoints and history of the project symphony's memory are dropped; the owner's words stay word for word in docs/checkpoints/2026-10-27-morning/project-memory/.
- FINDINGS.md: every study's results, each with the record it rests on: the naming studies in bordercall, the FleXray audit and its anomaly route, Flux realism, the DRR comparison, the corpus tiers and the held data, the textbook door, and the grid counts with what was sent.
