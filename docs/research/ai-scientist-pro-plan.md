# AI Scientist Pro: signed-in literature, lessons from long runs, and the key rule

Source: the thread "Plan AI Scientist Pro integration" (first named "Explore textbook RAG in control panel"), 2026-10-25, and the Claude Doc written in it, "AI Scientist integration plan" (https://claude.ai/artifact/AzcxFaDBdXVDkKDSZWjBv5), which also holds the roadmap drawing and the column where the owner picks each decision. The pages read are listed at the end.

On 2026-10-25 the owner asked three things: whether the PubMed connector reaches Scopus and ScienceDirect; for one sign-in, once, to every literature source; and for a plan to bring in "AI Scientist Pro" with authenticated access and the lessons of six Anthropic research posts, an X article and a Reddit post built in, with a start on relaxing the rule against API keys. AI Scientist Pro is the owner's own name for their build: Sakana's AI Scientist on the Console credits, through the one key the owner allowed that day (textbook-search-graph-in-the-panel.md), with those lessons. No product of that name exists. While this was being written, the owner also set what AI Scientist Pro writes (below).

## The PubMed connector does not reach Elsevier

It searches NCBI's PubMed and nothing of Elsevier's, and it has no sign-in, so it cannot carry the institution's access. Its seven tools in Claude's connector directory are search_articles, get_article_metadata, find_related_articles, lookup_article_by_citation, convert_article_ids, get_full_text_article and get_copyright_status.

- It gives the citations and abstracts PubMed indexes for Elsevier's journals.
- It gives full text only where PubMed Central holds a free copy. The directory names the tool but not its source, so this is inferred.
- It cannot give Scopus's cross-publisher citations and author profiles, the engineering and computing venues PubMed leaves out, or ScienceDirect's subscription full text.

The directory has no Elsevier, Scopus or ScienceDirect connector. Those need the owner's Elsevier key with the institutional token, cleared for private use by the library and Elsevier on 2026-10-19 (notebooks.md).

## One sign-in, once

Most of it is native. A connector added once at claude.ai/customize/connectors reaches every Claude session on that account, and Claude Code keeps a server's sign-in once `claude mcp login` has made it. The one piece to build is a small server for Elsevier.

| Where the work runs | How the sources arrive | The owner's one-time step |
| --- | --- | --- |
| Claude sessions: project threads, cloud sessions, Claude Code, the desktop app | claude.ai connectors, which Claude Code fetches under a claude.ai login or is handed in a cloud session | Connect each once per account: PubMed and bioRxiv take a click; Scite, Consensus, Wiley Scholar Gateway and alphaXiv a click and a sign-in |
| The research loop in GitHub Actions | No connectors: its token from `claude setup-token` "can only make model requests", so Claude Code loads none | None; it can name the sign-in-free PubMed and bioRxiv servers by URL in its own MCP settings |
| AI Scientist Pro: Claude Code on the Console key, on a grid node | Servers added to that Claude Code directly, since with ANTHROPIC_API_KEY set it loads no claude.ai connectors; Claude Code stores each sign-in and refreshes it | The setup command, once |

The setup command, grid/literature-setup.sh in SchwingNet, runs once in the owner's terminal on the grid, over `ssh -t`:

1. It adds PubMed and bioRxiv by URL with `claude mcp add`. They need no sign-in.
2. It adds Scite, Consensus, Wiley Scholar Gateway and alphaXiv, then runs `claude mcp login` for each. With no browser on the grid, Claude Code prints the sign-in link; the owner opens it on their own computer, signs in and pastes the address the browser lands on back into the prompt.
3. It asks for the Console key at a hidden prompt and writes it to a file only the owner can read, outside every repository. AI Scientist Pro's launcher sets it in its own process alone.
4. It adds the Elsevier server, tools/elsevier_mcp.py, written with the standard library alone: Scopus search and ScienceDirect full text by DOI. The server reads the key and token from their private file, never from its command line, which other users of a shared node can see, or from Claude Code's settings. It sends them only to api.elsevier.com, in headers.
5. It lists each server's state, so a failed sign-in shows at once.

The credential table in desktop-app-and-llm-agnostic.md names a grid worker's sign-in as the one credential that sits in a plain file; the Console key and the Elsevier values are two more on the grid, each a file of mode 600 in the owner's grid home, and that table gains their rows when phase 1 makes them.

Four facts from Claude Code's MCP page set this shape. A `claude -p` run has no /mcp panel and cannot run the OAuth flow, so each sign-in is made once interactively and the runs reuse it. `claude mcp login` prints the link where no browser is available, as over SSH. Claude Code reads its own credentials, ANTHROPIC_API_KEY among them, as empty in a remote server's url and headers, and strips credential-like variables from the helpers a repository supplies, advising such a script to read its credential from a file, which the Elsevier server does from the start. And a run without a terminal loads a repository's own `.mcp.json` servers without asking, so AI Scientist Pro's runs start with `--strict-mcp-config`, naming only the servers this plan allows.

A server that accepts only claude.ai's own sign-in address stays a claude.ai-only connector, and the command names it. A Managed Agents vault would hold the same sign-ins for runs on Anthropic's servers, but the experiments stay on the grid, so it is not needed.

## What AI Scientist Pro is built on

The proposed base is Sakana's newest, The Agentic Scientist (arXiv 2610.18933, 13 October 2026; code in SakanaAI/AI-Scientist-v3). It drives a coding-agent harness (Codex, Claude Code, OpenCode or Pi) over a frontier model: parallel workers, each with an ideation agent and an execution agent, then ablation, analysis and writing agents, with an evidence map and a check for unsupported numbers. People set the question, the constraints, the baseline and the rubric, or an agent drafts them for review. It reports reward hacking seen and rubrics tightened, calls reviewer scores a proxy and not evidence, and covers machine learning tasks only.

The AI Scientist v2 (Nature, 26 March 2026) picks its own question from a code template or a topic, runs a tree search over experiments, writes a LaTeX paper judged by an automated reviewer, calls several providers' APIs directly and searches Semantic Scholar for novelty and citations. Its stated limits are inaccurate citations, ideas implemented wrongly and computational experiments only.

v3 is preferred because it works through Claude Code, so the sign-ins above and Claude Code's hooks apply to it as to any session; v2's direct model calls would bypass both. v3's code was not read in this thread: how it calls Claude Code, what it sandboxes and where it searches the literature is the first thing phase 0 checks.

Where it runs:

- On a grid compute node, as Claude Code on the Console key, so the data never leaves the grid; the node reaches the internet over HTTPS.
- Each campaign is one SchwingNet issue, one branch and one pull request under the claim protocol. Its experiments are grid jobs, each under the owner's word and count, with the size rule on every fetch.
- Its papers stay drafts inside SchwingNet until the provisional is filed, and nothing it writes is submitted.

## The lessons, as checks

The articles agree that long runs fail through premature claims and lost state, not through a lack of intelligence, and Schwartz found in Vibe physics that honesty rules in CLAUDE.md helped only "a little". So AI Scientist Pro rests on checks and files, not on prompts.

| Lesson | Seen in | What AI Scientist Pro does |
| --- | --- | --- |
| Agents call work done or verified too early. | Harnesses; Vibe physics; Claude-shaped science | "Done" is a fixed list of checks, written before a campaign starts, that the agent cannot edit. A claim counts only when a separate checker finds its recorded run. |
| Under pressure they fit the result: tuned plots, reward hacking, the answer the person seemed to want. | Vibe physics; The Agentic Scientist | The evaluation code, the split and the witness frames are outside what it may change. Only the evaluator scores the held-out test, and prompts never name a hoped-for number. |
| A foundational error survives many rounds of self-review. | Vibe physics | A reviewer in a fresh context re-derives each keystone step, as Claude re-proved the zeta result from scratch, and the owner checks the keystone. |
| Ground truth comes from a checker, and from checking the right statement. | Riemann zeta; Fermat | The checker is the recorded evaluation with its intervals. Before any run, a comparison confirms that the split, the metric and the code digest match the registered plan. |
| Memory lives outside the context: progress files, a map of the work, hand-offs. | Harnesses; Fermat; The Agentic Scientist; Claude-shaped science | Each campaign keeps a progress file and a map of its claims in its branch. Every session reads them first, updates them last and commits after each step. |
| One small piece at a time, with a smoke check first. | Harnesses | One hypothesis per cycle; each session runs the block smoke test and reads the progress file before new work. |
| Fixed tools beat an agent's own retrieval and counting. | Agents in biology | Literature and data come through fixed tools: the Elsevier server, PubMed's tools and the data catalog. Every query is logged for re-running, and counts come from the catalog. |
| Check novelty before claiming. | Riemann zeta, 54 papers read first | It searches Scopus and PubMed before a campaign starts and again before writing, citing each paper by DOI. |
| People own the direction, the taste and the last word. | Vibe physics; Claude-shaped science; Fermat; The Agentic Scientist | The owner sets each campaign's question, baseline and rubric and approves its grid jobs. Nothing leaves a draft without the owner. |
| Agents grind, misjudge time, and scale alone fails. | Claude-shaped science; Riemann zeta, 650 failed ideas; Fermat, 6 billion tokens | Each campaign has a fixed budget in cycles, credits and grid hours, and stops after a set number of cycles without progress. |
| Results vary from run to run. | Agents in biology | Decisive comparisons repeat with fresh seeds and report intervals, as the project's results already do. |
| Mark AI-written work. | Sakana | Every draft records in its front matter that AI Scientist Pro wrote it. |

The X article and the Reddit post could not be read: X refuses fetches and Reddit is blocked from the cloud session. Nothing here comes from them; their text, pasted by the owner, would add their lessons.

## What AI Scientist Pro writes

The owner's brief of 2026-10-25, sent while this plan was being written: the textbook site is good but "too verbose and exposes the underlying raw artefacts via links too much", and AI Scientist Pro, "and perhaps any future sessions", should hide the underlying artifacts, embed their figures, relevant text and references, and present "a polished, edited, abridged version which follows a theme". The paper tells the story of an idea: its relation to prior art, its methods, its results against benchmarks, its conclusion and the vision of where the work goes next. It is "packed to the brim with reference", shows most of its information in the discipline's conventional figures, and argues "as definitive, absolute, and revelatory as possible", persuasively but "based on unbiased experimental methods and data". A minute later the owner added that none of the textbook's construction is to be disregarded: its artifacts are, or are to be, tied to specific experiments with CLAIM-compliant ledgers, so that a result can be reproduced in one click once the research loop is packaged and importable.

So AI Scientist Pro works over two layers:

| Layer | What it holds | What readers see |
| --- | --- | --- |
| The raw layer, kept whole | The textbook, its artifacts and figure records, and every run's ledger row, CLAIM 2024 and REFORMS report and provenance (SchwingNet's tools/flow.py and tools/report.py) | Nothing directly: AI Scientist Pro queries it through an embedding index on the grid |
| The paper | One theme told as a story: the idea, prior art, methods, results against benchmarks, conclusion, what it changes and what comes next | The paper alone, with its figures, the relevant text and dense references embedded, never linked out |

