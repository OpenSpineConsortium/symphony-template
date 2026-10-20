---
name: u251-project-containment
description: "Greg 2026-09-26: the U251 LITT study (Abstract 418 deck, GSEA, analyses) lives ONLY in the u251 dir and its git repo; checkpoints in its RESUME.md, never in spinesurg's RESUME; repo is PUBLIC"
metadata:
  node_type: memory
  type: feedback
  originSessionId: f1bdbd78-151f-470b-b703-dd9af9b3fecc
  modified: 2026-09-26T09:10:19.190Z
---

Greg (2026-09-26): "This project should be contained in the u251 dir and the respective git repo."

**Why:** I had written U251 checkpoints and pending-job tables into spinesurg-ct-nnunet/docs/RESUME_2026-09-22_PM.md
(five commits), the Abstract 418 build imported plumbing from CTSpinoPelvic1K-1/paper/cns2026, read data from a session
scratchpad, and wrote the deck into CTSpinoPelvic1K-1. All moved on 2026-09-26 (u251 commit 89a7182, spinesurg daea813).

**How to apply:**
- Repo: `~/OneDrive/Desktop/u251-xenograft-murine-RNASeq-study` = github Gregory-Schwing-MD-PhD/u251-xenograft-rat-RNASeq-study,
  branch research-letter-expansion. It is PUBLIC (GitHub API 200): nothing third-party or confidential goes in git
  (CNS template gitignored in SLIDES/templates; MBR/ manuscript untracked).
- Checkpoints / pending grid jobs for this study: u251 `RESUME.md`, not any other repo.
- Scripts read repo-relative paths (`SLIDES/u251_paths.py`; `SLIDES/fetch_grid_outputs.sh` fills them locally); grid
  work runs in `/wsu/home/go/go24/go2432/u251-xenograft-murine-RNASeq-study` (its clone is behind; rsync, don't pull).
- Outputs (decks, figures) are written inside the u251 dir only.
Related: [[cns-abstract-418-deck]], [[u251-translation-fall-il68b]].
