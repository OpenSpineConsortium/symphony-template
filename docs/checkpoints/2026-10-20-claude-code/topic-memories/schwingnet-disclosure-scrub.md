---
name: schwingnet-disclosure-scrub
description: "2026-09-26 scrub of public SchwingNet (Part B) disclosures: Greg's rule is make SchwingNet private, leave OSC/student/CT-side work public; what was done, what only GitHub Support can do"
metadata:
  node_type: memory
  type: project
  originSessionId: f1bdbd78-151f-470b-b703-dd9af9b3fecc
  modified: 2026-09-26T20:36:37.570Z
---

Greg, 2026-09-26: "I don't think it's necessary to erase the OSC and student work ... Just make sure anything that is
directly a part of the current SchwingNet work is private." The full plan is SCRUB_PLAN.md, now at
`Desktop\private_ip\TTO_package_2026-09-25\` (moved out of the public CTSpinoPelvic1K folder with the disclosure forms and idf_work).

**Done 2026-09-26:**
- Evidence bundles: all four repos, orphan SHAs included, at
  `/rs/rs_grp_oschome/go2432/private_ip/git_bundles_2026-09-26/`, sha256 verified.
- `Gregory-Schwing-MD-PhD/XRSpinoPelvic1K` made private via the REST API, using the token in WSL `~/.git-credentials`
  (no gh CLI is installed). It had `localize.py` (level under the C-arm centre) and a Cerner `.ica` credential file.
- CTSpinoPelvic1K 45df97d, pushed to both remotes: `paper/cns2026` untracked, ROADMAP "Landmark model (XR)" section cut.
  History not rewritten, since Zenodo cites the tag.

**Pending, Greg must file (drafts and SHA lists in `Desktop\private_ip\github_purge_requests\`):** GitHub Support
purges for the orphaned `proposals/**` (171 commits, a959ff7, both CTSpinoPelvic1K networks) and for the 5 detector
ONNX files on the OSC site (106 pre-rewrite SHAs). Until then all of these return HTTP 200 by SHA.

**How to apply:** never re-add paper/cns2026 or SchwingNet level-ID text to a public repo ([[fluorocap-repo-private]]);
leave the CT-side Part A docs and scripts, Student_Projects, OSC site text and ostk as they are. Related:
[[commercialization-stance]], [[level-service-serving]].
