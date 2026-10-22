---
name: button-home-default
description: Since site #136 (2026-10-21) the control panel's button home screen is the default on computers too; Legacy switch, drag-to-reorder kept in localStorage symphony_panel_home
metadata:
  type: project
  modified: 2026-10-21T22:21:09.118Z
---

greg asked on 2026-10-21 that the phone's button home screen be the default home on PC and phone, with a Settings switch to the legacy rail, and that the buttons can be dragged and kept in his Chrome profile. Site PR #136 (branch claude/button-home-default), checks symphony-app #89, note symphony-template #344 (docs/research/control-panel-button-home.md).

- Class `console--buttons` on #console (default; Legacy removes it on a computer; phones always show the buttons). `homeLayout()` = phoneLayout() || buttons chosen; showHome/leftPhone use it.
- One localStorage key `symphony_panel_home` = {layout:'legacy'?, order:[tab names]?}, absent at default; per browser profile, not per login; Forget the token leaves it.
- Buttons/Legacy and Reset order sit in `.console__me` under the tabs; colours are `data-hue` in the HTML.

**How to apply:** older panel-check suites start their profile on Legacy via e2e2/legacy-home.mjs; new desktop checks of the home screen go in home.test.mjs (mutants hm01-hm14). Pointer maths inside the console must divide by the text-size zoom (rail rect width / offsetWidth). Cross-device sync would need the Symphony extension's chrome.storage.sync, not built. Related: [[phone-home-screen]], [[panel-design-system]], [[panel-checks-run]].