How it stays honest while it argues:

- The writer is the idea's advocate, and the evidence stays neutral: the methods, the split and the metric are fixed in the registered plan before any result exists.
- Every number comes from a recorded run, and a number meant for publication from a run whose report passes the publication gate, `tools/report.py check --complete`.
- A sentence the evidence does not carry is cut, not hedged, which is what lets the prose stay definitive.
- Every experiment goes through the same flow as any other run, so each leaves its ledger row and report.

Each figure in the paper carries its run's id in place of a link. Once the research loop is packaged and importable, which SchwingNet #293 begins with the block framework, one click re-runs the run behind any figure; until then a figure record's Re-run issue does it through figure.yml. On 2026-10-25, 33 of the textbook's 99 figure records named the job, script or run behind them, 23 carried a re-run command, and one, the experiments panel of chapter 35, read the flow's ledger, which held two runs, both dry runs on a synthetic bank. Phase 2's check lists the rest so each can be tied to its experiment; until it is, the paper cites it as text and never as a result.

The Console credits cannot buy the textbook's embedding, since Anthropic offers no embedding model (textbook-search-graph-in-the-panel.md). The recommendation is an open embedding model on the grid, which needs no key and keeps the book there, over Voyage, which bills through MongoDB and would send the book out before the filing.

## The plan

