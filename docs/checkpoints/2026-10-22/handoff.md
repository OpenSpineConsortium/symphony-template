# Symphony handoff, 2026-10-22

Source: the thread "Checkpoint and handoff", 2026-10-22 at about 00:05 UTC, on the owner's order at 00:01 UTC to stop every thread, checkpoint and write a handoff so he can continue on another Claude account (the first account at 97% usage). It is written from each live thread's stop summary (00:01 to 00:03 UTC), the coordinator's notes, the organization's open pull requests read by GitHub search, the Project's artifact list and the Project memory. It replaces docs/checkpoints/2026-10-19/handoff.md as the place to start. Beside it: memory.md (the Project memory index at the handoff), topic-memories/ (eighteen topic memories; the patent and SchwingNet ones stay out of this repository) and grid-slurm-protocol.md (the Beethoven grid thread's own handoff, with the promoter-restart spec).

Every block below is copied whole, without the fence lines.

## 1. Project instructions

Where: claude.ai, the new account's Project, Settings, the Instructions field. Paste and press Save.

```
One pull request per change, from the thread's own branch. Run bash scripts/check.sh first where the repository has it. Run an adversarial review before each substantive pull request. Merge once green, on my standing permission. Never approve, publish or change a symphony-protocol release or its approval gate without my own words. Never push to or force-push a default branch. No API key and no Claude credential anywhere. If something you need is missing, say exactly what in your first message and stop. Ask me before anything marked mine. Every manual step you give me needs its exact link and what to click.
Commit what you find, intermediate or final, under docs/research/ in symphony-template with its line in docs/research/README.md, by pull request, before you stop.
Put every manual step for me in the reply's own text, numbered, never only on a card, in a widget or in a file.
```

## 2. Project goal

Where: the same Settings, the Goal (or Topic) field. Paste and press Save.

```
Build Symphony, OpenSpineConsortium's open coordination product for Claude Code, and prove that it works. Symphony lets many Claude sessions, routines and GitHub Actions workers share one repository without stepping on each other: the claim protocol as a library (symphony-protocol), the template that keeps a Claude project as files in a repository (symphony-template), the two GitHub Apps and the one-press front door, the plugin, and the control panel on openspineconsortium.com, which also organizes a person's OneDrive into projects and notebooks. The proof is measured: replicate CooperBench's curse of coordination and remove it with Symphony's protocol (coordbench), benchmark agentic workflows (flowbench), and go beyond cooperation against MAST's failure modes. This Project also carries my related work: the AIDaS spine grant (spine-program), the Beethoven extension and Symphony on the WSU grid. Done for now means every control panel tab fitting the screen with no scroll, the explorer modernized, the OneDrive work on direct Microsoft Graph now that Wayne State has consented, and the full coordination run recorded with its results.
```

## 3. Memory

Open https://github.com/OpenSpineConsortium/symphony-template/blob/main/docs/checkpoints/2026-10-22/memory.md, press the copy-raw button, and paste it into the first message after the block in part 5, saying "save this as the project's MEMORY.md". Save the files in topic-memories/ the same way, one each, when a thread needs one. The patentability memo and the SchwingNet topic memories are not here on purpose: the memo is in the old Project's files (patent/symphony/), and SchwingNet's facts are in SchwingNet's own docs/memory/.

## 4. Repositories to add

Where: the Project's Settings, Repositories, Add. Threads attach the others with push access as their work needs them.

```
OpenSpineConsortium/symphony-template
OpenSpineConsortium/SchwingNet
OpenSpineConsortium/spine-datasets
OpenSpineConsortium/symphony-protocol
OpenSpineConsortium/symphony-app
OpenSpineConsortium/symphony-start
OpenSpineConsortium/openspineconsortium.github.io
OpenSpineConsortium/hpcworker
OpenSpineConsortium/beethoven-extension
OpenSpineConsortium/beethoven-vscode
OpenSpineConsortium/beethoven-base
OpenSpineConsortium/beethoven-sites
OpenSpineConsortium/spine-program
OpenSpineConsortium/coordbench
OpenSpineConsortium/flowbench
```

Connect GitHub first: open https://claude.ai/connect-github, sign in as Gregory-Schwing-MD-PhD and press Authorize. For mail and OneDrive, connect Microsoft 365 under claude.ai, Settings, Connectors, with the Wayne State account.

## 5. First message for a new coordinator

```
Pick up Symphony where the last Project stopped on 2026-10-22 at 00:01 UTC, when I stopped every thread at 97% usage. Read docs/checkpoints/2026-10-22/handoff.md in OpenSpineConsortium/symphony-template first, then memory.md beside it (save it as this project's MEMORY.md) and grid-slurm-protocol.md. Restart the threads in part 6 in the order given, at most three at once unless I say more; grid jobs need no number from me, everything else that spends still does. Never give me a grid shell command or a hand step that a workflow or a gate word can do.
```

## 6. State of every thread, and its restart brief

Live at the stop (each stopped cleanly, nothing uncommitted unless said):

