# Withdrawing an invitation on the Share tab

From the thread "Share tab invitation withdraw" of the claude.ai Project "symphony_2", 2026-10-22.

## What happened

The owner withdrew aschehr's invitation to OpenSpineConsortium/symphony-template on the control panel's Share tab. The row stayed on the list. A second withdraw said GitHub answered 404 at /repos/OpenSpineConsortium/symphony-template/invitations/338318854 "since SymphonyBoard is not installed there".

GitHub's collaborators list, read on 2026-10-22, showed aschehr as a direct collaborator with Write. aschehr had accepted the invitation, so GitHub no longer had it, and the 404 was GitHub saying so. SymphonyBoard is installed on OpenSpineConsortium (installation 169803029), so the hint about the installation was wrong.

## Why the row stayed

GitHub answers authenticated REST reads with `Cache-Control: private, max-age=60`. A browser's fetch with the default cache mode may therefore hand back a list up to a minute old, including a list read straight after the page's own change. The Share tab read the invitations again after a withdraw, but it could get the browser's copy.

## The fix

Site #137 and symphony-app #90 carry the fix:

- **Fresh reads.** The Share tab's lists (collaborators and invitations) go out with fetch's `cache: 'no-cache'`. The browser revalidates by ETag, and GitHub's 304 costs nothing against the rate limit.
- **A 404 on an invitation.** On withdrawing it or changing its role, the page reads the invitations again.
  - If GitHub no longer lists the invitation, the note says it is no longer waiting. It says the invitee accepted where they now have access by name, and otherwise that it was withdrawn already, declined, or taken and the access since removed. The list is redrawn.
  - If GitHub still lists it, the usual refusal path names the cause. GitHub answers 404 both for what is gone and for what a sign-in may not reach, so the adversarial review insisted that a 404 is never called "gone" on its own.
- **The general 404 text.** It no longer states as fact that SymphonyBoard is not installed.

## How it was checked

- New checks S5 to S8 in symphony-app's signin/panel-checks/e2e2/signin.test.mjs, with mutants sh05 to sh08, each of which fails a check.
- Playwright turns the browser's HTTP cache off while it routes requests, so a stale answer cannot be produced under the mock. S5 instead reads the cache mode the page handed to fetch.
- All thirteen panel suites ran against the site branch. Every check passed except wandb's W3, which failed once under parallel load and passes alone on the branch and on master.
