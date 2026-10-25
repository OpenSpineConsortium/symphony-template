# A Symphony and Beethoven desktop app, a Chrome counterpart, and a path to any model

The thread "Plan Symphony desktop app and LLM-agnostic design", 2026-10-25, on the owner's message
of 11:24 UTC: the whole ecosystem in one PC and Mac desktop app where every interaction is click
and drag, one-click sign-in for the setup token of the GitHub workers, Claude's browser sign-in for
the grid workers and the local Claude Code for the desktop, scaling down to one Claude account,
sharing through the project's repository made from symphony-template, every tab of the control
panel kept and more integrated, the Claude Desktop and Claude in Chrome pair copied as Symphony and
Beethoven Desktop and Symphony and Beethoven in Chrome, and a start on making the ecosystem
LLM-agnostic, locally hosted and user-run remote models included.

This is a design and a plan, not a build: nothing was built, started or spent. What it rests on is
the template's own research, named where used (control-panel.md, control-panel-console.md,
control-panel-plus-style.md, grid-claude-accounts.md, beethoven-multi-account-workers.md,
claude-token-pool.md, native-ios-app.md). Facts about Anthropic's products and terms and about
outside tools are the author's knowledge as of mid-2026, marked "to verify" where a decision hangs
on them; the cloud session read no outside page for this note, to keep it lean as the owner's usage
asked.

## The answer in short

- Yes to the shape. One desktop app (Electron, as Claude Desktop is) whose window is the control
  panel's console, the same code the site serves, with three things a web page cannot do: drop files
  and folders from the computer, run the person's own Claude Code, and keep credentials in the
  operating system's keychain. One Chrome extension with a side panel (as Claude in Chrome has),
  merging symphony-extension and beethoven-extension, that talks to the desktop app through Chrome's
  native messaging when it is installed and falls back to the panel's GitHub-only powers when not.
- Yes to the three sign-ins, which is the right pattern and mostly built already: a setup token as
  an Actions secret for the workers in GitHub Actions, Claude's own browser sign-in for the grid
  workers, and the person's own Claude Code sign-in on the desktop. The app never holds, shows or
  stores a Claude credential itself; it starts the command that does and pipes the result to where
  it belongs (Auth, below).
- One account scales down by naming the same account in all three places; nothing changes in the
  design, the five-hour window is simply shared (Auth, One account).
- Sharing stays native: the project is a GitHub repository made from the template, shared by
  inviting a collaborator; whoever joins runs the same app on their own Claude account.
- LLM-agnostic is reachable in four steps because the coordination already is: claims, the board,
  checks and rulesets are git and GitHub, with no model in them. What is Claude-specific is the
  worker's runtime (Claude Code, its hooks and skills, claude-code-action). The plan puts a small
  runner interface between Symphony and the agent, keeps Claude Code first, and adds others behind
  it (LLM-agnostic, below).
- The terms question on offering a claude.ai sign-in is settled by the owner's written permission
  from Anthropic (Decisions for the owner, 1); code signing is still the owner's to decide.

## Flag for the owner: where credentials live

The project's rule is that no API key or Claude credential goes anywhere in a repository. The design
keeps to it, and says here where each one does live, since a desktop app makes it easy to get wrong:

