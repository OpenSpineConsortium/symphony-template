# Claude driving the control panel, and the panel as a command line

The notes of the thread "Phone layout for the control panel" of the claude.ai Project "symphony2",
2026-10-20. The owner's ask, in his words: "remove it completely I want a floating Claude in the
top right you click on to either add your first token if non is available or ask Claude something,
I'm more interesting in the user being able to get real time site help with the Claude being able
to actual control mouse and keystrokes to do what they ask in the app, maybe even add a CLI terminal
backend and start planning how this could be exported as a cli tool/package; the control board, not
the hit template, or maybe just a direct cli/code runner to let Claude programmatically do things
without a ton of error prone mouse clicks". The first half, the floating button, is built (site,
the pull request named in the last section); this note is the plan for the rest. The assistant it
builds on is ask-claude-bar.md beside this file; the panel's earlier notes are control-panel.md,
control-panel-console.md and control-panel-phone-home.md.

## The answer in short

Claude should drive the panel through the panel's own actions, by name, not through synthetic mouse
moves and key presses. Every button in the panel already runs a handler (Run the workers, Give to,
Merge, Add Token, open a tab); the assistant already names some of them in a fenced `symphony`
block and the page offers them as buttons. Widening that vocabulary to every action, and keeping it
in one registry, gives three things from one piece of code:

1. In the page, Claude's answer becomes a short list of steps that the page carries out on the
   person's press, with a pointer that moves to each control it presses so the person sees what
   happens, as if Claude had the mouse, without a pixel ever being guessed.
2. In a Terminal tab of the page, the person, or Claude, types the same actions as commands
   (`give #12 to nightly`, `run workers`, `merge #7`).
3. Outside the page, a command-line tool runs the same actions against GitHub's API, so Claude Code
   in a session or a terminal operates the control board directly, with no browser at all. That is
   the "direct cli/code runner": the control board exported, not the template.

Real mouse and keyboard control (Claude in Chrome, computer use) is possible but the wrong base: it
needs the person's own computer and browser extension, so it never works on a phone, which is where
the owner uses the panel most; it is slow, since every step is a screenshot and a guess; and it
breaks whenever a layout moves, as the phone redesign moved every button this week. A named action
is the same press, done exactly.

## What exists today

- The floating Claude button at the top right, on every layout. With no Claude token set for the
  repository it opens the Tokens tab's Add Token; otherwise the Claude dialog, whose box asks the
  assistant (site, symphony-panel.js pressClaude).
- The assistant: an issue labelled assistant on the repository, a comment per question, answered by
  the repository's claude.yml on the repository's own Claude subscription token, read-only, in ten
  turns, with .github/symphony/assistant.md appended to its system prompt. Its answer may end with a
  `symphony` block: reads (`tab`, `focus`, `open`, `filter`, `show`) run by themselves; changes
  (`run`, `give`, `merge`, `task`, `ask`) are buttons the person presses. tests/test_claude_assistant.py
  pins the verbs to the page's.
- Its limit is speed: an answer is a GitHub Actions run, so it takes the runner's start, the
  checkout and Claude's turns, typically half a minute to a few minutes. That is help, not real-time
  help.

## The plan

### Step 1: one registry of panel actions (site only)

A table in symphony-panel.js, one entry per action: its name, its arguments, whether it only reads
or changes something, the element it presses or the handler it calls, and a sentence saying what it
does. The buttons, the assistant's `symphony` block and the Terminal tab all go through it, so an
action added once is offered everywhere, and assistant.md's verb list is generated from it, with
the template's test still pinning the two together. Every action the panel has gets an entry,
starting with the ones people ask for most: open a tab, choose a repository, add a task, give a task,
run the workers, the board, the checks or the metrics, merge, add a token, add a worker, track a
folder, share.

### Step 2: Claude's steps, carried out visibly (site only)

The answer's block may hold several steps. The dialog shows them as a numbered list with one
button, Do these steps, and a Step button beside each. Reads run at once, as now. For each change
the page closes the dialog, moves a visible pointer to the control, outlines it, presses it through
the registry and says what happened in the message note, then goes to the next. A step that would
merge, remove or spend still stops on that control's own confirmation, as it does by hand. The
guards of ask-claude-bar.md stay: a step belongs to the answer it came with, runs once, and does
nothing once the page has read the repository again, since the answer can be steered by any text
the run read, such as an issue anyone may open on a public repository.

### Step 3: a Terminal tab (site only)

A tab with a command line and a scrolling record. It parses the registry's commands, completes
names (tabs, workers, issue numbers), and prints what each did. `help` lists the actions with their
sentences; `ask TEXT` asks the assistant and prints its steps, which `do` then carries out. It runs
in the browser, as the signed-in person, through the same GitHub calls the buttons make; there is
no server behind it.

### Step 4: the control board as a command-line tool

The panel's GitHub operations move out of symphony-panel.js into one module with no dependencies
that the page loads and that a command-line program imports. The program, `symphony`, signs in
through gh's own sign-in (`gh auth token`) and runs the registry's actions: `symphony board`,
`symphony tasks`, `symphony give 12 nightly`, `symphony run workers`, `symphony merge 7`,
`symphony tokens`, `symphony workers`, `symphony ask "..."`. Reads print plain text, or JSON with
`--json` for Claude Code to read back; a change asks for confirmation unless `--yes` is given. It
holds no Claude credential: `symphony ask` goes through the assistant issue like the page, and
adding a token stays scripts/tokens.py's pseudo-terminal flow or the Token run, which never show the
token.

The recommendation is JavaScript for this module, since the page is the most complete
implementation and sharing its code is what keeps the two from drifting; Node has fetch built in,
so the program needs no package. It ships first inside the symphony plugin of
OpenSpineConsortium/symphony-marketplace, with a skill that tells Claude Code to use it, so any
session with the plugin drives the board by command at once and nothing is published elsewhere; an
npm package can follow. The checks are the panel-checks' kind: the program run against a mocked
GitHub, each action's request asserted.

### Step 5, optional: real-time answers from the person's own Claude Code

The assistant is slow because it starts a runner. A person who has Claude Code on their computer
can run `symphony serve`, which listens only on the computer's own address and pairs with the page
by a one-time code; the page then asks that Claude Code, signed in on the person's own
subscription, and gets answers in seconds, with the same registry for its steps. No credential
reaches the page or the repository, and no server of ours exists. Chrome asks the person before a
public page may reach a local address (Private Network Access), which is that pairing's consent.
This step changes what the panel can reach, so it waits for the owner's yes and a security review.

## Where it stands

The floating Claude button and the removal of the Ask Claude bar and the message line on every
layout are merged (site #117, 2026-10-20). Steps 1 to 5 are parked as a future feature: on
2026-10-20 the owner said "lets park this to a future tab, feature", after weighing Python against
JavaScript for step 4 and leaning towards Python for the idea of two code bases. If the work
resumes, these choices are open:

1. Step 4's language: JavaScript, one copy of every action, perhaps in a repository of its own that
   the site and the command line both vendor; or Python with the standard library, matching the
   template's tools, at the cost of a second copy of every action and a test pinning the two lists
   together.
2. Publishing the program on npm, which is outward-facing and waits for the owner's word.
3. Step 5, the local bridge, which waits for the owner's yes and a security review.
