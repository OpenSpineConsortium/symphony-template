---
name: chart-preferences
description: Slide figures: no sideways bar charts (donuts/lines for results); background slides get PUBLISHED figures from the cited papers, Greg obtains attribution rights
metadata:
  node_type: memory
  type: feedback
  originSessionId: f1bdbd78-151f-470b-b703-dd9af9b3fecc
  modified: 2026-09-25T23:20:41.623Z
---

Greg, 2026-09-25, on the CNS deck charts: "I hate that sideways bar chart. I prefer line graphs or pie charts." Then, on the redrawn background charts: "please pull a figure from the citation and I'll get the attribution rights" and "I like your results plots, just not the intro plots."

**Why:** the horizontal bar charts drawn for the rates, costs, prior-art, corpus, test-set and census slides read as
tables to him; a share reads better as a donut and a trend as a line.

**How to apply:** background/motivation slides should show a figure reproduced from the cited paper (open-access PMC or BMC copies fetch fine through WSL curl; mark the caption "permission pending" and Greg gets the rights), never a chart I draw from the paper's numbers. For results slides, draw a share or fraction as a donut/pie with the value in the centre
and a trend or ordered series as a line with markers; put dollar or count points on an axis as markers with their
ranges, not bars. Never a horizontal bar chart. This is a slide preference; manuscript figures follow the journal
rules in [[journal-figure-and-style-rules]] and [[tables-black-not-colour]]. Chart code for the deck lives in
`CTSpinoPelvic1K-1/paper/cns2026/make_v3_charts.py` ([[cns-deck-v2-2026-09-25]]).

Also 2026-09-25, on the CNS-template deck: "way too much text and what text there is is too small, even the figure legends and axis titles are tiny." **How to apply:** slides carry 3-4 lines of 18-20 pt, titles 30 pt; charts drawn at 17-30 pt type; a manuscript figure goes on a slide one panel at a time (crop by the white gutters, add slide-size labels with PIL, or draw the legend as coloured slide text) so its 8 pt print lettering scales about 2x; never a whole multi-panel print figure on one slide.

2026-09-26, on the power/census slides: "use the exact power chart from the supplementals with the n = estimated if I screen the entire CT corpus ... fuck the map, just visually represent the quantity of each somehow, it doesn't have to be a plot ... mostly figure and not a bunch of white space with tiny text" and "you could increase the axis title and legend etc. on the power chart to optimize for PowerPoint". **How to apply:** when a manuscript figure exists, reproduce it with the manuscript's own drawing code (import the tool, raise its font constant) and add the new marks on top; never redraw it in my own style. Quantities can be a pictogram/waffle with big numbers. A slide is the figure filling the content area plus one caption line.
