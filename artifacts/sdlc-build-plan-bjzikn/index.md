# SDLC Build Plan

Oct 8, 2026 · @f

## Recommendation

Build the focused utility, Route B, and leave Claude Swap Cloud as it is. The architecture wants every piece of project knowledge as files in the repository, and cswap's export already produces those files; what is missing is about 300 lines that put them where `CLAUDE.md`, `docs/memory/` and `docs/history/` expect them, deterministically, plus two short GitHub Actions. The extension and bridge are 14,907 lines of Chrome-only plumbing built for a one-time move with a person at the keyboard, and the one thing the architecture would need from them, an export on a schedule, is the one thing the terms forbid a browser script to do. A routine inside the Project, running the export prompt cswap already ships, is the sanctioned way to get the same files without a paste.

The companion spec, "SDLC Primitives Spec", holds the inventory and the gaps this plan rests on. Its finding in one line: the read side of a Project is proven (instructions, memory, files, history, settings), the write side is proven only for a new project, and nothing in cswap can or should drive claude.ai unattended.

&#91;embedded content: the repository as the one shared plane · Projects per account, cswap export once, an Action on push\]

Each account's Project becomes a thin window on the repository: ten lines of instructions that point at `CLAUDE.md`, the repository linked, nothing else kept there. cswap exports the Project once to seed the repository, a routine keeps the export branch fresh, and an Action turns each export into a pull request a person can read.

## Route A: expand Claude Swap Cloud

This route teaches the extension and its bridge to feed the repository. Three pieces would have to be built.

1. **A repository writer in the bridge.** A new job kind after an export: the bridge reads the whole `export.json` (today it reads `name`, `kind`, `problems` and the file rows, `bridge.py:1066-1102`), writes `CLAUDE.md`, `docs/memory/` and `docs/history/` into a checkout, and commits or calls GitHub. That is a new bridge command, a new side-panel button under greg's rule that the button layout never changes, new lines in `PRIVACY.md` and the store listing (the extension would now write outside the export folder), and a store review.
2. **A scheduler.** Document 23's orchestrator inside the service worker: alarms, a state machine in `chrome.storage.local`, a keepalive, a tab the worker opens on its own. The extension's own decisions forbid most of it: nothing is retried on its own, the person is at the Save As window, the sign-in and the Open window, and the Consumer Terms allow claude.ai to be scripted only by a routine or a cloud session. A scheduled export from the extension is the thing the terms name.
3. **Accounts inside the extension.** The SDLC wants one Project per account. Per-account logic and automatic switching inside the extension are out of scope by decision (`CLAUDE.md`, "Out of scope"), and the import deliberately takes whoever is signed in.

What it costs. The extension and bridge are already 14,907 lines of plumbing for 6,864 lines of script, Chrome only, one job at a time, with a store listing that changed its privacy text in PR #44 for the scripts alone. Every new path lands in that plumbing and in that review cycle. The scheduler is the piece the architecture most wants and the piece this route cannot have.

What it buys. A no-paste export for a person who already has the extension installed and is sitting at the browser. That is worth having and already exists.

Verdict: keep Claude Swap Cloud as it is, a convenience for the one-time export, and build nothing of the SDLC inside it.

## Route B: a focused utility on top of what exists

The repository is the plane every account shares, so the utility's one job is to turn an export of a Project into files in a repository, the same way every time. Everything else is a tool that already scales.

**The materializer.** One Python module in the standard library, about 300 to 480 lines plus 300 to 500 lines of tests (sized on 2026-10-09: the export readers return counts, not rows, so the row walk and a safe .tar extraction are new), reachable as `cswap project-move materialize <export> --repo <dir>` and as a file on its own. It takes an export in either layout, the script's folder or `.tar` with `export.json`, or the prompt route's `.claude/project-export/`, and writes:

- `CLAUDE.md`: the Project's instructions between a marker pair, with the hand-written text around them untouched, the same mechanism the checkpoint already uses for its section.
- `docs/memory/<path>`: each memory entry as the export has it, byte for byte, and `docs/memory/MEMORY.md` as the index, which `CLAUDE.md` pulls in with one `@docs/memory/MEMORY.md` line.
- `docs/history/<yyyy-mm-dd>/`: `Timeline.md`, `Threads/` and the session Markdown; never the `.events.json` logs.
- `docs/project.md`: the name, the topic, the repositories and the model and effort settings, nothing else.

It drops `exported_at` and writes by content, so an unchanged Project gives an empty `git diff`. It makes no request, reads no credential and runs anywhere Python runs, including a GitHub Action.

