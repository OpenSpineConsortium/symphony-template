# Symphony beyond cooperation: what one agent spends, and how to spend less

The owner's ask of 2026-10-15 23:35 UTC (item 5 of the message that resumed the project from the 2026-10-15b handoff): a more general use of the Symphony protocol for LLM usage optimization beyond cooperation, "including but not limited to context compression, profiling, decreased tool usage, decreased code reading through hashing/RAG, etc all in a reproducible way with autonomous research continuously", with two pointers, kitaisreal/agentprof and a dev.to article that profiled Claude Code with strace.

This page is that programme: its questions, the instrument that measures them, the first measurement, the loop that keeps measuring, and what each step costs. Where the ask forked, these defaults were taken and are said here: a plan with a first reproducible measurement rather than a plan alone; the programme lives in this repository, under docs/research/, with its instrument under tools/ beside the usage trailer it extends; benchmarks on other people's tasks (SWE-bench and the like, the owner's item 6) are the business of repositories like coordbench and are only pointed to from here; and no run that spends tokens starts without the owner's word and the number.

## 1. Why this is Symphony's to do

Symphony's one idea is that coordination state lives in the work itself, in GitHub objects, and is read by code (docs/agents/PROTOCOL.md; the taxonomy spec, docs/checkpoints/2026-10-15b/taxonomy/spec.md, section 3). The same idea applied to cost already exists here: what each session spends rides on its commits as the Symphony-Usage trailer, each Claude run in Actions leaves a symphony-usage-* artifact, and the field metrics add them up per pull request and compare work done alone with work done in parallel (tools/usage.py, tools/economics.py, docs/setup/metrics.md, Economics). Coordination is the first thing Symphony optimized, and the ratios in METRICS.json's coordination block are its measure.

Everything else an agent spends can be measured the same way, from the same records, with the same discipline, and that is the programme:

