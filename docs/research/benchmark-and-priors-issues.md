# Benchmark and priors issues: where the findings are, and the public facts

Source: the thread "Benchmark and priors issues", 2026-10-22. The owner's messages of 21:18 to 21:32 UTC that day asked for a login-gated Zenodo dataset and the dataset of arXiv 2412.08020 to be fetched, named arXiv 2412.08020 and 2506.13292 as "the people to beat", asked for FluoroSAM to be evaluated for how it handles the gap between synthetic and real fluoroscopy, asked for an opinion on github.com/arcadelab/VertebralDiffusion as a training template, and asked that all of it become self-contained tasks other accounts can take. The findings describe SchwingNet's methods, so they live in that private repository, docs/research/benchmarks-to-beat.md (the owner's account ran out before that pull request; the content waits in the checkpoint on SchwingNet #130), under its confidentiality rule; this note keeps only what is public.

## The public facts

- arXiv 2412.08020 is Killeen et al., "Intelligent Control of Robotic X-ray Devices using a Language-promptable Digital Twin", IPCAI 2025. Its cadaver dataset (80 X-rays from 46 viewpoints of one torso, registered to four CTs) is a Google Drive zip of 845 MB linked from github.com/benjamindkilleen/IPCAI-language-digital-twin (code MIT; the dataset's licence is not stated). The Drive link the owner gave is that file.
- arXiv 2506.13292 is Flepp et al., "Automatic Multi-View X-Ray/CT Registration Using Bone Substructure Contours", IPCAI 2025 and IJCARS. It registers the distal femur, not the spine. Its dataset is Zenodo 15753063: open access, no login, one zip of 6.7 GB under a "Research-Only Dataset License"; its code is request-only under a licence agreement with a pending patent application. The owner's link anchor #S7.F8 is an appendix figure; the HTML has no Section 7.
- The token the owner sent is for MAGIC-CT (Zenodo 18389015, spine-datasets #7), approved on 2026-10-22; SchwingNet #124 added the grid fetch that reads it from a file on the grid. It is written nowhere else.
- FluoroSAM (MICCAI 2025, arXiv 2403.08059) and its training set FluoroSeg (2.95 million synthetic X-rays from 1,621 CTs, gated on Hugging Face) are CC BY-NC-SA 4.0 in both repositories. Its renders come from a modified DeepDRR (the paper's v2), and it handles the synthetic-to-real gap by randomisation at training time (no fine-tuning on real images), and its real-cadaver Dice equals its synthetic Dice for large structures; individual vertebral levels it does not discriminate (Dice 0.04 in the digital twin paper).
- github.com/arcadelab/VertebralDiffusion is one commit on the ashleve Lightning-Hydra template with its README unchanged and no LICENSE file: a 3D VQ-GAN and a 3D DDPM over per-vertebra CT crops at hard-coded Johns Hopkins paths, no paper, no weights, no data. Not a template to adopt and, with no licence, not code to copy.

## What was filed

Five SchwingNet tasks, #130 to #134; #133 and #134 were closed as duplicates of #127, the gold segmentations another thread already held. Two spine-datasets tasks, #170 (the Drive set) and #171 (FluoroSeg). Comments on spine-datasets #34 and #7 and on SchwingNet #70.

## How the papers were read from a cloud session

arxiv.org, zenodo.org, huggingface.co and semanticscholar.org are refused by the container's proxy; raw.githubusercontent.com and git clone of public repositories work. The session's web fetch tool reads a page once its address has appeared in a web search result or in a message, so each paper was found by searching its arXiv number and then fetched (the arXiv HTML of 2506.13292v2 and the PDF of 2403.08059v3 in full). The Hugging Face dataset card and the Springer PDF were not readable by any route.