| Credential | Where it lives | Never |
| --- | --- | --- |
| Setup token for the Actions workers | The repository's or organization's Actions secret (CLAUDE_CODE_OAUTH_TOKEN, the pool's SYMPHONY_CLAUDE_n), written by piping `claude setup-token` straight to `gh secret set`, as scripts/tokens.py does today | On disk, in the app's settings, in a log, in a repository file |
| An optional local copy of it | The operating system's keychain: macOS Keychain, Windows Credential Manager, libsecret on Linux (tokens.py already keeps one in Credential Manager on Windows) | A plain file |
| The desktop's own Claude sign-in | Where Claude Code keeps it: the Keychain on macOS, `~/.claude/.credentials.json` elsewhere; the app reads nothing of it | Copied by the app |
| A grid worker's sign-in | The node's CLAUDE_CONFIG_DIR under the student's grid home (hpcworker, `$HOME/.beethoven/claude`), a file of mode 600, since a compute node has no keychain | Anywhere else; this is the one place a credential sits in a plain file, and the owner should know it |
| A key for a user-run model server | The keychain on the desktop, an Actions secret for a worker in Actions | A repository file |
| The GitHub sign-in | The keychain (the App's user token, renewed as the panel renews it) | localStorage, as the web panel must use |

## The two apps

### Symphony and Beethoven Desktop

- Shell: Electron, recommended over Tauri. Claude Desktop is Electron; it ships the same Chromium on
  Windows and Mac, so the console that already runs in Chrome runs here unchanged, and the extension
  shares the same engine; Node's child processes start `claude`, `git` and `gh` with no extra layer.
  Tauri's installer is much smaller, but it uses Safari's WebKit on the Mac and WebView2 on Windows,
  which would put the console under two more engines to test.
- The window is the console: the rail of tabs, one tab at a time, the status line at the foot, the +
  dialogs and the cards (control-panel-console.md, control-panel-plus-style.md). The site's
  symphony-panel.js is loaded as the app's renderer, so a fix lands in both; what is desktop-only sits
  behind one bridge object (`window.symphonyDesktop`) the page checks for, as it checks the sign-in
  service today.
- What the desktop adds, through that bridge only: open a project (clone into a folder the person
  picks), run the local Claude Code in that folder (a session the app shows in a pane, or `claude
  --remote-control` so claude.ai and the phone can reach it), drop files and folders, read the
  keychain, and be the native messaging host for the extension.
- Updates: electron-updater from the app repository's GitHub releases, signed (Decisions).

### Symphony and Beethoven in Chrome

- One extension, merged from symphony-extension (the Migrate and Ready for Symphony buttons on
  GitHub's pages) and beethoven-extension (the grid worker, the portal's shell, the claude.ai tab
  switch of beethoven-multi-account-workers.md), with Chrome's side panel holding the same console.
- With the desktop app installed, the extension asks it, over native messaging, for what a browser
  cannot do (start a local session, drop a file to the grid); without it, the extension is today's
  panel plus today's Beethoven.
- The Chrome Web Store release kit already releases both extensions; the merge is one listing, with
  the old two kept for a deprecation period, since an extension's id cannot move.

## Drag and drop

Every drag is an action the panel already has as a button, so the drop is a shortcut and never a
second code path. Each drop that changes GitHub shows what it will do on a card the person confirms
once, as the + dialogs do.

| Drag | Onto | Does |
| --- | --- | --- |
| A folder from the computer | The app's start page | Make a project: a repository from the template, both Apps' install, the form (the front door's one press) |
| An existing repository folder | The start page | Adopt it (protocol only or whole template), as Migrate does |
| A task card | A worker card | Give it: the label worker:<name> (the coordinator's own move) |
| A task card | The Done or Queue column | todo on or off |
| A worker card | An account in Tokens | Run that worker on that slot (SYMPHONY_CLAUDE_SETTINGS) |
| A file or folder | The Grid tab | Upload through the portal to the lab volume, held to the size rule first |
| A file or folder | The Folders or Notebook tab | Track it (OneDrive through Graph) or add it to the notebook by id, never moving it |
| A Word document | A reviewer in Lens review | Start the lens review |
| A person (from Share) | The project | Invite as a collaborator |
| A pull request card | Merge | Merge once green, on the standing permission |

## Tabs carried over

All of the console's tabs come as they are: Command, Board, Tasks, Dependencies, Pull requests,
Runs, Workers, Agents, Tokens, Share, Grid, Folders, Explore, Notebook, About and the Claude button.
Three become more integrated, which is the point of the desktop:

- Grid: the worker's terminal and the Slurm queue in panes beside the board, and files dropped
  straight on, instead of the portal tab Beethoven drives today.
- Folders and Notebook: the local folder and the OneDrive item side by side, so tracking is a drag.
- Claude: a local session in a pane, on the project's own folder, with the board in the next pane;
  claude.ai's Remote Control link opens it on the phone.

## Auth: the three sign-ins, and why this is the right pattern

1. Workers in GitHub Actions: `claude setup-token` (a year-long subscription token, made for CI) as
   an Actions secret. This is the documented way claude-code-action runs on a subscription, and
   Actions can do nothing interactive. One click: the app runs `claude setup-token` behind a
   pseudo-terminal that masks it, the person signs in on Anthropic's page in the browser, and the
   token goes straight into `gh secret set` (tokens.py, today, as a command line; the app is a
   button over it). The Tokens tab's Add a Claude account already mints it on a runner instead.
2. Grid workers: Claude's browser sign-in, `claude auth login` on the compute node, the link opened
   in the person's browser and the code pasted back (built: hpcworker framework 21,
   grid-claude-accounts.md). This is better than a setup token there, since the sign-in renews
   itself and a worker can swap accounts (cswap's way, one CLAUDE_CONFIG_DIR per account). In the
   app it is one button that opens the link and a paste box, as Beethoven does.
3. The desktop: the person's own Claude Code, signed in once by Claude Code itself. The app only
   starts `claude` and never sees the credential.

So the pattern is right: interactive sign-in wherever a person can be present and the machine is
the person's, a long-lived token only where nothing can be interactive. The one place it bends is
the grid, where the interactive sign-in sits in a plain file (the flag above).

### One account

One Claude account works for all three: the same account signs in on the desktop, makes the setup
token and signs in on the grid. Nothing in the design changes; the cost is that every worker shares
that account's five-hour and seven-day windows, which the pool already reads and the hook already
hands off at 90 percent. The app's first run asks for one account and offers "add another account"
later, which fills the pool's next slot; the advice that a CI token is best one of an account nobody
uses by hand stays advice, as the owner set on 2026-10-13.

## Sharing

The project is its repository. Share invites a collaborator (built, the Share tab); the person
invited installs the app, signs in to GitHub and to their own Claude account, and opens the same
repository: the board, the claims and the checks are the same for both. A Claude project on
claude.ai belongs to one user and cannot be shared (the template's Constraints), so the repository
is what is shared and each person's sessions are their own, exactly as today.

## LLM-agnostic

### What already is

Claims (the first push of `claude/N`), the board, the releases, the overlap check, the required
check, the rulesets and the review record are git and GitHub; no model is in them. A worker that can
run `git`, read PROTOCOL.md and open a pull request can work here whatever runs it.

### What is Claude-specific

- The runtime: Claude Code, its hooks (the push guard, the board at session start, the usage
  trailer), its skills and commands, and claude-code-action in the workflows.
- The instructions file is CLAUDE.md; most other agents read AGENTS.md.
- The pool, the five-hour windows and the handoff read Claude's own rate_limit_event.

### The plan, in four steps

1. Move the push guard's rules where every agent meets them: a git pre-push hook (scripts/ already
   installs hooks for beethoven-qa) calling the same tools/guard_push.py, with the rulesets behind
   it as today. The Claude hook stays; the git hook covers every other agent, and a person.
2. A runner interface, one small file per runner under `.github/symphony/runners/` beside the
   workers' registry, naming the command, how a prompt goes in, how the result comes back, the
   instruction file it reads, and where its credential lives (an Actions secret name or a keychain
   entry, never a value). A worker's file gains `"runner": "<name>"`, with claude-code the default.
   workers.yml, the coordinator and the desktop all start a worker through it. AGENTS.md becomes a
   generated pointer to CLAUDE.md, so both kinds read one text.
3. Runners, in the order they cost least to add (to verify against each tool's current release
   before building): Claude Code pointed at another endpoint (it reads ANTHROPIC_BASE_URL, and a
   gateway such as LiteLLM, or a server that speaks Anthropic's Messages API, puts another model
   behind it with every hook and skill kept); then other agent command lines that run headless in
   Actions (OpenAI's Codex CLI, Google's Gemini CLI, Aider, OpenHands, goose), each reading
   AGENTS.md and the git hook.
4. Measure before claiming: coordbench runs the same CooperBench tasks under each runner, the
   protocol fixed, so "works with model X" is a number. That spends tokens and waits for the owner's
   word and count, as every run does.

### Local and user-run models

- On the desktop: Ollama, llama.cpp's server or LM Studio, each serving an OpenAI-compatible
  endpoint on localhost (Ollama also an Anthropic-compatible one, to verify); the app lists what it
  finds and the person picks a model per worker.
- On the grid: a GPU job serving vLLM (OpenAI-compatible) as a Slurm job through hpcworker, the
  grid workers on the same node or a peer pointing at it; this uses the lab's GPUs with no
  subscription at all, and is held to the grid's rules: no job without the owner's word and count.
- A user-run remote server: any OpenAI- or Anthropic-compatible URL and a key, the key in the
  keychain or an Actions secret.
- What to expect: the protocol is long and asks for careful tool use; small local models are
  likely to break claims or skip the check, which is what step 4 measures and the required check
  and rulesets catch regardless.

## Phases

1. Desktop shell over the console: Electron, the site's panel as the renderer, GitHub sign-in in the
   keychain, open a project, start the local Claude Code in its folder. Read-only beyond what the
   panel already writes.
2. The one-click token and the grid sign-in buttons over tokens.py and hpcworker; drag and drop for
   the moves in the table, each confirmed once.
3. The merged Chrome extension with the side panel, and native messaging to the desktop.
4. The git pre-push guard and the runner interface, Claude Code over a gateway as the second runner,
   a local Ollama model as the third.
5. coordbench across runners, on the owner's word.

Each phase is one repository's pull requests: the desktop app is a new repository (the owner makes
it, since a session cannot), the extension work lands in symphony-extension, the runner interface
in symphony-protocol and the template.

## Decisions for the owner

1. The terms question, settled by the owner. Anthropic's Agent SDK documentation says, as the
   author recalls it, that unless previously approved, third-party developers may not offer
   claude.ai sign-in or rate limits for their products, agents built on the SDK included. The owner
   said on 2026-10-25 at 11:36 UTC that an Anthropic representative gave the owner written permission for
   any of the owner's third-party apps to offer a claude.ai sign-in without further approval, given the
   nature of the owner's research. The session has not seen that writing; it should be kept with the
   project's records, outside git if it is private, so the permission can be shown when the app is
   published. On that permission the app may offer its own claude.ai sign-in; driving each person's
   installed Claude Code stays the default where it is simpler.
2. Electron (recommended) or Tauri.
3. Code signing: an Apple Developer membership for notarising the Mac build, and a Windows
   code-signing certificate, both paid each year; unsigned builds warn on every install.
4. Merge the two extensions into one (recommended) or keep both.
5. Which local runtime comes first: Ollama on the desktop (recommended, least setup) or vLLM on the
   grid.
