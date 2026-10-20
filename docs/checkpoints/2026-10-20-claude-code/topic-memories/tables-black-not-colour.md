---
name: tables-black-not-colour
description: "Greg wants capability/matrix tables colour-agnostic -- solid black cells plus at most one other mark (outlined) -- cells full-width and touching, no dots"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: e44eca96-f48c-494d-ba1f-7dae68bdf06d
  modified: 2026-09-04T06:31:51.806Z
---

Table 1 of the MPDA paper (2026-09-04): Greg rejected dots, then teal/amber colour cells,
and asked for "solid black and something else for the one other thing to encode", cells
flush (touching) and each header inside its column.

**Why:** colour carried nothing a mark could not; gaps between cells looked broken.
**How to apply:** encode presence as a solid black run, the single qualified case as an
outlined empty cell; never colour. In REVTeX `ruledtabular`, per-cell fills always get glue
between them -- put each row's cells in ONE spanning cell of `\rule`s of a width computed
from `\linewidth` (`\cellw`), and give rules an explicit ex height (`\baselineskip` is 0
inside a tabular). Fixed-width `p{}` columns break under REVTeX + colortbl ("Extra \or").
Related: [[figure-captions-terse]].