Five phases, each ending at a decision of the owner's. Everything for AI Scientist Pro lands in SchwingNet by pull request, since it touches the research loop.

0. Read and pin, with no tokens spent: read v3's code, pin one commit and map each stage to the claim protocol and the size rule; find how it calls Claude Code, what it sandboxes and where it searches; write the plan into a SchwingNet issue (credentials, containment, confidentiality, the measure). Gate: the owner approves the plan on the issue.
1. Sign-in, once: the Console key in a private file on the grid, set only in AI Scientist Pro's process; the setup command, the Elsevier server and the key gate's Elsevier names, tested on faked answers. Checked by one test query per server, and by a secret scan that finds nothing in git or logs. Gate: the owner runs the setup command once.
2. The lessons as checks: per campaign a locked rubric, a progress file, a claims map and a budget, kept in its branch; a hook that refuses edits to the evaluation, the split and the rubric; a comparison against the registered plan; a fresh-context reviewer that accepts a claim only with its recorded run; and the paper's checks: each figure names its run, each number its ledger row and each reference its DOI, and the reader's version holds no link to a raw artifact. Checked by SchwingNet's CI. Gate: the owner's word, a credit limit and one CPU grid job, for the first spend.
3. A dry campaign on a toy task: three cycles on the CPU smoke data in one CPU grid job, which first builds the textbook's embedding index and ends in one short paper written as above, measuring credits per cycle against the budget. The embedding model's download is a fetch under the size rule. Checked by a planted edit to the evaluation, which the hook must refuse, and a planted false claim, which the reviewer must reject. Gate: the owner's word and the count of grid jobs.
4. Beside the research loop: campaigns on the same ranked claims as research.yml, each one issue, one branch and one pull request, compared with the loop by the recorded evaluation and never by the scores of its own reviewer.
5. The owner's decision: keep, change or drop it, by the measured difference.

