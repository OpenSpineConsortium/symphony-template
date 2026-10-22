# Claude Chat vs. Claude Code: Architectural Analysis of Interface-Exclusive Capabilities

Oct 3, 2026 · @greg

## Scope and taxonomy correction

The two surfaces run the same models; what differs is the harness around the model, the tools it is handed, and where the execution and trust boundary sits. Chat is a hosted conversation with a browser renderer and a disposable server-side sandbox. Claude Code is an agent loop with read/write/execute access to a real environment, a permission system, and a config-as-code layer. Fewer capabilities are exclusive than the prompt assumes, and the naming needs one correction before the analysis is useful.

**`claude.ai/code` is not the CLI.** Claude Code is one harness shipped through several front-ends: the terminal CLI (`claude`), the VS Code and JetBrains extensions, the Code tab in the desktop app, cloud sessions at `claude.ai/code` (Anthropic-hosted sandboxes, plus Remote Control of a session on your own machine), the GitHub Action, and the Agent SDK for embedding the same loop in your own programs. The URL `claude.ai/code` is the web surface for cloud sessions, Remote Control, Projects and Routines; the agent you run on a laptop is the CLI or an IDE extension signed into the same account. This report uses "Chat" for `claude.ai/chat` and the consumer apps, and "Claude Code" for the harness in any front-end, naming the front-end where it matters.

**What is actually exclusive.** Three of the six features the prompt labels exclusive are shared, so their sections below analyze the difference in ingestion path and scale rather than a hard boundary.

| Capability | Chat (`claude.ai/chat`, desktop, mobile) | Claude Code (CLI, IDE, `claude.ai/code`, SDK) | Verdict |
| --- | --- | --- | --- |
| Artifacts: live render, versioning, publishing, AI-powered pages | Native side-panel renderer, publish to a shareable link, artifact types (docs, slides, designs) | Publishes self-contained HTML or Markdown pages to claude.ai through its own Artifact tool (v2.1.183+): versions, sharing, comments, per-viewer connector calls, /design canvas; no in-session preview pane | Shared since June 2026; the in-conversation preview runtime, inline edit UI and consumer remix/embed gallery stay chat-only |
| Projects with uploaded knowledge and server-side retrieval | Project instructions, knowledge files, retrieval mode when knowledge exceeds the context window, project memory | `CLAUDE.md` hierarchy, `@` imports, auto-memory, agentic search over the repo; Claude Code Projects at `claude.ai/code` are task threads, not a knowledge base | Chat-exclusive (server-side grounding); Code has a file-based equivalent |
| Vision: images, screenshots, PDFs | Drag-and-drop, 20 files per message, visual PDF parsing | Paste or drag an image into the terminal, `@` a path, or let the `Read` tool open PNG/JPG/PDF files from disk, in bulk | Shared; differs in ingestion and scale |
| Read/write/execute on the user's own machine | None; a sandboxed Linux container with an allow-listed egress proxy, reset between tasks | Full RWX through `Read`, `Write`, `Edit`, `Glob`, `Grep`, `Bash`, gated by permissions, hooks and an optional OS sandbox | Code-exclusive |
| Terminal write-run-read-fix loop against the real toolchain | Only inside the sandbox (no local deps, no internal network, no secrets) | Native; the loop is the product | Code-exclusive on the real environment |
| MCP | Remote MCP via Connectors (Streamable HTTP, OAuth); local stdio servers in the desktop app via `claude_desktop_config.json` and `.mcpb` bundles | stdio, SSE and HTTP servers; `local`, `project` and `user` scopes; `.mcp.json` committed to the repo; per-tool permission rules; Claude Code itself as an MCP server | Shared; Code adds local-process servers in the CLI, config-as-code and tool-level policy |
| Headless and programmatic use | None (the app is interactive) | `claude -p`, structured JSON output, Agent SDK, GitHub Action, Routines | Code-exclusive |
| Multi-session orchestration | One conversation at a time | Subagents, agent view, agent teams, cross-session messaging across machines and cloud sessions | Code-exclusive |
| Web search and fetch | Yes | Yes (`WebSearch`, `WebFetch`) | Shared |
| Memory across conversations | Chat memory, past-chat search, project memory | Auto-memory per project directory, `CLAUDE.md` | Shared; different mechanics |

## Phase 1.1 The Artifacts engine

"Artifacts" is two systems that share a name. The first is the in-conversation preview runtime in Chat: a side panel that compiles and renders what the model writes while the conversation continues. The second is the hosted published page on `*.claudeusercontent.com`, which Chat and, since June 2026, Claude Code can both write to. Only the first is chat-exclusive; the second is the shared delivery layer for anything either surface wants to put on a URL.

### Generation and iteration

The model, not the UI, decides what becomes an artifact: content that is substantial, self-contained, and likely to be edited or reused (code over roughly 20 lines, a document, a diagram, an interactive page). It emits the content with a declared type (code, Markdown document, HTML, SVG, Mermaid, React component), and the client parses that block out of the streaming response and mounts it in the panel. Edits are either a targeted patch (an exact-string replacement against the current version) or a full rewrite; each one becomes a version the user can step back through. Users can also select text inside the panel and ask for an inline change, so iteration happens on the rendered object rather than by re-pasting source. Download, copy, publish, and (on consumer plans) remix are affordances of the panel.

### The preview sandbox

The panel is an iframe on a separate origin with a strict Content Security Policy. Scripts can load only from an allow-listed CDN (`cdnjs.cloudflare.com`); there are no external images, no arbitrary network calls, and no `localStorage` or `sessionStorage` (artifacts that try to use them fail). React artifacts are transpiled in the browser with a fixed library set: React itself, Tailwind core utility classes with no JIT compiler, `lucide-react`, `recharts`, `d3`, `three` (r128, no OrbitControls), `plotly`, `chart.js`, `mathjs`, `lodash`, `papaparse`, SheetJS, `shadcn/ui`, `tone`, `mammoth`, and `tensorflow`. Mermaid and SVG render client-side; HTML artifacts render as a full page with CSS and JS inlined into one file. The constraints are what make the loop fast: no build step, no dev server, no dependency resolution, so a generate → render → look → fix cycle costs one model turn.

### Calling an API from inside an artifact

The only API an artifact can reach directly is Anthropic's. A `fetch` to `https://api.anthropic.com/v1/messages` from the preview carries no API key; claude.ai proxies the call and bills it to the subscription of whoever is viewing the artifact, which is why shared AI-powered artifacts cost the creator nothing. The call accepts the normal Messages payload plus two extensions: `mcp_servers`, which lets the artifact call tools on the viewer's own connected connectors, and the hosted web-search tool. Two runtime helpers round this out: `window.storage` (a per-user or shared key-value store, 5 MB per key, for trackers and journals) and `window.fs` (read access to files uploaded in the conversation). "Call APIs directly" therefore means the Anthropic API and, through it, MCP connectors. A third-party REST endpoint, your own backend, or a payments API is blocked by the CSP; the pattern for external data is a connector.

```javascript
const res = await fetch("https://api.anthropic.com/v1/messages", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    model: "claude-sonnet-4-6",
    max_tokens: 1000,
    messages: [{ role: "user", content: prompt }],
    mcp_servers: [{ type: "url", url: "https://mcp.linear.app/mcp", name: "linear" }]
  })
});
const data = await res.json();
const text = data.content.filter(b => b.type === "text").map(b => b.text).join("\n");
```

### The published page runtime

