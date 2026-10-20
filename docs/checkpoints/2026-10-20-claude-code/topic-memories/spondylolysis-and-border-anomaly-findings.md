---
name: spondylolysis-and-border-anomaly-findings
description: "Two paper-worthy findings from the 2026-08-02 spine review session -- LCC postprocessing destroys spondylolytic vertebrae, and T-L/L-S border anomalies co-occur"
metadata: 
  node_type: memory
  type: project
  originSessionId: 601aef39-3c17-45b7-9ce6-4f172acc8773
  modified: 2026-08-02T22:11:24.278Z
---

Two findings from the 2026-08-02 spine-review session, neither recorded in code.

**1. Largest-connected-component postprocessing destroys spondylolytic vertebrae.**
A vertebra with bilateral pars defects is genuinely TWO fragments -- body + pedicles +
superior facets in front, "loose lamina" (lamina + spinous + inferior facets) behind.
LCC postprocessing (a default in several vertebra segmentation pipelines, incl. some
nnU-Net configs) silently deletes the loose lamina. At ~4-8% prevalence of isthmic
spondylolisthesis this is a systematic failure on exactly the surgical population the
dataset targets. Worked example: case 155__fused (flagged needs_expert; L5 body
fragment 132,947 vox + lamina 29,406 vox, 8.6 voxels apart, lamina wedged between the
L4 and S1 labels). Same reason "one bone = one connected component" is the wrong
invariant -- see [[rib-qc-gates-never-block-lstv]].

**2. Thoracolumbar and lumbosacral border anomalies co-occur.**
Numerical variation of the spine is global, not local: the Hox expression boundaries
that set where ribs stop and where the sacrum starts move together. So hypoplastic /
absent 12th ribs are associated with LSTV, and vice versa. Consequences: (a) the
ribless-T12 cases are ENRICHED for LSTV and vice versa, so triaging them into separate
queues splits one correlated population -- relevant to [[lstv-reread-queue]]; (b) a model
that counts from the rib anchor fails preferentially on LSTV cases, because that is
exactly where the anchor itself has moved -- relevant to [[rib-approach-ts-trust]].
TLTV as a named entity is thin in the literature compared to LSTV, which is itself a
niche worth claiming.