Before the third decision the only work is reading code and writing tests. Phase 3's one CPU job of three cycles is the first use of the credits and of the grid.

## Relaxing the rule against API keys

The rule was already relaxed twice: for Elsevier and citation-manager keys on 2026-10-19, and for one Console key for AI Scientist on 2026-10-25. Its old wording still stands in four places, and four checks enforce parts of it.

| Where | What it says or does | Proposed |
| --- | --- | --- |
| The Project's instructions | "No API key or Claude credential anywhere." | The owner replaces it with the wording below |
| symphony-template CLAUDE.md | "no API billing", and coordbench "never with ANTHROPIC_API_KEY" | Reworded by pull request after the owner's OK |
| SchwingNet CLAUDE.md and docs/project.md | "usage credits are never used" | Say it means a subscription's extra usage, so no session reads it as the Console credits |
| SchwingNet's research loop prompt, .github/symphony/research.md | "No API key and no new credential" | Kept: the loop stays on the subscription |
| scripts/tokens.py | Refuses an API key on sight | Kept: it stores subscription tokens only |
| tools/metrics.py | Its judge refuses to run while ANTHROPIC_API_KEY is set | Kept: it guards the subscription's billing |
| tools/crowd_check.py | A crowd repository may hold no ANTHROPIC_API_KEY | Kept: contributors' credentials are never held |
| tools/check_docs.py | Fails on the shape of an Anthropic key | Kept: no key in git |

The template's own pages, such as README.md's "No API key anywhere.", docs/setup/claude-action.md and the start pages, describe Symphony itself, which still needs no key, and this folder's README describes how its measurements run; they stay as they are. SchwingNet's docs/setup/claude-action.md already reads usage credits as the subscription's overage ("Keep usage credits off on the main account unless overage billed at API rates is wanted"), the reading the clarification makes explicit.

The proposed wording, for the Project's instructions and both CLAUDE.md files:

> An API key is allowed only where a subscription cannot do the job: one key per purpose, listed in docs/setup/keys.md with its owner, cap and location. GitHub Actions reaches the Claude API only through Workload Identity Federation, which stores no key. A key lives in a private file on the machine that uses it, never in git, an issue, a log, a URL or browser code. Claude Code sessions, the research loop and `@claude` stay on the subscription, and contributors' credentials are never held.

