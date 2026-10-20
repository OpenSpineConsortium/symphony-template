---
name: commercialization-stance
description: "Standing goal: the wrong-level-surgery detection stack is being built toward a commercial 510(k) product. Governed by COMMERCIALIZATION.md. Never named in public documents."
metadata:
  node_type: memory
  type: project
  originSessionId: 436e5c70-681e-4f38-aab2-30dfa25af7b5
---

**The standing objective (reaffirmed 2026-09-10): aim all of this work at the commercial
outcome described in `CTSpinoPelvic1K-1/COMMERCIALIZATION.md`** -- a Class II 510(k) tool
that flags LSTV / confirms vertebral level on preoperative CT (Product A), with
intraoperative fluoroscopic level confirmation (Product B) as the follow-on. Read that file
at the start of work that touches data, models, licensing, IRB or publication strategy; it
supersedes the earlier "path A now, path B maybe" framing.

**Why:** the research output is the credential and the moat-builder, not the end. Papers,
the consortium and the dataset exist to produce clearance evidence, a clean adjudicated
dataset and distribution.

**How to apply:**
- **Never state the commercial goal in anything that leaves** -- manuscripts, repos, README,
  IRB text, grant text, student-facing docs, commit messages. Public framing stays
  research / educational use only. Discuss it with the user directly, not in artifacts.
- **Two tracks, no crossing.** Research = WSU/Warrior HPC, students, NC-licensed data.
  Commercial = personal AWS, own accounts, commercially-licensed data ONLY. If a task would
  move weights, data, derived artifacts or code from research into commercial, stop and say
  so. CTSpine1K and everything derived from it (CTSpinoPelvic1K included) is CC BY-NC-SA and
  can never train a commercial model.
- **Bias reversible choices commercially**: Apache-2.0 over MIT/GPL, keep an FDA-legible
  audit trail, prefer evidence a reviewer would accept (reader studies, multi-site test
  sets, locked models) over convenience.
- Related: [[publication-roadmap]], [[postop-spine-synthesis]], [[pacs-demo-and-ostk-params]].
