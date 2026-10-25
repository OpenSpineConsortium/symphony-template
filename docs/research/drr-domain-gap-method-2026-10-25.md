# FleXray's DRRs beside real X-ray corpora: the method and the count

The thread "Compare FleXray DRRs to real X-ray corpora", 2026-10-25, on the owner's ask of that day to plot FleXray's synthetic DRRs beside every held X-ray corpus, plain film and fluoroscopy, in t-SNE and other dimension-reduction maps, with the statistical tests for separation a machine-learning reviewer would expect. It belongs to the FleXray audit (SchwingNet #391; this repository's docs/research/flexray-audit-plan-2026-10-25.md). This note holds the public half: what is compared, how, and what the grid job costs. The design in full, the numbers once they exist and the project's own synthetic sets are in the private companion, SchwingNet docs/research/drr-domain-gap/README.md, which never leaves that repository.

## Where it stands

The code and its tests are written in SchwingNet and nothing has run. The study is one GPU job through the gate word `bench` with a new id, `flexray_drr_gap`, which the existing `schwingnet-bench-<name>` job word of grid-accounts.yml already accepts, so nothing changes in this repository's grid route. FluXray, FleXray's FLUX-edited DRR set (VictorButoi/flexray-data on Hugging Face, CC BY-NC 4.0), joins the job only after the one fetch item 6 of the audit plan already names; until then the job skips it and says so. The owner's word and count are asked once, as a decision card in the thread. The thread was checkpointed mid-build at the owner's word of 2026-10-25 22:35 UTC, after the owner asked for rendering to become a block part and for a replication test of FleXray's dataset from the same raw CTs (a replica through the blocks, FleXray's own renderer as reference, FluXray as shipped; the count is unchanged); the handoff and the restart steps are SchwingNet's docs/checkpoints/2026-10-25-drr-domain-gap/HANDOFF.md, on SchwingNet's branch claude/project-thread-7ltron.

## What is compared

- Synthetic: FleXray's raw DRRs, rendered in the job by FleXray's own renderer (the nanodrr pose profile its training used) from held TotalSegmentator v2.0.1 CTs, 250 CTs at four views; FluXray once fetched; and, as a control that shares the CTs and changes only the renderer, the project's own synthetic sets.
- Real fluoroscopy: C-ArmLSpine spot frames, DeepFluoro's vendor fluoroscopy (cadaver pelvis) and the Geneva hip phantom (one subject, so plotted and never tested).
- Real plain film: VinDr-SpineXR, BUU lumbar spine, AASCE, NHANES II scanned films, CSXA, KUB StoneX, the IEEE DataPort lateral whole-spine set, LUMOS (from its bank, where built) and the Aariz cephalograms.
- Each corpus gives at most 1,000 images, chosen person by person in a salted order with a cap a person; the frozen test persons are left out everywhere. Left out with reasons: web video clips (their record allows tracker screening only), literature figure panels, linac CBCT projections (MetaImage, not a C-arm), sets whose records exclude them, sets of fewer than 20 frames, true video files (no decoder without a new dependency) and archives never unpacked.

## How

- Every image takes one path: decoded at its own depth (DICOM through its modality LUT, MONOCHROME1 turned bone-bright), windowed to its 0.5 and 99.5 percentiles, the centre square of 0.9 of its shorter side resized to 256. A cut square rather than a padded one keeps a pad's border from telling the corpora apart.
- Three feature spaces, so no finding rests on one encoder: FleXray's own encoder (the spatial mean of the input to the last instance norm of its deepest block, since the norm's output has the same spatial mean for every image), an ImageNet ResNet-18, and handcrafted physics measures (intensity histogram, power spectrum shape, gradients, noise, local contrast, clipping). The primary reading is inversion-invariant, the mean of an image's features and its inverse's, since fluoroscopy is often bone-dark and DRRs bone-bright.
- Maps: PCA, t-SNE (perplexity 30 on PCA-50), UMAP (30 neighbours on PCA-50) and LDA (supervised, labelled so), each but LDA with its trustworthiness.
- Tests: person-grouped classifier two-sample tests (logistic and 15 nearest neighbours) with person-cluster bootstrap intervals and person-level permutation p-values; the unbiased MMD with person-level permutations; Frechet distance and KID in each space's first 64 principal components; precision, recall, density and coverage; silhouette and neighbour purity; Benjamini-Hochberg within each space.
- Calibration: every corpus of 40 persons or more split in two by person and tested against itself, where every test must find nothing; real corpus against real corpus as the baseline a synthetic set is measured against, so that "separable" means farther than two real corpora are from each other, not merely distinguishable.
- Primary endpoints, fixed before any number: in FleXray's space, the C2ST AUC of FleXray's DRRs (and FluXray's) against pooled fluoroscopy and pooled film, and their Frechet distance against each family over the median distance between that family's own real corpora.

## What leaves the grid

Only printable text comes back from the grid: a summary of at most 80 lines of numbers and group names, carried by the bench report through the gate's redaction. The figures and the map coordinates go to the project's private W&B where the grid's key is found; the full results and the plan, which names files, stay on the grid.

## The count

| step | kind | count | note |
| --- | --- | --- | --- |
| flexray-data (FluXray) | fetch | 1 | item 6 of the audit plan's existing fetch; its exact size is read before a byte lands and the size rule refuses it whole if it would pass the quota |
| bench flexray_drr_gap | GPU job | 1 | renders, decodes, three feature spaces and the analysis in one job; runs without FluXray if the fetch is not approved |
