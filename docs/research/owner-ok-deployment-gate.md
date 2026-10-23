# The owner's tap before a merge: an environment, not a review

Source: the thread "Handoff merges and grid checks", 2026-10-23, answering symphony-template #386, where the owner asked that the organisation ruleset "Require owner approval to merge" (one approval, last-push approval) stop blocking the owner's own pull requests, then asked for a step the owner must still take, and one that GitHub Mobile turns into a push notification to approve or reject.

## What GitHub offers natively

- An approving review cannot be the owner's step: GitHub never lets a pull request's author approve it, and every session opens its pull requests under the owner's login. A ruleset has no condition on the author, so it cannot exempt the owner either; the owner's admin bypass ("Always") covers merges made through the API as well, which is why sessions merged the owner's pull requests on the standing permission with no box ticked (SchwingNet #143 on 2026-10-23 was refused only for a running check).
- A label read by a required check would need the owner to open the pull request and add it; nothing notifies the owner to do so.
- A deployment to an environment with a required reviewer waits for that reviewer, and GitHub Mobile notifies the reviewer and offers Approve and Reject in the app. A reviewer may approve a deployment the reviewer's own push started unless the environment's "Prevent self-review" is ticked. The waiting job's check run is pending until then, success after Approve and failure after Reject, so a required status check of the job's name makes it the gate.
- "Require deployments to succeed" is a ruleset rule too, but GitHub's documentation says it is not available for rulesets made at the organisation level (github/docs, available-rules-for-rulesets.md), so the required status check is the one form that works in the organisation's ruleset as well as a repository's.

## What was built

.github/workflows/owner-ok.yml in symphony-template and SchwingNet: on a pull request that is not a draft, one job named owner-ok deploys to the environment owner-ok and does nothing else, with no permissions, no checkout and no secret. A draft's run is skipped, so workers' draft pushes notify no one; a newer push cancels the waiting run, so one request is pending per pull request and the approval always covers the head that merges. The owner's clicks, the environment's reviewer and the ruleset's required check, are docs/setup/github.md section 10; until the environment names a reviewer the job passes at once, so the file alone changes nothing.

## Admins pass at once (2026-10-23, later the same day)

The owner wanted to tap only other people's pull requests, never his own. Since every session opens its pull requests under the owner's login, the workflow now reads the author's collaborator permission first and sends an admin's pull request to the environment owner-self, which names no reviewer, and every other author's to owner-ok. A required check named owner-ok cannot tell the two apart, so the split lives in the workflow; a failed read leaves the check missing, which holds the merge. The workflow runs from the pull request's branch, as pull_request workflows do, so a writer could edit it away in their own pull request: the gate stops honest pull requests, not a writer set on getting around it, and in an organisation of two people that was judged enough. The setup of 2026-10-23: owner-ok's reviewer set in both repositories, the organisation ruleset Owner OK (25710532) requiring owner-ok with an empty bypass list and the check from any source, since an organisation ruleset offers only installed apps as sources, and both repositories excluded from Require owner approval to merge (25608346).

## What is left open

The organisation ruleset's other repositories keep their one required approval unless the owner changes it; the gate's file is only in the two repositories above, so requiring owner-ok in a ruleset that covers a repository without it would hold that repository's pull requests for good.
