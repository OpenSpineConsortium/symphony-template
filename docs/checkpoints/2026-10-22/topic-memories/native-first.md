---
name: native-first
description: greg's rule of 2026-10-20: before building any new feature or approach, check native GitHub, Microsoft 365 and device support first
metadata:
  type: feedback
  modified: 2026-10-20T18:26:37.171Z
---

On 2026-10-20 greg said: "add a short instruction to check these permissions for possible native feature support before building a whole new feature/approach". It is written into CLAUDE.md's Conventions as "Native first", pointing to docs/research/microsoft-365-permissions.md (the section "One request, 2026-10-20") and docs/research/device-permissions-for-a-person-like-claude.md.

**Why:** greg wants as much of GitHub's and Wayne State's Microsoft 365 native support as possible, and less custom machinery.

**How to apply:** before designing a feature, list which native feature or permission already covers it, and build only the gap. The same day greg also asked for the Outlook digest to go through GitHub Actions and GitHub's own notification email, not Wayne State's Graph mail permissions. Related: [[reproducibility-rule]], [[no-manual-steps-for-greg]].
