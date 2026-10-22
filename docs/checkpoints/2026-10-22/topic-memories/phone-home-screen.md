---
name: phone-home-screen
description: The control panel's phone layout since site #112 (2026-10-20): fixed full-screen console, home screen of tab buttons, no page scroll anywhere
metadata:
  type: project
  modified: 2026-10-20T16:50:37.498Z
---

Since site #112 (merged 2026-10-20), on any window up to 900 px wide or 520 px tall the control panel's console is fixed full screen and the page never scrolls. A home screen of square tab buttons (console--home, showHome) opens each tab under a back bar (#cp-back). Full screen and Ask Claude live only on the home screen.

**Why:** greg asked for iPhone-style square buttons, one window at a time, and no scrolling into the footer.

**How to apply:**
- Panel checks open phone tabs through phoneTab/toTab, which press #cp-back first.
- The page-scroll code (holdStage, graphPhoneFit's height, graph--held, the foot's follow-on-scroll) is now dead.
- 18 equivalent mutants are listed in symphony-app's panel-checks README.
- footBounds' `stacked` follows phoneLayout(), except for a tab's foot held sideways, which is one row.
