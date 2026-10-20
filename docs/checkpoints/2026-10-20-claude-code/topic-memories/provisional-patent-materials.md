---
name: provisional-patent-materials
description: "Where the SchwingNet provisional + WSU invention disclosure live (spine-program provisional_patent/, merged PR #212, 2026-10-20) and Greg's informed choice to keep confidential parts there"
metadata:
  node_type: memory
  type: project
  originSessionId: 0599380b-0d32-4e19-b5be-65bdd1017566
  modified: 2026-10-20T04:16:41.495Z
---

Since 2026-10-20 every SchwingNet patent document is in spine-program `provisional_patent/` (issue #211, PR #212,
merge 240cabc). Its README says which packet is current and what is confidential.

- **Current provisional packet** = `provisional_patent/provisional/` (SPECIFICATION, CLAIMS, COVER_SHEET,
  FILING_CHECKLIST, README) of 2026-09-18, from spinesurg-ct-nnunet/docs/provisional/ (commits b063b3c, df26da0,
  19d8dbf). The only provisional draft on the laptop. It frames the invention as chain-linking of overlapping exposures
  plus commanded acquisition; the later WSU disclosure (2026-09-25, `wsu_tto/TTO_package_2026-09-25/`) frames it as
  Part A (CT transitional classifier) + Part B (single-exposure C-arm naming). No provisional was drafted after 25 Sep.
- Originals stay at `Desktop\private_ip\` and spinesurg-ct-nnunet/docs/. Grid evidence bundles:
  /rs/rs_grp_oschome/go2432/private_ip/git_bundles_2026-09-26/.
- Whether the TTO package was actually SENT is not recorded anywhere found (signed + zipped + cover email drafted 25 Sep).

**Why:** Greg was told on 2026-10-20 that spine-program is INTERNAL (gh: visibility INTERNAL, isPrivate true; 1 org
member = Greg, 1 outside collaborator = a student) and that DISCLOSURE_MEMO.md is counsel-only and the Part B manuscript
is the unpublished first disclosure. He answered "Everything". Root .gitignore still lists `private_ip/`; the folder
name `provisional_patent/` is the deliberate exception.

**How to apply:** don't re-ask whether the confidential parts may sit in spine-program. Do keep them out of every
PUBLIC surface (repos, site, Spaces, talks). Student usernames in the two scrub text files were redacted to
[student A]-[D]; binaries (CNS decks, Part B PDFs) carry student author names unchanged. The Neurocheck provisional
(Desktop zip, Feb 2025, different invention) was deliberately left out: "just the schwingnet material".

Related: [[commercialization-stance]], [[symphony-spine-program-adoption]], [[spine-program-no-manual-edits]].
