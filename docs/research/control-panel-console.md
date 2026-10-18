# The control panel as a console

The notes of the thread "Control panel redesign as a console" of the claude.ai Project "symphony2",
2026-10-18. The owner's ask, in his words: "the entire layout for the tokens page, and the control
board is not CONTROL PANEL DESIGNED! IT SHOULD ALL FIT ON ONE PAGE WITHOUT SCROLLING, MAYBE USE
INPAGE TABS? THINK LIKE A CONTROL BOARD WHERE A GENERAL WOULD INITIATE WAR MANUEVERS, LIKE NATURAL
INTUITIVE BUTTONS". The earlier notes on the panel, its sign-in and its sections are
control-panel.md beside this file; this one covers only the layout.

## What changed

Before: https://openspineconsortium.com/symphony/control/ was one long article, nine sections and
about four screens of explanation, read by scrolling, with the actions as small pill buttons inside
the prose; the Claude accounts were a second page, /symphony/control/tokens.html, with its own
sign-in box and its own repository picker.

After: the panel is one console that fills the window under the site's header and the Symphony
strip and never makes the page scroll at a laptop's size:

- A command bar: the repository picker, the four links to GitHub, who is signed in, Refresh and
  Forget the token.
- A rail of ten tabs on the left: Command, Board, Tasks, Pull requests, Runs, Workers, Ask Claude,
  Tokens, Repositories, About. Tasks, Pull requests and Workers carry their counts.
- Command, the tab it opens on: seven readouts (Queue, Given to workers, At work, In review,
  Blocked, Pull requests, Workers), each a button that opens its list, then eight large launch
  buttons: Run the workers now (green, the one that sets work going), Rewrite the board, Run the
  checks, Run the metrics now, Queue a task, Ask Claude, Claude accounts, Add a repository.
- Every other tab holds one subject, its list on the left and its form on the right where it has
  one (Queue a task beside the task lists, Add a worker beside the registry, Add a Claude account
  beside the slots). A list longer than the tab scrolls inside the tab, never the page.
- The long explanations are folded behind a "?" in each tab's head and open over the tab, so they
  move nothing; the privacy text is the About tab, word for word.
- The Tokens page is the Tokens tab. tokens.html stays at its address for the links and bookmarks
  that name it and sends the visitor on to /symphony/control/#tokens with its query. One sign-in
  and one repository picker now serve both.
- Each tab has an address (#command, #board, #tasks, #pulls, #runs, #workers, #ask, #tokens,
  #repos, #about), so a link or a reload opens it again; nothing about the tab is stored.
- The deck is dark inside the cream site, so it reads as an instrument, not an article.

## Design decisions

- One page with in-page tabs, not several pages: one sign-in, one repository, and switching costs
  no request. Each tab's reads still happen once per repository, as before; the Tokens tab reads the
  branch pool only when it is opened, so a person who never opens it sends none of its reads.
- The height is measured, not guessed: the script sets the deck's height to the window's height
  below the header and strip on load, on resize and once the fonts have loaded, since the strip's
  height depends on them. Below 900 px wide or 520 px high the deck gives up: the page scrolls as
  before, the rail becomes a row, and each tab is shown whole.
- Every element id the script and the browser checks use is kept, so no behaviour moved. Where the
  page points at something in another tab (the assistant's focus on a task row, its filter, a board
  section, "Ask Claude on it" from a row), it opens that tab first and then scrolls as before.
- The tab's address (#tokens) matches no element's id, the rail buttons being rail-NAME, since a
  browser scrolls the window to an element the address names and would carry the bar and the strip
  out of sight; a scroll margin on the button did not stop it (the review below). An address that
  names no tab, such as the skip link's #main, leaves the tab as it is.
- Where the page scrolls to a row or a heading, it scrolls the tab's own box and puts the window
  back, since scrollIntoView moves every box around the node, the window too.
- A new sign-in reads the Tokens tab afresh, so another account never sees the last one's slots.
- Between 901 and 1279 pixels wide the bar takes a second row for its links rather than cut them,
  and the rail and the side forms narrow.
- The rail's buttons are ARIA tabs (aria-selected, arrow keys move between them), the panels
  tabpanels, so a screen reader and a browsing Claude read the same structure.

## Measured

Playwright with Chromium against a mocked api.github.com (the panel checks' fixtures in
OpenSpineConsortium/symphony-app, signin/panel-checks/e2e2, widened to 24 tasks): at 1366 x 657,
a 1366 x 768 laptop's window under the browser's own bars, and at 1920 x 969, every tab's console
ends at the window's bottom edge (656.7 of 657 and 968.7 of 969 pixels) with the window unscrolled;
the readouts, the eight launch buttons and the whole rail fit at both sizes. The site's footer is
still below the deck, reachable by scrolling, as the site's build requires.

## For the threads that add sections

A new section is one rail button and one panel in tools/pages/symphony/control/index/body.html of
the site: `<button type="button" role="tab" data-tab="NAME" id="rail-NAME" aria-controls="tab-NAME">` in
the rail, and `<section class="console__panel" id="tab-NAME" data-tab-panel="NAME" role="tabpanel"
aria-labelledby="rail-NAME" hidden>` in the stage, with a `console__head` and a `console__scroll` inside;
`console__panel--split` gives a list on the left and a form on the right. The Dependencies section
and the Folders page are expected to arrive this way.

The panel's browser checks press a tab's rail button before they read or press anything inside it,
since a hidden tab's contents are not visible to Playwright: symphony-app's
signin/panel-checks/e2e2/console-tabs.mjs wraps the page's actions and its locators so that each
opens the tab holding its selector first, and each suite installs it once after launching the
browser.

## Review

An adversarial review of the first version, run in the thread before the pull request, found the
window scrolled 107 pixels on every signed-in load, since the tab's address named a rail button;
scrollIntoView from "Ask Claude on it" and the assistant moving the window; the Tokens tab keeping
the last sign-in's readings after a new one; any other address sending the person to Command; the
bar cutting its links between 901 and about 1250 pixels; Home and End doing nothing on the rail;
and words that still said "below" or "Tokens page". Each is fixed as the decisions above say, and
the four addresses (/symphony/control/, ?repo=, #board, tokens.html?repo=) now load with the window
at 0 at 1366 x 657 and 1000 x 700. Two edges stay: a sign-in begun on the old tokens.html before
this change and finished after it is refused once and asks to try again, and a return from Sign in
with GitHub opens Command, since GitHub's callback carries no address fragment.
