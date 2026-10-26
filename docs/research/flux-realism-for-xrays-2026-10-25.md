# Flux realism for X-rays: what CSAIL released, and how a finetune is set up

Source: the thread "Finetune Flux Realism for X-rays", 2026-10-25 to 2026-10-26, on the owner's ask to find and implement "CSAIL's trained version of Flux realism" from the FleXray paper (arXiv 2609.26756v2, its source uploaded by the owner on 2026-10-26) and the Hugging Face model VictorButoi/flexray, and to make a reproducible finetune whose X-rays are numerically indistinguishable from the paper's enhanced DRRs. This is the public side: what exists, what the paper did, the licences, the tooling, and the shape of a reproducible study. The project's own renders, measurements and adapters are described in the confidential SchwingNet repository and not here.

## 1. There is no trained realism model to find

The paper's "Enhanced DRRs is a dataset of DRRs pre-rendered from MOOSE and refined with the diffusion model flux.2-klein-9b" describes a zero-shot use of Black Forest Labs' FLUX.2 klein-9B, not a model trained by the authors. The appendix (the paper's section on the data engine's enhanced DRRs) says it "requires no task-specific fine-tuning" and gives the whole recipe: the released klein-9B weights, 4 denoising steps, bfloat16, guidance 1.0, one fixed five-sentence prompt (make the synthetic X-ray look real, preserve all anatomy, add a little clinical text and X-ray texture, stay registered with the input), 90 fixed camera poses (three source heights by six vertical offsets by five rotations about one axis), a 1250 mm source-to-detector distance, 0.6 mm detector pixels at 1024 by 1024, the isocentre at the volume's centre; edited pixels zeroed where the raw DRR is below 0.05; and a paired filter that keeps an edit when a U-Net's soft Dice on it, against the exact projected labels, falls no further below its soft Dice on the raw DRR than a per-pose cut-off (twice the median minus the 2nd percentile of the paired difference), dropping about 4 percent.

Released: FleXray's segmentation weights (five members trained with 0 to 75 percent enhanced DRRs; CC BY-NC 4.0), the enhanced-DRR dataset FluXray (138,063 images stored at 256 by 256, with masks and a table of each image's pose; CC BY-NC 4.0 as a collection), and the code (pip flexray 1.0.2, MIT), including the renderer and the MOOSE label profile. Not released: the edit script and seeds, the edits at their 1024-pixel size, and the filter's U-Net trained on raw DRRs alone. The CTs are ENHANCE.PET 1.6k (1,683 whole-body FDG-PET/CT studies with MOOSE labels), on a public S3 bucket that lists without a key.

## 2. What 256 pixels mean

The first limitation to address was resolution. With the paper's geometry a detector pixel spans 0.31 to 0.55 mm at the isocentre at 1024 by 1024 (over the three source heights), and one pixel of rise across a 45 mm lumbar endplate changes its angle by 0.40 to 0.70 degrees. FluXray is stored at 256 by 256, where a pixel spans 1.25 to 2.21 mm and one pixel of rise is 1.6 to 2.9 degrees; FleXray's inference canvas is 256 pixels too. A measurement that needs a degree cannot come from a 256-pixel mask, which is the LinkedIn review's second point as a number. A reproduction therefore renders and edits at 1024, keeps the edits at 1024, and drops to 256 only where it compares with FluXray, since nothing larger of FluXray exists; and an adapter trained to match FluXray trains at 256, while one trained to match a 1024-pixel teacher keeps its size.

## 3. The models and their licences

| Model | Parameters | Distilled | Licence | Gated |
| --- | --- | --- | --- | --- |
| black-forest-labs/FLUX.2-klein-9B | 9B | yes (4 steps) | FLUX Non-Commercial License | yes, a click-through |
| black-forest-labs/FLUX.2-klein-4B | 4B | yes | Apache-2.0 | no |
| black-forest-labs/FLUX.2-klein-base-9B | 9B | no | FLUX Non-Commercial License | yes |
| black-forest-labs/FLUX.2-klein-base-4B | 4B | no | Apache-2.0 | no |