The safeguards behind it:

- Keyless first. For GitHub Actions, Anthropic's Workload Identity Federation trades the workflow's own GitHub identity token for a short-lived one, bound by a rule to one repository and branch.
- A cap on every key. Each key gets its own Console workspace, with a spend limit no higher than the monthly credits.
- No silent switch. Claude Code prefers ANTHROPIC_API_KEY over the subscription and then loads no connectors, so the key is set only inside AI Scientist Pro's own process, never in a shell profile.
- Rotation. The key is a service-account key made with a 90-day expiry, which Anthropic warns of a week ahead, and it is disabled at once after a suspected leak. The secret scans already look for the key's shape, and the grid readout masks long strings.

The order: the owner approves the wording and edits the Project's instructions; then one pull request in each repository changes the CLAUDE.md lines and adds docs/setup/keys.md. The checks stay as they are.

## Decisions waiting for the owner

Six, each with a recommendation; the owner picks in the doc's last column or answers in the thread.

1. The base: The Agentic Scientist (v3), with v2 only as the fallback if phase 0 finds v3 cannot run on the grid.
2. What a search may send out before the filing, since a query's words reach the service: Scopus, ScienceDirect by DOI and PubMed only, with a Claude Code hook refusing any query that holds a word from a list the owner keeps in a private file on the grid. The other services are signed in but denied until the filing, and web search, web fetch and any search v3 makes outside Claude Code stay off.
3. Where the keys live: the Console key typed once at the setup command's hidden prompt, so it never passes through GitHub, which keeps the owner's rule of 2026-10-25 (never in git, CI or logs). The Elsevier key and token take the owner's key route of 2026-10-23 (service-keys-to-the-grid.md), which needs the key gate to learn their two names.
4. The new key wording above, adopted as written.
5. The credit cap for phase 3: 25 dollars, a tenth of a month's credits, set as the workspace's spend limit. It is a starting figure, not a measured one; phase 3 measures what a cycle costs.
6. How the textbook is embedded: an open embedding model on the grid, with no key, since the Console credits cannot buy one and Voyage would send the book out before the filing.

## Sources

Opened on 2026-10-25:

- Anthropic research: Effective harnesses for long-running agents (26 November 2025), https://www.anthropic.com/research/effective-harnesses-for-long-running-agents; Vibe physics: The AI grad student (23 March 2026), https://www.anthropic.com/research/vibe-physics; Paving the way for agents in biology (8 June 2026), https://www.anthropic.com/research/agents-in-biology; the Riemann zeta result (10 August 2026), https://www.anthropic.com/research/riemann-zeta; Formalizing Fermat's Last Theorem (4 September 2026), https://www.anthropic.com/research/formalizing-fermats-last-theorem; Claude-shaped science (1 October 2026), https://www.anthropic.com/research/claude-shaped-science; and the Science team's index, https://www.anthropic.com/research?team=science.
- Sakana: https://sakana.ai/ai-scientist-nature/, https://arxiv.org/html/2606.15497v1, https://pub.sakana.ai/agentic-scientist/ and https://arxiv.org/abs/2610.18933.
- Claude's documentation: https://code.claude.com/docs/en/mcp, https://platform.claude.com/docs/en/managed-agents/vaults, https://platform.claude.com/docs/en/managed-agents/mcp-connector and https://platform.claude.com/docs/en/manage-claude/authentication.
- Claude's connector directory, searched for literature connectors.
- This folder: handoff-2026-10-25.md (section 9), notebooks.md, service-keys-to-the-grid.md and textbook-search-graph-in-the-panel.md.
- SchwingNet's records: the textbook's figure records under docs/textbook/figures/ (counted on 2026-10-25), tools/report.py and its note docs/research/run-report.md, the flow's ledger docs/research/v1-demo/LEDGER.md, and issue #293.
- Not read: https://x.com/omarsar0/article/2065880971031834786 (X refuses fetches) and https://www.reddit.com/r/ClaudeCode/comments/1tmm4sd/how_i_ran_a_9hour_autonomous_goal_session_with/ (blocked from the cloud session).
