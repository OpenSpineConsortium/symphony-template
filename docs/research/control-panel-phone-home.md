# The control panel on a phone: a home screen of square buttons

The notes of the thread "Phone layout for the control panel" of the claude.ai Project "symphony_2",
2026-10-20. The owner's ask, written in the OneDrive thread and moved here by the coordinator:
"instead of these sliding tabs left and right I want each tab to be its own square button about
the same size as the original iPhone apps ... like 1 cm and I want the tab to take up the entire
screen I don't want to show anything more than one window at a time so if a dialogue button comes
up when you're filling out a form it should occupy the entire screen frozen until you finish the
form and then when you finish it, it should return to the tab you were on ... when you scroll
down, you don't scroll past the control panel onto the footer of the page ... a back button in the
top left that you get back to the square buttons for the tabs". The console's desktop layout is
control-panel-console.md beside this file; fitting the other tabs on a computer (the "Chips" plan)
stays held, and this home screen replaces it on a phone.

## What changed

Before: on a phone (a window up to 900 px wide, or up to 520 px tall) the rail of tabs was a row
that slid sideways above the tab, the page scrolled as a whole, past the console into the site's
footer, and a dialog was a card over the dimmed tab.

After, on the same screens only (a computer's layout is untouched):

- The console is fixed over the whole screen, below the Home Screen app's top inset, so the page
  under it never scrolls; the breadcrumb and the footer are not drawn under it at all, and the
  site's bar still comes down from the handle at the top centre.
- With no tab open the console is a home screen: the repository card, then every tab as a 60 px
  rounded square (about 1 cm on an iPhone, the original iPhone's icon size) in one of five
  colours with its name under it, a count as a red badge on the icon's corner (none for zero),
  then the Ask Claude bar and the foot with who is signed in. Only the repository card and the
  buttons scroll, inside the console, so a phone held sideways reaches every button.
- A button opens its tab over the whole screen under a bar with "< Tabs" at the top left and the
  tab's name; only the tab scrolls. The foot keeps the page's message line and its grip; dragged,
  it leaves the stage its least of 180 px, as on a computer. Held sideways, the back bar is a
  slim row and a tab's foot is one row, message beside Clear, sized or not.
  The Ask Claude bar and the sign-in controls stay on the home screen; the Command tab's Ask Claude
  button goes home to it. Claude's answer drawer, fixed to the screen, opens over either view.
- Every dialog (a + button, a gear, a card's status) fills the screen on an opaque ground and the
  page stays still beneath it; closing it returns to the tab as it was.
- The home screen keeps no tab in the address, so a reload there returns to it; a tab opened from
  it is a history step, so the phone's back gesture returns home as the button does, and a link
  to #tokens or any tab still opens that tab directly, with the back button going home.
- Explore folded wide used to fix itself over the whole page on a phone; it now stays in the stage
  under the back bar like every other tab. Its Panel button changes nothing on a phone.
- Since the page no longer scrolls anywhere the phone layout applies (a window up to 900 px wide,
  which takes in a tablet held upright, or up to 520 px tall), Refresh no longer holds the stage
  to keep a scroll position: the code that did so (holdStage, under pageScrolls) is left in place
  and is reached by no layout today.

## Where it is

Site pull request on OpenSpineConsortium/openspineconsortium.github.io, branch
claude/project-thread-6cxgh2: tools/pages/symphony/control/index/body.html (the back bar),
assets/js/symphony-panel.js (showHome, openFromHome, leaveTab, the badge's data-zero) and the last
block of assets/css/control.css (the phone's home screen). The rules stand last in the stylesheet
because a media query adds no specificity and the earlier phone rules, written for a page that
scrolls, must lose to them.

## How it was checked

Rendered with Playwright against the mocked GitHub the panel checks use, at 390 x 844 (an iPhone
upright) and 844 x 390 (sideways), with touch: every one of the fifteen tabs opened from its
button and the back button returned home with the address cleared, the task dialog filled the
screen and closing it kept the Tasks tab, the browser's back returned home, and a wheel scroll
left the page at 0. At 1280 x 800 the computer's layout was unchanged. The site's build reported
0 problems. The symphony-app panel-checks suites were run on master and on the branch. The checks
whose premise was a phone page that scrolls (signin P6, P12, P13, P35, P43, P44, P46; graph AJ,
AM, AR, BL, BV, BW; explore XP11, XP12, XP19; app H3 to H6) were rewritten to the new layout in a
symphony-app pull request of their own, BW's short screen now expecting the one-row foot. One
real fault they found, the foot's least on a phone leaving Clear cut off once the console no
longer scrolled, was fixed in footBounds, which now reads the phone's layout for whether the foot
stacks and the console's overflow for whether the page scrolls.
