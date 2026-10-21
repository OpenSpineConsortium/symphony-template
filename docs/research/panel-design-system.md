# The control panel's design system

The notes of the thread "Panel design system", 2026-10-21. The owner asked, after seeing the
Folders tab's first cloud mounting, for every tab of the control panel to look alike: one common
set of objects, every panel shaped like the Workers tab's cards, Tasks split into tabs of its own
so nobody scrolls a long row of lists, and the orange Claude mark on the Ask Claude button. The
work landed as site pull request #121 (squash c0aa182, live 2026-10-21) with its checks in
symphony-app #75 (f766419). Screenshots of before and after, desktop and phone, are in the
project's files under panel-design-system/.

## What changed

- Tokens. One set of custom properties on `.console`, all named `--ds-*`: corner radii (12px for
  a card, 8px for a small part, a pill), the surface and raised colours, the border, hover and
  pressed borders and fills, the icon tile's size (44px), gaps, two shadows, type sizes and the
  easing. Other blocks use them as `var(--ds-*, fallback)`, so a tab built before or beside them
  still draws.
- Components. A card is the Workers tab's shape: 12px corners, the panel's border, its surface,
  a 3px inner edge in the card's own accent (`--card-accent`) and a soft shadow, lifting on
  hover except when disabled. The same rule draws the board's card rows, the Command tab's launch
  buttons and readouts, the token tiles, the worker tiles, the repository cards, the Tasks side
  column and the kanban headings. The shared classes are `.ds-card`, `.ds-card--press`,
  `.ds-card--add` (dashed, for a +), `.ds-icon`, `.ds-ctl` (a round control), `.ds-seg` (a row of
  chips, pressed by `aria-pressed`), `.ds-table` and `.ds-note` (a dashed quiet notice).
- Frame. On a desktop, the side column and the stage are large cards; every tab's head has the
  same gap and a soft rule beneath it, except Folders, whose drive cards are its head.
- Tasks. The head is a segmented row of seven views (queue, given, claimed, review, blocked,
  epics, all); one list shows at a time, scrolling inside the stage on a desktop and with the tab
  on a phone. The choice is kept per browser (`symphony_panel_tasks_view`); a readout or an Ask
  Claude answer that opens a row switches to that row's list without overwriting the kept choice.
- The Claude mark. An inline twelve-ray SVG filled #D97757 on the floating Claude button, the
  Ask Claude launch tile and its dialog's heading.
- Explore was left to its own thread's rebuild, which uses the same tokens; Folders' mounting is
  the "WSU grid files in Folders" thread's, drawn with the same tokens.

## What the review found

An adversarial review before the merge found six faults, each fixed and each given a check
(DS8 to DS10 beside DS1 to DS7): task cards had lost their list colours; the "other" list was
hidden under a single view; disabled launch buttons lifted on hover; the go button lost its
green; on a phone the list scrolled inside itself instead of the whole tab; and a jump from
elsewhere overwrote the kept view. After master brought in the Grid tab, Explore's planning
canvas and Folders' drive cards, two more showed: Folders' head grew by the shared rule (now
exempt) and a chip's `display:inline-flex` showed Explore's hidden undo button (now
`[hidden]` wins for chips and add buttons). All twelve panel suites passed on the merged heads.

## Mutants

The run of run-mutants.sh stopped at about 590 of 700. Its survivors (g139, g156, g157, g164,
g183, k40, p04, p20, p49) survive on master too, and k35, m7 and p11 are stale on master, so
none comes from this change.

## Lessons

- `pkill -f` with a pattern that the running bash command also contains kills its own shell
  (exit 144); stop a server by its PID.
- The site's build needs the four sibling checkouts (beethoven-extension, beethoven-vscode,
  symphony-extension, symphony-start) named by BEETHOVEN_REPO, BEETHOVEN_VSCODE_REPO,
  SYMPHONY_REPO and SYMPHONY_START_REPO; built pages conflict on every merge, so take master's
  and build again.
- A blanket rule on `.console button` reaches too far; scope a component rule to the elements
  that are that component.
