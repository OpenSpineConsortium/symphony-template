# The control panel's privacy section against statement 35

From the thread "Control panel sign-in" of the claude.ai Project "symphony_2", 2026-10-20.

## What changed

The About tab's "What this page keeps and sends" (the site's tools/pages/symphony/control/index/body.html)
left out three things the Apps' privacy statement version 35 already said: the Google Fonts
stylesheet and font files the browser fetches on each load, the pending sign-in record a press of
Sign in with GitHub keeps in the tab's own storage until GitHub's return, and the Dependencies
tab's stored chart choice. Site #96 adds all three in the statement's terms. A review read the
script to confirm them: the pending record is sessionStorage symphony_panel_oauth_state, cleared by
any GitHub return and by Microsoft's, never by Forget the token; the chart choice is localStorage
keyed by the repository's name, removed neither by Forget the token nor by taking the repository
off the list. Site #97, prepared by the Tokens thread, makes the Token 404 and the Share refusal say
what is really missing; it needed no statement version.

## Found on the way

- The panel checks in symphony-app must be pulled to main before each run: a stale checkout failed
  41 checks against the rebuilt Folders and Explore tabs (site #98, #99) that pass on main.
- On the site's master at 751fcfb, run-mutants.sh kills 588 of 590 mutants: k40_box_out_of_sight
  (K24, code.test.mjs) survives and m7_no404 (E5) is stale, its text gone from the script. Both
  are the same without this thread's changes, so they are the checks' owners' to refresh.
- The privacy section does not name symphony_panel_repo, the repository last opened, which the
  statement counts among "the names of the repositories you listed"; statement 36 may say it.

## Statement 36

Collected for it so far: the direct Microsoft Graph switch for Folders, Notebooks and the drive
walk; the Folders tab as a native explorer of OneDrive, which no longer reads catalog.json on
drive-catalog (correct the statement's lines on the Folders and Notebooks catalogs and the version
26 note); the Explore tab's live job log and re-run and cancel buttons if greg keeps them; and the
panel's own section changed in the same release.
