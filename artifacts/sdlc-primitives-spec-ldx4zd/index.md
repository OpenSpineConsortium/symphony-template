# SDLC Primitives Spec

Oct 8, 2026 · @f

## Purpose and scope

This spec lists what cswap and Claude Swap Cloud can already export and import of a claude.ai Project, so the SDLC in "22-Multi-Agent GitHub CI Architecture" can be built on the fewest pieces. It names, for the Project's instructions, memory, topic and goal, description and the rest of its metadata, where each lives on claude.ai today, which primitive reads or writes it, in what file format, and what nothing carries yet.

It covers the two browser scripts, the extension and its bridge, `cswap project-move`, `cswap teleport`, the checkpoint and the handoff note, and the account registry's read-only surface. It leaves out the quota-based auto-switch, the TUI and the store release machinery, which move no project knowledge. Every claim below cites a file and line in the claude-swap repository as of 2026-10-08 (main at PR #45); "not verified" marks what the code cannot show.

## What the architecture needs from project metadata

The architecture wants every piece of project knowledge in the repository as plain files, and the Project on claude.ai only as a per-account window onto that repository. Document 22 puts the agent's standing rules in a `CLAUDE.md` at the repository root, hands task intent in as a Linear issue through `repository_dispatch`, and passes working state between sessions as a compressed markdown brief of about 500 tokens. Document 23 and the plan of 2026-10-08 ("Shared multi-account Claude project") add the rest: shared facts in `docs/memory/` with a `MEMORY.md` index pulled in by `@docs/memory/MEMORY.md`, the board in `docs/agents/STATE.md`, claims as branches named after the issue, and the old conversations under `docs/history/`. Nothing first-party lets one account's Project reach another's, so the repository is the only shared plane.

| Knowledge | Where the architecture keeps it | Which Project field holds it today | Read by |
| --- | --- | --- | --- |
| Standing rules and conventions | `CLAUDE.md`, `.claude/rules/*.md`, committed | Project instructions (one text) | Every session, at start, by Claude Code itself |
| Shared facts and decisions | `docs/memory/MEMORY.md` index plus one file per fact | Project memory (MEMORY.md and one file per entry) | Every session through the `@` import; tidied by a coordinator by PR |
| The goal of a task | A Linear or GitHub issue: title, description, acceptance criteria | The Project's topic, and the asks in its chat | The agent's first prompt (`direct_prompt`, `client_payload`) |
| The board: who holds what | `docs/agents/STATE.md`, `docs/agents/claims/<issue>.md`, the branch `claude/<issue>` | Threads and their status (not exported as state) | Every session before it starts work |
| Working state between sessions | A committed brief: `.claude/session.md` or a `docs/agents/` checkpoint | A thread's transcript | The next session's start prompt |
| Past conversations | `docs/history/` | Project chat, threads, session transcripts | People, and an agent asked to read them |
| Per-account window | A Project per account, same repository, same instructions | Name, description, repositories, model, effort, settings | The account's own threads only |
| Agent limits | `--allowedTools`, `--max-turns`, `.claudeignore`, the Action's `settings` JSON | Not a Project field | The runner's workflow file |

What the architecture does not need carried: live threads, uploads, routines, artifacts, connectors and the cloud environment, which document 25 keeps per account on purpose. What it needs done once per Project and then kept current by pull requests: the instructions as `CLAUDE.md`, the memory as `docs/memory/`, and the history as `docs/history/`. The primitives inventoried next are measured against that list.

## The Project's fields, where each lives and what carries it

The export script writes one folder, or one `.tar`, per Project. At its root sits `export.json`, a manifest of format `claude-project-export` version 1 with `kind` either `code` (a Claude Code project, the kind the SDLC uses) or `standard`, and beside it Markdown and raw files (`project-export.js:361-375`, `3411-3446`, `4039-4049`). The import script reads that folder and makes a new private project from it; it never changes an existing one. The table reads each field of a Claude Code project across the four places it can be: the route the script reads it from on claude.ai, the file it lands in, the request the import makes, and whether the round trip is whole.

