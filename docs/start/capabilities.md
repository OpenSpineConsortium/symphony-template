# What Symphony can do

This page lists everything a Symphony project can do today, what sets it apart, and worked examples you can hand to someone new. It is the owner's handout (2026-10-19), written from the code on the default branch. Each line links to the page or tool that does the work. A line marked "not built yet" or "waits on" says exactly what is missing.

## What is different about it

- **The repository is the project.** The instructions, the goal, the memory, the board and the rules live as files in one GitHub repository. Every Claude session reads them at start, whether it runs locally, in the cloud, in a claude.ai Project, as a routine or as a worker in GitHub Actions. Nothing lives in one person's chat history or one account ([how-this-repository-works](../memory/how-this-repository-works.md)).
- **Many workers coordinate through GitHub alone.** An issue is a task. The first push of `claude/<issue>` is the claim, and GitHub refuses a second push of the same name, so two workers never hold one issue. The board (STATE.md on the branch `board`) is the shared state, and a pull request is the handoff. Any number of people, sessions, routines and Actions workers, on any number of Claude accounts, work one repository without talking to each other ([PROTOCOL.md](../agents/PROTOCOL.md)).
- **No server of ours and no API bill.** Claude in CI runs on a subscription token from `claude setup-token`, never an API key. The board, the coordinator's releases and the metrics run in GitHub Actions on the repository's own token.
- **The rules are tested like code.** The claim protocol is one public Python library with no dependencies, symphony-protocol. It is vendored here, checked against its hashes, and validated by a harness that runs every interleaving of a few workers against an oracle written from the spec. Every repository's required check holds it.
- **Work and benchmark share one file.** An agent written for daily work is the same file coordbench and flowbench measure. The repository is a place to build software and a place to compare agent designs on that same work.
- **It reaches past the code.** Claude works on a university's computing cluster, on the owner's OneDrive and Word documents, and on licensed literature, each under its own owner's rules (below).

## Capabilities

### Coordinating work

| What | How | Where |
| --- | --- | --- |
| Claim, work in the open, finish | Claim branch, draft pull request, the required check, merge | [PROTOCOL.md](../agents/PROTOCOL.md), the claim skill |
| The board | Rewritten on every issue, push and pull request event; the Queue, Given to workers, Blockers, Overlaps | board.yml, `/board` |
| Workers of every kind | A person's sessions by GitHub login, routines and Actions workers as files under .github/symphony/workers/, added by the "Add a worker" form | [WORKERS.md](../agents/WORKERS.md), workers.yml |
| The coordinator | Releases idle claims and tells overlapping work in the board's own run; Claude in coordinator.yml plans an epic into tasks for registered workers | board.yml, coordinator.yml |
| Push guard | A hook refuses a push to the default branch, to another worker's claim, and every forced push but a lease on your own claim | tools/guard_push.py |
| Shared memory and research | One fact per file under docs/memory/, findings under docs/research/, both by pull request | [MEMORY.md](../memory/MEMORY.md), [research](../research/README.md) |
| Crowd mode | Volunteers each on their own Claude account; the project never holds anyone's credential | [crowdsourcing.md](../setup/crowdsourcing.md) |

### Running Claude autonomously

| What | How | Where |
| --- | --- | --- |
| @claude on an issue or pull request | claude.yml on the repository's subscription token | [claude-action.md](../setup/claude-action.md) |
| Workers in GitHub Actions | Registered workers take queued tasks on their own, each within the turns per run and the runs in a row its file sets | workers.yml |
| A pool of Claude accounts | Up to 32 token slots as organization secrets; tools/pool.py picks the slot with the most room in its five-hour and seven-day windows, steered per slot (model, effort, paused) | [the token pool](../memory/the-token-pool.md), pool.yml |
| Adding a token with no terminal | The control panel's Tokens page mints one on an Actions runner, and the token leaves it only sealed; one token per person, lent to the repositories they choose and revoked any time | token.yml, [claude-tokens.md](../setup/claude-tokens.md) |
| What the work cost | A Symphony-Usage line on each session's commits and a usage artifact per Actions run, summed by metrics.yml with alone-versus-parallel ratios | [field metrics](../memory/field-metrics.md) |
| Profiling a session | Context, tool calls, re-reads and time, as counts only | tools/profile.py |

### Agents and benchmarks

| What | How | Where |
| --- | --- | --- |
| Agents as files | Claude Code subagent files under .claude/agents/; reviewer, developer and tester ship with it | [AGENTS.md](../agents/AGENTS.md) |
| Importing your own agent | The Agents workflow imports an agent file by pull request, checked for its name, description and tools | agents.yml, tools/agents.py |
| Giving agents tokens | .github/symphony/accounts.json maps agents and workers to token slots by name | [agents](../memory/agents.md) |
| Benchmarking coordination | coordbench runs CooperBench's task pairs under each way of coordinating (solo, coop, team, sdlc and others) and scores them with CooperBench's own evaluation | [benchmark.md](benchmark.md) |
| Benchmarking an agent design | `coordbench --agent-file` and a flowbench stage's agent run the same file used in daily work; flowbench builds on SWE-bench's task repository | coordbench, flowbench |
| Leaderboard | Issues a token closes carry token:<id>, crediting the token and its owner | [the token pool](../memory/the-token-pool.md) |

Every benchmark run spends the account's usage, so none starts without the owner's word and a number.

### The control panel

