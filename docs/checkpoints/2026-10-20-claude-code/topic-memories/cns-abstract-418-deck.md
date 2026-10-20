---
name: cns-abstract-418-deck
description: "CNS 2026 Abstract 418 talk SSTU02 (LITT glioblastoma recurrence, U251 rat xenograft; Mon 2 Nov 7:00-7:06 AM) - CURRENT v5 2026-09-27 (46 slides: v4's 21 + 5 main + 20 backups, SLIDES/14_build_deck_v5.py); the instrument-seeding slide is Greg's headline"
metadata:
  node_type: memory
  type: project
  originSessionId: f1bdbd78-151f-470b-b703-dd9af9b3fecc
  modified: 2026-09-27T10:01:43.295Z
---

**CURRENT: v5 (2026-09-27), `SLIDES/CNS2026_Schwing_Abstract418_CNStemplate_v5.pptx`, 46 slides** =
v4's 21 unchanged + 5 main + 20 backups. Built by `SLIDES/14_build_deck_v5.py`, which OPENS the v4 deck and inserts
(v4's builder is never edited); figures by `SLIDES/13_v5_figures.py`, which imports the manuscript's own drawing code
(`MBR/nature_draft/figures/make_figures_rna.py`, untracked) and re-saves each panel at slide type, and copies the
R-drawn grid panels. Plan + cut order: `SLIDES/STORY_v5.md`. Numbers come from `figures_cns/v5_data/*.json|tsv`
(byte copies of the grid outputs); the builder types no result number and asserts the load-bearing ones.

**New main slides:** 9 composition split exactly (C-share 0.47, 13 % of the 133 bulk DE genes composition-dominant) -
10 where the mesenchymal shift comes from (host myeloid) - **14 tumour in the opposite hemisphere and what it means in
the OR** - 15 methylation (nothing survives correction; the difference is tumour content, under all 14 exclusion
lists) - 18 the experiment six animals size (rats-needed curves). Backups B8-B27 carry every other result.

**Greg's framing, 2026-09-27 (binding):** even if the contralateral signal is carry-over, that IS the positive finding
for a neurosurgical audience - tumour cellularity is detectable molecularly on what the instrument touched, and
surgeons should be aware of seeding distant brain. Anchor checked against Europe PMC: malignant cells on gloves or
instruments in 14/47 canine cancer operations (30 %), 57 % involved v 19 % clear margins, P = 0.016 (Orjefelt,
J Small Anim Pract 2026;67:528-533); seeding case reports Steinmetz 2001, Perrin 1998, Bouillot-Eimer 2005, Bekar 2010.
New refs numbered 21-28; v4's 1-20 untouched.

**Rendering is part of the build.** PowerPoint COM exports the deck to PNG (`$ppt.Presentations.Open(...).Export(dir,
"PNG", 1920, 1080)` in PowerShell; LibreOffice is NOT installed on this machine). Looking at the render caught three
defects the numbers did not: text colliding with the footer on two slides, a dilution null quoted in the wrong
direction, and a nine-panel figure too small as a top figure. Always export and read the slides before reporting done.

v4 (13 + 8 backups, `09_build_deck_v4.py`, `STORY_v4.md`) is still the 6-minute talk; v5 adds two results beats and a
cut order, since 8 minutes of main slides now exist against a 6-minute slot. Never cut slides 7, 9 or 14.

**Indrani Datta's credential is DHI** (Greg, emphatic); the JNS 2026 author list prints PhD and is wrong for her.
Sequencing: NextSeq 2000, 2x100, SMARTer Stranded Total RNA-Seq v2 Pico, one run over TWO lanes. Rats 64-71; 64 is the
failed graft, 65 absent. Related: [[u251-project-containment]], [[chart-preferences]], [[cns-deck-v2-2026-09-25]],
[[u251-translation-fall-il68b]].
