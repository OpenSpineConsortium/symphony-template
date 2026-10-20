---
name: hf-org-token-location
description: The anonymous-mlhc org token lives at ~/.hf_org_token in WSL and is exported as $HF_ORG_TOKEN from ~/.bashrc
metadata:
  type: reference
---

The HuggingFace **anonymous-mlhc** org token is stored in WSL at `~/.hf_org_token`
(mode 0600) and `~/.bashrc` exports it as **`$HF_ORG_TOKEN`** in every new shell. Use
`$HF_ORG_TOKEN` or `cat ~/.hf_org_token`; never paste the value into a command line or a
file that gets committed.

It authenticates **as the org itself** (`whoami` returns `anonymous-mlhc`, with an empty
`orgs` list -- that is expected and not a sign of missing scope). It grants read/write to
the private review ledgers:
`CTSpinoPelvic1K-reviews-{ribs,spine,nerve,ili,triaged,classfix}`.

Greg's **personal** token is separate, at `~/.cache/huggingface/token`, and is scoped to
the `gregoryschwingmdphd` namespace only -- it cannot touch the org, not even to open a
pull request. Two different tokens for two different namespaces; reach for the right one.

Related: [[hf-identity]], [[review-space-repos]], [[annotator-roster]], [[wsl-for-network]].