**The unattended export.** The prompt route already exists and is the one sanctioned way: a routine on the main account's Project runs `prompts/project-export.md` on a schedule and commits `.claude/project-export/` to the `project-export` branch. A GitHub Action on a push to that branch runs the materializer and opens a pull request to `main`. The Action needs no Anthropic key and no secret beyond `GITHUB_TOKEN`. The prompt's one gap, that it cannot read the instructions reliably, stops mattering once `CLAUDE.md` is the source and the Project's instructions are a pointer to it.

**The Projects.** One per account, thin: instructions of ten lines ("read `CLAUDE.md`; memory is `docs/memory/`; the board is `docs/agents/STATE.md`"), the repository linked, the model and effort set. Made once by hand or by one paste of the import script, which already does the create and the two `PATCH`es. Nothing to sync afterwards, because nothing lives in the Project.

**The rest is GitHub and Anthropic.** GitHub Issues as the task queue, branch protection on `main`, a small Action that regenerates `docs/agents/STATE.md` from branches and pull requests and comments on stale ones, Anthropic-run routines and cloud threads as the agents, and `cswap teleport --checkpoint` as the brief when a session moves between accounts. Linear, the edge proxy and `claude-code-action` from document 22 come later and only if Issues run out.

What it costs: about 300 lines of Python, two workflow files of about 30 lines each, and one routine made by hand per Project. What it does not touch: the two scripts, the extension, the bridge, the store listing, the terms.

## Industry tools to lean on instead of bespoke code

Almost every need in the architecture is met by a tool that already exists and scales on its own; what remains to build is the one bridge from a claude.ai Project to repository files.

| Need | Tool that already does it | What it saves writing |
| --- | --- | --- |
| Standing rules every session reads | `CLAUDE.md` with `@` imports and `.claude/rules/*.md`, read by Claude Code at start in the cloud and on a PC | Any instruction sync; the Project's instructions become a committed file |
| Shared memory across accounts | `docs/memory/MEMORY.md` plus one file per fact, imported by `@docs/memory/MEMORY.md`, changed by pull request | Document 23's memory daemon, path-hash translation and extension orchestrator |
| Claiming work without duplicates | A branch named after the issue (`claude/<issue>`): git accepts only the first push of a new branch | A Redis or KV lock, `github/lock`, a claim service |
| The board | `docs/agents/STATE.md` rewritten by a GitHub Action on every push to `main` (gh CLI, a few lines of YAML) | A coordinator service with its own store |
| Task intent and conversation | GitHub Issues and pull requests, with their native events; Linear later if its views are wanted | The HMAC-verifying edge proxy and `repository_dispatch` relay of document 22, which exist only because Linear is not GitHub |
| Agents that act on events | Claude Code routines (PR events, API trigger, hourly) and cloud threads, run by Anthropic under each account's subscription; `anthropics/claude-code-action` on GitHub Actions where a key-based runner is acceptable | Runners, schedulers and the loop guards around them |
| Handoff between sessions | `cswap checkpoint` (`.claude/session.md` and the `CLAUDE.md` marker section), committed; the next session's start prompt from `checkpoint.start_prompt` | A context-compression step |
| History | `docs/history/` in git from the export's `imported-history/` markdown | A transcript database |
| Freshness | Branch protection: require a pull request, a green check and an up-to-date branch | Rebase nagging code |
| Build, test, release | GitHub Actions already in the repository (`ci.yml`, `release.yml`, `publish.yml`), PyPI trusted publishing with no token | Nothing new |
| Identity for pushes | The Claude GitHub App, which cloud threads need anyway; a GitHub App token for any Action that must trigger CI | `GITHUB_TOKEN` loops and stored keys |

Two choices follow from the preference for fewer parts. First, GitHub Issues before Linear: GitHub's own events reach both Actions and routines with no proxy, signature check or dispatch relay, and Linear can be added later without changing the repository layout. Second, Anthropic-run agents before self-run ones: routines and cloud threads act as the signed-in account, so no API key is stored anywhere and the subscription already paid for does the work.

## Phased plan

Each phase ends with something measured on the real claude-swap Project, and the next phase starts only on that measurement.

**Phase 0, settle two choices (an hour).** GitHub Issues or Linear as the task queue, and routines and cloud threads or `claude-code-action` as the agents. The plan below assumes Issues and routines. On 2026-10-09 greg chose GitHub Issues and asked for the repository side first, as a GitHub template repository built from the bottom up with no export or import in its first layer (the sdlc-template work in the same thread); Linear and the materializer come later. Turn on branch protection for `main` in the claude-swap repository.

