# Fetching the granted gated CT sets through the gate

Source: the thread "Granted datasets onto the grid" in the project symphony_2, 2026-10-22. The work
is SchwingNet #113 (merged as f4fc504) and the spine-datasets claims #86 (CADS, draft #159), #87
(RSNA RATIC, draft #158) and #88 (RSNA RSPECT, draft #160).

## Why a new gate word

Three sets the owner already has access to need a credential to download: CADS through a Hugging
Face token, RATIC through a presigned link from the RSNA MIRA page, and RSPECT through a Kaggle
token. The spine-datasets promoter fetches only public manifests and never holds a token, so it
cannot take them. SchwingNet's grid/run-platform-fetch.sh already knew how to fetch each one (its
GATED_LIST, routes hf-token, curl-link and kaggle), but only as part of the whole chain. A session
that may not run grid shell commands needed one word per set.

## What the gate now does

`fetch <id>` in SchwingNet's grid/gate.sh takes, besides the X-ray ids, the three ids of the gated
list (hf_cads_unique, rsna_ratic_abdominal_trauma, rsna_rspect_pe). CT-RATE and NLST stay refused,
since they are submitted only on the owner's own word and number. Before anything is queued the
login node checks that the id's token or link file exists at mode 600 or 400, reading only its
mode and never its contents, so a missing secret refuses with exit 2 and queues nothing. The job
waits (afterany) on any live X-ray fetch, so X-ray keeps coming first; it refuses while the same
set is still live, and is recorded as dp_<id>. The files land at
/rs/rs_grp_oschome/go2432/data/<id>/raw. A session sends it through symphony-template's
grid-accounts.yml with action job and job schwingnet-fetch-<id>; the answer is on the branch grid
at logs/job-<job>.json.

The same check changed the whole chain's --gated run: a gated source whose file is missing is now
left out with a line saying so, and the rest is submitted, where before one missing file stopped
everything.

## What the first sends found

- RATIC: refused, no ~/.rsna/ratic_link on the grid, though the record said the link was saved.
  The link expires on 2026-10-28 at 02:38 UTC.
- CADS: refused, no ~/.hf/token.env.
- RSPECT: ~/.fluorocap/credentials.env exists; job 40703031 ran and failed after 6 seconds with
  exit 1. The log is withheld by the gate; the likeliest cause is the Kaggle token revoked earlier.

All three now wait on a secret only the owner can type. Once a file is written, the word is sent
again, schwingnet-status reads the result, and the set's record takes the job and the outcome
through its claim's pull request.

## What did not work on the way

The protocol check failed twice because main moved between the pull request event and its
checkout; GitHub's update-branch, not a hand merge, brought it green. SchwingNet's pre-push hook
refuses a push while any untracked file is in the tree, so a hook a usage tool leaves under
.githooks goes in .git/info/exclude.