The site's /symphony/control/ drives a repository as the signed-in person through GitHub's API: the board, tasks, @claude, workers, pull requests, workflow runs, tokens, the Share tab, Dependencies, Folders and the Explorer, Explore, Notebooks, and the Ask Claude bar, which answers read only and offers the panel actions its answer names as buttons ([the control panel](../memory/the-control-panel.md)). Sign in with GitHub goes through a stateless Worker. Each feature ships only after the Apps' privacy statement describing it is live.

### Getting a project started

| What | How | Where |
| --- | --- | --- |
| One press | Install the App, press Create on the form, and the run opens the adoption pull request and merges it | [the front door](../memory/the-front-door-is-one-press.md) |
| Settings applied for you | Symphony Setup applies the repository's settings and pins the required check in the same run; every setting is on one tracked list in symphony-start | scripts/setup-repo.sh, symphony-start |
| From Claude Code | `/symphony:new` makes the repository, installs both Apps and opens a cloud session | [claude-code.md](claude-code.md) |
| An existing repository | The protocol alone, or the plugin, added to code you already have | [existing-repo.md](existing-repo.md) |

### Wayne State's grid

.github/workflows/grid.yml runs one command on a WSU compute node through a runner chain that hpcworker serves as Slurm jobs. The output comes back as the job's log and an artifact. grid-gate.yml starts, reads or stops the chain over an ssh key whose forced command takes only those three words. No Claude token goes to the grid ([grid.md](../setup/grid.md), [the grid](../memory/the-grid-runs-a-job-through-beethoven.md)).

### OneDrive, notebooks and Word

| What | How | Where |
| --- | --- | --- |
| Native OneDrive access | Wayne State approved the SymphonyBoard Folders app on 2026-10-19, so the panel's Folders tab and the drive organizer read a WSU OneDrive directly through Microsoft Graph under the owner's own Microsoft sign-in, which the owner confirmed live on 2026-10-20; the connector walk is retired | [drive organizer](../memory/drive-organizer.md), [OneDrive on Graph](../research/onedrive-direct-graph.md) |
| Organizing a drive | The whole drive read into a catalog, sorted into proposed projects, each a possible repository; files move only on the owner's own go, and every move can be undone | the drive-organize skill |
| Notebooks | A group of drive files held together, as NotebookLM does, in a private repository that points at them by id and never moves them, with research, drafts and references | the notebook skill, tools/notebook.py |
| Revising Word documents | Revisions written as tracked changes in a copy beside the file, never over a file the owner changed; several reviewers each as their own author | tools/docx_review.py, the lens-review skill |
| Citations in Word | Citations inserted as tracked changes, either as Word's own citations with the document's source list, where Insert Bibliography or Update Field builds the reference list (tested in Word desktop, 2026-10-19), or as Zotero fields naming each item in the owner's library | tools/docx_cite.py |
| References from a citation manager | BibTeX or RIS from Mendeley, EndNote or Zotero, or Zotero's web API with each item's library link, read into references.json | `tools/notebook.py refs` |
| Syncing both ways | A connected Google Drive or OneDrive synced through drive-sync.yml | [drive-sync](../research/drive-sync.md) |

The Mendeley app, a Mendeley sign-in in the panel, is planned and not built yet ([mendeley-sign-in](../research/mendeley-sign-in.md)). Zotero's Refresh in Word is not tested yet.

### Licensed literature (Elsevier)

The institution's Elsevier access (ScienceDirect and Scopus, with an API key and an institution token) may be read by Claude for academic work, as the university's library and Elsevier itself confirmed on 2026-10-19, on two conditions: the token and the text are never made public, and no model is ever trained on them. The key and the token are kept as secrets the owner sets, an Actions secret for private repositories or a cloud environment's variable, and are used only in private places, never in a public repository, a log, a URL or browser code. The template has no Elsevier client of its own yet: a session reads with the secrets where the work needs them ([notebooks research](../research/notebooks.md)).

## Worked examples

1. **A lab with several students.** The PI makes a repository with one press. Each student works under their own Claude account and GitHub login. They take issues from the board, and none of them ever overwrites another's work, because a claim is a branch GitHub will not let anyone push twice. The coordinator plans an epic into tasks for them, and the board tells two students when their pull requests touch the same file.
2. **Work overnight.** The owner queues tasks labelled todo before bed. Registered workers in Actions take them on the repository's token pool, open pull requests and pass the required check. Each stops at the runs its file allows. In the morning the board shows what landed and what waits.
3. **A paper with references you can trace.** The owner's draft sits on OneDrive. A notebook repository points at it and its data. Claude researches in the notebook and drafts revisions. It writes each citation into a copy of the document as a tracked change, from references exported from Mendeley or Zotero, and Word builds the reference list itself. The owner accepts or rejects each change in Word.
4. **A job on the cluster.** A task needs a GPU. grid.yml sends the command to a WSU compute node as a Slurm job, and the log and outputs come back to the pull request's run, with no credential of Claude's on the cluster.
5. **Compare agent designs.** A team writes a reviewer agent, imports it by pull request, and uses it on every pull request. With the owner's word, the same file then runs in coordbench or flowbench against the default agent on the same tasks. The result is a measured comparison of the design, not an impression.
6. **Sort a drive into projects.** Claude reads a whole OneDrive into a catalog, reads a sample of the files, and proposes projects, each with tasks and a possible repository. Nothing moves until the owner reads the list of moves and says go, and every move can be undone.

## What it never does

It never pushes to the default branch, never holds an API key for Claude, and never puts anyone's credential in a file. It never moves or overwrites the owner's files without their word. It never makes licensed text public, and it never starts a paid run without the owner's word.