**Phase 1, the materializer (one to two days).** Write `materialize.py` against the export already on disk from greg's live run of 2026-10-08 (19 memory entries, PR #41). Tests from the fixtures in `tests/js/mock_claude_ai.js` and `tests/test_project_move.py`, plus one test that the same export twice gives the same bytes. Run it once on the real export and open the pull request by hand. Measured: the diff is readable, `CLAUDE.md` holds the instructions, `docs/memory/MEMORY.md` lists those 19 entries.

**Phase 2, the thin Projects (half a day).** On each account that will work the repository, make the Project by hand or by one paste of the import script: pointer instructions, the repository linked, model and effort set. Measured: a cloud thread on account B reads `CLAUDE.md` and `docs/memory/` from the repository and answers a question only the memory knows.

**Phase 3, the unattended loop (one day).** A routine on the main account's Project runs `prompts/project-export.md` weekly to the `project-export` branch; `.github/workflows/materialize.yml` runs the materializer on that branch and opens a pull request to `main`. Measured: one pull request arrives without anyone pasting anything, and `cswap project-move check OWNER/NAME --wait` sees the branch the same way it does today.

**Phase 4, the board (one day).** `.github/workflows/state.yml` regenerates `docs/agents/STATE.md` from the open issues, the `claude/<issue>` branches and the pull requests on every push and pull-request event, and comments once on a pull request idle for a day, the rule in greg's plan of 2026-10-08. No model call in it. Measured: a thread that claims an issue by pushing its branch appears on the board within a minute.

**Phase 5, the handoff (half a day).** Add a `--headless` mode to `cswap checkpoint write` that takes the transcript path and the output paths and nothing interactive, so an Action or a routine can render the brief. Capture the cloud session's id in `teleport.py` where today only the exit code is kept. Measured: a session moved from account A to B with `--checkpoint` starts from `.claude/session.md` and names the right next task.

**Later, only on demand.** Linear and the edge proxy, `claude-code-action` with a GitHub App token, the worktree pool and the lock branch of document 22, once Issues and routines show a limit. Each is a drop-in behind the same repository files, which is the point of putting the files first.

## Risks and open questions

- **The terms.** Anthropic's Consumer Terms forbid automated access to claude.ai except through an API key or where Anthropic explicitly permits it, and name no other exception; routines and cloud threads are Anthropic's own features, not scripts against the site. Every claude.ai step in this plan is a person's paste or a routine. Any scheduler that drives a browser, inside the extension or outside it, is the thing the terms name, and the plan has none.
- **Several accounts on one repository.** Projects cannot be shared across accounts, which is why the repository is the plane. Whether one person's several accounts may work one repository is a terms question greg raised in his plan of 2026-10-08 and has not settled. The plan works the same with one account per person.
- **Routine caps.** Thirty runs an hour per routine and a hundred an hour per account, from the same plan. A weekly export and a daily board are far under them.
- **The prompt route is lossy and varies.** The Project's Claude writes the export, so file names and wording differ run to run, no name, topic or settings travel, and `check` verifies only that the branch and its README exist. The materializer normalizes paths and drops dates, and the pull request shows a human the diff before it lands. If that proves too noisy, the script export pasted once a week by a person is the fallback, and it is exact.
- **Memory flows one way.** A live export read a Project's 19 memory entries on 2026-10-08; the write never was (the precondition is guessed, and refused entries land as files). The plan sends memory from the Project to the repository only, and the repository is the copy that counts. Seeding a new Project's memory from the repository is a hand paste or the import script, and may land under `carried-memory/`.
- **Instructions drift.** If the Project's instructions hold rules of their own, they diverge from `CLAUDE.md`. Make them a pointer and there is nothing to diverge.
- **Branch protection on a private repository** needs a paid GitHub plan or a public repository. claude-swap is private today; rulesets on the free plan cover part of it. To be checked on the repository's settings page, not assumed.
- **A key in Actions.** The materializer and the board need none. Document 22's `claude-code-action` needs an Anthropic key or OAuth token held as a secret, which the Beethoven rule "no API key anywhere" forbids in that project; decide per repository before Phase 4's successor.
- **Unpublished routes.** The export script uses the routes the site's own pages use; a site change stops it with the server's reason. The prompt route does not have this failure, which is one more reason it is the unattended path.
- **Not verified.** Whether proactivity and PR attribution exist as config keys on a Project; whether a routine can push a branch from every account (greg's plan says cloud sessions can); whether the site pages a standard project's file list. Each is one live look before the phase that needs it.
