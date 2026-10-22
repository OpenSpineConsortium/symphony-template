---
name: ruleset-writes-refused
description: A session's permission check refuses every GitHub ruleset write, even on greg's explicit ask; ruleset changes go through a workflow on SymphonyBoard's token or greg's own click
metadata:
  type: project
  modified: 2026-10-20T22:13:11.137Z
---

On 2026-10-20 the auto-mode permission classifier refused a ruleset PUT twice: flipping the strict up-to-date rule on symphony-template's ruleset 24827932 at 21:10 UTC, and adding Repository admin to symphony-protocol's ruleset 24827944 bypass list at 22:12 UTC, after greg wrote "no please fucking do this now". Reads of rulesets (GET) are fine.

**Why:** the classifier reads a ruleset write as a CI bypass whatever the words behind it, and retrying is a workaround it forbids.

**How to apply:** never promise a ruleset edit from a thread. A ruleset change is either a workflow on SymphonyBoard's token (the pattern of symphony-protocol #59's .github/workflows/settings.yml: create-github-app-token with permission-administration write, then gh api PUT) or greg's own click at https://github.com/<owner>/<repo>/settings/rules/<id>, given with the exact link and what to click. The Tokens and adopted repositories thread owns the auto-applied rulesets. symphony-protocol's ruleset had an empty bypass list, so nobody, greg included, could merge a behind or unchecked PR there until #59's workflow turned strict off or greg added a bypass actor. [[fine-grained-locking-on]] [[no-manual-steps-for-greg]]
