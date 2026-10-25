# The Unberath and Killeen lab's X-ray learning, from its public papers alone

Source: the thread "Compare lab's X-ray learning to SchwingNet", 2026-10-25, on the owner's ask that day about the papers of two Google Scholar profiles and github.com/benjamindkilleen. This note holds only what the public papers say. The comparison with SchwingNet's own results, the contradictions and the five papers chosen to benchmark against are confidential and live only in OpenSpineConsortium/SchwingNet, as docs/research/arcade-lab-x-ray-learning-against-schwingnet.md and docs/research/training-framework-against-published-frameworks.md, each with its line in that repository's docs/research/README.md.

## What the lab is and how its record was reached

Mathias Unberath's ARCADE lab at Johns Hopkins, with Benjamin D. Killeen, a postdoc at TUM's CAMP chair since September 2025 (his TUM page). Google Scholar, Scopus, OpenAlex, Semantic Scholar and arxiv.org refused the cloud container, and Scholar refused the owner's machine's proxy too, so the record was read from dblp's mirror (dblp1.uni-trier.de), arXiv HTML pages reached through WebFetch, PubMed Central and the lab's repositories. A Scholar profile a session cannot read is best given to it as a pasted list.

## Its themes, in its own papers

- Simulation first: real labelled intraoperative X-rays are scarce, so networks are trained on renders of CT with labels projected through the geometry (DeepDRR, MICCAI 2018 and IJCARS 2019; SyntheX, Nature Machine Intelligence 2023; FluoroSAM, MICCAI 2025).
- The renderer is physics (spectrum, materials, scatter, noise), and the bridge to real frames is strong intensity randomisation, which beat CycleGAN and ADDA in SyntheX.
- Parity is claimed where the renders come from the test cadavers' own CTs at the real poses: hip landmarks 6.44 against 6.46 mm, Dice 0.80 against 0.79 (SyntheX, DeepFluoro's 366 frames of six cadavers). The authors say synthetic training "hardly matches" real training where real data is abundant (COVID-19 chest X-rays).
- The work runs from perception to autonomy: phase recognition (Pelphix, 71.7 percent on a cadaver against 99.2 in simulation), natural-language control of a robotic C-arm ("Take a shot!", IJCARS 2024; the language-promptable digital twin, arXiv 2412.08020), and generative data (2D against 3D diffusion, arXiv 2606.21414, 2026).
- Validation is on cadavers, one or a few, on one or two devices.

## How an outside test reads FluoroSAM

FleXray (Butoi, Gopalakrishnan, Guttag, Dalca, Dey; arXiv 2609.26756; MIT) trains on DRRs of 2,159 CTs edited toward clinical appearance by a general image editor and tests on eight held-out real X-ray sets. On AASCE's Cobb-angle task (218 spine radiographs) FluoroSAM's mean absolute error is 31.82 degrees with 42 failures, against FleXray's 5.13 with none; on DeepFluoro FleXray reaches Dice 0.915. The lab's own digital twin paper gives FluoroSAM Dice 0.16 to 0.25 for single lumbar vertebrae by name on its cadaver.

## ClassyVision

github.com/benjamindkilleen/ClassyVision is an unchanged fork of Meta's ClassyVision, a registry-and-config training framework for image classification, which Meta archived on 1 July 2024 ("no longer actively maintained"; last stable 0.7.0).
