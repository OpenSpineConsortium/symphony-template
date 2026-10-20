---
name: schwingnet-manuscript
description: "SchwingNet/ (started 2026-09-22) -- the focused RSNA AI manuscript built ONLY from rigor-passing numbers, with CLAIM map, ATLAS cards, rigor fixes, data-contribution analysis, and the algebraic rule removed; workflow wf_0b84540b-455"
metadata: 
  node_type: memory
  type: project
  originSessionId: f1bdbd78-151f-470b-b703-dd9af9b3fecc
  modified: 2026-09-23T00:06:19.569Z
---

Greg, 2026-09-22 evening: create `spinesurg-ct-nnunet/SchwingNet/` -- an RSNA AI article whose introduction and
motivation are SYNTHESISED from the abandoned/partial manuscripts under `paper/` (no more internet research; "the
motivation has been researched like 5 times"), containing only data from the rigorous approach, following CLAIM,
the RSNA AI author instructions, and the cai4cai RSNATemplate; plus an ATLAS card (RSNA/ATLAS schema 2025-11)
for the best model and for the final training dataset. **Remove all mention of the R + C = 22 rule** -- it does
not hold ([[anomaly-rule-rc22-evaluated]]); the evaluation doc stays as the record.

**Standing rules for that folder:** every number carries a case-clustered interval, a stated operating point
(abstention coverage beside every headline) and a source file listed in `SchwingNet/NUMBERS.md`; nothing from
the leaked banks (allspine v2/v6/v7; v8 for VerSe; anchor_drr; vindrps) or from `verse_drr` millimetres; 3,000
words, 250-word structured abstract, <=6 figures of <=4 panels (Figure 1 must split), <=4 tables, <=35 refs; no
"origin"; no commercial/regulatory naming. Both `pubs.rsna.org` pages 403 -- limits come from
[[rsnai-author-instructions]]. Template + ATLAS schemas were fetched raw from GitHub and are pasted in the
workflow prompt (`workflows/scripts/schwingnet-manuscript-wf_0b84540b-455.js`).

**The DeepFluoro question** (why does it contribute so much; weight / expand / exclude sources by a measurable
quality?): the single-training-device arms `dc_A_held_<X>_1dev_<Y>` exist for all six ordered pairs under
`~/spine-detector/runs/devcorpus/`; `docs/MODEL_CARD.md` sec. 4.6 has the held-out rows. Known point: Elekta held out,
Surgio alone 0.1221 -> Surgio + Cios 0.3024 (one seed). Answer lands in `SchwingNet/results/DATA_CONTRIBUTION.md`.

Rigor items the build must address: A1-A9 in [[rigor-audit-findings]] and `docs/RESUME_2026-09-22_PM.md`.
Resume from that file's SCHWINGNET section. Related: [[resume-2026-09-22-pm]], [[identity-audit-findings]].
