---
name: share-tab-state
description: The control panel's Share tab works end to end since 2026-10-20; how its permissions are checked
metadata:
  type: project
  modified: 2026-10-20T21:06:49.021Z
---

On 2026-10-20 the Share tab's Invite (PUT collaborators with the App user token) was verified working. Both SymphonyBoard installations accepted every permission that day: OpenSpineConsortium is 169803029, and greg's personal account is 170148056. The personal one had lacked Administration and nine others.

symphony-app scripts/permissions.py and permissions.yml read every installation's permissions with the App's JWT. They run weekly, by hand, and on a PR that changes them. The run goes red when an owner installation is short of something. It never asks for account permissions (codespaces_user_secrets), or for organization_* on a personal account, because no installation can ever hold those.

Site #116 names a Share refusal by its cause: not an admin (from repo permissions.admin), installation short (from /user/installations), or GitHub's own words. It is covered by checks S1-S4 in signin.test.mjs and mutants sh01-sh04.

**Why:** greg was unsure Share had ever worked. GitHub's 403 looked the same for every cause, and Invite had no test.
**How to apply:** if Share fails, run the Installation permissions workflow first. Related: [[signin-worker-deploy]].