1. SchwingNet video demo plan (SchwingNet). Open: #82 (ingest reads both C-ArmLSpine banks' view and kVp, ready), #83 (PhysioNet fetch says what PhysioNet answered; VinDr-PCXR is Restricted, draft), #78 (every grid job through `hpcworker job submit`, draft), #73 (gate words for the counting prior, covariate census and chain evaluation, draft). The v1 rerun change was reviewed (3 blocking, 7 should-fix, 5 nits) and was being fixed at the stop. Next: merge #82, #83 and the v1 rerun change; rerun ingest and catalog; send the v1 run; move all jobs onto `hpcworker job submit`; add the `samples` gate word (#73, #77) so the 3D-priors census runs.
2. SchwingNet latency and ONNX (SchwingNet #13). Merged #46, #52. Open: #85 (sweep reads the angle as the real banks write it, auto-merge on). Next: the demo-plan thread runs the grid probe, this work records its answer in docs/research/latency-and-sweep/; timing and video jobs once v1 exists.
3. 3D CT priors for 2D detection (SchwingNet). Merged #55, #71, #76; none open. Research in SchwingNet docs/research/xr-from-3d/ and docs/research/data-manifest/, handoff SchwingNet docs/checkpoints/2026-10-21-xr-from-3d/HANDOFF.md. Next: census via the `samples` gate word, then fill the Any-View Spine Plan artifact's per-region table; correct the report: BUU-LSPINE is held (3,600 AP+lateral pairs). Open question for greg: is NHANES II the unannotated set for the screener (#64)?
4. Beethoven grid node wait (hpcworker, beethoven-*). hpcworker framework 27 live on the grid since 2026-10-21 23:49 UTC (hpcworker #29, #30; beethoven-sites #5; beethoven-base #5, #6 merged). Open: beethoven-vscode #20 (draft; needs `npm run test:vscode` on a machine with VS Code). Next, first: build the `promoter-restart` gate word (spec in grid-slurm-protocol.md); then move the promoter and CT-priors jobs onto `hpcworker job`. Multi-project worker plan awaits greg's go. Its docs/research note for this repository was skipped at the stop; write it from grid-slurm-protocol.md.
5. Button home screen as default (site, symphony-app, symphony-template). Open, CI green: site #136, symphony-app #89, symphony-template #344. The full mutant run stopped part-way with 5 graph-suite survivors and 1 stale mutant, not yet compared with master. Next: compare those with master's mutant run, then merge all three.
6. Dataset status audit (spine-datasets). All merged (#104, #112, #114, #118). VinDr-PCXR fetching on the grid (Slurm 40697734 -> 40697735 -> 40697736, to /rs/rs_grp_oschome/go2432/data/vindr_pcxr/raw, about 30 GB): mark it fetched (#17) once files land and match SHA256SUMS.txt. MIMIC-CXR, MIMIC-CXR-JPG and VinDr-CXR wait on PhysioNet's CITI review. Letters sent 2026-10-21 to IRI-VFI (#21), TVGH-SpineXR (#14), TVGH AS films (#108): record replies. Its docs/research note for this repository is still undone.
7. Automated dataset PR review (spine-datasets). All merged; #121 moves promote.sh onto `hpcworker job submit`, but the running promoter chain (Slurm 40696334 lineage) still runs its old code, since it self-updates only from commits authored by greg. Decision card open; recommended and in progress: a `promoter-restart` gate word (item 4). Ashley's Mendeley User-Agent fix, macOS SSL note and Python 3.14 test failures are this thread's. See topic-memories/dataset-promoter.md.

Finished and resolved (restart only on a new ask): Control panel sign-in, Modernize the explorer, OneDrive on direct Graph, Tokens and adopted repositories, Capabilities demo and sandbox, Patent counsel answers, Phone home screen for the panel, Outlook digests and next steps, Symphony patentability research, Faster backend than Actions, Stale branch failure statistics (template #318 still open, see part 7), WSU grid files in Folders, Fine-grained locking on, Panel design system, Explore as dependency brainstorm, SchwingNet bank recipes and leak checks, SchwingNet witness frames and W&B, W&B tab in the control panel.

## 7. Open pull requests, 2026-10-22 00:05 UTC

Read by GitHub search over the organization (`org:OpenSpineConsortium is:open`).

| Repository | PR | State | Owner thread / note |
|---|---|---|---|
| symphony-template | #344 button home screen research | draft, green | Button home screen |
| symphony-template | #318 date the clean after period at 0.6.1 | open | Stale branch statistics; check and merge |
| openspineconsortium.github.io | #136 button home screen | draft, green | Button home screen |
| symphony-app | #89 home screen checks | draft, green | Button home screen |
| symphony-app | #82 Runs tab's Cancel checks | open | Panel design system; check and merge |
| SchwingNet | #85 sweep angle | auto-merge on | Latency and ONNX |
| SchwingNet | #82 ingest view and kVp | ready | Video demo plan |
| SchwingNet | #83 PhysioNet fetch | draft | Video demo plan |
| SchwingNet | #78 jobs through hpcworker job submit | draft | Video demo plan |
| SchwingNet | #73 grid gate words | draft | Video demo plan |
| beethoven-vscode | #20 placement from the site profile | draft | Beethoven grid; needs VS Code test run |
| spine-program | #216 board files up to date | open | sync; check and merge |
| spine-program | #89 05: CT-2 spinopelvic | draft, old | spine-program |
| symphony-protocol-canary | #5 bring in 0.5.1 | open | protocol |
| claude-swap-cloud | #46 cswap state | draft, old | cswap |
| Student_Projects | #1 proposal | open since 2026-09-07 | not ours |
| Dependabot | SchwingNet #2 #3, spine-datasets #5 #6, symphony-protocol-canary #6, test #2 #3, beethoven-vscode #16 #18 #19 | open | merge when green |

## 8. Running on the grid at the stop

- VinDr-PCXR fetch chain, Slurm 40697734, 40697735, 40697736 (started by the SchwingNet video demo plan thread).
- The spine-datasets promoter chain on hao1 (started 2026-10-21 19:36 UTC, Slurm 40696334 lineage), on its old code until promoter-restart.
- The Beethoven always-on worker chain on greg's Wayne State Claude Max account.

## 9. Artifacts

Every artifact is private by default. Patent material is marked: share it only to greg's own new account, never "Anyone with the link".

| Artifact | Link | From | Patent material |
|---|---|---|---|
| Any-View Spine Plan | https://claude.ai/artifact/XofcEieMWzL443pSG8qrLh | 3D CT priors | yes |
| SchwingNet grid pipeline | https://claude.ai/artifact/UMnwCkV9SQm2kokkCXWUKA | SchwingNet video demo plan | yes (SchwingNet) |
| SchwingNet Data Registry | https://claude.ai/artifact/L4pJez6yLFzaX8x5jiA3JL | SchwingNet data requests | no methods; private data list |
| Several grid workers, one per project | https://claude.ai/artifact/UjuFBMxLEL8CnifRofU3Vv | Beethoven grid node wait | no |
| Grid and cloud Claude workers: review | https://claude.ai/artifact/L7nL3xkYzoitmWf4ab8ARN | Beethoven grid node wait | no |

Every artifact of the first account is now also kept as files, so any account can read, edit and republish it (the owner's ask of 2026-10-22, after this handoff): artifacts/ in OpenSpineConsortium/symphony-template for the Symphony and Beethoven ones (four), and artifacts/ in OpenSpineConsortium/SchwingNet for the spine, fluoroscopy, SchwingNet and spine-program ones (fifteen, the patent material among them). Each folder holds one artifact, a page as index.html with its other files beside it or a Claude Docs document as index.md, and each artifacts/README.md lists title, folder, link and what it is. The copy in the repository is the one to edit, by pull request; republish from it with the Artifact tool on whichever account is working.

Do the same on every other account of the owner's, and keep doing it as new artifacts are made, so all of them end up in one place: list the account's artifacts (Artifact tool, action list, scope all), read each page (action read, path index.html, and each file a scope files listing shows), export each Docs document as Markdown (Claude Docs read, then export with format markdown), and add one folder per artifact and one row to the matching artifacts/README.md, in one pull request per repository. SchwingNet's methods go only to SchwingNet, never to a public repository. Sharing on claude.ai is set per artifact in its Share menu by the owner; a session cannot change it, and the repository copy is what makes an artifact editable by everyone with access.

The old Project's shared folder (/mnt/project-files/) holds the rest: patent/ (counsel package, inventor responses, the Symphony patentability memo), schwingnet/ and schwingnet-demo/ (plans, dataset requests), data-requests/, handoff/grid-slurm-protocol-2026-10-22.md (copied here) and the screenshots. A new Project does not see that folder; download what is needed from the old Project first.

## 10. Waiting on greg, numbered

1. Share the artifacts so the new account can open them (or skip this: every artifact is now in the two repositories' artifacts/ folders, part 9). For each link in part 9: open it while signed in to this account, press Share at the top right, and choose "Anyone with the link" for the three marked no; for the two marked patent material, share only by adding your new account's email, if the Share dialog offers it, or keep them on this account.
2. Choose on the promoter card in the "Automated dataset PR review" thread (recommended: Add a promoter-restart gate word), or say so in the new Project.
3. Confirm NHANES II is the unannotated set for the X-ray screener (SchwingNet #64).
4. Say go or no for the multi-project grid workers plan (https://claude.ai/artifact/UjuFBMxLEL8CnifRofU3Vv).
5. Your hand on spine-datasets: the MAGIC-CT application (#7), the BRAX agreement (#110), the BIMCV IEEE login and a space decision (#111).
6. Run `npm run test:vscode` for beethoven-vscode #20 on a computer with VS Code, or let a Remote Control session do it.
7. Grid AccessID and GitHub invitation for Nishan (spine-datasets collaborator).
8. Revoke the Kaggle token you pasted earlier: https://www.kaggle.com/settings, API, Expire Token.
