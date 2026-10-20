---
name: local-level-identity-thesis
description: Reframing of CTSP1K around locally predictable level identity -- a net learns what L4 looks like instead of counting down from C2
metadata:
  type: project
---

Greg's framing as of 2026-08-24: the dataset's central claim should be that **each vertebra's
identity is predictable from its own morphology**, not from its position in a count. A network
should be taught what L4 looks like rather than taught to count down from C2.

**Why:** every counting method needs an unambiguous starting landmark, and C2 is the only one.
These are spine-limited CT colonography scans that begin in the mid-thorax, so counting is
simply unavailable -- which is exactly why sacralisation and lumbarisation cannot be told apart
here (see [[thoracic-gt-fov-limited]]). Local morphology is the only signal that survives a
partial field of view. It is also what makes the collection valuable: 802 records on one
screening protocol means between-scan variation is anatomy rather than acquisition.

**How to apply:** prefer count-free, locally-measurable properties throughout -- the paper
already does this, and the gallery cards should too. When a case is genuinely ambiguous
(1090's rib-bearing L1; 1153's eleven rib pairs), say the reading is undecidable from the
field of view and that morphology is the better hint, rather than asserting a number. Note the
tension recorded in [[spondylolysis-and-border-anomaly-findings]]: morphology is *local*, and a
thoracic body genuinely looks different from a lumbar one, so local prediction is plausible --
but the paper must state that this is a hypothesis the dataset enables, not a result it shows.
Related: [[label-scheme-v4-vs-ostk]], [[lstv-reread-queue]].