FluXray was made with the first. The FLUX Non-Commercial License covers the weights and what they output for non-commercial use; a finetune trained on those outputs inherits the question, and one trained on FluXray's images (CC BY-NC 4.0) is a derivative of them. The Apache bases carry no such question, so an adapter the project may keep and sell is trained on klein-base-4B, with FluXray used to measure and never to train, and ENHANCE.PET's three CC BY 4.0 sites (Leipzig, Careggi, UC Davis) kept apart from its two CC BY-NC 4.0 sites (autoPET, Tuebingen) if the CTs are to stay open. The licence choice is the owner's and blocks nothing.

## 4. Tooling for an edit finetune

diffusers' Flux2KleinPipeline runs the edit (an input image, the prompt, the step count, the guidance, a seeded generator). ostris/ai-toolkit (MIT) trains LoRA adapters for FLUX.2 klein, including the edit form where a control folder of input images stands beside a target folder of outputs and each target carries the prompt as its caption; its configuration names the base, the rank, the learning rate, the steps, the resolution, the optimizer, the schedule and the seed, and a run is `python run.py <config>`. A reproducible setup pins the trainer to one commit and the libraries to one release each (on 2026-10-26: diffusers 0.42.0, transformers 5.20.2, accelerate 1.15.0, peft 0.21.2, safetensors 0.8.0, huggingface_hub 2.3.0), and keeps them in a throwaway environment rather than a project's lock file.

## 5. The shape of a reproducible study

- The recipe as data, not prose: every setting the paper gives, in one record a program reads, with each deviation named (a stand-in for the unreleased filter U-Net; seeds derived from the subject, the pose and a repeat arm, so a rerun draws the same noise).
- Raw DRRs of the same CTs at the same poses, with exact masks projected from the CT labels, so the comparison with FluXray is paired by subject and pose and the geometry is checked (PSNR, SSIM, the phase-correlation shift) before any texture is read.
- "Numerically indistinguishable" as a pre-registered two-sample test, not a picture: several feature spaces (handcrafted image physics, the segmentation model's own reading, a generic ImageNet network), a classifier two-sample test with subjects held out and a bootstrap interval over subjects, a kernel MMD with permutation p-values read at their Benjamini-Hochberg q over the spaces, Frechet and kernel distances on principal components, and the reference set's own split halves as the null every number is read against; one verdict word per space.
- The review's other limitations in the design: no probability is trusted as truth (the filter's Dice is against exact masks); endplate angles are measured from the exact masks at 1024 and at 256 so the resolution floor is known before a model is asked for one; the edit runs in two seed arms, and a verdict that changes with the arm is not a result.
- The adapter pre-registered before any run: base, rank, alpha, learning rate, steps, resolution, optimizer, schedule, save interval and seed, a split by subject (never by image) and every number read on held-out subjects; three possible targets (the paper's enhanced DRRs, a larger model's own edits as a teacher, real X-rays).
- Compute only on the owner's word and count: one GPU job per stage (edit, measure, finetune, evaluate), each refused until its inputs have landed and the stage before it has finished, each run once with its report kept.

## 6. Pointers

- The paper: arXiv 2609.26756v2 (FleXray), appendix section on the data engine's enhanced DRRs; the model card VictorButoi/flexray and the dataset VictorButoi/flexray-data (folder FluXray) on Hugging Face; the package flexray on PyPI.
- ENHANCE.PET 1.6k: Science Data Bank doi 10.57760/sciencedb.34150 and the S3 bucket enhance-pet-1-6k (imaging-data/images/CT, imaging-data/ground-truth, labels.json, CT-details.xlsx with each study's site).
- FLUX.2 klein: the four Hugging Face repositories above; ostris/ai-toolkit on GitHub.
- The grid word in this template's grid accounts workflow: schwingnet-realism-<stage>, one of edit, stats, lora and eval.
