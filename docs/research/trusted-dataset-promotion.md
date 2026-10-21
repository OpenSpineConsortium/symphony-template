# A reviewed pull request as the only way into a read-only shared data tree

Source: the thread "Automated dataset PR review", 2026-10-21, on the owner's ask to "set up an
automated review system for pull requests to be evaluated for meeting all those standards ... so
that these requests can be written into read only space", after a collaborator's Slurm fetch job
on OpenSpineConsortium/spine-datasets (issue #31, the Fraiwan spine X-ray set, pull request #99)
stopped because her grid account could not create /rs/rs_grp_oschome/shared/datasets. The work is
spine-datasets issue #100, pull request #101.

## The question

Collaborators obtain public datasets for the owner's measurement work. The bytes belong on
Wayne State's grid under one shared tree that collaborators read and never write. Granting each
collaborator a write entry in that tree's access list (the collaborator's own proposal, mkdir and
setfacl) would make the tree as trustworthy as the least careful account that can write it, and
would need a hand step for every new collaborator. What lets a collaborator's work reach the tree
with no write access of theirs, no hand step per set, and a check before anything lands?

## Native first: what already covers it

- GitHub's required status check, already on the default branch through the template's ruleset,
  holds every pull request to scripts/check.sh and the job check: the review needs no ruleset
  change, only a step inside the check that is already required. A session cannot write rulesets
  (the project's memory, ruleset-writes-refused), so a new required check name would have been a
  hand step; a step inside the existing one is not.
- The merge itself is the human gate: the owner, or a session on the owner's standing permission,
  merges. GitHub's API says who merged a pull request (merged_by) and which pull request a commit
  belongs to (commits/{sha}/pulls), so the grid side can verify the gate after the fact without a
  token of the repository's own reaching the grid.
- The sources publish checksums: Mendeley Data's public API gives every file's sha256 and size
  (read on 2026-10-21 for xkt857dsxk version 1: six zips, 85,596,630 bytes, matching the
  collaborator's own count), Zenodo's API gives md5. The manifest is written from the source's
  own list, so the check compares the download with what the publisher states, not with what a
  collaborator measured.
- The grid already has the owner's identity in a batch-capable form: gh signed in as the owner for
  hpcworker, sbatch, and the reqp/requeue partition with afterany chains that come back after a
  preemption, the shape hpcworker's runner chain uses.

What none of these do: act on the grid as the owner after a merge. The hpcworker runner (the
self-hosted runner behind grid.yml) cannot, by design: its container sees no home and no lab
volume, so a workflow's code never holds the account's reach (docs/setup/grid.md). The gap is a
small pull-based promoter under the owner's account, which reads GitHub and is never reached from
it.

## The design

1. The collaborator's pull request carries the record (status fetching) and manifests/<id>.json:
   every file's https link on the source's own site, bytes, and sha256 (or the source's md5).
2. tools/dataset_review.py, in the required check, fails on: a manifest that does not hold (the
   record's link and licence copied exactly, an open licence or a recorded grant, never "to
   confirm"; paths under raw/ with no ".."; links on the source's site with no token, key or
   signature; sizes that add up; checksums of the right shape); a word the confidentiality rule
   bans in an added line of a record, manifest or letter, or in the pull request's title or body;
   a history entry changed or removed; a data file committed; a token in the title or body. It
   flags for the merger: wording that reads as something binding done in the owner's name, a
   licence or link changed other than by replacing "to confirm", a non-commercial or
   no-derivatives licence, and any change to the promoter's own code or space budget. X-ray before
   CT is an order, not a gate: the promoter takes X-ray groups first.
3. After merge, tools/promote.py, run every ten minutes inside a self-renewing Slurm chain
   (grid/promote.sh) as the owner's grid account, acts only on a manifest whose last change came
   from a pull request into main merged by an owner login; downloads inside the job, checks the
   bytes and checksum of what landed, renames the checked tree into shared/<id>/raw in one step,
   makes it 0444/0555, writes PROMOTED.json, and opens the record's update to fetched as a pull
   request with auto-merge, which the same required check reviews. It takes its own code from
   main only under the same provenance rule, so a collaborator with write access who merges alone
   can neither trigger a fetch nor change what runs as the owner.
4. Nothing under the shared tree is deleted or overwritten: a failed or mismatched download stays
   in .incoming-<job> to be resumed, and an existing raw/ that differs is left and reported.

## What the adversarial review found

The review before merge found that "an owner merged it" is weaker than it sounds where the
ruleset asks for no approving review and a session merges on green, as this project's do:

- A push by anyone who may write to the promoter's own record branch, before its auto-merge
  landed, would have been merged as the owner's, carrying code or a manifest with it. Auto-merge is
  now pinned to the exact commit the promoter wrote (GraphQL enablePullRequestAutoMerge with
  expectedHeadOid), and nothing from a promote/ branch is ever acted on but its one record.
- What runs as the owner, the promoter's code and its space budget, needs more than an owner's
  merge: the owner must have opened the pull request and no commit in it may be tied to another
  account. A session's commits, made under its own name, are tied to none, so the owner's sessions
  still change it. The review fails such a change in anyone else's pull request too, though only
  the promoter's own rule binds, since a pull request can edit the review.
- A wrong file of the right size was never fetched again, a stray file could land in raw/, a busy
  scheduler could fork or end the chain, and the first copy of the code was taken from main
  unchecked. Each is fixed: a wrong whole file is removed and fetched afresh, singleton jobs and a
  lock keep one pass at a time, the job keeps its own clock, and the owner names the commit the
  chain starts from.

What remains: a manifest an owner's session merges on green is fetched; its blast radius is data
under one id's folder, bounded by the budget, never code.

## What stays a hand step

One, once: the owner starts the chain in a grid shell (two lines, in grid/README.md). It cannot be
done from a cloud session today: the ssh gate takes only the runner chain's three words, and the
Remote Control route into a grid worker waits on that worker being signed in to the project's own
Claude account (the project's memory, grid-job-handoff-path). Creating the shared root is not a
hand step: the promoter, running as the owner, makes it.

## Open questions, not yet measured

- The compute nodes' python3 version: the promoter is written to Python 3.6 and checked for 3.6
  syntax, but has not run on an EL7 node yet.
- Whether Mendeley's file_downloaded link redirects to a presigned store the compute node reaches;
  curl follows redirects and the checksum decides.
- Whether gh on a compute node finds the owner's sign-in in the home, as hpcworker's chain assumes.
