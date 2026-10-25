# Beethoven's Add account in Settings

The thread "Add account button to Beethoven settings", 2026-10-24, from the owner's report that
the extension's Settings page had no way to add a Claude account and only listed the ones it had
already picked up. The change is OpenSpineConsortium/beethoven-extension pull request 25 (24.1.0).

## What was there

Settings' *Your Claude account in this browser* (24.0.0, beethoven-extension pull request 24) is
not a sign-in: Beethoven never reads claude.ai and holds no Claude credential. It is one preference,
`Prefs.claude_account`, the e-mail address of the account this Chrome profile is signed in to on
claude.ai, so the panel's *Your workers* can say which Chrome profile opens a worker on another
account. Its options came only from the accounts the workers' status files on the grid report
(`claude_login.email`, read by core/workers.ts `accountsOf`), and the card was hidden until at least
one did. The addresses the owner saw were those workers' accounts, not browser profiles.

## What 24.1.0 changes

The card is always shown, and *Add account* opens an e-mail field. The typed address goes through
the same `set-pref` action and the same `accountOf` check as a picked one, so anything that is not an
address is refused with the reason under the field, and a kept one is lower-cased. It becomes the
picked account and stays among the options while picked; picking another drops it unless a worker
reports it. Still one account per browser, kept in `storage.local` only, so the privacy statement
went to version 19 alone and the agreement stayed at 15.

## Why no list of accounts

Each Chrome profile signs in to one claude.ai account and runs its own copy of Beethoven, so a
browser needs to know only its own account; a stored list would add a remove control and a privacy
line for no use. A worker on a new account appears among the options by itself once its status file
names that account.