- The records. A Claude Code session leaves a transcript, one JSON object a line, with the API's own token counts on every call and every tool call with its answer; a run in Actions leaves the Agent SDK's execution file with the same messages. tools/usage.py reads them for the trailer. Nothing more has to be installed or hooked, and nothing is sent anywhere.
- The discipline, from OpenSpineConsortium/coordbench: keep the task, the agent and the scoring fixed and make the thing under study a plug-in, an arm; pre-register the question and the analysis before a run (its bench/cooperbench/PLAN.md); say for every measure whether it is taken as the reference work takes it, equivalently, differently for a reason, or not yet (its PARITY.md); write an audit record per run and leave spoiled runs out of every figure (its audit.json, coordbench#21); have a model judge only when the owner runs it.
- The protocol. A research question is an issue; an epic is planned into tasks by the coordinator; a task is an arm run by a worker, which pushes its results and opens a pull request; the required check runs the tests that hold every measure to its definition; the board shows what is running. The research loop is Symphony's own way of working, applied to measuring itself.

## 2. The questions

Each domain the owner named has a measure a transcript already contains, an arm that would change it, and an outcome that must be read beside it: fewer tokens is trivially reached by doing nothing, so every cost measure is reported with whether the work landed (the pull request merged, its required check green, no reverts; or, on a benchmark, the task's tests passed).

| Domain | The measures (tools/profile.py) | Baseline | Arms to measure | Better means |
| --- | --- | --- | --- | --- |
| Profiling | Tokens by kind and model; the context sent on each API call, its first, peak, mean and last; the share served from the prompt cache; calls, failures, bytes in and out, seconds and the tokens brought in, per tool; seconds in tools, waiting for the model and thinking | This page's section 4 | None by itself: it is the instrument the other rows use. One arm of its own: the harness's file I/O under strace (section 6) | A reader can say where a session's tokens, time and context went |
| Context compression | First context, peak, mean, cached share, compactions and drops, growth from tool results | The same | Claude Code's automatic compaction as it is; /compact at milestones; reading through helpers whose transcripts stay out of the main context; results trimmed at the source (head, grep, sed ranges in place of cat); shorter instructions at session start | Lower peak and mean, higher cached share, at the same outcome |
| Decreased tool usage | Calls per tool, failed and unanswered calls, shell commands by use (read, search, list, git, run) | The same | Rules that batch independent calls and join commands; permission allowlists, so fewer calls wait on a prompt; skills that bundle a procedure (the claim skill); a tool that answers in one call what took several | Fewer calls and failures per landed pull request |
| Decreased code reading through hashing and retrieval | Reads, files named and distinct, re-reads and the bytes they returned, partial reads | The same | An index at session start (each file's size, hash and outline) so a session reads only what it does not know and re-reads only what changed; a search-first rule; a retrieval tool that returns the span that matters rather than the file; a code map in CLAUDE.md | Fewer bytes read and re-read per landed pull request, at the same outcome |

The arms are hypotheses, not recommendations: the attached package-search report (the owner's item 6) recommends retrieval for rules and context compaction on general grounds, and here each is measured before it is adopted. The questions extend the taxonomy spec's section 11, whose R3 (what one coordination step costs) and R7 (what free minutes are worth) are the two cost questions already open there.

## 3. The instrument: tools/profile.py

`python3 tools/profile.py TRANSCRIPT [--json FILE] [--paths N]` reads one session's transcript and its helpers' (the subagents' transcripts beside it, as tools/usage.py reads them) and prints a report; --json writes the record. tests/test_profile.py holds every count to its definition on a transcript the test writes, so a change to a definition fails a test before it changes a figure.

What it counts, and how:

- Each API call once, by its message id, since a message written as several lines, one per block, carries the same usage on each. The context of a call is its uncached input plus its cache writes plus its cache reads; the cached share is the cache reads over the contexts summed.
- Each tool call once, by its block id, matched to its answer by that id: the answer's size is the text the model saw, an error is what the harness marked, the seconds in the tool run from the line that asked to the line that answered.
- The growth of the context from one call to the next, less the call's own output, is what the calls between them brought in; it is shared among that call's answered tools by the size of their answers. This is an estimate, and its keys say so.
- A read is a call of the Read tool or a shell command of cat, head, tail, sed, less, more or nl naming a file; the paths are resolved against the line's working directory, following a cd inside the command, and a pattern or a variable names nothing. A re-read is a file named by a read after an earlier read of it in the same transcript. A here-document's body is data, not commands.
- A compaction is the harness's own boundary line or the summary it starts the continued conversation with; a drop is a fall of the context by more than half between two calls, however it came about.
- Seconds waiting for the model run from the last line before a call to the call's last line, which holds its thinking and its answer; the harness's own count of the thinking is beside it.

What it does not see, so that its figures are read right: a file read by git show, python or any program not in the list; what a helper read counts as a read of its own, in its own context; an image answers as nothing; and the growth attribution cannot tell a tool's answer from a system reminder that arrived with it.

The record carries counts, bytes, seconds, tokens, tool names and model names and never a path, a command, a prompt or a line of the conversation (tests/test_profile.py checks that the fixture's paths, commands and words are absent from it), so a record can be committed here; --paths prints the files read most often on the screen only.

How it compares with the pointers:

- agentprof (kitaisreal/agentprof, Rust) registers PreToolUse and PostToolUse hooks that log every tool call, and reports per-call latency, estimated tokens per tool and the slowest calls, live. profile.py reads the transcript afterwards, so it needs no install, works on a cloud session's and an Actions run's records, and has the API's own token counts rather than estimates; it has no live view.
- The strace article (dev.to, vmitro, early 2026; unreachable from this environment, read through the author's issue anthropics/claude-code#19459 of 2026-01-20, closed as not planned without a maintainer reply) profiled the harness, not the agent: on Claude Code 2.1.x under WSL2 it saw .credentials.json opened 339 times in 181 seconds, the changelog read 683 times in 38 seconds (5.45 MB) and the debug log re-read whole about every 2 seconds. That is a third thing to measure, below the agent's behaviour, and section 6 keeps it as its own arm.
- ccusage and claude-tokens read the same transcripts for billing; claude-tokens' authors say ccusage over-counts by 30 to 70 percent because the same message appears in several files after a resume or a subagent run (a vendor claim, not checked here). profile.py counts each message once by its id, as usage.py does.

## 4. The first measurement

The transcript of the thread that wrote this page was profiled while it worked, on 2026-10-15; the record is [baseline-2026-10-15.json](baseline-2026-10-15.json) and the report [baseline-2026-10-15.md](baseline-2026-10-15.md). It is a baseline of this project's own way of working, a cloud session on a repository whose instructions and memory load at the start of every session, and it is read with that in mind.

One number is fixed by construction and worth stating here: the first API call of that session sent 120,867 tokens before any work, the project's instructions (CLAUDE.md and what it imports), the memory index, the thread's relay and the harness's own context. Every session of this project starts there, and every call after it carries it, served from the cache at a quarter of the input price (tools/economics.py, PRICES). The experiment thread found the same shape on coordbench's route, where every bench agent re-reads an inherited prompt of about 80,000 tokens (docs/checkpoints/2026-10-15b/handoff.md, section 2.3). What a session starts with is the first thing the context-compression arms change, and the first thing to measure across the project's sessions.

To reproduce: a transcript is at ~/.claude/projects/<folder named for the working directory>/<session id>.jsonl on the machine the session ran on, a cloud session's in its container only; `python3 tools/profile.py <that file> --json out.json` gives the same record for the same file.

## 5. The loop: measuring continuously, under the protocol

Each step is its own pull request, reviewed and checked, in this order. None spends a token until step 5.

1. The profile beside the usage. The hook that reads the transcript before each commit (tools/usage.py hook) writes a second trailer, Symphony-Profile, with the session's counts since its last commit: calls, failed, reads, re-reads, bytes read, context peak, compactions, seconds in tools. Then every session of every adopted repository measures itself at no cost, the record rides with the commit as the usage does, and a cloud session's container may die without losing it. A run in Actions gets the same block in its symphony-usage-* artifact from the execution file.
2. The aggregation. tools/metrics.py sums the profile trailers per pull request and by work setting, and gives the coordination block's siblings: reads, re-reads and calls per merged pull request, and the context peak, alone against parallel. The keys stay in the repository's own records until the Apps' privacy statement lists them (its version 5 is the exhaustive list of what the collector keeps, and a new shared key is listed there, with its site page live, before the collector keeps it); then they join METRICS.json.
3. The report. A deterministic page under this folder, regenerated by a tool from the records, with one table per question of section 2 and the baseline's row first, so a reader sees each arm against the baseline with the outcome beside the cost.
4. The arms as tasks. Each question of section 2 is an issue labelled epic; the coordinator plans it into tasks, one per arm, with the files each owns, and gives them to a registered worker (docs/agents/PROTOCOL.md, Planning). A task is: run the arm on the fixed task set, commit the profile records and the outcome under runs/<date>-<arm>/ in this folder, and open the pull request; the required check holds the records to the schema. A finding that settles goes to docs/memory/ by the remember skill, in the same pull request.
5. The runs. For the template's own work, the arm is a change to the way of working (an instruction, a skill, a tool) tried on this project's own pull requests, and step 1 measures it as it goes: the cost is the project's ordinary work. For a fixed task set with an outcome, coordbench's harness already runs headless Claude Code per task and keeps each run's transcript and audit record; a profile record per run is one more file there, and the arms of section 2 become arms there. Either way the owner says how many runs of what before any start, with the expected usage windows, as for the coordination experiment.
6. The harness's own I/O, once per Claude Code version: strace is installed in the cloud environment and ptrace works there, so one headless run under `strace -f -e trace=openat,read,write` reproduces the article's measure at the current version, with the counts per file kept and the paths dropped. One run, by the owner's word.

The loop closes by the protocol: the report's open rows are the queue, the epics are re-planned from the findings, and the board shows what runs. A schedule, if one is ever added, is a fallback and never the only trigger, as with every schedule in Symphony.

## 6. What it costs, and what is the owner's

- This pull request: nothing. The profiler reads a file; its tests write their own transcript.
- Steps 1 to 4: nothing beyond the project's ordinary work.
- Step 5 on coordbench: the usage of the task set under each arm, about the cost of one coordination arm per arm; the owner chooses the pair count and the arms, as for the full run chosen on 2026-10-15.
- Step 6: one headless session of a few minutes.
- The owner's: the word and the number before any run; and, when the shared keys of step 2 are wanted, the privacy statement's next version in OpenSpineConsortium/symphony-start and its site page, before the collector keeps them.

## 7. Where this stops

This page settles the measures and the order and makes the instrument. It does not decide which arm comes first, which task set the arms run on (the coordination experiment's pairs are the obvious one, since their harness and scoring exist), or whether the profile trailer should join the usage trailer in one line (two trailers keep every reader of Symphony-Usage unchanged, which is why the plan says two). A reader who finds a measure defined wrongly changes tests/test_profile.py first, since the test is the definition.