| Field | Read from (route in `project-export.js`) | In the export | Written back by `project-import.js` | Covered |
| --- | --- | --- | --- | --- |
| Name | `record.name` of the channel (`3413`) | `name` in the manifest; the folder's name | `POST /v1/code/channels {name}` (`2041`); a taken name becomes `<name> (imported)` (`772-780`) | yes |
| Instructions | `config.system_prompt_addendum` (`3177-3180`) | `Channel Instructions.md` and `instructions` in the manifest | `PATCH .../config {system_prompt_addendum}`, one request (`1891`, `2260-2269`) | yes |
| Topic, which the architecture calls the goal | `record.topic` (`3414`) | `description` in the manifest; `Channel Info.md` | `PATCH /v1/code/channels/{id} {topic}`, after the settings (`2288-2291`) | yes. No separate goal field exists on a Project. |
| Memory | `GET /v1/code/memory/channel/{channel}/memories?limit=100` (`2538-3132`); 19 entries read on the live site on 2026-10-08 (PR #41), though the script's comments still say the route's replies were not seen; the `memory_stores` fallback answered 404 on 2026-10-07 | `Memory/<path>`, one file per entry, listed first among the file rows as type `project_memory` | `POST .../memories {path, content, precondition}` with preconditions guessed in turn (`1490-1509`, `1674-1678`); never confirmed live; what is refused lands as files under `carried-memory/` (`2126-2145`) | partial: the read is proven, the write is not |
| Files | `files:list` and `files:open` in 24 MiB pieces (`2441-2536`) | `Files/<path>`, rows of type `project_file` with byte counts | upload then `files:write` in batches of 10 or 100 MB (`1252-1447`); over 30 MB left out (`74`); a reserved path goes to `imported-not-placed/` | yes |
| Repositories | inside the config object, `default_source_urls` (`3421`) | the whole `settings.config`, verbatim | `PATCH .../config {default_source_urls}` (`1892`); the URLs only, GitHub must be connected in the new account | yes |
| Linked folders | `record.context_sources` (`3420`) | `settings.context_sources` | `PATCH {context_sources}`, one at a time (`1941-1970`) | yes, as links the account must be able to reach |
| Model, effort, auto-continue | config keys | `settings.config` | `PATCH .../config`, one key each: `default_model`, `channel_session_model`, `default_effort_level`, `channel_session_effort_level`, `limit_auto_continue` (`1893-1897`) | yes |
| Environment | `config.default_environment_id` | `settings.config` | left out by design (`1903-1904`) | no |
| Browser access | `config.allow_worker_chrome` | `settings.config` | left out by design (`1905-1906`) | no |
| Plugins, skills, MCP servers, tasks, member config | config keys seen in the mock (`tests/js/import.test.js:316-337`) | `settings.config` | dropped without a report line | no |
| Proactivity, PR attribution | no key named anywhere in either script | whatever the live config holds | nothing | not verified |
| Icon, colour | `record.icon`, `record.color` (`3418-3419`) | `settings.icon`, `settings.color` | in the create body (`2033-2036`) | yes |
| Memory on or off, visibility | `record.memory_enabled`, `record.visibility` (`3417`, `3424`) | `settings.memory_enabled`, `settings.visibility` | reported only; the new project is always private (`2041`) | partial |
| Members | a count of accounts other than the exporter (`3425`); the full list in `Raw JSON/channel.json` | `settings.other_members` | cannot add people; reported (`2275-2280`) | no |
| Timeline and threads | `/v1/code/channels/{id}/timeline` and the thread routes, 200 rows a page (`3241-3350`) | `Timeline.md`, `Threads/NNN <title>.md`, `Raw JSON/` | files under `imported-history/` with a README (`2147-2216`) | partial: files, never live threads |
| Sessions | the session event routes, 500 events a page (`2336-2399`) | `Sessions/<title>.md`, `.json`, `.events.json` | files, plus a `cswap teleport` line per session in the README (`1975-1989`) | partial |
| Connectors, routines, artifacts, decision cards, pull requests | no route (`282-349`) | not exported; a PR appears only as a link in thread text | nothing | no |
| Source account and organization | `source.id` only (`368-375`) | `source` in the manifest | a warning when the source is visible from the new login (`824-836`) | partial |

A standard project (`claude.ai/project/<uuid>`) exports the same way with other names: `Project Instructions.md` from `prompt_template`, `Project Description.md`, `Project Memory.md` as one text blob from `GET /api/organizations/{org}/memory?project_uuid=` (`286`, `1553`), `Files/` from the knowledge files and docs, and `Chats/<title>/` with the active branch of each conversation rendered to Markdown and its artifacts rebuilt by replaying the tool calls (`1328-1491`). The import creates the project, `PUT`s the instructions, uploads the files, and adds each chat and the memory as knowledge documents (`1023-1056`); no memory store is written.

The folder a code project leaves behind:

```
<Project name>/
  export.json              manifest: format, version, kind, name, description,
                           instructions, settings{...}, files[], history[], memory, problems[]
  Channel Info.md          the record's first text: instructions, prompt_template, description, topic or purpose
  Channel Instructions.md  the instructions, one text
  Timeline.md              every top-level message
  Memory/<path>            one file per memory entry
  Files/<path>             the project's files, byte for byte
  Threads/NNN <title>.md   one file per thread with replies
  Sessions/<title>.md      one transcript per cloud session, with .json and .events.json
  Raw JSON/                channel.json, timeline*.json, thread <id>.json, routes used.json
```

Three facts about the manifest matter to a repository: `exported_at` is wall-clock time (`372`), so the same project exported twice gives different bytes; no checksum is recorded for any file; and the manifest names neither the organization nor the account that exported it.

## The primitives, one by one

Ten things in the repository move or hold project knowledge. The line counts are `wc -l` on main at PR #45; the tests are counted apart.

| Primitive | Where | Lines | What it does | Its output | Where it runs |
| --- | --- | --- | --- | --- | --- |
| Export script | `src/claude_swap/browser/project-export.js` (byte-equal copy in `extension/src/`) | 4,149 | Reads one Project through the routes the site's own pages use, read-only, and writes the folder of the previous section | a folder through the directory picker, or a `.tar` download | in the claude.ai tab: pasted into DevTools, injected by the extension, or driven by `project-move auto` |
| Import script | `src/claude_swap/browser/project-import.js` | 2,715 | Makes a new private project from an export: create, memory, files, config keys one at a time, topic, context sources, then pauses it | the new project, and a report in the page | in the claude.ai tab, the same three ways |
| `cswap project-move` with a folder | `cli.py:1234-1425`, `2141-2416`; `project_move.py` (`read_export` 634-699, `MoveState` 175-217) | about 2,520 with the CLI parts | Hands the script out, opens the tab, keeps one move's state in `project-move.json`; `check` validates `export.json` against the files and `--wait` polls for it | the export folder; `check` exits 0, 2 or fails | the person's machine, no network |
| `cswap project-move export OWNER/NAME`, the branch carrier | `cli.py:2498-2558`; `project_move.py:908-995`; `prompts/project-export.md` and `project-import.md` | 18 lines of prompt, about 90 of polling | Pastes a prompt into the Project's chat; the Project's own Claude commits `.claude/project-export/{timeline.md, threads/, memory/, files/, instructions.md, README.md}` to branch `project-export`; `check --wait` polls GitHub's REST API every 30 s for branch and README | a branch in the repository | the Project's Claude, so inside the terms; the person pastes |
| `cswap project-move auto` | `project_move_auto.py`, `browser/automation.js`, `cli.py:1427-1716` | about 2,000 | Drives Chrome windows on profiles of its own over the DevTools protocol, runs both scripts, and watches for the sign-in | a new project; a `.log` of the run | the person's machine; the sign-in is still the person's |
| The extension and its bridge | `extension/src/*` (9,758), `bridge.py` (4,661), `file_dialogs.py` (287) | 14,907 | Export this project, Sign out and reload, Import, behind a native-messaging host; the job in `bridge/job.json`, its events in `events-<id>.jsonl`; the Save As and Open windows are the computer's own | the `.tar`, then the new project | Chrome only; one job at a time; the person at three points |
| `cswap teleport` | `teleport.py` (462), the pre-dispatch in `cli.py:238-386` | about 610 | Runs `claude --teleport` under one account's environment, commits a handoff note or the checkpoint, pushes, starts `claude --cloud` under the other account | a commit and a cloud session whose id is not captured | the person's terminal, interactive |
| The handoff note | `handoff.py` | 610 | Renders the local Claude Code transcript (JSONL) to a note of at most 12 KiB with a fixed redaction list, under `.claude/handoff/<id>.md`, meant to be `git rm`'d by its reader | Markdown, transient | local |
| The checkpoint | `checkpoint.py` (\`cswap checkpoint write | start | show\`) | 1,084 | Renders the same transcript to `.claude/session.md` (16 KiB cap) and the marker section of `CLAUDE.md` between `cswap:checkpoint:begin` and `end`, deterministically: the same transcript gives the same bytes, no wall-clock time; `Decision:` and `Constraint:` lines come first in the lists and are never cut, but the sentences inferred by regex land in the section too; `start_prompt(task)` is the opening prompt for the next session |
| The account registry, read-only | `switcher.resolve_account` (`switcher.py:947-972`), `SessionManager.launch_env` (`session.py:560-643`), `bridge.list_accounts` (`bridge.py:824-878`), `cswap list --json` (`json_output.py:305-360`, schemaVersion 1) | the core is about 10,050, of which these surfaces are a few hundred | Turns a slot number, alias or email into `(slot, email, organizationUuid)`; builds a `CLAUDE_CONFIG_DIR` environment for one account with every `ANTHROPIC_*` and OAuth token variable scrubbed; lists slots without touching a credential | a tuple, an environment, JSON rows | local |

The proportions say where the weight is. The two scripts are 6,864 lines and do all of the reading and writing of a Project. The extension and bridge are 14,907 lines of plumbing around them, 2.2 lines for every line of script, and they parse nothing of `export.json` but `name`, `kind`, `problems` and the file rows (`project_move.py:591-631`, `bridge.py:1066-1102`). The teleport group, 2,310 lines, reads no Project data at all: its inputs are the local transcript and git. The account core, about 10,050 lines, holds nothing about a Project; it is the per-machine registry of logins.

The formats, each pinned at a version:

- `export.json`, format `claude-project-export` version 1; any other version is refused by `project_move.py:597-606` and `project-import.js:420-424`.
- `.claude/project-export/` on branch `project-export`, the prompt route's layout, checked only as "the branch exists and `README.md` is on it" (`project_move.py:908-920`, `951-995`).
- `project-move.json`, one move's state; `bridge/job.json` and `events-<id>.jsonl`, one job and its story, redacted by allowlist.
- `.claude/session.md` and the `CLAUDE.md` marker section, rewritten whole on every checkpoint; `.claude/handoff/<id>.md`.
- `<backup root>/sequence.json`, the registry (email, uuid, organizationUuid, organizationName, alias, kind); `cswap list --json`, schemaVersion 1.

The one written-down model of what a Project is made of is the test mock, `tests/js/mock_claude_ai.js` (1,624 lines): its header dates each observed behaviour between 2026-10-04 and 2026-10-08 and says which routes were seen live and which are modelled on the site's front-end code or on Claude Code's own requests; `tests/js/harness.js` (368 lines) runs the two unchanged scripts against it under Node, and `tests/js/export_to_disk.js` writes a real export folder for the Python tests. Fixtures for any new tool come from there, not from a fresh guess at the site.

What the SDLC can call from a shell today without a browser: `cswap project-move check` (an export's validity), `cswap project-move check OWNER/NAME --wait` (the branch's arrival), `cswap checkpoint write` (the brief), `cswap list --json` (the accounts), and `launch_env` (an account's environment). Everything that touches claude.ai needs a signed-in tab and a person's paste or click, or runs as the Project's own Claude.

## What nothing carries yet, measured against the architecture

Each row takes a need from the second section, names the nearest primitive, and says what is missing. The order is the order the SDLC would hit them.

| Need | Nearest primitive today | The gap |
| --- | --- | --- |
| `CLAUDE.md` from the Project's instructions | The export writes `Channel Instructions.md` and `manifest.instructions`; the checkpoint already owns a marker section of `CLAUDE.md` | Nothing writes the instructions into `CLAUDE.md`. The prompt route cannot even set them on import: `project-import.md:6` replies with text for the person to paste, and `project-export.md:7` exports them only "if you can see them". A small materializer closes this. |
| `docs/memory/` from the Project's memory | `Memory/<path>` in the export, one file per entry, 19 entries read live on 2026-10-08 (PR #41) | Nothing writes them under `docs/memory/` or builds the `MEMORY.md` index. The reverse direction, repository to Project memory, rests on a write precondition never seen live, so the plan should never need it. A standard project's memory is one blob with no entries. |
| The goal as task intent | `topic` is the only field; the import sets it last | A Project has no goal field and no link to an issue. Issues and `STATE.md` live outside every Project field, so nothing in cswap is needed for them; the `topic` can carry a one-line pointer. |
| A handoff brief between sessions | `cswap checkpoint write`, deterministic, 16 KiB | Interactive only: no headless mode, local transcript only, nothing read from the Project, and the cloud session's id is never captured (`teleport.py:218`). The inference beyond tagged lines is word-list regexes (`checkpoint.py:73-97`), so a plausible wrong line can reach `CLAUDE.md`. |
| `docs/history/` from the conversations | `Timeline.md`, `Threads/`, `Sessions/` in the export; the import files them under `imported-history/` | A path, nothing more. Session `.events.json` logs can run to hundreds of MB (`project-export.js:351-359`); only the Markdown belongs in a repository. |
| An export nobody has to click | None. Every route needs a signed-in tab; the folder and extension routes need the person at Save As, sign-in and Open; `auto` still needs the person's sign-in; the extension runs one job at a time in Chrome | This gap cannot be closed by cswap code: the terms (next section) allow claude.ai to be scripted only by a routine or a cloud session. The prompt route, run by a routine inside the Project, is the one sanctioned unattended export, and it is lossy (no name, topic, settings, sessions or raw JSON, `prompts/project-export.md:3-7`) and non-deterministic. |
| Updating a Project that already exists | The import always creates a new private project (`project-import.js:36-39`); `auto --into` only resumes a part-made one | No sync, diff or merge. A second import of the same export makes "\<name> (imported 2)". For a thin Project whose instructions only point at the repository, this stops mattering. |
| One Project per account pointed at the same repository, with the same instructions | The import's create, `PATCH {system_prompt_addendum}` and `PATCH {default_source_urls}` do exactly this | Covered, once per account, by a person pasting the script, or by ten lines typed into a new Project by hand. |
| Settings the SDLC may care about: proactivity, PR attribution, plugins, skills, MCP servers | `settings.config` carries the whole object; the import applies seven keys and drops the rest silently | Not verified that proactivity or PR attribution exist as config keys at all. Measure on a live export before planning around them. |
| Connectors, environment, routines, members, browser access | Never read or written; the README lists them as to be set up again | Per-account setup by hand, by design on claude.ai's side. A routine in particular cannot be exported, so the export routine is made once per Project by hand. |
| Determinism and verification of an export | `check` validates that the manifest's rows exist; `exported_at` is wall-clock; no checksums | A materializer must drop `exported_at` and commit by content, so an unchanged Project gives an empty diff. The prompt route's output varies run to run and is checked only by the branch's existence. |
| A GitHub token in the loop | `project_move.py:969-979`: a private repository looks like 404 without a token; a 401 or 403 is reported as a bad token or rate limit | Fine for a person at a terminal. In an Action the token is `GITHUB_TOKEN`, which is in scope for the plan, not a gap here. |

The CI side confirms the picture from the other end. No workflow, action or script under `.github/workflows/`, `release-kit/` or `scripts/` reads or writes `CLAUDE.md`, `.claude/`, a memory file, a handoff note or an `export.json`, none calls a cswap move primitive, and none runs on a schedule: the four workflows move built artifacts (the test matrix, the store zip, the wheels) and nothing else. The repository's own checkpoint shows what happens without tooling: `.claude/session.md` was written by hand at the PR #37 hand-over and holds four `Decision:` and four `Constraint:` lines, while the `CLAUDE.md` marker section says `(none recorded)` for both; nothing checks the two against each other, and the next `cswap checkpoint write` replaces the hand-written file whole.

Two things the architecture asks for are simply not in cswap's remit and should not be added to it: a webhook receiver or edge proxy (document 22's Linear path), and a scheduler of browser sessions (document 23's orchestrator). The first is GitHub's and Linear's own machinery; the second runs against the terms and against the extension's own decisions (nothing retried on its own, the person at three points).

## Constraints that bind any design

The binding constraints come from Anthropic's terms, the Chrome Web Store, and the decisions already recorded in the repository; a design that breaks one is not a shortcut but a dead end.

- **Nothing scripts claude.ai on a schedule.** The Consumer Terms forbid access "through automated or non-human means" except through an API key or where Anthropic explicitly permits it; the Terms name no other exception, and routines and cloud sessions are Anthropic's own features rather than scripts against the site (document 25, section 2). So an export is a person's click in their own signed-in tab, as the scripts work today, never a daemon polling a Project. Memory that must flow continuously flows through git, not through claude.ai's routes.
- **Projects cannot be shared across accounts.** "A project belongs to one user" (document 25, from the Claude Code docs). Any shared state has to be a file in the repository or an issue on GitHub.
- **Every account signs in itself.** Nothing automates a sign-in or passes a challenge: a challenged, blocked or unauthenticated request is never re-sent by code, and a Retry-After is honoured in full (CLAUDE.md, Decisions; greg's rule that a failed step never loops and a person can always step in).
- **The trust boundaries stay.** The bridge's origin check, the manifest key, the tab id, the nonce and the sender-url checks; browser-side code never touches tokens; the extension's own code reads no cookie (the import script's `lastActiveOrg` read is the one disclosed exception); logs and events never carry cookies, tokens, headers, bodies or query strings (CLAUDE.md, Constraints; PRIVACY.md version 16).
- **The store's rules.** Manifest permissions are exactly `nativeMessaging`, `scripting`, `storage`, `sidePanel`, `alarms`, `notifications` with host permission `https://claude.ai/*`; the scripts ship inside the package (PR #44), minified but never obfuscated; any change to data handling bumps PRIVACY.md in both repositories, byte-equal.
- **No new runtime dependencies.** Python standard library only; the extension is plain ES modules with no build step (CLAUDE.md, Constraints). The repository is private and cswap reaches the public as bytecode-only wheels on PyPI (publish.yml, not yet tagged).
- **The two scripts are not changed for the import side** and the extension's copies stay byte-equal to them; `browser/*`, `project_move.py` and `handoff.py` are reused read-only (CLAUDE.md, Constraints).
- **Checkpoints are deterministic.** The same transcript gives the same bytes, with no wall-clock time (CLAUDE.md, Decisions), so a committed handoff diffs cleanly.
- **Platform limits that shape the plan.** A routine's API trigger takes 30 fires an hour, an account 100; events above that are dropped, not queued. Branch protection on a private repository needs a paid GitHub plan. Files over 30 MB stay out of an import (document 25; move-gaps.md).