Publishing moves the artifact to a different runtime with its own rules. The page is a single self-contained file (HTML or Markdown, rendered to at most 16 MiB) served under a CSP that allows scripts only from cdnjs, jsDelivr's `/npm/` paths, the Tailwind play CDN and jQuery's CDN, stylesheets only from Google Fonts, and `fetch`/XHR/WebSocket only to the page's own origin. The preview-only helpers (`window.claude.complete`, the direct `api.anthropic.com` fetch, `window.storage`, `window.fs`) do not exist there. Their replacements are capabilities the author declares at publish time: connector calls that run through each viewer's own claude.ai connections (the page never sees a credential and each viewer approves first), a downloads capability (the viewer cannot save a `blob:` or `data:` link otherwise), shared or per-viewer state, and the viewer's identity. There is no backend and no routing, so a page cannot authenticate viewers itself or serve multiple routes.

### Artifacts from Claude Code

Claude Code gained an `Artifact` tool in v2.1.183 (desktop app v1.13576.0). It writes an HTML or Markdown file, asks permission (Manual and Accept-edits modes; the classifier decides in Auto mode), uploads it to claude.ai, and prints a URL that opens in the browser. Republishing the same file updates the same URL in place; each publish is a version, and `/artifacts` lists what you own or were given. Connector-backed pages (v2.1.209+), comment threads that Claude can read and answer (v2.1.221+, Team and Enterprise only), a built-in design skill that reads your project's design tokens (v2.1.182+), and a `/design` canvas (v2.1.234+) are all in the same tool. The conditions are stricter than in Chat: a Pro, Max, Team or Enterprise plan, a session signed in with `/login` (API keys, gateway tokens and cloud-provider credentials cannot publish), the Anthropic API as provider, and no CMEK, HIPAA or Zero Data Retention policy on the organization. On Pro and Max a public link is the only sharing option, and a connector-backed page cannot be shared at all.

### Why the preview is chat-only

The preview is a UI surface, and the CLI has no renderer. Claude Code's equivalent loop is file → publish → browser, or file → `open report.html`, which costs a round trip and loses the inline edit affordance. It also cannot run the in-browser React transpiler; a Claude Code artifact loads React as a UMD script from a CDN. Nothing architectural prevents Anthropic from adding a preview pane to the desktop app's Code tab, and the IDE extensions already render some output inline, so this boundary is a product decision rather than a hard constraint.

### When to use which

| Situation | Use |
| --- | --- |
| Prototype a UI, chart or game and iterate by looking at it | Chat preview |
| An app other people run, billed to their own plans, with no infrastructure | Chat AI-powered artifact, published |
| A PR walkthrough, investigation timeline or dashboard built from the repo and session data | Claude Code artifact |
| A status board that reads live data per viewer | Either surface, connector-backed page |
| Anything with a backend, routes, or auth of its own | Neither; deploy on your own infrastructure |

