# Switching the Claude tab between workers, and workers on other accounts

The thread "Beethoven multi-account worker switching", 2026-10-23. The owner's words: switch which
worker the claude.ai tab shows, quickly; reach the workers that run on his other Claude accounts
("i just assumed in one window you have to be logged into the same claude account, but if you
could get this working itd be sweet"); and keep the automatic move of the same worker between
accounts, so both work together. The change is OpenSpineConsortium/beethoven-extension#24
(Beethoven 24.0.0).

## What limits it

- A claude.ai tab shows the Remote Control environments of the account it is signed in to, and no
  other. A Chrome profile holds one claude.ai sign-in at a time.
- Beethoven runs no code on claude.ai and reads nothing from it (its CLAUDE.md), so it cannot learn
  which account a tab is signed in to; and an extension cannot open a tab in another Chrome profile.
- hpcworker framework 22 runs several workers at once, each kept to one account
  (`hpcworker accounts start N [NAME]`, the run folder's account.pin); each writes its own
  status.json under the state directory, with claude_login.email from `claude auth status`.

## The design built

One Chrome profile per Claude account, each with Beethoven. The panel reads every run folder's
status.json through the portal's Files app (one listing and one download per worker, at most 12,
once a minute while a page is open and when the fold opens) and lists them under a folded "Your
workers" with each one's state and account. "Show" loads the chosen worker's link in the claude.ai
tab Beethoven opened (tabs.update needs no permission), so the switch is one press and no new tab.
Settings' "Your Claude account in this browser" is picked from the accounts the workers report; a
worker on another account then shows no Show but the profile to open it in and Copy link. A worker
that auto mode or `accounts use` moves shows its new account in the fold on the next read, so the
automatic handoff (symphony-template #392, its own thread) and the manual switch live side by side.

## Not measured yet

Two accounts on the real grid through the panel; whether claude.ai changes environment cleanly when
the same tab is loaded with another environment link (it is the same navigation Open my session
already makes, into a new tab).
