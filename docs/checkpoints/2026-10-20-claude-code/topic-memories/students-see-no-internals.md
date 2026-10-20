---
name: students-see-no-internals
description: "Greg 2026-09-28: student-facing tools (Ashley) must not expose under-the-hood options (building containers, runtimes, QoS details); students do what they know; complexity stays with the lab admin"
metadata:
  type: feedback
---

Greg on Ashley (2026-09-28): "I'm not sure I want to give students the option to build their own singularity
container of Claude ... it would introduce complexity. I want them to just do what they know and limit how much
complexity about under the hood stuff I expose to them to avoid intimidating them."

**Why:** first-year medical students are intimidated by infrastructure; every exposed option is a support question.

**How to apply:** in student-facing UI, messages and docs offer one path (the lab's shared container, the wizard);
admin-only flags (`--build-own`, publishing containers, partitions/QoS) live in the leads section and ARCHITECTURE,
never in prompts students see. Related: [[ashley-extension-project]], [[student-onboarding-structure]].
