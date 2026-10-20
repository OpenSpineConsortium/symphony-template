---
name: student-onboarding-structure
description: "Where student onboarding lives (Student_Projects root CLAUDE.md, GETTING_STARTED.md, /onboard, projects/IDEAS.md, make_env/get_dataset jobs) and the grid-access facts (Google Authenticator via OnDemand 2FA Setup, SSH key bypasses the OTP)"
metadata: 
  node_type: memory
  type: project
  originSessionId: e44eca96-f48c-494d-ba1f-7dae68bdf06d
  modified: 2026-09-07T18:05:12.738Z
---

Student onboarding (built 2026-09-07) is one command: `curl -fsSL
https://openspineconsortium.com/onboard.sh | bash` (or `irm .../onboard.ps1 | iex`), scripts
at the website root; it installs git/gh/VS Code+extension/Claude Code, clones the PUBLIC
`OpenSpineConsortium/Student_Projects` into `~/OpenSpineConsortium/Student_Projects` and runs
`claude "/onboard"`. Proposals and project work live in the PRIVATE
`OpenSpineConsortium/Projects` repo, cloned inside the public one as `projects/` (gitignored
there), so PRs stay private; students are added as collaborators after emailing Greg. Pieces: root `CLAUDE.md` (lab in one page, read on
open), `GETTING_STARTED.md` (seven human steps), `.claude/commands/onboard.md` (resumable
setup: tools, SSH key, grid clone, `templates/make_env.sh` and `templates/get_dataset.sh`
as SLURM jobs, demo, then project choice), `projects/IDEAS.md` (about twenty ideas with
measurement, comparison, difficulty, source), `templates/CLAUDE.md` per project. The primer
at openspineconsortium.com/onboarding mirrors it. Local clone:
`C:\Users\grego\OneDrive\Desktop\Student_Projects`, branch `main`.

Grid access facts: WSU grid account request via tech.wayne.edu/kb/high-performance-computing
(sponsor Greg, ~2 business days, hpc@wayne.edu); second factor is Google Authenticator set
up through ondemand.grid.wayne.edu -> Interactive Apps -> 2FA Setup (VPN needed); an SSH key
installed with `ssh-copy-id` (one password + code) lets `ssh -o BatchMode=yes grid` run
with no prompt, which is what Claude needs. Student environments go to `~/miniforge3`
(Greg's own is `~/mambaforge`); dataset path convention `~/data/CTSpinoPelvic1K`.

**Why:** Greg wants onboarding "literally seamless"; every student setup question should be
answerable from these files rather than from him.
**How to apply:** when changing the workflow (grid rules, label ids, dataset path), update
root CLAUDE.md, templates/CLAUDE.md, onboard.md and the primer together. See
[[grid-access]], [[scheme-bone-hardware-only]].
