# The Explore and Folders tabs redesigned

Source: the thread "Explorer modernization", 2026-10-20, from handoff part 6.2 (docs/checkpoints/2026-10-19/handoff.md) and the owner's word of 03:50 UTC in the OneDrive thread, relayed by the coordinator. The code is in OpenSpineConsortium/openspineconsortium.github.io (branches claude/explore-modern and claude/folders-native) and its checks in OpenSpineConsortium/symphony-app (signin/panel-checks/e2e2, branches of the same names).

## Which explorer

The handoff's "Explorer" was read first as the Explore tab, the goal to epic to issue to pull request to run, job, step and log tree. The owner then said he meant the Folders tab: a native Windows File Explorer view of his OneDrive through direct Microsoft Graph, with the right side panel removed and the old connector-made scan never offered. The coordinator made Folders the main work and kept the Explore changes because they were already built.

## Explore: what changed

- Cards on the zoom stage the Dependencies tab uses (stageMake): no box scrolls; the wheel, a pinch, + and - zoom; zooming out past the whole level comes out one level, once a wheel gesture so a trackpad's glide stops there; a swipe or an arrow on the stage goes to the level beside; with a card in hand the arrows move between cards, zoomed or not, and a key held down steps sideways once, since each level below a task is a read.
- A level's cards are laid out in the column count, from 1 to 24, that draws them largest, and grown to fill the stage.
- A log is drawn at its own size on its first error, else its end; a plain wheel moves along it whether it fits or not; its width follows the stage; its lines copy from a button, since a drag pans.
- While the tab is shown the side column folds to its icons and the foot to one line; Panel, or a press on either, brings them back; on a phone the tab is the whole screen. The fold applies only once the signed-in app is shown, so the sign-in page at #explore still scrolls on a phone.
- The read budget is kept: reads below a task happen only on entry, a double click goes one level and not two, and none starts under the reserve of 100 calls.
- Checks: explore.test.mjs XP1 to XP19 pass; the mutants x01 to x40 are killed. An adversarial review of the first commit found ten faults (the fold locking a signed-out phone, a short log left by the wheel, a double click reading two levels, held keys reading every level passed, arrows panning while zoomed, a log clipped after Panel, log text not copyable, word-only levels with no zoom-out, gestures surviving a level, Panel's pressed state inverted); each is fixed and the first five that a check can reach are held by XP16 to XP19.

## Folders: what changed

- The tab is one column: a one-line head (Folders, who is connected, Connect OneDrive, Track in a repository, How it works) over the explorer, which fills the rest of the tab; only its tree and its list scroll inside, as Windows' panes do.
- The right side column is gone. Its steps (what is ticked, Make the repository, Track) are in a dialog, Track in a repository, with every element id kept, so the tracking code is unchanged.
- The saved catalog (catalog.json on a private repository's drive-catalog branch, written by the drive organizer through the connector) is no longer read or shown by the tab, and no text offers it; with no drive the explorer says only to connect OneDrive. The Notebooks tab still reads catalog.json, which is that tab's design and the sign-in thread's.
- No new read or write: the layout change needs no privacy statement change.
- Checks: folders.test.mjs drops CAT1 to CAT9 and their mutants f56 to f63, and adds NC1 (no catalog read or word), NC2 (no side column, the explorer fills the tab, the page does not scroll) and NC3 (the Track dialog); mutants f64 to f66 hold them, and f45 follows the steps' new names.

## Proposed next, waiting for the owner

Native file actions, each a write to the drive through Graph, so each waits for the owner's choice and for privacy statement version 36 to be live first (the sign-in thread writes it): new folder, rename (F2), delete to the recycle bin, upload by drag and drop, download, cut, copy and paste to move, a sharing link, properties, multi-select with Shift and Ctrl, a preview pane, search across the whole drive, and more views (List, Tiles, Content). Navigating several connected drives and git repositories as if local is the owner's later idea and is not designed yet.

For Explore the list proposed before building was: a breadcrumb with sibling menus, search, state filters, a live log of a running job, re-run and cancel (writes, so privacy 36 first), and links out to GitHub; the owner has not picked from it.
