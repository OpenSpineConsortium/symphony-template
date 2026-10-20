---
name: figure-preferences-schwingnet
description: "Greg's figure-by-figure verdicts for the SchwingNet manuscript (2026-09-22) -- keep A, B (bigger text), E (+ how it works), G, I (better arrows); replace C with a numbered full-spine panorama in the focused-paper Fig 6 cartoon style; drop D, J and the three audit figures; H becomes a table"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: f1bdbd78-151f-470b-b703-dd9af9b3fecc
  modified: 2026-09-23T02:58:19.818Z
---

Greg, 2026-09-22, reviewing the figure gallery for the SchwingNet manuscript. Six figures plus one table -- the
journal limit exactly. Letters refer to the gallery artifact; file names are in `paper/rsnai/figures/`.

**Keep**
- **A** `fig1_problem.png` -- the sliding field of view holding L4-L3-L2 in one spine and L5-L4-L3 in another.
  Liked because it shows the count from the sacrum is *mathematically undetermined* in a limited field, which is
  the problem statement: the goal is a network that, given an instrument on a vertebra shot in a limited field,
  says exactly how many levels up from the sacrum it is.
- **B** `fig1_row1_pipeline.png` -- keep, but text too small and too much empty space inside the boxes.
- **E** `fig1_row3_confirm.png` -- "love it"; wants a *visual explanation of how it works* added.
- **G** `fig1_row6_confirm_fluoro.png` -- "can't get enough of these localization figures". More like it.
- **I** `fig1_row6_arch.png` -- better than before, but the arrows look poor next to a real AI journal. Fix the
  arrows (orthogonal connectors, consistent stroke, proper arrowheads, skip arcs) -- don't redesign the blocks.

**Replace**
- **C** `fig1_row2_anatomy.png` -- "absolutely hate". Wanted instead: the LEFT cartoon of Figure 6 in
  `paper/focused/main.tex` (`fig:mechanism`, TikZ lines 876-941: body rectangle with a posterior element on top,
  light grey fill, head left, posterior up, sacral anchor as a thick line at right), extended to the WHOLE
  spine following lordotic / kyphotic / lordotic curvature, every body labelled with an upright NUMERAL counted
  from the sacrum -- not a vertebral name -- to show that after all iterations a full-spine panorama exists at
  essentially 100 %. That cartoon is the entire panel.

**Drop from the paper**
- **D** `fig1_row3_overlap.png` -- hated.
- **J** `fig13_feature_cartoon.png` -- "doesn't belong in this paper".
- The three audit figures (`fig_contribution`, `fig_device_params`, `fig_device_spread`) -- "too technical to
  interpret". They stay as documentation, not manuscript figures.

**Turn into a table**
- **H** `fig1_row5_corpus.png` -- the training-data pictograms become a TABLE.

**Revision the same night (23:00), superseding the six-figure list above:** ONE four-panel Figure 1 --
(a) the problem redrawn on LATERAL cartoon spines with NO prose, purely visual (ordinary vs extra-lumbar spine,
same field box, numerals from the sacrum differ); (b) processing chain; (c) detector + localiser architecture
immediately after the chain; (d) the sliding-window algorithm representation drawn ON the numbered panoramic
spine (crop sliding, correlation trace beneath, one-body-off peaks, search window) -- the separate mechanism
panel is removed. Figure 2 = the fluoro confirmation with the needle. The render-confirmation figure (old E) is
DROPPED. "Can't figures only contain 4 subfigures? that's 4." Result plots (naming curves, detection curve)
placed as Figures 3-4 pending his verdict; flow diagram and contribution matrix supplemental.

**Why:** he judges figures as a reader would, not as the person who made them; a figure that needs the
caption to be understood fails. **How to apply:** for any new figure in this line of work, ask whether it reads
at a glance like A, E or G; anything that looks like an audit plot goes to `docs/`, not the paper.
Related: [[schwingnet-manuscript]], [[figure-captions-terse]], [[journal-figure-and-style-rules]].
