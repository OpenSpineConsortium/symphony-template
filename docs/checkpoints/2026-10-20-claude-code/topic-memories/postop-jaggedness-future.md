---
name: postop-jaggedness-future
description: FUTURE -- fix post-op synthesis voxel roughness so endplates can be auto-remeasured (instead of analytic carry-forward)
metadata: 
  node_type: memory
  type: project
  originSessionId: 436e5c70-681e-4f38-aab2-30dfa25af7b5
---

The post-op synthesis (rotate/bend the spine, resample the voxels) leaves **microscopic voxel roughness** on the vertebral endplates. It's invisible to the eye (the image looks smooth/good), but the automatic endplate plane-fit in [[postop-spine-synthesis.md]] trips on it and returns wrong angles (measured LL *dropped* 45.7->~24 when it should *rise* to ~55).

**Current workaround (decided 2026-06-23):** don't re-measure the resampled image at all. Compute post-op numbers + overlay **analytically** -- take the clean pre-op endplate measurements and apply the known bend rotation (proven exact: rotate L1 by +9.3 deg -> 45.7->55.0 deg). The resampled image is used for *display only*.

**Future goal (user wants):** fix the jaggedness so automatic re-measurement works again -- e.g. anti-aliased/higher-order label resampling, morphological endplate smoothing before fitting, a more robust endplate fitter, or per-vertebra rigid placement (no shear) instead of a continuous per-voxel rotation field. Then the synthesis becomes self-validating again.
