---
name: physics-three-defects-measured
description: "Of the three physics defects found 2026-09-22, only the AEC one changed an image: the merged density path already carries bone (identical render), the zero bone path made the box spread larger not smaller, and extrapolating the card's exposure model is what starved the frame. What still hides a lateral spine is the display window over the whole field"
metadata:
  type: project
---

Record with every number: `spinesurg-ct-nnunet/docs/PHYSICS_THREE_DEFECTS_MEASURED_2026-09-22.md`; the four
diagnostics are in `tools/diagnostics/`.

- **Merged density path vs water+bone pair: identical.** `1 + HU/1000` already contains the bone at the effective
  energy (mu_w-min(1+HU/1000,1) + mu_b-(HU/1000)(mu_w/mu_b) = mu_w(1+HU/1000)). Measured box spread 24.0, sd 9.2
  either way. The earlier "the physics mode has no bone term, that is why no spine" is WITHDRAWN.
- **The figure tool's zero bone path** gave a box spread of 62 against 56 for the correct pair -- larger, not flatter.
- **The AEC extrapolation is the real one.** Cards fit log10 photons on thickness over 9.3-11.5 cm (PIXIUM) and
  9.7-19.7 cm (Cios); a lateral abdomen is 28-38 cm and the PIXIUM slope is negative. `device_style.aec_gain` now
  holds the DETECTOR's quanta outside the fitted range (capped x30, flagged per frame): PIXIUM 4,607 -> 103,084
  photons/mm^2 and the speckle disappears.
- **What still hides the vertebrae** is the display window over the whole exposed field plus colonography gas:
  collimating to the spine moves the box spread from 27 to 153 grey levels. A protocol arm, not a bug.

**Why it matters:** three plausible causes, one real. Render the frame and change ONE term at a time before
believing any of them. Related: [[sweep-physics-no-bone]] (superseded in its causal claim), [[rsnai-paper-endpoint]].
