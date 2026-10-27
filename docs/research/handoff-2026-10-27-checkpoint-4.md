# Handoff of 2026-10-27 at 04:50 UTC: every thread of the project, and how to restart

Source: the thread "Plan the FleXray audit for #391" in the claude.ai project symphony (https://claude.ai/code/project/chan_014WUU19NHgHPhf7QetT9cbS), written between 04:50 and 05:30 UTC on 2026-10-27 at the owner's checkpoint of 04:47 UTC, "YO PLEASE CHECKPOINT ALL SESSIONS AND PUSH ALL FILES AND WRITE A HANDOFF SO A NEW ACCOUNT CAN PICK UP WHERE THESE LEFT OFF!", on the coordinator's word that this thread writes the project-wide page. It is taken from each thread's own messages and checklist, the pull requests and branches of SchwingNet, bordercall, symphony-template and the site, each thread's handoff as its pull request carries it, the grid branch's records and the project's memory. No secret, token or credential is written here, and no career material. SchwingNet's and bordercall's confidential notes and handoffs are named by path only; they live in those private repositories and never leave them.

This page is the entry point and replaces handoff-2026-10-26-checkpoint-3.md as such; where the two differ, this page holds. Section 0 was added after the rest, on the owner's word of 05:48 UTC, and it overrides every other section.

## 0. The owner's priority: nothing else until the owner says otherwise

At 05:48 UTC on 2026-10-27, after this page was first written, the owner set the order of the new account's work, in the CNS thread. The goal of SchwingNet issue #391 (the section "First" of handoff-2026-10-25.md) waits behind this section until the owner says otherwise, and so does everything else on this page.

1. **First, and alone: flesh out Panjabi's tables in bordercall.** That is item P of bordercall's TODO.md, whose README.md opens with the same priority (bordercall's main, 7015802 and after). The work is bordercall's and needs no grid, no CT and no fetch; no grid job, fetch or training is approved for it. Its findings stay in bordercall, and nothing of it goes to symphony-template. The thread works in archive/bordercall and starts no other item of bordercall's TODO.md. When item P's work has merged, it reports the results to the owner and stops.
2. **Then, only when the owner says so: gold 1, 2 and 3 data** for testing bordercall's rule on real spines. That is item 5 of bordercall's TODO.md. The tiers are the owner's of 03:06 UTC (section 4). The thread for this item takes over the tiers thread's drafts and handoff (section 2), and no other thread of section 2 restarts with it. bordercall's approved grid pilot (section 3) belongs to this item and stays unsent until the item starts.

Until the owner says otherwise, none of section 2's other threads is restarted. Their pull requests stay as they are, and nothing is sent to the grid for them, approved or not. The DRR comparison's segmentation job that was running at the checkpoint (Slurm 40799505) is left to end on its own. Sections 1 to 6 below are the record each of those threads restarts from when the owner says so. bordercall's old paths, here and in the threads' handoffs, start with archive/ since bordercall bb86584. Section 0 of SchwingNet's docs/checkpoints/2026-10-27-morning/README.md gives both items in full: what is transcribed already, where the earlier studies left off, and what gold data is held and pending.

## 1. How to restart, from a new project

The restart kit of 2026-10-27, restart-kit-2026-10-27.md beside this page, gives the new project's goal, its instructions and the first prompt ready to paste, with the memory compacted in SchwingNet's docs/checkpoints/2026-10-27-restart-kit/; its first prompt and steps replace those below, and this section stays as the record.

A new claude.ai project sees none of the old one's shared files, memory or threads, so what only the project symphony held was copied at this checkpoint into SchwingNet's docs/checkpoints/2026-10-27-morning/ (on main since SchwingNet #421 merged at 05:06 UTC): the project's memory word for word as ASCII, this thread's handoff, and a README that names every other thread's handoff by path and says where each of the project's shared files went. That folder is confidential and stays in SchwingNet. Everything else is in git already: the repositories, their pull requests and boards, the grid and its words, the GitHub Apps and the secrets belong to no Claude project or account. Section 6 says what lives nowhere in git.

### The owner's steps

1. Only if the new project is on another Claude account: open https://claude.ai/connect-github and connect GitHub as Gregory-Schwing-MD-PhD. Then open https://claude.ai/customize/connectors, click Microsoft 365, click Connect and sign in with the Wayne State account, so a thread can read and draft the [XR/CT Imaging Research] mail.
2. Open https://claude.ai/code, click Projects in the sidebar, make a new project (of docs/setup/claude-project.md only the parts on the plan and the name apply: this project attaches three repositories on purpose, and its coordinator writes the instructions), and attach OpenSpineConsortium/symphony-template, OpenSpineConsortium/SchwingNet and OpenSpineConsortium/bordercall when it asks for repositories. Leave its instructions empty: the coordinator writes them in the next step.
3. In the new project's chat, send the first prompt below as it stands.

### The first prompt

```
You are picking up the "symphony" project from an earlier project, perhaps on another Claude account. First read docs/research/handoff-2026-10-27-checkpoint-4.md in OpenSpineConsortium/symphony-template on main, section 0 first: it is my priority and it overrides the rest of that page. Then, in order:
1. Write this project's instructions yourself: section 0 of the checkpoint-4 page at the very top; then section 2 of symphony-template's docs/research/handoff-2026-10-25.md, verbatim, except that its line "No API key or Claude credential anywhere." is replaced by the key rule in section 0 of handoff-2026-10-25.md and its line "No fixed thread cap; ..." by "One thread only, on the first item of section 0, until I say otherwise."; then the goal line of handoff-2026-10-25.md's section 11, step 3, marked "waits behind section 0 until I say otherwise"; then the standing rules of section 4 of the checkpoint-4 page (not its one-off decisions of 2026-10-27). Attach OpenSpineConsortium/FleXray, OpenSpineConsortium/bordercall, OpenSpineConsortium/hpcworker and OpenSpineConsortium/openspineconsortium.github.io with add_repo, and the other repositories the Repos line of that section 2 lists when a thread needs one.
2. Read SchwingNet's docs/checkpoints/2026-10-27-morning/README.md on main, section 0 first, and write into this project's memory whatever in its project-memory/ folder still holds.
3. Start one thread, for the first item of section 0 alone: fleshing out Panjabi in bordercall, told to read section 0 of both pages, then bordercall's README.md and TODO.md, item P; to keep its findings in bordercall; and to report to me and stop when item P's work has merged. Start no other thread and restart none of section 2's threads until I say otherwise. When I do, the second item of section 0 comes next, and section 2's threads come back only on my word.
Send nothing to the grid until I say otherwise. When I name the next item, send only the approved counts of section 3 of the checkpoint-4 page that item needs, each word once and only after reading the grid's status record, and ask me for any other count once, as a decision card. Never give me a step that only moves or edits text. When I answer idk, take the option you recommend. Do not copy anything from SchwingNet or bordercall into a public place, and put no career material in git.
```

### What every restarted thread does

1. It reads, in order: this page, section 0 first, which decides whether the thread may run at all; its own handoff (section 2 names each by path); SchwingNet's docs/checkpoints/2026-10-27-morning/README.md and the project memory copied there; the section "First" of handoff-2026-10-25.md; then SchwingNet's board (`git fetch origin +refs/heads/board:refs/remotes/origin/board && git show origin/board:STATE.md`). symphony-template has no board branch. The copied MEMORY.md was last kept on the evening of 2026-10-26 in places (its grid lines, its thread list, which lacks the tiers thread); where it and this page's sections 2 and 3 differ, this page holds. A project with several repositories runs none of their hooks, so no push guard and no board at session start: read the board by hand and keep the push rules of .claude/rules/board.md yourself.
2. Before any grid send, it reads logs/job-schwingnet-status.json on symphony-template's branch grid. The newest status read is 2026-10-27 04:08 UTC: 17,597 GB used of 21,990 GB, 4,393 GB of room for a new fetch, nothing owed to running fetches, one job running (section 3). The status word is sent again only once a stage needs a fresh read, never twice for one read.
3. It runs checks as each repository's memory says: symphony-template's `bash scripts/check.sh` in the clone; SchwingNet's only in a throwaway copy, with beartype, icontract and pydantic in a venv, and CI's check and gate jobs as the verdict for the steps that need pixi. SchwingNet's gate proves only what a change reaches (beethoven-qa 9.0.0), and since 10.0.0 (#413) an unproven entry in pyproject.toml reaches nothing; a change to pixi.toml, pixi.lock, vendor/ or another pyproject key still re-proves every module, 30 minutes or more before a push.
4. It merges a pull request once its checks are green, on the owner's standing permission, with the head sha copied from git, and reads main afterwards. It marks a SchwingNet pull request ready in a call of its own.
5. It keeps the owner's rules (section 4): no fetch, grid job or training without the owner's word and count; every fetch sized first against the quota; SchwingNet's and bordercall's notes never leave them; docs.yml runs only when the owner starts it; a key only as the key rule in the project's instructions allows (section 0 of handoff-2026-10-25.md), and never a Claude credential in git, a log or a URL; no OneDrive upload.
6. Before any dispatch it checks the newest Actions run's annotation: from about 21:00 UTC on 2026-10-26 to 03:10 UTC on 2026-10-27 every job in the organization failed unstarted on a billing limit, which the owner then raised. A word that failed that way never ran and may be sent once more.

### If the project symphony itself is still open

The same work can go on there instead: in its project chat at https://claude.ai/code/project/chan_014WUU19NHgHPhf7QetT9cbS, send "Resume from symphony-template docs/research/handoff-2026-10-27-checkpoint-4.md, section 0 first. Put that section at the top of this project's instructions, mark the #391 goal line as waiting behind it, and replace the thread-cap line with 'One thread only, on the first item of section 0, until I say otherwise.' Then start one thread on its first item alone, fleshing out Panjabi in bordercall, restart no other thread until I say otherwise, and send nothing to the grid."

## 2. The threads at the checkpoint

Six threads have work open and one is done. Each was told by the coordinator at 04:47 UTC to push, open a draft pull request for unfinished work, write its handoff and stop. None of them is restarted until the owner says so (section 0); the first item of section 0 is new work in bordercall, after the studies the CNS thread below ran. A branch's head may have moved after this page was written; the pull request is the record.

### Plan the FleXray audit for #391 (this thread): open

- Merged since the last checkpoint: SchwingNet #410 (the pack stage) and #412 (the folder of the last checkpoint); symphony-template #498 (the last restart page). SchwingNet #421, this checkpoint's folder, merged at 05:06 UTC; this page comes in symphony-template #501 from claude/project-thread-x16ebc.
- Grid: nothing sent since the last checkpoint. The timing stage sent at 00:16 UTC on 2026-10-26 (Slurm 40785227) ended FAILED after 30 minutes, exit 1, by the status read of 2026-10-27 04:08 UTC; its report is not read, so the cause is not known. The pack stage cannot go until a timing report ends in exit 0.
- Its handoff: SchwingNet docs/checkpoints/2026-10-27-morning/anomaly-route.md, with the next session's steps in order. The first is to send the timing word once, which both prints the failed report and queues the stage once more at the current checkout. The timing code is the same at that checkout as in the failed run, so the rerun helps only if the node was at fault; it waits behind the DRR thread's running job, then holds the gate's checkout for up to 4 hours, so tell the DRR thread first; cancel the rerun at once if the report shows a fault in the code. That page says how.

### Compare FleXray DRRs to real X-ray corpora: open

- Merged since the last checkpoint: SchwingNet #401 (the DRR domain-gap study and the configurable segmenter block, src/schwingnet/segmenters.py), #413 (beethoven-qa 10.0.0), #414 (the segmentation job's environment); symphony-template #493 (the public method note) and #499; beethoven-qa #15 (10.0.0), beethoven-research #8 and beethoven-agents #6, so every repository in the organization that carries beethoven-qa is on 10.0.0, as the owner asked at 03:09 UTC on 2026-10-27.
- Open: SchwingNet #418, a draft from claude/project-thread-d14v3r: the study run from the CT alone where no mask is needed, the owner's question of 04:15 UTC on 2026-10-27.
- Its handoff: SchwingNet docs/checkpoints/2026-10-27-drr-comparison/HANDOFF.md on that branch (the earlier one, docs/checkpoints/2026-10-26-drr-comparison/HANDOFF.md, is on main).
- Grid: both approved fetches landed on 2026-10-26. The segmentation word went four times: Slurm 40790826 (2026-10-26 16:37 UTC, failed after 3 minutes for a missing module, fixed by #414), 40799410 (queued by the resend of 2026-10-27 03:13 UTC, cancelled at 03:16), 40799494 (03:37 UTC, cancelled at 03:38) and 40799505 (03:40 UTC at 6b2daf4, running at 04:08 UTC). Only 40799505 ran the segmentation; the owner chose at 04:31 UTC to keep it running, and whether the failed and cancelled ones spent the count is the owner's to say. The comparison job is unsent and goes once, only after the segmentation job has ended and its report reads well. While that job runs, its hold keeps the gate's checkout at 6b2daf4 for every word.

### Finish CNS slides with junction predictor: open

- Since the last checkpoint the thread ran the studies bordercall's HANDOFF.md steps 7 to 11 record, built two five-slide decks in bordercall (the CNS one results only), and copied the owner's white paper (a Claude Doc on the owner's account, at revision 189) into bordercall with its records; the CNS thread's handoff names the Doc and the copy's path. bordercall's main was bed7516 at the checkpoint (the paper's copy landed in df976d7, the handoff note in bed7516); on the owner's words of 05:17 and 05:24 UTC the thread then moved all of it under archive/ (bb86584) and wrote a new README.md and TODO.md, and after the word of 05:48 UTC it put section 0's priority at their top (7015802); bordercall #2, hpcworker #50 and symphony-template #495 merged.
- Open: SchwingNet #416, a draft from claude/project-thread-7qoboa: the textbook chapter 36 that carries the white paper, with five figures drawn by committed code. An adversarial review confirmed about twenty defects in the thread's own framing and figures, none in the owner's text; they are listed with their fixes beside the handoff.
- Its handoff: SchwingNet docs/checkpoints/2026-10-27-cns-junction/README.md and review-findings.md on that branch, after the earlier docs/checkpoints/2026-10-26-cns-junction/README.md on main and bordercall's HANDOFF.md.
- Grid: the 2 CPU jobs of section 3 are unsent and wait for section 0's second item; their pass-through (hpcworker #50) merged after the last `update`, so when that item starts they go after one `update` and a status read, the pilot first.

### Let readers open the live front door (once "Stage the textbook for this project"): open

- Merged: SchwingNet #415 (docs/research/reader-access.md: who the claude.ai door can serve). The claude.ai door serves the owner alone, since claude.ai gives an artifact's connectors only to the owner's own organization; the shared door becomes a page on the organization's site that each reader opens signed in with GitHub, reading with that reader's own access.
- Open: the site's draft https://github.com/OpenSpineConsortium/openspineconsortium.github.io/pull/147 (the reader at /symphony/door/, not yet reviewed) and SchwingNet #419, a draft from claude/project-thread-24opi2 (the repository's starting points, .github/symphony/door.json, and the handoff).
- Its handoff: SchwingNet docs/checkpoints/2026-10-27-door-for-readers/HANDOFF.md on that branch: the browser test to write, the three adversarial reviews (security first, since a reader's token sits on the control panel's origin), the merge, and the owner's one-time step after it. The owner's steps for the owner's own door are still those of docs/checkpoints/2026-10-26-front-door/HANDOFF.md, its section "The owner's remaining steps, in order" (this page's section 5, step 1).

### Finetune Flux Realism for X-rays: open

- Merged: SchwingNet #406 on 2026-10-26 at 03:51 UTC (the realism module, its tool, the grid word `realism <stage>` and the fetch rows); nothing of the work is left on a branch.
- Merged at the checkpoint: SchwingNet #417, which brought the handoff up to it.
- Its handoff: SchwingNet docs/checkpoints/2026-10-26-flux-realism/HANDOFF.md, whose section "State at the second checkpoint" holds.
- Grid: nothing sent. The dataset it needs landed through the DRR thread's fetch and is not fetched again. On restart: a status read, then the four fetches that may go now, each once, then the four GPU jobs each once in turn; the 9B model's fetch waits on the owner's licence click (section 5, step 2). Before the first GPU job: hpcworker's grid gate (tools/grid_gate.sh, its JOBS_RE) does not yet admit `schwingnet realism <stage>`, so an hpcworker pull request that adds realism, as hpcworker #50 did for bordercall, merges first, then `update`; the fetches do not wait on it, and the thread's own handoff does not say this.

### Sort the corpus into gold and silver tiers: open

- Started at 03:07 UTC on 2026-10-27 on the owner's tiers of 03:06 UTC (section 4): every source of the corpus sorted into gold 1 to 4 and silver 1 to 4, a person counted once at the best tier, with a per-case sorter, a census grid word and the power of each planned experiment per tier still to come.
- Open: SchwingNet #420, a draft from claude/project-thread-cdwl0r (the tier table of 310 sources, the per-case sorter and power tool, the census grid word, the research page and the dataset records brought up to date), and symphony-template #500, a draft from the same branch name (the public method note docs/research/corpus-evidence-tiers-2026-10-27.md, which names no holdings). Neither has run its check or carries its adversarial review yet.
- Its handoff: SchwingNet docs/checkpoints/2026-10-27-corpus-tiers/HANDOFF.md on claude/project-thread-cdwl0r: apply the last lens's adjudicated corrections, rebuild the table, run the checks, write the reviews, merge both, then ask for the census job.
- Grid: the census is one CPU job the owner has not counted; it is asked once, as a decision card, after its code merges.

### Add fetch size readers for #163: done

Resolved on 2026-10-26 at 01:58 UTC; SchwingNet #400 and symphony-template #496 merged. What it could not verify from a container is in SchwingNet's docs/research/exact-fetch-sizes.md.

### Not this project's

SchwingNet #264, a draft from an earlier session, is still open; its branch claude/263 is gone from origin, so it cannot be updated as it stands.

## 3. The owner's recorded answers and counts

| Work | Approved, by the owner's word | Sent |
| --- | --- | --- |
| The anomaly route of #391 | 15 grid jobs, 2 CPU and 13 GPU, no fetch (2026-10-25 21:22 and 22:30 UTC); the words `schwingnet-anomaly-<stage>`, each once, each once its code has merged and the stage before ended well, the fold jobs only after the main tune and eval look sane | 2 of 15: select (2026-10-25 23:42 UTC, Slurm 40785048, exit 0) and timing (2026-10-26 00:16 UTC, Slurm 40785227, FAILED, report unread; the gate queues it once more when its word is sent again) |
| The production segmentation array of the route | no count; the timing report's estimate goes to the owner once, as a decision card | none |
| The required test of #391, item 13 | 1 GPU and 1 CPU job, every setting in one job (2026-10-25 20:49 UTC), after the inventory and the code the item brings in have landed, with a line to the owner first | none |
| The two benchmark reruns (FleXray and xvr on DeepFluoro) | approved on 2026-10-25; their fixes are on SchwingNet's main; no thread holds them | none |
| The bordercall measurement | 2 CPU jobs (2026-10-25 about 23:56 UTC): the pilot first, then full only if the pilot ends well; both wait for section 0's second item | none |
| The DRR comparison | 2 fetches and 2 GPU jobs (2026-10-26 about 01:19 UTC), in order, each once | the 2 fetches, both landed on 2026-10-26; the segmentation word four times (section 2), its run Slurm 40799505 from 2026-10-27 03:40 UTC, running at 04:08 UTC and kept running on the owner's word of 04:31 UTC; the comparison job unsent |
| Flux realism | 5 fetches and 4 GPU jobs (2026-10-26 about 01:58 UTC); the dataset fetch was the DRR thread's and has landed; the 9B model's fetch waits on the owner's licence click; the edit job once the fetches have landed | none of its own |
| The tier census | 1 CPU job, not yet counted; asked once as a decision card after its code merges | none |
| Scoring the CNS thread's naming rule on real segmentations | not counted; the CNS thread's handoff says what it needs | none |
| The rest of the #391 audit (items 3, 6 to 12 and 14) | waiting for the owner's word: 1 fetch, 5 GPU and 3 CPU jobs, as the plan's section 6 counts them | none |
| The six 20-epoch trials and the scaling study SchwingNet #385 | no count | none |

The job word `update` brings the gate's hpcworker clone to hpcworker's main; it was last sent at 23:41 UTC on 2026-10-25, installing hpcworker #49, which admits `schwingnet anomaly <stage>` for every stage, so the anomaly words, pack included, need no `update` (each word pulls SchwingNet's main itself unless a running job's hold stands). It goes again before the first bordercall word, since hpcworker #50 merged after it. No realism word can pass until an hpcworker pull request admits it (section 2, Flux realism), then `update`. The census word of the tiers thread is admitted already. The cancel word is `schwingnet-cancel-<job>`.

## 4. The owner's rules since the evening of 2026-10-25

Word for word in the files of SchwingNet's docs/checkpoints/2026-10-27-morning/project-memory/ (all of them, not only those MEMORY.md names) and, for the CNS thread's rules, in its handoff (section 2); here in substance, with their times, since each thread reads them first. The standing rules are those without a date of 2026-10-27; the dated ones of that day are decisions, kept so a thread knows why things stand as they do:

- 2026-10-26 00:16 UTC: only full-spine columns countable from the second cervical vertebra to the pelvis count as ground truth for a level name; every evaluation is on such columns.
- 2026-10-26 00:17 and 00:26 UTC: the production runs use the lab's own segmenter, reusing the segmentations already on the grid; the replication of FleXray's dataset uses FleXray's; the segmenter is a configurable block and the two label schemes are handled correctly everywhere.
- 2026-10-26 01:17 UTC: figures look like Benzel's (clean anatomical line drawings and plots), drawn by committed code from recorded inputs; 3D renders over sideways bar charts in a deck.
- 2026-10-26 00:13 and 00:18 UTC: no owner step ever for the textbook; the reader loads the repository live, never a staged copy. 2026-10-27 04:19 UTC: other people should see the live door as the owner does, after one publish.
- 2026-10-26 02:48 and 02:55 UTC: no upload to OneDrive; figures stay in the repositories.
- 2026-10-26 06:31 UTC: no arbitrary constraints on the naming problem; build a series of solutions and report each one's accuracy, per phenotype.
- In the CNS thread: the owner's text in the white paper wins, and corrections go in only as narrow, checked edits; the owner's uploaded papers are read, never committed or copied; results may be shown and the method may not until the provisional is filed and the technology transfer office has read the decks.
- 2026-10-27 03:06 UTC: the gold and silver evidence tiers (gold, one study showing the second cervical vertebra to the sacrum; silver, partial; 1 to 4 by whether a real CT is paired with a real X-ray of the same person and whether a person annotated it); machine masks and synthetic images never raise a tier; experiment power is reckoned from gold data where possible.
- 2026-10-27 03:08 and 03:09 UTC: beethoven-qa 10.0.0 in every repository of the organization that carries it.
- 2026-10-27 04:15 UTC: the DRR tests should run without segmentations where they need none; 04:31 UTC: keep the running segmentation job.
- 2026-10-27 04:47 UTC: this checkpoint.
- Standing: on "idk" take the recommended option; ask only where a rule needs the owner's own word and count, once, as a decision card, and keep working meanwhile; never give the owner a step that only moves or edits text; owner steps numbered, with the exact link and what to click.

## 5. The owner's open steps

1. The owner's own textbook door: the steps in SchwingNet's docs/checkpoints/2026-10-26-front-door/HANDOFF.md in order, the GitHub App, its installation and the custom connector named GitHub, then on your own computer, in your SchwingNet clone, run `git pull` and `python -X utf8 tools/textbook_publish.py local --url https://claude.ai/artifact/XYY2CdsjvyRfxQfYq2EkkV`, approve both publishes when the Artifact tool asks, open the link and allow GitHub.
2. The FLUX.2 klein 9B licence: open https://huggingface.co/black-forest-labs/FLUX.2-klein-9B, signed in as the Hugging Face account whose token the grid holds, and accept the licence on the page.
3. If the new project runs on another Claude account: the Microsoft 365 connector (section 1, step 1).
4. The technology transfer office: whether the junction slides and the two newer five-slide decks may be shown before the provisional is filed, and whether an outside reader of the shared door needs a confidentiality agreement; the CNS thread's and the door thread's handoffs say what to ask.
5. The shared door's one-time step, once its pull request is reviewed and merged: the door thread's handoff gives it with its link.
6. In Outlook's Drafts: the follow-up to a scoliosis registry's contact that the tiers thread drafted, tagged [XR/CT Imaging Research]; open Outlook, open Drafts, read it and press Send if it reads right.
7. Still open from handoff-2026-10-25-checkpoint-2.md, section 4: secret scanning's three extra checks in both repositories (its step 2); the returned dataset letter in Outlook's Junk Email (step 3); the reply drafts in Outlook's Drafts (step 4); the Bournemouth data use agreement (step 5); the NIA Biobank request when you choose (step 6); AI Scientist Pro's phase 1 after the #391 audit, by a comment on SchwingNet #397 (step 7).
8. When a thread asks, as a decision card: the production segmentation array's count with the timing estimate; the tier census's one CPU job; the rest of the #391 audit's counts.

## 6. What lives nowhere in git

- The owner's uploads to the project, each read and none committed, since each but the last is a third party's paper: the FleXray paper's LaTeX source (arXiv 2609.26756v2, 2026-10-26 00:28 UTC), a 2010 anatomy paper (08:21 UTC), two published papers on intraoperative level checking and the second one's supplement (21:31 UTC), and Radiopaedia's outcome letter on non-commercial use of its content (2026-10-27 03:06 UTC), whose terms the tiers thread recorded in SchwingNet's dataset record. A thread that needs one whole asks the owner to upload it again, once.
- The white paper's live text is the owner's Claude Doc, which belongs to the owner's account; bordercall holds its copy at revision 189 (the CNS thread's handoff names the path), so another account works from that copy until the owner shares the Doc.
- The owner's CNS deck v13, on the owner's computer only, as before; the Outlook drafts, in the owner's mailbox.
- The project's staged copy of the textbook (86 MB in its shared files): a retired design, needed by nothing.
- The grid's own files, the selections, the harvests and the job logs, on the grid as always; the record of every send is on symphony-template's branch grid.

Everything else the threads made, the decks, the figures, the records, the handoffs and the memory, is in git at the paths above; the project's shared files are matched one by one in the companion README's section 2.
