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

## Where it stood on 2026-10-23

The thread was resumed under the owner's new account on 2026-10-23, with no session of its own on
the grid, so everything below is read from the gate's answers on the branch grid: each answer to
schwingnet-status is a commit of logs/job-schwingnet-status.json, so `git log` over that file is a
time series (00:28, 00:35 and 01:04 UTC today), and each fetch word's answer is
logs/job-schwingnet-fetch-<id>.json.

- CADS: once ~/.hf/token.env was on the grid, the word of 2026-10-22 17:12 UTC queued job
  40710713 (hf-token, 123.3 GB) afterany the X-ray fetch 40704982. Its record moved to fetching
  (spine-datasets #159).
- RATIC: nothing was ever queued. The record's line saying the link was in ~/.rsna/ratic_link was
  wrong; the owner was asked to write it in the OnDemand shell (umask 077, chmod 600, one line),
  and the record now says so (#158).
- RSPECT: job 40703031 failed after 6 seconds with exit 1 because Kaggle answers 403 to an account
  that has not accepted the competition's rules, here gregoryschwingmdphd, the account the token
  in ~/.fluorocap/credentials.env belongs to; not the revoked token the section above guessed. The
  owner was asked to accept the rules there, after which the word goes again (#160).

### Every CT fetch waits behind one X-ray fetch

word_fetch_gated makes each CT fetch wait afterany on every live X-ray fetch (the owner's order of
2026-10-21). The one live X-ray fetch is VinDr-PCXR, job 40704982, the video-demo thread's, started
about 2026-10-22 15:39 UTC. The status answers give its landing: 81 files and 295 MB at 23:17 UTC,
86 files and 318 MB at 00:35, 88 files and 327 MB at 01:04, about 10 KB/s over the whole run and
5 KB/s over the last hour, so its 34.1 GB would take weeks. Its wall time is four days, ending
about 2026-10-26 15:39 UTC, and later if it is preempted and requeued, since a requeued job keeps
its id and the dependency holds. Behind it wait CADS (40710713), OL3I (40722025), CheXpert Plus
(40722124), MAGIC-CT (40731142), the FluoroSAM weights (40731148), the Killeen Drive archive
(40731313) and FluoroSeg (40731321), and any RATIC or RSPECT job queued from now; so do NLST
(40711959, 2.3 TB) and ReXGradient (40712197, 156 GB), queued by other words, each afterany 40704982
and one X-ray fetch of its own (40711923 and 40712010, both ended by 01:04), as their fetch answers
say. The status answer's sacct table has no dependency column, so what a job waits on is read from
its fetch answer, logs/job-schwingnet-fetch-<id>.json, never from the status. Only RATIC has a
deadline: its presigned link dies on 2026-10-28 at 02:38 UTC and its size is stated nowhere (RSNA
says over 4,000 CT exams), so a job queued today would start when 40704982 ends, no later than its
wall time's end about 2026-10-26 15:39 UTC unless it is requeued, with under 35 hours left on the
link.

The owner was given three ways out, on a card and in the reply's text: a way for one named set to
skip the wait on his say-so (recommended, and prepared as SchwingNet's draft #144, which adds
grid/fetch-now.txt with rsna_ratic_abdominal_trauma already on it and teaches the gate's fetch word
to queue a listed set with no afterany on the X-ray fetches; the owner merges it himself, which is
the word, and until then every gated CT fetch waits as before; after the merge the fetch word's
answer must show its "goes now" line, since the gate's side keeps the checkout where it is while
grid/logs/HOLD stands); letting RATIC wait and asking RSNA for a fresh link if this one dies; or
cancelling 40704982 himself. The last is his because the job is the other thread's, which he tabled on
2026-10-23 noting that PhysioNet offers the same set as one 23.4 GB zip and through AWS, and
because the gate's `stop` cancels every live job of the gate's, so it is no way to cancel one.

### Two things the resume taught

The status answer keeps of a failed fetch job's log only what grid/log-shapes.awk keeps, its
tracebacks, its start and _RC= lines, Slurm's errors and wget's and curl's status lines, since such
a job can print DICOM header values or a sign-in; for 40703031 that was the start line, DP_FETCH_RC=1
and "2 of its last 400 lines withheld", since the kaggle command's one-line 403 and the job's own
files-newer line fit no kept shape, so the cause of a six-second failure was read from what the
earlier attempt recorded, or by the owner on the grid, not from the answer. And a secret file is
written by the owner in the OnDemand shell (https://ondemand.grid.wayne.edu, Clusters, the shell),
never pasted into a chat: this account has no Remote Control session on the grid, and the earlier
one belonged to the previous account.
