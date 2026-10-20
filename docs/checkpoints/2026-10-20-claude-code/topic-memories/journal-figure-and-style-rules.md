---
name: journal-figure-and-style-rules
description: "Medical Physics figure/style rules the MPDA paper is checked against (sans-serif, gray grid both ways, ticks,  deg not deg, numbers under ten spelled out, kV not kVp) and the journal's page-estimate formula"
metadata: 
  node_type: memory
  type: project
  originSessionId: e44eca96-f48c-494d-ba1f-7dae68bdf06d
  modified: 2026-09-21T18:56:18.173Z
---

Medical Physics (Wiley) rules applied to paper/mpda (checked 2026-09-06): every figure in
sans-serif (Arial/Helvetica; TikZ Fig. 1 uses `\sffamily`, standalone export loads helvet),
black axes, gray grid on BOTH axes, major ticks out / minor ticks in, same decimals per
axis, 80 or 180 mm wide, 600 dpi; angles labeled "( deg)" not "(deg)". Text: numbers under
ten spelled out unless with a unit, "significant" only statistically, kV not kVp, CT
defined at first use in the abstract. Audit script pattern: scratch `style_audit.py`
(regex for bare single digits not followed by a unit/count noun).

NO ABSTRACT IN THE MAIN DOCUMENT for a Dataset and Software article (returned unreviewed
2026-09-21 for carrying one). PUB 3-C still requires a structured abstract under 300 words,
but it goes in the submission form's box (dist/submission/Abstract.txt), not the PDF/.tex.
main.tex keeps it behind `\ifabstract` (off); reprint check and arXiv switch it on.

Journal page estimate: 4.3 + words/3000 + (figures + tables)/1.9. It disagrees with the
REVTeX reprint in EITHER direction: with 10 floats it over-reported (11.9 vs 10 typeset);
with 6 floats it under-reported (9.75 vs 11 typeset, 2026-09-21). Check both --
`page_estimate.py` and `build.sh --reprint`. Last-page columns are balanced, so "full"
hides slack: measure it by inserting filler lines until it spills (6 lines as of ca00953).

**Why:** the user asked "you follow these image guidelines right?" and pasted the rules;
the render scripts had DejaVu Serif and no gridlines until this pass.
**How to apply:** after any figure regeneration re-run the font/size check with pymupdf
(`get_fonts()` must show only ArialMT/Helvetica) and rebuild the reprint page count.
See [[figure-captions-terse]] and [[tables-black-not-colour]].
