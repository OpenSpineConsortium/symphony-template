# Auditing the spine dataset records against the owner's own mail and the grid

Source: the thread "Dataset status audit", 2026-10-21 and 2026-10-22, on OpenSpineConsortium/spine-datasets.
The work is in spine-datasets #98 (issue #97), #104 (#103), #112 (#107), #114 (#113), #118 (#117) and
#132 (#131). This note was left unwritten when every thread stopped on 2026-10-22 at 00:01 UTC
(symphony-template docs/checkpoints/2026-10-22/handoff.md, part 6, item 6), and it is written here now.

## The question

Every record in spine-datasets (datasets/<id>.json) says where its dataset stands: a status, a
route, a result, a history that only grows, the obstacles and the next step. The collection began
from a sweep of the literature, and the owner had already done a lot by hand before the repository
existed: letters, agreements, credentials, and sets already copied to the grid. A record that says "to ask" about a set
the owner has asked for, or holds already, wastes a collaborator's day and can lead to a second
letter going to the same author. How does a session find out what the owner has already done, and
how does it keep each record true afterwards?

## Where the truth lives, and how each source is read

- The owner's Wayne State Outlook, read through the Microsoft 365 connector. Every letter carries
  the subject tag [XR/CT Imaging Research], so a search for the tag finds both the letters and
  the replies, which keep the tag in their "Re:" subject. Sent Items gives the exact time each
  letter went. A reply that drops the tag (an auto-reply, a bounce, a new thread) is found by
  reading the Inbox and Junk Email by date since the letter went.
- The grid, read only through Beethoven's gate words (symphony-template grid-accounts.yml, action
  job), whose answers land on symphony-template's branch grid as logs/job-<word>.json. The
  schwingnet-status word prints the newest Slurm jobs from sacct and each stage's report, with any
  line that could quote a credential or a DICOM value held back. A session never gives the owner a
  grid shell line (the owner's rule of 2026-10-21).
- spine-program's data_mining/ notes and MANIFEST_GRID.md, for sets copied to Ceph before the
  registry existed (DysphagiaBank's UNM swallow corpus, 87 files, 19 GB).

## What the audit changed (2026-10-21)

- Task labels follow record status. A set that has been asked for is labelled asked and loses
  todo. A granted set keeps todo, since the fetch is next. A set waiting on the owner is labelled
  needs-owner. A set already held closes its task as completed, and a refused one closes it as not
  planned.
- The answers the owner already had were recorded. Balgrist refused, because the data is licensed
  to a startup. Siewerdsen answered that the LevelCheck cohort is at Johns Hopkins and should be asked of Ali Uneri, and the
  follow-up went at 13:37 UTC. Radiopaedia acknowledged the follow-up. Daradia said it would look
  for the original fluoroscopy.
- PhysioNet: the owner has been credentialed since 2026-10-09. MIMIC-CXR, MIMIC-CXR-JPG and VinDr-CXR are
  credentialed sets, so they open only once PhysioNet approves the owner's CITI record. Its
  training-application notices came on 2026-10-21 at 17:11 and 19:27 UTC, and the approval had not
  come by 2026-10-22 04:25 UTC. VinDr-PCXR is under the restricted licence, which needs no CITI
  review.
- The owner corrected the record for the two Stanford AIMI CT sets, Merlin and INSPECT. They are
  held pending more storage, not dropped, so they are needs-owner with their issues open. The rule
  that follows: when the owner says a set is too big, it is held, never refused.
- The three letters of 2026-10-21 (IRI-VFI at 19:54, TVGH-SpineXR at 19:54, TVGH ankylosing
  spondylitis films at 19:56 UTC) are kept word for word under letters/, so a reply can be read
  against what was asked.

## The second pass (2026-10-22)

- Letters #21, #14 and #108: there was no reply in the Inbox, Junk Email or under the tag by
  04:25 UTC, about eight and a half hours after they went to Taiwan. There was no bounce either, so
  each address took the mail. The records stay at asked and change nothing.
- VinDr-PCXR (#17): the record said fetching, but no file had landed. The grid's reports showed
  two separate failures:
  1. Fetch job 40697734 (2026-10-21 21:36 UTC) ended after 8 seconds. PhysioNet answered 401 and
     then 403. physionet-build asks an anonymous wget for a login with 401, asks again with 401
     when the login is wrong, and answers 403 when the login is good but the account may not read
     the files. So the grid's login held and the account was refused this version's files. Either
     the agreement for VinDr-PCXR 1.0.0 was not yet in effect for that account, or the grid's netrc
     names a different PhysioNet account from the one holding the agreement. Only the owner,
     signed in on the project page, can tell which.
  2. Fetch job 40702518 (2026-10-22 04:23 UTC, SchwingNet ff9c743) ended before it made any
     request. SchwingNet #83 had added a check that reads ~/.netrc with Python's netrc module
     before the fetch, so that PhysioNet's answer could be named. That module refused the grid's
     file, the same file wget had read: "not a netrc file this tool can read". Every PhysioNet
     fetch through the gate stops there until the check reads what wget reads.
  The record went back to granted with both obstacles listed. #17 stays open until a copy passes
  `sha256sum -c SHA256SUMS.txt`.

## What this teaches

- A job reported as submitted is not a fetch. A record moves to fetching when the chain is
  submitted, and the next pass reads the job's own report before it trusts that status. An
  8-second fetch job with exit 1 is a failure, whatever the later stages report: the bank and
  catalog stages ran afterany, finished, and found nothing to do.
- A check placed before a tool must accept everything that tool accepts. Otherwise the check
  turns a clear answer from upstream (PhysioNet's 403, which #83 was written to explain) into a
  failure of its own that hides that answer. The check should read the netrc the way wget does,
  taking the login for one machine from a plain split on whitespace.
- No reply after a day is not a refusal. Letters to Taiwan went in the evening, US time, and are
  checked again after the next working day there.

## Not yet known

- Whether the owner's VinDr-PCXR agreement is in effect, and whether the grid's netrc names the
  account that holds it.
- When PhysioNet approves the CITI record that opens MIMIC-CXR, MIMIC-CXR-JPG and VinDr-CXR.
- Any answer to the three Taiwan letters.
