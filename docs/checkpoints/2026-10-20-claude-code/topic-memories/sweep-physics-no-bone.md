---
name: sweep-physics-no-bone
description: sweep_map --perturb physics and the figure tool's card styling rendered from a merged density path with no bone term -- frames LOOKED AT 2026-09-22 show no spine; linking numbers under them measure soft tissue; fix is make_drr_dataset --paths2-only (water+bone with the cards' definitions)
metadata:
  type: project
---

Rendered and looked at 2026-09-22 (Figure 1 row f): `sweep_map --perturb physics` frames (VerSe 602, CTSP 175) and
`fig_story_rows --perturb card` frames (Cios card, CTSP 149) show NO visible spine -- soft-tissue gradient, noise,
collimator. Cause: both render from `path/<case>.npy` = `make_drr_dataset.water_path_cm`, one density-weighted path
(1 + HU/1000) with no photoelectric bone term; a lumbar body adds a few per cent to ~30 cm of water. The figure tool
also passed an all-zero bone path. Chains then came out with too many nodes (VerSe 27-41 for 25 bodies) or exact
only through the linker's commanded-displacement prior.

**Why:** a finite, plausible number with nothing under it -- the docstring even claimed the error made counting
easier. Records: `spinesurg-ct-nnunet/docs/PHYSICS_SWEEP_NO_BONE_2026-09-22.md`.

**How to apply:** do not quote any linking/confirmation number measured under `--perturb physics` (including the
physics-linking handoff's figures) until its frames are rendered and show bone. Use `make_drr_dataset
--paths2-only` (path2/<case>.npz: water capped at water density, bone = clip(HU,0)/1000 x MU_RATIO_E0 -- the
definitions the device cards were fitted with); the figure tool now refuses card mode without it. The training
corpus (`devcorpus_build` -> `deepfluoro_render.raycast`) always had separate water and bone and is unaffected.
VerSe whole-spine chains ALSO break on clean frames (32-33 nodes for 25 bodies, thoracic region) -- whole-spine
linking is unsolved. Related: [[rsnai-paper-endpoint]], [[detection-is-the-binding-constraint]].

**Second cause (13:45):** with the bone term added, the Cios/BV Pulsera/Elekta cards still show no spine on a lateral CTSpinoPelvic1K sweep: 28-38 cm of lateral water path photon-starves the frame and the colonography gas takes the window -- those cards were fitted on thinner paths. Use the Surgio-B51 (C-ArmLSpine, real lateral lumbar) card for lateral sweeps (row f queued as 40414418 behind its fit).