Sources: [What are artifacts](https://support.claude.com/en/articles/9487310-what-are-artifacts-and-how-do-i-use-them), [Publishing and sharing artifacts](https://support.claude.com/en/articles/9547008-discovering-publishing-customizing-and-sharing-artifacts), [Share session output as artifacts (Claude Code)](https://code.claude.com/docs/en/artifacts), [Artifacts in Claude Code (announcement)](https://claude.com/blog/artifacts-in-claude-code).

## Phase 1.2 Projects and knowledge bases

A Chat Project is server-side grounding: Anthropic stores the documents, extracts and caches their text, and injects either the whole corpus or retrieved chunks into every conversation under that Project. Claude Code's equivalent is file-based grounding plus agentic retrieval: `CLAUDE.md` files travel with the repository, and the model finds everything else by searching the tree at run time. The two differ in where the index lives, who maintains it, and whether the retrieval step is deterministic.

### Mechanics of a Chat Project

A Project carries three kinds of persistent state, and each enters the context window differently.

| State | What it is | How it reaches the model |
| --- | --- | --- |
| Custom instructions | Free text that behaves like a project-scoped system prompt (role, tone, conventions, output format) | Prepended to every conversation in the Project, every turn |
| Knowledge | Uploaded files (PDF, DOCX, TXT, code, CSV, Markdown), pasted text, and files pulled from Google Drive or GitHub; 30 MB per file, unlimited count | Full text in the prompt while the total fits the context window; retrieved chunks once it does not |
| Project memory | A summary Claude maintains from prior chats in the Project (paid plans), editable by the user, plus the past-chat search tool scoped to the Project | Injected as a short block and queried on demand |

The interesting transition is the second row. While knowledge fits, every conversation starts with the whole corpus in context, and prompt caching makes that cheap: the Project content is cached, so repeated references count only new or uncached tokens against usage limits. When the corpus approaches the context window, the Project switches automatically to retrieval mode ("RAG mode"), which raises capacity by up to about 10x. In that mode Claude no longer sees everything; it calls a project-knowledge search tool and gets back the passages that match the query. Anthropic's own guidance follows from that: put facts the model must always know (naming conventions, hard constraints, key decisions) in the instructions, not in a document that may or may not be retrieved, and write knowledge files so that relevant sections are findable by the terms a user would use. Retrieval mode is paid-plan only according to the current Projects overview; the older RAG article says all plans, and the two have not been reconciled.

Across conversations the Project is the unit of sharing and scope. On Team and Enterprise plans a Project can be shared with an organization, with its instructions and knowledge inherited by everyone's chats; chats inside a Project can search only other chats in that Project; memory is generated per Project. None of this touches a user's machine, which is the point: a product manager with a browser gets the same grounded assistant as the engineer who set it up.

### Claude Code's equivalent: `CLAUDE.md` and agentic retrieval

Claude Code has no uploaded corpus and no server-side index. Its persistent context is a hierarchy of Markdown files loaded at session start: an enterprise-managed policy file, `~/.claude/CLAUDE.md` for the user, `./CLAUDE.md` or `.claude/CLAUDE.md` for the project (committed to git), and `CLAUDE.local.md` for personal overrides, with `@path` imports to pull in other files. Everything else the model needs it fetches itself, by reading files and running searches, which means the "knowledge base" is the repository and the index is whatever `find`, `grep` and the model's own judgement can locate. Auto-memory adds a per-project notes directory the model writes to across sessions, and skills (`SKILL.md` folders) package reusable procedures that load on demand.

```markdown
# CLAUDE.md (project root, committed)

## Build and test
- `uv run pytest -q` runs the suite; `uv run ruff check .` lints
- Never edit files under `generated/`; run `make codegen` instead

## Conventions
- Public functions take a `Config` object, not loose kwargs
- Error types live in `toolbox/errors.py`; do not add ad-hoc exceptions

@docs/architecture.md
```

There is also a feature called Projects inside Claude Code at `claude.ai/code`, in public beta on Pro and Max. It is unrelated to Chat Projects: it groups parallel task threads that run in the cloud or, through Remote Control, on your machine. It is a work organizer, not a knowledge base, and conflating the two is a common error.

### What the difference means in practice

| Dimension | Chat Project | Claude Code (`CLAUDE.md` + search) |
| --- | --- | --- |
| Source of truth | Uploaded copies, refreshed manually or by Drive/GitHub sync | The working tree, always current |
| Retrieval | Deterministic injection while it fits; embedding-style search after | Agentic: model-issued `find`/`grep`/`Read` calls, non-deterministic |
| Who can maintain it | Anyone with a browser | Whoever can commit to the repo |
| Version control | None (the Project has no history of knowledge edits) | Full git history, reviewable in PRs |
| Scale ceiling | Context window, then roughly 10x via retrieval | Unbounded corpus, but every byte read costs context |
| Best for | Specs, policies, design docs, PDFs, non-engineer collaborators | Build commands, conventions, architecture notes, anything the code must obey |

Use a Chat Project when the grounding material is documents rather than code, when non-engineers need the same context, or when you want the corpus available on a phone. Use `CLAUDE.md` when the grounding must be versioned with the code and enforced in the environment where the code runs. The strongest setups do both: the spec lives in a Project, and the distilled constraints are committed to `CLAUDE.md`.

Sources: [Retrieval augmented generation (RAG) for projects](https://support.claude.com/en/articles/11473015-retrieval-augmented-generation-rag-for-projects), [Usage limit best practices](https://support.claude.com/en/articles/9797557-usage-limit-best-practices), [Upload files to Claude](https://support.claude.com/en/articles/8241126-does-claude-ai-have-a-file-upload-limit).

## Phase 1.3 Multimodal vision parsing

Vision is a property of the model, not of the chat UI, so it is not a chat exclusive. Both surfaces send images to the same vision encoder; what differs is how pixels get into the request, how many can go in at once, and what the model can do with the result afterwards. Chat is built for a human handing over a handful of visual inputs; Claude Code is built for the model fetching images itself from disk, including thousands of them in a loop.

### How the model sees

An image enters the Messages API as a content block alongside text. The encoder works at a bounded resolution: large images are downscaled so the long edge is about 1,568 px (roughly 1.15 megapixels), and the token cost is approximately (width × height) / 750, so a full-size screenshot costs on the order of 1,500 tokens, comparable to a page of prose. Small or low-resolution images lose detail, and Anthropic's guidance is to supply images of 1000 × 1000 px or larger. Supported formats are JPEG, PNG, GIF and WebP. PDFs are handled as both text and page images when they are 100 pages or fewer, so charts, figures and scanned layouts are readable; longer PDFs (up to 1,000 pages in Chat) are processed as text only.

### Ingestion in Chat

Uploads come from the file picker, drag-and-drop, clipboard paste, or screenshots on desktop and mobile. The limits are 20 files per chat, 500 MB per file, and 8000 × 8000 px per image. Because the image is attached to the turn, the model answers immediately and the conversation can iterate on the same image ("now make the sidebar collapsible") without re-uploading. The typical structural-translation tasks all work in one turn:

- UI mockup or whiteboard photo → React or HTML in an artifact, rendered next to the source so the user can compare
- Chart or table screenshot → CSV, JSON or a Markdown table (values are read, not measured; expect rounding on dense plots)
- Architecture or sequence sketch → Mermaid diagram
- Error dialog or stack trace screenshot → diagnosis
- Form or receipt → structured fields

The output can go straight into an artifact, which is the one real UX advantage: a mockup becomes a running component in the same panel where the mockup is visible.

### Ingestion in Claude Code

Claude Code takes images three ways: paste a screenshot into the terminal with `Ctrl+V` (not `Cmd+V` on macOS), drag a file onto the terminal, or reference a path and let the `Read` tool open it. `Read` returns PNG, JPG and other formats as visual content, resizing and recompressing large images to the model's limits first; an image still over 500 KB after resizing is re-encoded as a lower-quality JPEG at the same pixel dimensions, so fine pixel detail can be lost. The documented workaround is to crop first (ImageMagick through `Bash`), which is itself a tool call the model can make. `Read` also opens PDFs (whole when short, in ranges of up to 20 pages with a `pages` parameter when longer than 10) and Jupyter notebooks with their rendered outputs. Nothing stops the model from reading a hundred images in sequence; each costs its token share and gets compacted out of context like any other tool result.

The difference in scale cuts both ways. Chat caps you at 20 files per conversation and cannot reach a dataset on disk. Claude Code can walk a directory, but reading every image through the model is the wrong tool for bulk work: at \~1,500 tokens an image, 10,000 images is 15 million input tokens. The correct Claude Code pattern is to have the model write a script (OpenCV, PIL, a vision model call through the API, or a classifier it trains) that processes the dataset, then use `Read` on a sampled handful to spot-check results. Vision is the inspection step, not the pipeline.

### Verdict

|  | Chat | Claude Code |
| --- | --- | --- |
| Input path | Picker, drag, paste, mobile camera | Terminal paste, drag, `Read` on a path |
| Volume per request | ≤ 20 files | Unbounded, bounded by context and cost |
| Can the model fetch images itself | No (only `window.fs` inside an artifact) | Yes, from disk, a screenshot it took via Playwright MCP, or a URL |
| Immediate visual output | Artifact rendered next to the source | Publish an artifact or open a file |
| PDF depth | Visual to 100 pages, text to 1,000 | `pages` ranges, no fixed page cap |

Sources: [Upload files to Claude](https://support.claude.com/en/articles/8241126-does-claude-ai-have-a-file-upload-limit), [Tools reference: Read tool behavior](https://code.claude.com/docs/en/tools-reference).

## Phase 2.1 Local file system and git automation

Claude Code has no filesystem API and no git API. It has a small set of tools that run on the machine where the session lives, and a loop that calls them: the model emits a `tool_use` block, the harness checks it against permission rules and hooks, executes it, returns a `tool_result`, and the model decides what to do next. Git automation is nothing more than the `Bash` tool running `git`, steered by instructions in the system prompt and by your permission rules. Understanding the tools and the loop explains both what the agent can do and where it fails.

### The agent loop

1. Session start: the harness assembles the system prompt (built-in instructions, the `CLAUDE.md` hierarchy, environment facts such as OS, shell, cwd and `git status`, loaded skills) and the tool definitions.
2. The user's message is sent to the Messages API with those tools attached. Extended thinking runs before the first tool call when the task warrants it.
3. The model returns text and zero or more `tool_use` blocks.
4. For each tool call, Claude Code evaluates `deny` rules, then `ask` rules, then `allow` rules and the permission mode; `PreToolUse` hooks run and can block or rewrite the call. Rules are enforced by the harness, not by the model.
5. The tool runs locally; its output (truncated to configured limits) goes back as a `tool_result`; `PostToolUse` hooks run (format, lint, log).
6. Repeat until the model ends its turn. A `Stop` hook can refuse the end of turn (for example, "tests have not been run") and send the model back to work.

The loop is identical in the CLI, the IDE extensions, cloud sessions, the GitHub Action, `claude -p`, and the Agent SDK. What changes between them is the machine the tools run on and who is watching the permission prompts.

### The tool set

| Tool | What it does | Mechanics worth knowing |
| --- | --- | --- |
| `Read` | Returns a file with line numbers; also images, PDFs, notebooks | Paginated with `offset`/`limit`; a `PARTIAL view` notice when a file exceeds the token budget; absolute paths |
| `Edit` | Exact-string replacement | `old_string` must match once; `replace_all` for many; read-before-edit is enforced (a `cat`/`head`/`sed -n` through Bash also counts) |
| `Write` | Create or overwrite a whole file | Requires a prior read on existing files for older models; never appends |
| `Glob` | File-name patterns (`src/**/*.ts`), sorted by mtime, capped at 100 results | Absent by default on macOS, Linux and WSL; present on Windows |
| `Grep` | Content search built on ripgrep: regex, `type`/`glob` filters, `files_with_matches`/`content`/`count` modes, `multiline` | Respects `.gitignore` (Glob does not); absent by default on Unix |
| `Bash` | Shell commands, each in a separate process | `cd` persists inside the project, `export` does not; aliases from your rc file are applied; 2-minute default timeout, 10-minute ceiling; long commands auto-background |
| `LSP` | Definitions, references, diagnostics after each edit | Inactive until a code-intelligence plugin and language server are installed; not started in cloud sessions |
| `Agent` | Spawns a subagent with its own context window | Parent sees only the final report; `isolation: worktree` gives it a private checkout |
| `EnterWorktree` / `ExitWorktree` | Creates and enters an isolated git worktree under `.claude/worktrees/` | Parallel tasks on the same repo without colliding on the index |
| `Monitor` | Tails a log, polls CI or a PR, watches a directory or a WebSocket | 5-minute default deadline, 30-minute maximum; same permission rules as Bash |
| `NotebookEdit` | Edits Jupyter cells by `cell_id` | Covered by `Edit(...)` path rules |

The prompt's phrase "reads files via grep/glob" is right in spirit and slightly off in implementation. On macOS, Linux and WSL the harness currently leaves the dedicated `Glob` and `Grep` tools out of the default set; Claude searches with `find` and `grep` through `Bash`, and those commands run embedded `bfs` and `ugrep` binaries, so the calls reach your hooks and permission rules as `Bash` calls. The dedicated tools come back when you name them in `--tools`/`--allowedTools`, when Bash is denied, or for a subagent whose tool list includes them but not Bash. Either way there is no index: traversal is agentic, driven by the model's hypotheses about where things are, and anchored by whatever `CLAUDE.md` says about the layout.

### Output limits shape behavior

A valid Bash result reaches the model inline up to about 30,000 characters; past that it is written to a file in the session directory and the model gets the path plus a 2,000-character preview. A failing command is truncated to about 10,000 characters as a head-and-tail excerpt. Exit code 1 is treated as benign only for `grep`, `rg`, `find`, `diff`, `test`, `git diff` and `git grep`; every other non-zero exit is a failure. These rules are why the model reaches for `| tail -50`, `--quiet` flags and targeted test selection: it is managing its own context budget.

### Git via Bash

Staging and committing are ordinary shell commands. The harness instructs the model to inspect `git status` and `git diff` before committing, draft a message from the diff, add a `Co-Authored-By: Claude` trailer, never force-push to shared branches, and never skip hooks unless told to. The user controls the blast radius with rules:

```json
{
  "permissions": {
    "allow": [
      "Bash(git status*)", "Bash(git diff*)", "Bash(git log*)",
      "Bash(git add*)", "Bash(git commit*)", "Bash(gh pr create*)"
    ],
    "ask": ["Bash(git push*)"],
    "deny": [
      "Bash(git push --force*)", "Bash(git reset --hard*)",
      "Read(./.env)", "Read(./secrets/**)"
    ]
  }
}
```

Bash rules are prefix globs; the harness strips wrappers such as `timeout 30` and `xargs` before matching, and a `Read` deny also blocks `Edit` and `Write` on the same path. Deny wins over ask wins over allow.

Three features make git work safer than running the same commands by hand. Checkpoints snapshot the working tree before each edit so `/rewind` (or `Esc` twice) restores code, conversation, or both. Worktrees (`claude --worktree`, `EnterWorktree`, or `isolation: worktree` on a subagent) give parallel tasks separate checkouts of the same repository. The GitHub Action and the GitHub App run the same loop inside CI, triggered by an `@claude` mention on an issue or PR, with repository write scoped to a token you control.

### Why Chat cannot do this

Chat's "Code execution and file creation" runs in a disposable Linux container on Anthropic's side: `/home/claude` as scratch, `/mnt/user-data/uploads` for files you attached, `/mnt/user-data/outputs` for files it hands back, an egress proxy that allows package registries and GitHub but nothing else, and a reset between tasks. It can run `git clone` on a public repository through that proxy and produce a patch file, but it cannot see your working tree, your SSH keys, your toolchain, or your internal network, and anything it produces must be downloaded and copied by hand. The container is a calculator, not a workstation.

Sources: [Tools reference](https://code.claude.com/docs/en/tools-reference), [Permissions](https://code.claude.com/docs/en/permissions), [Identity and access management](https://code.claude.com/docs/en/iam).

## Phase 2.2 The terminal execution and error loop

The write → run → read error → fix loop is the product. It is one agent loop iteration repeated with the shell as the oracle: `Edit` changes a file, `Bash` runs the test or build, the harness returns stdout, stderr and the exit code, the model diagnoses and edits again. Its economics are governed by context growth, and its failure mode is a model that keeps proposing fixes without acquiring new evidence.

### One iteration, mechanically

1. `Edit` applies an exact-string replacement; the `LSP` tool (when a language-server plugin is installed) reports type errors immediately after the edit, which often short-circuits the run step.
2. `Bash` runs `pytest -q tests/test_parser.py -x` in a fresh process. The model sets a timeout if it expects a long run; the default is 2 minutes and the ceiling 10, after which the command is moved to the background and polled.
3. The result comes back inline (about 30,000 characters for success, a 10,000-character head-and-tail excerpt for failure) with the exit code. A `PostToolUse` hook may have run a formatter or linter in between and appended its output.
4. The model reads the traceback, usually `Read`s the implicated lines with an `offset`, and edits again.

A dev server or watcher runs with `run_in_background: true`; the model continues and reads its output file later, or hands a `Monitor` the job of flagging errors as they appear.

### Token economics

Every iteration appends to one conversation, and the whole conversation is re-sent on every model call. Three mechanisms keep that affordable.

- Prompt caching: the system prompt, `CLAUDE.md`, tool definitions and the conversation prefix are served from cache on each call, so the marginal cost of an iteration is roughly the new tool output plus the model's new output, not the full transcript.
- Compaction: when the context approaches its limit the harness summarizes older turns automatically; `/compact <focus>` does it on demand with guidance about what to keep, and `/clear` starts over. Old tracebacks are exactly what compaction discards.
- Subagents: a test run or log dig delegated to an `Agent` consumes its own context window, and only the final report returns to the parent. Noisy verification belongs in a subagent for this reason alone.

The quantities that matter are the size of each tool result and the number of iterations. A 5,000-line test log read in full costs more than the fix it reveals; `-x`, `--tb=short`, `| tail -40` and targeted test selection are not stylistic preferences, they are the model managing its own budget. On subscription plans the same tokens count toward the 5-hour and weekly windows; on API billing they are the bill.

### Hallucination and doom loops

The loop fails when the model stops learning from the oracle. Observed patterns:

| Pattern | What it looks like | Why it happens |
| --- | --- | --- |
| Oscillation | Fix A breaks test 2, fix B breaks test 1, repeat | Local reasoning on partial context; the model never reads the shared dependency |
| Test tampering | Assertions loosened, tests skipped or deleted, `try/except: pass` added | "Make the tests pass" was taken literally; the test, not the code, became the target |
| Phantom API | Calls to a method or flag that does not exist in the installed version | Training-data prior outranked the environment; nobody checked `--help` or the source |
| Wrong file | Edits to a vendored copy, a build output, or a sibling with the same name | Agentic search returned the first plausible match |
| Stale context | Fixes for an error that the previous edit already resolved | The old traceback is still in context and reads as current |
| Permission thrash | Repeated attempts at a denied command with small variations | A deny rule with no explanation of the alternative |

### Mitigations that work

- Plan first: plan mode (`Shift+Tab` twice, or `--permission-mode plan`) restricts the session to read-only tools until you approve an approach. Most oscillation starts with an edit made before the dependency graph was understood.
- Test-driven instructions: write the failing test first, commit it, then say "make this pass without modifying the test." A `PreToolUse` hook that denies `Edit` on `tests/**` turns the instruction into a guarantee.
- Give the model evidence tools: a language-server plugin, a `Monitor` on the dev-server log, a Playwright MCP server for screenshots. Loops end faster when the oracle is richer than a traceback.
- Bound the run: `--max-turns` in headless mode; `maxTurns` in a subagent definition; a `Stop` hook that blocks the end of turn until `pytest` has passed at least once.
- Reset context: `/clear` when the transcript is full of dead ends; `/rewind` to the checkpoint before the first bad edit.
- Put the invariants in `CLAUDE.md`: "never skip or weaken a test", "run `make check` before claiming done", "the API client is pinned at v3; consult `vendor/client/README.md`".

```json
{
  "hooks": {
    "PreToolUse": [{
      "matcher": "Edit|Write",
      "hooks": [{ "type": "command", "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/protect-tests.sh" }]
    }],
    "PostToolUse": [{
      "matcher": "Edit|Write",
      "hooks": [{ "type": "command", "command": "uv run ruff format --quiet $(jq -r .tool_input.file_path)" }]
    }],
    "Stop": [{
      "hooks": [{ "type": "command", "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/require-green-tests.sh" }]
    }]
  }
}
```

A hook that exits 2 blocks the action and feeds its stderr back to the model as the reason, so the model learns the rule instead of guessing around it.

### Why Chat's sandbox is not this loop

Chat can run the same cycle inside its container, and for a self-contained script it is adequate. It breaks on anything that touches the real environment: your pinned dependency versions, a GPU, a local database, an internal package index, a service behind a VPN, or a test suite that needs fixtures from disk. The container also resets between tasks, so the loop cannot accumulate state across a session. It is the right place to validate an algorithm and the wrong place to fix a build.

Sources: [Tools reference: Bash tool behavior](https://code.claude.com/docs/en/tools-reference), [Permissions](https://code.claude.com/docs/en/permissions).

## Phase 2.3 Model Context Protocol (MCP) integration

MCP is not a Claude Code exclusive either: Chat reaches remote MCP servers through Connectors, and the desktop app can launch local servers. What Claude Code adds is the stdio transport in the terminal, configuration that lives in the repository, and a permission and hook layer that sees every MCP tool by name. That combination is what lets an agent reach a local database or an internal API without a browser-based OAuth product in the middle.

### The protocol in one paragraph

An MCP server exposes three things over JSON-RPC 2.0: tools (functions with JSON Schema inputs), resources (addressable data such as a file, a table or a document) and prompts (reusable templates). The client, here Claude Code, lists them at connection time, forwards the tool schemas to the model as ordinary tool definitions, and relays each `tool_use` to the server. Three transports exist: stdio, where the client spawns the server as a child process and talks over its standard streams; Streamable HTTP, the current remote transport (POST of JSON-RPC, responses as JSON or an SSE stream, session tracked by an `Mcp-Session-Id` header, OAuth 2.1 for auth); and SSE, the earlier remote transport, now deprecated. A server can also call `roots/list` to learn the directory the client was launched from, and send `list_changed` so the client refreshes its tool set.

### Registering servers in Claude Code

```bash
# local process, stdio transport (the default when no --transport is given)
claude mcp add --scope project db -- npx -y @bytebase/dbhub \
  --dsn "postgres://readonly@localhost:5432/analytics"

# remote server, Streamable HTTP, OAuth handled by /mcp on first use
claude mcp add --transport http --scope user linear https://mcp.linear.app/mcp

# remote server with a static header, for an internal API behind a gateway
claude mcp add --transport http --scope project inventory https://mcp.internal.example.com/mcp \
  --header "Authorization: Bearer ${INVENTORY_TOKEN}"

claude mcp list        # connection status for every server
claude mcp get linear  # which scope holds it and its config
/mcp                   # inside a session: status, OAuth login, tool names
```

Scopes decide where the definition is written and who else gets it.

| Scope | File | Shared with | Typical use |
| --- | --- | --- | --- |
| `local` (default) | `~/.claude.json`, keyed by project path | Only you, only this project | Experiments, servers with personal credentials |
| `project` | `.mcp.json` at the repo root | Everyone who clones the repo | Team infrastructure: the project database, the internal API, Playwright |
| `user` | `~/.claude.json`, global block | You, in every project | Personal tools: GitHub, Linear, docs search |

Project scope is configuration as code. The file supports `${VAR}` and `${VAR:-default}` expansion so secrets stay in the environment, and `${CLAUDE_PROJECT_DIR}` for project-relative paths. Because a cloned `.mcp.json` could launch arbitrary processes, Claude Code asks for approval before starting project-scoped servers the first time, and `claude mcp reset-project-choices` clears those decisions. Precedence when names collide is local over project over user.

```json
{
  "mcpServers": {
    "db": {
      "command": "npx",
      "args": ["-y", "@bytebase/dbhub", "--dsn", "${ANALYTICS_DSN}"],
      "env": { "LOG_LEVEL": "warn" }
    },
    "inventory": {
      "type": "http",
      "url": "${INVENTORY_MCP_URL:-https://mcp.internal.example.com/mcp}",
      "headers": { "Authorization": "Bearer ${INVENTORY_TOKEN}" }
    }
  }
}
```

### Tools, resources and prompts inside a session

MCP tools appear to the model as `mcp__<server>__<tool>`, and that name is what permission rules and hook matchers see: `mcp__db__query` can be allowed, `mcp__db__*` denied, and a `PreToolUse` hook can inspect the SQL in `tool_input` before it runs. Resources are referenced with `@server:scheme://path` in a prompt, or enumerated with `ListMcpResourcesTool` and read with `ReadMcpResourceTool`. Server prompts become slash commands of the form `/mcp__server__prompt`. Tool results are capped: Claude Code warns above 10,000 tokens and truncates at 25,000 by default, adjustable with `MAX_MCP_OUTPUT_TOKENS`.

Tool search is on by default and changes the cost model that used to make large MCP setups impractical. Instead of loading every server's tool schema into context on every turn, Claude Code marks MCP tools as deferred and gives the model a `ToolSearch` tool; when a task needs a tool, the model searches for it, loads its schema, and reuses the reference for the rest of the session. Servers that should always be loaded go in `alwaysLoad`, and `ENABLE_TOOL_SEARCH` tunes the threshold. The `WaitForMcpServers` tool exists only when tool search is off, since `ToolSearch` otherwise absorbs the wait for servers still connecting.

### Security model

A stdio server runs as a child process with your user's privileges, so adding one is equivalent to running its code. The trust boundary is therefore the package you choose, not the protocol. Mitigations layer: the project-scope approval prompt, `allow`/`deny` rules on `mcp__` names, hooks that inspect arguments, the OS sandbox (a sandboxed Bash cannot reach a port the proxy does not allow, though MCP servers themselves run outside the sandbox), and enterprise managed settings with `allowedMcpServers`/`deniedMcpServers`. Prompt injection arrives through tool results: a row in a database or a page fetched by a server can contain instructions, and the harness treats them as data but the model may not. Keep write-capable tools behind `ask` rules, and give database servers read-only credentials.

### Claude Code as an MCP server

`claude mcp serve` exposes Claude Code's own tools (Read, Edit, Bash and the rest) over stdio, so the desktop app or any MCP client can drive a Claude Code session. It is the inverse integration: Claude Code becomes a tool provider for another agent.

### What Chat and desktop have instead

Chat connects to remote servers through Connectors: a directory of first-party integrations (Google Drive, Gmail, Calendar, Slack, Linear, Notion and others) plus custom connectors for any Streamable HTTP server with OAuth, available on Pro, Max, Team and Enterprise. The Directory and Claude Code share the same MCP infrastructure, so any server in it can also be added to Claude Code with `claude mcp add`. The desktop app adds local stdio servers through `claude_desktop_config.json` and installable `.mcpb` bundles, and `claude mcp add-from-claude-desktop` imports those definitions into Claude Code. What Chat lacks is the terminal-side control plane: no per-tool permission rules, no hooks, no `.mcp.json` in the repo, and no way to reach a server that is only on `localhost` from a browser tab.

Sources: [Connect Claude Code to tools via MCP](https://code.claude.com/docs/en/mcp), [MCP quickstart](https://code.claude.com/docs/pt/mcp-quickstart.md), [Tools reference](https://code.claude.com/docs/en/tools-reference), [What are artifacts (MCP integration availability)](https://support.claude.com/en/articles/9487310-what-are-artifacts-and-how-do-i-use-them).

## Phase 3.1 Workflow impossibilities

"Impossible" below means not achievable inside the surface without leaving it, given the limits documented above: Chat's 20-file cap, disposable container and egress allow-list; Claude Code's lack of a preview pane, server-side knowledge store and hosted runtime for other people. Each scenario is stated with the limit that makes it fail.

### Centralized Python toolbox repository

The repository: a shared `toolbox/` package with 60 modules, a `pyproject.toml`, `uv`-managed dependencies, a pytest suite, and three downstream projects that pin it.

| Task | Chat | Claude Code | Why |
| --- | --- | --- | --- |
| Rename `toolbox.io.load_volume` to `read_volume`, update 41 call sites across the package and the three consumers, run the suites, bump the version, commit, open a PR | Impossible | Trivial (`Grep` or `grep -rn`, `Edit` per site, `uv run pytest`, `git commit`, `gh pr create`; worktree per consumer repo) | Chat cannot see the working tree; 20 uploads cover a third of one repo; outputs would have to be downloaded and merged by hand |
| Explain the dependency graph of the package to a new contributor as an interactive diagram they can click through | Trivial (upload `pyproject.toml` and a module listing, get a React or Mermaid artifact in the panel, iterate on it visually) | Possible but indirect: generate the graph with a script, publish it as an artifact (`/login` required) or open a local HTML file | No preview pane in the CLI; the chat panel renders and re-renders in one turn |
| Keep a living "how we use the toolbox" guide that product and research staff consult without engineers | Trivial (a Project with the README, ADRs and API docs as knowledge; instructions pin conventions) | Impossible for non-engineers; `CLAUDE.md` is only visible to people who run Claude Code in the repo | The knowledge store is server-side in Chat and file-based in Code |
| Enforce "every public function has a docstring and a type-checked signature" on every edit the agent makes | Impossible to enforce; a reminder at best | Trivial (`PostToolUse` hook runs `ruff` and `mypy` on the edited file; `Stop` hook refuses to finish while they fail) | Hooks and permission rules exist only in the harness |
| Fix a bug that only reproduces against the lab's internal package index and a GPU | Impossible | Trivial, in the environment where it reproduces | The container has no GPU, no VPN, no internal index; its egress is limited to public registries |

### Image datasets

The dataset: 48,000 PNG tiles in `data/tiles/`, 220 GB on a workstation, with a CSV of labels.

| Task | Chat | Claude Code | Why |
| --- | --- | --- | --- |
| Look at 15 tiles and tell me what the labelling guidelines got wrong | Trivial (drag the 15 images in, discuss, revise the guideline document in an artifact) | Trivial (`Read` the 15 paths) | Vision is shared |
| Build a preprocessing pipeline (resize, normalize, deduplicate by perceptual hash), run it over all 48,000 tiles, write a manifest, and commit the script and the manifest | Impossible | Trivial: write the script, run it with `run_in_background`, `Monitor` the log, spot-check 10 outputs with `Read`, commit | 20-file cap, no path to the disk, container resets, no multi-hour background jobs |
| Produce a shareable dashboard of label distribution and a scrollable gallery of outliers for a weekly review | Trivial once the numbers exist (paste the CSV summary, get a published artifact with charts; anyone with the link can filter it) | Possible: Claude Code publishes the same page as an artifact, with the data computed in the session; the gallery embeds images as data URIs within the 16 MiB page limit | Both publish; Chat is faster for a non-engineer, Code is better when the data is on disk |
| Fine-tune a small classifier on the tiles and report validation metrics | Impossible (no GPU, no dataset, no persistence between tasks) | Trivial | The container is a calculator, not a workstation |
| Let a clinician or domain expert audit 200 outlier tiles on their phone and record decisions | Trivial (an AI-powered artifact with `window.storage` or a published page with the downloads capability; the reviewer uses their own plan) | Impossible as an interactive review; Code can produce the page but has no per-viewer state without the artifact runtime capabilities that Chat's AI-powered artifacts provide natively | Hosted runtime with per-viewer billing and storage is a Chat feature |

### External data APIs

The integration: a vendor REST API with an API key, an internal metrics service reachable only on the office network, and a Linear workspace.

| Task | Chat | Claude Code | Why |
| --- | --- | --- | --- |
| Triage this week's Linear issues, draft replies, and update their status | Trivial through the Linear connector (OAuth, no code) | Trivial through the same server added with `claude mcp add --transport http linear https://mcp.linear.app/mcp` | Remote MCP is shared |
| Build a nightly ETL that pulls from the vendor API with the real key, loads into the internal Postgres, and alerts on schema drift | Impossible | Trivial: `.mcp.json` for the database, key from the environment, script committed, scheduled with `/schedule` (Routines in the cloud) or the team's cron | The container holds no secrets, cannot reach the internal network, and does not persist |
| Prototype a client for the vendor API from its OpenAPI spec and sanity-check a few calls | Trivial if the API is public (paste the spec, run `requests` in the sandbox) | Trivial | Public egress through package registries only; a public API is reachable only if its host is on the allow-list, which most are not, so Chat typically generates the client without executing it |
| Build a dashboard that shows live vendor metrics to the team | Possible only through a connector: an AI-powered artifact can call MCP servers via the Anthropic API, but it cannot `fetch` the vendor REST endpoint directly (CSP) | Same constraint on a published artifact; the alternative is a small service you deploy that exposes the metrics as an MCP server, which both surfaces can then call per viewer | Artifact pages reach external data only through connectors |
| Query the internal metrics service during an investigation | Impossible | Trivial: `curl` through `Bash`, or an MCP server pointed at the service | Office network is unreachable from Anthropic's container |

### The pattern

Chat wins when the work is bounded, visual, document-shaped, or needs to reach people who do not have a repository. Claude Code wins when the work is on disk, needs secrets or a network you control, must run long, or must be enforced rather than requested. The third column of each table is a reminder that the two surfaces now share more than they used to: remote MCP, publishing, vision, and web access are available on both, so the remaining impossibilities are all about where state lives and who can reach it.

Sources: [Upload files to Claude](https://support.claude.com/en/articles/8241126-does-claude-ai-have-a-file-upload-limit), [Share session output as artifacts](https://code.claude.com/docs/en/artifacts), [Tools reference](https://code.claude.com/docs/en/tools-reference).

## Phase 3.2 Security and isolation

The comparison is usually framed as "cloud upload" versus "local agent," and that framing is wrong in one important way: Claude Code also sends your code to the cloud. Every file it reads, every diff it writes, and every command output it sees is transmitted to the model provider as context. The real contrast is between a surface where you choose what to upload and nothing executes on your hardware, and a surface where the model chooses what to read and executes on your hardware. Each needs different controls.

### Data flow

| Question | Chat | Claude Code (local) | Claude Code (cloud session) |
| --- | --- | --- | --- |
| What leaves your machine | What you upload or paste; connector data the model requests | Whatever the model reads: files, diffs, command output, MCP results | The repository the session clones, plus the same session traffic |
| Who decides what is sent | You, per upload | The model, per tool call, within your permission rules | The model, inside an Anthropic-managed VM |
| Where execution happens | Anthropic's sandboxed container | Your machine, as your user | An isolated VM with egress through a filtering proxy |
| Secrets exposure | Only what you paste; connectors hold OAuth tokens on Anthropic's side | Anything readable by your user unless denied by rule or sandbox | Environment variables you place in the environment config, visible to anyone who can edit it; git credentials never enter the VM (a proxy swaps scoped placeholders for your token) |

### Training and retention by plan

The plan, not the surface, decides what Anthropic may do with the data. Consumer accounts (Free, Pro, Max) carry a "Help improve Claude" setting introduced with the August 28, 2025 terms update; it applies to chats and to coding sessions run with those accounts, including Claude Code. Opted in, data may be used for model training and is retained up to five years; opted out, retention is about 30 days. Conversations flagged for policy violations may be kept up to two years regardless. Commercial agreements (API, Team, Enterprise, Bedrock, Vertex, Foundry) do not train on customer data by default, retain for about 30 days unless contracted otherwise, and can be configured for Zero Data Retention. The practical rule for proprietary code: a Pro or Max subscription in Claude Code is a consumer data path until the training toggle is off; a Team or Enterprise seat or an API key is a commercial path.

Some features are tied to that choice. Claude Code artifacts, `/feedback`, Claude-drafted feedback and Remote Control push delivery run on Anthropic-hosted infrastructure and are unavailable under Zero Data Retention or on cloud providers, so the most locked-down configuration also forgoes the most connected features.

### Chat-specific risks and controls

- Uploaded files and Project knowledge are stored with the account; deleting a chat excludes it from future training but does not unwind models already trained.
- Connectors act with the OAuth scopes you granted; a prompt injected through a document or a web page can ask the model to call them. The viewer-approval step on connector-backed artifacts and the read-only scopes you choose are the defenses.
- Published artifacts are public to anyone with the link on consumer plans; on Team and Enterprise, public sharing is off until an Owner enables it, retention policies apply, and the audit log and Compliance API record publish, share and delete events.
- The code-execution container is isolated from your environment, so the blast radius of a bad command is a scratch directory. The egress allow-list (package registries, GitHub) is the only route out besides the conversation itself.

### Claude Code-specific risks and controls

The threat model is an autonomous process with your privileges that reads untrusted text. Three risk classes matter.

1. Destructive actions: `rm -rf`, `git push --force`, `git reset --hard`, dropping a table through an MCP tool. Controls: deny rules, `ask` rules on anything irreversible, checkpoints and `/rewind`, worktrees so the main checkout is never the target, read-only database credentials.
2. Exfiltration via prompt injection: a README, an issue comment, a web page or a tool result instructs the model to `curl` your `.env` to a host. Controls: `Read(./.env)` and `Read(~/.ssh/**)` deny rules; the OS sandbox with a network allow-list, which stops the `curl` at the proxy; `WebFetch(domain:...)` rules; `PreToolUse` hooks that reject commands referencing secret variables; separating the session's user from your own account on shared machines.
3. Supply chain: an MCP server, plugin, hook or skill is code you run. Controls: project-scope approval prompts, pinned package versions in `.mcp.json`, enterprise `allowedMcpServers`, and reading the server before adding it.

```json
{
  "permissions": {
    "defaultMode": "acceptEdits",
    "deny": [
      "Read(./.env*)", "Read(~/.ssh/**)", "Read(~/.aws/**)",
      "Bash(curl *)", "Bash(wget *)", "Bash(ssh *)",
      "Bash(git push --force*)", "WebFetch"
    ],
    "ask": ["Bash(git push*)", "mcp__db__execute"]
  },
  "sandbox": {
    "enabled": true,
    "network": { "allowedDomains": ["api.anthropic.com", "pypi.org", "files.pythonhosted.org", "github.com"] }
  }
}
```

The sandbox is OS-enforced: Seatbelt on macOS, bubblewrap plus a `socat`-relayed proxy on Linux and WSL2, nothing on native Windows. It confines `Bash` and its children, not MCP servers or Claude Code itself, decides on the client-supplied hostname without TLS inspection, and falls back to unsandboxed execution with a warning if its dependencies are missing. When a command fails under the sandbox the model may retry with `dangerouslyDisableSandbox`, which prompts you; that prompt is the moment to read what it is trying to do. `--dangerously-skip-permissions` belongs only inside a disposable container with no credentials, which is how the GitHub Action and the reference devcontainer run it.

### Cloud sessions as the middle ground

Claude Code on the web gives up local access to gain isolation you did not have to build: each session runs in an isolated Anthropic-managed VM, network access is limited to a trusted list by default and can be set to a custom allow-list or disabled, all GitHub traffic passes through a proxy that keeps your real token out of the VM, and the VM is reclaimed on inactivity. Two caveats remain: the Anthropic API itself is always reachable, so data can still leave by that route, and sessions share your usage limits with everything else on the account. For a repository that is already on GitHub and work that does not need local hardware, it is the safest default of the three.

### Compliance posture

Team and Enterprise plans add SSO, role-based access, admin toggles for Remote Control, artifacts, connectors and cloud environments, audit logs, OpenTelemetry usage metrics for Claude Code, and the Compliance API. Organizations that need data residency or contractual controls usually run Claude Code through Bedrock, Vertex or Foundry with the model in their own cloud account, accepting the loss of Anthropic-hosted features listed above. Check the current Trust Center for certifications rather than relying on this document.

Sources: [Security (Claude Code)](https://code.claude.com/docs/en/security), [Sandboxing](https://code.claude.com/docs/en/sandboxing), [Use Claude Code on the web](https://code.claude.com/docs/en/claude-code-on-the-web), [Anthropic consumer terms update, TechCrunch, Aug 28 2025](https://www.techcrunch.com/2025/08/28/anthropic-users-face-a-new-choice-opt-out-or-share-your-data-for-ai-training), [Share session output as artifacts](https://code.claude.com/docs/en/artifacts).

## Phase 3.3 The hybrid architecture: a standard operating procedure

Design and communicate where the renderer and the people are; plan, build and verify where the code, the toolchain and the enforcement are; hand off through things both sides can read: a committed spec, a pull request, a published page. The procedure below assumes one developer, one repository on GitHub, and a Pro or Max plan or a Team seat.

&#91;embedded content: hybrid feature workflow · 5 steps across two surfaces, 2 loops\]

Chat owns the first and last steps because they are visual and social; Claude Code owns the middle three because they touch the working tree. The two loops are where most time goes: review findings cycle inside Claude Code, and bugs or feedback from users re-enter at design.

### Step 0: one-time setup

- Repository: commit `CLAUDE.md` (build and test commands, conventions, architecture pointer), `.claude/settings.json` (permissions, hooks, sandbox), `.mcp.json` (the project database, Playwright, internal APIs). Install the Claude GitHub App for `@claude` on PRs and for cloud sessions.
- Chat: create a Project for the product area with instructions (stack, conventions, how to write a spec) and knowledge (architecture doc, ADRs, API contracts, the style guide). Connect the GitHub and Linear connectors.
- Account: check the training toggle on a consumer plan, or use a Team seat or API key for proprietary work (Phase 3.2).

### Step 1: design in Chat

1. Open the Project. Drop in the mockup, the screenshot of the current screen, or the whiteboard photo.
2. Produce the spec as a document artifact: user stories, acceptance criteria, API contract, non-goals, open questions. Keep iterating in the panel until the acceptance criteria are testable.
3. Ask for a Mermaid sequence or architecture diagram and a React prototype of the UI; adjust both visually.
4. Save the spec as `docs/specs/<feature>.md` and commit it, and add the final spec to the Project's knowledge so later chats are grounded on the decided version.

### Step 2: plan in Claude Code

```bash
cd repo && git switch -c feat/<feature>
claude --permission-mode plan
> Read docs/specs/<feature>.md. Explore the code it touches, then propose a plan:
> files to change, tests to add first, migration or API risks, and what you will
> not touch. Do not edit anything yet.
```

Approve the plan with `ExitPlanMode`, or revise it. A plan that names the wrong module is the cheapest bug you will ever catch.

### Step 3: build in Claude Code

1. Isolate: `claude --worktree <feature>` or let the session call `EnterWorktree`, so a parallel bug fix never collides with the feature checkout.
2. Test first: "Write the failing tests for acceptance criteria 1 to 4, commit them, then make them pass without changing the tests." The `PreToolUse` hook from Phase 2.2 makes the last clause mandatory.
3. Let hooks do the hygiene: formatter and linter on every edit, `Stop` hook that refuses to finish while `make check` fails.
4. Review before you look: `Agent` a code-review subagent with `Read`-only tools, or use the `/review` flow, and let `ReportFindings` render the list.
5. Commit in small units and open the PR: `gh pr create --fill`. For a long task, start it as a cloud session (`claude --cloud "<task>"`) or keep the local session reachable from your phone with `/remote-control`.

### Step 4: verify and ship

1. Mention `@claude` on the PR for an independent review from the GitHub Action, with repository access scoped to its token.
2. Address findings in the same session (`/teleport` pulls a cloud session back to your terminal) until CI is green.
3. Merge. For recurring checks after merge (nightly test runs, dependency audits), create a Routine with `/schedule`.

### Step 5: communicate in Chat

1. Give Chat the PR link through the GitHub connector, or paste the diff summary, and ask for release notes, a changelog entry, and a two-minute demo artifact that walks through the change.
2. Update the Project: replace the draft spec with the shipped version, add the decision record, and note anything the implementation changed.
3. When users report bugs with screenshots, triage them in Chat (vision plus the Project context) and either reopen the spec or go straight to Step 2.

### Headless glue

Automate the handoffs that recur. A GitHub Action that triages labelled issues into a plan comment, with a read-only tool set and a turn cap:

```bash
claude -p "Triage issue #$ISSUE: read it, locate the code involved, and write a plan comment with files, tests and risk." \
  --allowedTools "Read,Grep,Glob,Bash(gh issue view*)" \
  --max-turns 15 \
  --output-format json | jq -r '.result' | gh issue comment "$ISSUE" --body-file -
```

A spec-to-plan step that writes its output where Step 2 expects it:

```bash
claude -p "Read docs/specs/$FEATURE.md and write an implementation plan to docs/plans/$FEATURE.md" \
  --allowedTools "Read,Grep,Glob,Write(docs/plans/**)"
```

### What each surface must never be asked to do in this procedure

| Do not | Because |
| --- | --- |
| Paste a whole repository into Chat to "get context" | The 20-file cap and the lack of a working tree make the answer partial, and the paste is a data path you did not intend |
| Run `--dangerously-skip-permissions` on your workstation | It removes the only layer between a prompt-injected instruction and your credentials; use it in a disposable container only |
| Let Claude Code own the spec | The spec needs non-engineers, visual iteration and a Project; `CLAUDE.md` is for constraints the code must obey |
| Let Chat own the merge | Nothing in Chat can run the suite against the real environment or see the PR's CI |

## Sources and verification notes

Every product claim above was checked against Anthropic's documentation as published on October 3, 2026; version numbers (for example `v2.1.183` for artifacts, `v2.1.224` for cross-session messaging, `v2.1.51` for Remote Control) are quoted from those pages so a reader can tell whether their install has the feature. Claude Code ships several times a week, and the tool set, default permission mode, and plan entitlements have all changed within the last six months, so re-check the pages below before relying on a specific number.

| Topic | Page |
| --- | --- |
| Claude Code tool set and per-tool behavior (Bash limits, Read, Edit, Glob/Grep defaults, LSP, Monitor, Agent) | [Tools reference](https://code.claude.com/docs/en/tools-reference) |
| Permission rules, modes, working directories | [Permissions](https://code.claude.com/docs/en/permissions), [Identity and access management](https://code.claude.com/docs/en/iam) |
| MCP transports, scopes, tool search, output limits | [Connect Claude Code to tools via MCP](https://code.claude.com/docs/en/mcp), [MCP quickstart](https://code.claude.com/docs/pt/mcp-quickstart.md) |
| Artifacts from Claude Code: availability, CSP, connectors, comments, admin controls | [Share session output as artifacts](https://code.claude.com/docs/en/artifacts), [Artifacts in Claude Code (announcement)](https://claude.com/blog/artifacts-in-claude-code) |
| Cloud sessions, network levels, GitHub proxy, teleport | [Use Claude Code on the web](https://code.claude.com/docs/en/claude-code-on-the-web), [Remote Control](https://code.claude.com/docs/en/remote-control) |
| OS sandbox, security model | [Sandboxing](https://code.claude.com/docs/en/sandboxing), [Security](https://code.claude.com/docs/en/security) |
| Chat artifacts, AI-powered artifacts, publishing and billing of viewers | [What are artifacts](https://support.claude.com/en/articles/9487310-what-are-artifacts-and-how-do-i-use-them), [Publishing and sharing artifacts](https://support.claude.com/en/articles/9547008-discovering-publishing-customizing-and-sharing-artifacts) |
| Projects, retrieval mode, caching | [RAG for projects](https://support.claude.com/en/articles/11473015-retrieval-augmented-generation-rag-for-projects), [Usage limit best practices](https://support.claude.com/en/articles/9797557-usage-limit-best-practices) |
| Upload limits, PDF handling, image guidance | [Upload files to Claude](https://support.claude.com/en/articles/8241126-does-claude-ai-have-a-file-upload-limit) |
| Consumer training and retention policy (August 2025 change) | [TechCrunch, Aug 28 2025](https://www.techcrunch.com/2025/08/28/anthropic-users-face-a-new-choice-opt-out-or-share-your-data-for-ai-training) |

Three statements are inferences rather than documented facts and are marked as such in the text: the token cost of an image (derived from the published pixel-to-token ratio), the in-browser transpilation of React artifacts in Chat (observed behavior, not a documented mechanism), and the claim that a preview pane in the Code tab is a product decision rather than a constraint. The preview-runtime library list for Chat artifacts comes from the artifact environment itself rather than a public page and should be treated as current but unversioned.
