---
name: hf-osc-token-and-namespace
description: OpenSpineConsortium is a real HF org (admin = OpenSpineConsortiumUser); its token lives at ~/.hf_osc_token on Windows/WSL/grid and in repo .env as $HF_OSC_TOKEN
metadata: 
  node_type: memory
  type: reference
  originSessionId: e44eca96-f48c-494d-ba1f-7dae68bdf06d
  modified: 2026-09-01T14:51:41.417Z
---

**`OpenSpineConsortium` is a HuggingFace organization** (settled 2026-09-01). Greg's login
on it is the user account **`OpenSpineConsortiumUser`**, which holds **admin**. The org is
the public, permanent namespace cited by the arXiv/MDPI paper.

Getting there took a rename: the org name was first taken by a *user account*, which cannot
hold members or co-maintainers, and a user account blocks an org of the same name. The
account was renamed to `OpenSpineConsortiumUser` (Settings -> Account -> **Username**, not the
cosmetic "Full name" field) to free the name, then the org was created at it. Nothing broke
because that account had 0 datasets/models/spaces at the time.

**The token** is at **`~/.hf_osc_token`** (mode 0600) on all three machines that need it --
Windows `$HOME`, WSL `$HOME`, and the grid (`go2432@grid.wayne.edu:~`) -- and in the repo's
gitignored **`.env`** as `HF_OSC_TOKEN`. It is fine-grained with `repo.write` on **both** the
org and the user entity. Read it from a file; never paste the value into a command line, a
SLURM `--export`, or anything committed. **Do not ask Greg for it again** -- it is on disk in
four places, and if it is ever rotated, overwrite those same four.

This is the **third** HF token in play and they are not interchangeable -- see
[[hf-org-token-location]] for the other two:

| token file | authenticates as | used for |
|---|---|---|
| `~/.hf_osc_token` | `OpenSpineConsortiumUser` (admin of the org) | the **public flagship release** |
| `~/.hf_org_token` | `anonymous-mlhc` | anonymised review revisions v1-v6 + private review ledgers |
| `~/.cache/huggingface/token` | `gregoryschwingmdphd` | Greg's own namespace only ([[hf-identity]]) |

Target repo: **`OpenSpineConsortium/CTSpinoPelvic1K`**, dataset, public, v6 on `main`. Do not
confuse it with `anonymous-mlhc/CTSpinoPelvic1K`, whose branches the paper's reviewers are
still reading -- never wipe or repoint those.

Related: [[hf-org-token-location]], [[hf-identity]], [[wsl-for-network]], [[grid-access]],
[[publication-roadmap]], [[commercialization-stance]].
