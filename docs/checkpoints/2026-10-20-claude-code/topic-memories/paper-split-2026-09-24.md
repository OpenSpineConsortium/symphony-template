---
name: paper-split-2026-09-24
description: "Greg 2026-09-24 19:25 -- the LevelCheck / surgeon comparison is PAPER 2; paper 1 (SchwingNet, five figures) reports cross-validation, the unseen-C-arm test and the data case, and scores NO G3 test transitional person (SchwingNet/PAPER1_SCOPE.md); supersedes the six-figure plan's Figure 6"
metadata:
  node_type: memory
  type: project
  originSessionId: f1bdbd78-151f-470b-b703-dd9af9b3fecc
  modified: 2026-09-25T01:09:31.115Z
---

On 2026-09-24 Greg moved the pre-specified LevelCheck / registration-assisted-surgeon comparison out of the
SchwingNet manuscript into a second paper. Paper 1 = five figures (phenotypes, embedding, network, one exposure,
persons needed), three tables, title "SchwingNet: a convolutional-recurrent network for level naming in spine
surgery, robust to transitional anatomy". Everything removed sits verbatim in
`SchwingNet/paper2_levelcheck/MOVED_FROM_PAPER1.md`; the rule is `SchwingNet/PAPER1_SCOPE.md`.

**Why:** ordinary-only superiority over 0.976 is unreachable (n_min 152 zero-error persons; only 13 reference-ordinary
COBRA persons are in the open gate; the automated reference's PPV is 0.971; the endpoint is per person, all bodies
correct), and the transitional strata that make the comparison cheap (19 persons vs 0.822) need human reads that
do not exist yet. Greg first asked to keep an ordinary-only comparison ("if it crosses 97 %, revert"); the numbers
said it cannot, so the removal stood.

**How to apply:** never score or report a G3 test transitional person in paper-1 work (the blinded gate 40438005
and LEVELCHECK_MODEL.md s1-s15 stay valid for paper 2); the open gate's ordinary-person result, if ever printed in
paper 1, must be logged as "H6 seen" in paper 2's ledger; the paper-2 path to "outperforms" is human reads of the
~90 transitional COBRA test candidates, not more ordinary scans. Related: [[six-figure-paper-plan]],
[[resume-2026-09-24]], [[flagship-paper-frame]].
