# The control panel's button home screen on every screen

The notes of the thread "Button home screen as default" of the claude.ai Project "symphony_2",
2026-10-21. The owner's ask: "the mobile view with the buttons should be the default for both
pc/browser and mobile view, you can put in the settings like a way to switch to legacy view, but i
want it to default to mobile with the buttons as the homepage, its way cleaner" and "give me the
ability to click and drag buttons to new positions and for it to be persistent saved to my google
chrome profile along with my login info, last open repo". The phone's home screen this extends is
control-panel-phone-home.md beside this file; the shared look it follows is panel-design-system.md.

## What changed

Before: a computer showed the console as a side column (the repository, the rail of tabs, who is
signed in) beside one open tab; only a phone had the home screen of square buttons.

After, on the site (openspineconsortium.github.io, branch claude/button-home-default):

- Every screen opens on the home screen of buttons. On a computer the class `console--buttons` on
  the console turns it on (symphony-panel.js, initHome): the side column fills the console, the
  rail is a grid of icons whose size follows the window's height (`--home-icon`, 52 to 76 px), and a
  button pressed opens its tab across the whole console under the back bar, as on a phone. The
  back button and the browser's own back return to the buttons; a link such as `#tasks` opens that
  tab with the back bar.
- Legacy, beside Buttons under the tabs, gives a computer the side rail back. A phone always has the
  buttons, so the switch is not shown there.
- The buttons are put in any order: a mouse drags once it has moved 6 px, a finger once it has held
  a button for half a second (a finger moving sooner scrolls, and one held and let go where it was
  is a slow tap that opens the tab), and Alt with the arrows, Home or End moves the focused button
  from the keyboard. Escape during a drag puts everything back. The others glide out of the way
  unless less motion is asked. A live region says the button's new place. Reset order appears
  once the order differs from the first one. The legacy rail uses the same order.
- A button keeps its own colour wherever it goes (`data-hue` in the page, in place of the old
  `nth-child` colours, which followed the place).

## Where it is kept

One localStorage key, `symphony_panel_home`, holds `{"layout": "legacy"}` and the order as a list
of tab names, and is absent while both are the default. localStorage belongs to the browser
profile, so the same Chrome profile finds the choice and the order again, beside the sign-in
token (with Keep me signed in) and the last repository, which the page keeps the same way. Forget
the token leaves it, as it leaves the sizes and the text size. A kept order naming a tab the page
no longer has is ignored, and a tab added since appears in its first place. A storage event carries
a change to the profile's other open tabs. The About tab's "What this page keeps" says so.

Native first: the profile's own storage is the native place for a per-browser setting, and nothing
here needs a server or a GitHub write. Chrome syncs a profile's extension storage across devices
(chrome.storage.sync) but not a site's localStorage. Following the layout to another computer
would therefore go through the Symphony for Chrome extension. It was not built, since the ask was
the Chrome profile.

## How it was checked

- A new suite, symphony-app's signin/panel-checks/e2e2/home.test.mjs, has 16 checks. They cover
  the default on a computer and a phone, Legacy and its reload, the order kept and reset, colours
  kept, Escape, the keyboard, a finger's hold, a quick swipe and a slow tap through Chromium's
  touch input, a drag at a larger text size, a mouse let go outside the rail, odd storage, and
  another tab's change. Nothing scrolls at 1280x900, 1366x768, 1920x1080, 960x600, 820x1180,
  844x390 or 390x844.
- Fourteen mutants (`hm01` to `hm14`) under mutants/ were each killed by the checks they name.
- The older suites were written for the side rail, so each now starts its browser profile with
  Legacy chosen (legacy-home.mjs). A phone ignores that choice, so their phone checks still see the
  buttons.
- The adversarial review found eight faults, all fixed before the pull request:
  - A drag at a text size other than 100% moved the button by the console's zoom, so the pointer
    is now mapped through it.
  - A mouse let go outside the rail before the drag began left a half-started drag that a later
    hover picked up. The press is now captured at once, and a move with no button held ends it.
  - A slow tap was taken for a drag.
  - A pinch that started on a button was blocked.
  - A glide's leftover transition made the next drag lag.
  - The lifted look while dragging lost to the hover and active rules.
  - A glide could skip its animation with no style flush.
  - Another tab's change in the middle of a drag was overwritten.

## Lesson

A drag measured with `offsetLeft` against `clientX` holds only at zoom 1. The console's text size
is CSS `zoom` on .console__app, so any pointer arithmetic inside the console divides by the scale
(the rail's on-screen width over its offsetWidth).

## State at the stop (2026-10-22, 00:02 UTC)

The owner stopped every thread. At that moment every suite was green on the final code: home.test.mjs and the thirteen older suites. The full mutant run was stopped about 356 mutants in. Five mutants had survived, g139, g156, g157, g164 and g183, all from the graph suite. f134 was stale. It is not yet known whether these predate the change, so the next step is to run those six against master and against the branch. Then merge site #136, symphony-app #89 and this pull request, #344, if the survivors are the same on master. All three are pushed and their CI is green (the site has none).
