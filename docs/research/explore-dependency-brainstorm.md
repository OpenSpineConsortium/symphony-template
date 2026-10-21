# Explore as a dependency brainstorm

The thread "Explore as dependency brainstorm" of the claude.ai Project "symphony_2", 2026-10-21,
after the owner's words on the control panel that evening. The sketch shown to the owner is the
project file explore-brainstorm/sketch-wide.png; this note is the design it draws and what was
checked before drawing it.

## The ask

The owner, 2026-10-21 01:40 UTC, on the Explore tab: "there is nothing intuititve abouyt the
explort panel, idk what its even trying to do just hide it, please let me make something useful
out of as i want that to essentially have claude suggest new connections betweem the dependency
and that swhat explore does, it should suggest new nodes for a graphical represenation of
brainstormong/code planning , and you shoul d be ble to push the alterations in the dependencies
to the actual tasks/ect and work like that". In the same message: one style for every tab, built
from shared parts shaped like the Workers tab's cards (the thread "Panel design system" owns that).

So the tab becomes a planning canvas over the repository's real task graph: Claude proposes edges
and new tasks, the person accepts, edits or dismisses each, draws their own, and one press writes
the accepted changes to GitHub as native issues and links.

## Step one: the old tab is hidden

Site branch claude/hide-explore removes the Explore rail button and its address from the About
tab's list. The panel's markup and script stay, unreachable, since the new tab replaces them
whole: with no rail button, `#explore` opens the first tab, as any unknown address does. In
symphony-app the old tab's browser checks (e2e2/explore.test.mjs and its 39 `x*` mutants) are
parked: e2e2/PARKED leaves them out of a run of every mutant, and each still runs when named.

## Native first: where the graph already lives

Nothing new is stored. GitHub holds every edge the canvas draws, on every plan, and the panel
already reads them for the Dependencies tab (symphony-panel.js reads `sub_issues` and
`dependencies/blocked_by` per epic, docs/research/control-board-graph.md verified both on
2026-10-17):

- An epic and its tasks: sub-issues. Written with `POST /repos/{r}/issues/{n}/sub_issues` and the
  body `{"sub_issue_id": <the task's id>}`, removed with `DELETE .../sub_issue`.
- A precondition: "blocked by". Written with `POST /repos/{r}/issues/{n}/dependencies/blocked_by`
  and `{"issue_id": <the blocker's id>}`, removed with `DELETE .../blocked_by/{issue_id}`. Only
  blocked_by and blocking exist; a "relates to" endpoint answered 404 (same note).
- A new node: an issue, `POST /repos/{r}/issues`, labelled todo as the Task form labels one, then
  made a sub-issue of the epic the canvas is focused on.

Projects v2 draft items were considered as the store for an idea not yet accepted, and left out:
they need the Projects permission on the App's user token and a project per repository, and an
idea not yet accepted has no reason to outlive the page except where Claude wrote it, which is
already kept (below).

## Claude's suggestions come through the assistant issue

No Claude credential enters the page. The panel already asks Claude through the issue labelled
assistant, which claude.yml answers read-only on the repository's own Claude token, with
.github/symphony/assistant.md appended, and the page already turns a fenced `symphony` block at
the end of the answer into buttons that run only on the person's press
(docs/research/ask-claude-bar.md). The brainstorm adds two offered changes to that vocabulary:

- `link #A blocks #B [why TEXT]`: an edge, drawn dashed on the canvas between the two cards.
- `node TITLE under #E [blocks #X] [after #Y] [why TEXT]`: a new task, drawn as a dashed card in
  the epic with its edges.

"Ask Claude for ideas" posts a question naming the focused epic; the run reads the board, the
issues and the code as it does today and answers with prose and those lines. The answer is the
record of the ideas: a reload draws them again from the comment, so nothing needs a store of ours.
The guards of the Ask Claude bar carry over unchanged: a suggestion belongs to the answer it came
with and does nothing once the page has read the repository again; each is one press; the run
itself writes nothing. tests/test_claude_assistant.py pins the verbs, so the two new ones are added
there and in the page together.

## What the person does on the canvas

- Focus one epic (chips over the canvas, "All epics" for epics as nodes), as Dependencies does.
- Accept, Edit or Dismiss each dashed idea; Accept moves it into "Changes to push".
- Draw their own: + Node for a new task, Connect or drag from a card's edge for "blocked by",
  a card's menu to remove a link or move the task to another epic.
- Push: one press writes the pending changes in order (issues first, then sub-issue links, then
  blocked_by), each as the signed-in person, and says each result in words; Undo after a push
  removes what that push made (DELETE of the links; a new issue is closed as not planned, since
  GitHub lets nobody but an admin delete one).

A cycle in blocked_by is refused before the push, since a task blocked by itself through others
could never become free under Pick. The canvas reads each task's state, claim and checks as
Dependencies does, so a card says "claimed by nightly" or "0 of 2 met" without a read of its own.

## Built

The owner said yes to the sketch on 2026-10-21 01:53 UTC ("yes finally you understand what i
want"). The tab is built in the site's assets/js/symphony-panel.js (the block after the comment
"Explore: plan an epic with Claude"), its look in assets/css/control.css under #tab-explore, and its browser
checks in symphony-app's signin/panel-checks/e2e2/explore.test.mjs (BS1 to BS8) with `b*`
mutants that prove each check bites. The two verbs are in .github/symphony/assistant.md and pinned
by tests/test_claude_assistant.py.

What the build settled beyond the sketch:

- The canvas lays the cards out in columns by the longest chain of "blocked by" before each, so
  a task always stands to the right of what it waits for, and scales between half and full size
  to fit the panel.
- A link Claude names between two tasks that are not both on the focused epic's canvas is listed
  under the canvas, never drawn to nowhere.
- Pressing Connect, then two cards, adds "the second is blocked by the first"; the same pair again
  takes a waiting change back, and a pair already linked on GitHub becomes a removal. A pair that
  would close a loop is refused with those words.
- Push writes new tasks first, then removals, then links, and stops at the first failure, saying
  which; a link to a task the same push made is written with that task's new number. Undo walks
  the push back in the reverse order.
- An idea GitHub already holds is not offered again when the answer is read anew after a push or
  a reload: a task of the same title under its epic, with or without "Task: ", or a link GitHub
  has. A task still Claude's idea is accepted before Connect takes it, so no waiting link names a
  card that may go.
- A task whose issue was opened but not placed under its epic, the push stopping between the two,
  is placed on the next push and never opened twice; a later push adds its writes to the same Undo,
  and Undo writes only as the account that pushed. A link GitHub already has, or an unlink it no
  longer holds, counts as done instead of stopping the push.
- Dragging from a card's edge and moving a task to another epic are left for later: Connect does
  the first, and the Tasks tab's settings the second.
