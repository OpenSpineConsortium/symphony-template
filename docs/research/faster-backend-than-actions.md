# A faster backend than GitHub Actions

Source: the thread "Faster backend than Actions", 2026-10-20. The owner asked at 19:40 UTC: "would using these somehow replace the github actions with instantaneous or near instantaneous backend? if not what paid or even free if possible feature could directly convert my yaml scripts into github backend process of equivalent or greater power/protection/security/latency?" and said at 19:43 UTC that "these" are the agent sandboxes: GitHub Copilot's local and cloud sandboxes (Microsoft's MXC, using Seatbelt on macOS, bubblewrap on Linux and silos on Windows) and Docker Sandboxes (the sbx CLI, one microVM per agent). Research only: nothing was built, started or spent. It follows docs/research/rust-coordinator.md of 2026-10-19, which measured the template's own runs and weighed a webhook edge; this note adds the sandboxes, a fresh measurement that includes a copy's board, and the plan limits that decide what a free personal account can use.

## The answer

No. A sandbox is a fence around an agent's shell commands on one machine: it decides what a command may read, write and reach on the network. It has no trigger, so nothing on GitHub starts it, and it hosts nothing, so no workflow can move into it. It makes a Claude or Copilot session safer, not anything sooner. Copilot's cloud sandbox runs a session in an ephemeral Linux VM on GitHub's side, which is the same shape as an Actions job, and it was still public preview or experimental on 2026-10-20 (only the local sandbox reached general availability, on 2026-10-07); Docker Sandboxes run on the person's own computer.

Nor does any GitHub feature, free or paid, turn workflow YAML into a faster GitHub-side backend. GitHub's only event-driven compute is Actions; GitHub Agentic Workflows, Copilot's coding agent and Copilot's cloud sandbox all run on it or on the same kind of VM. What GitHub offers that is instant is enforcement, not compute: rulesets, required checks, auto-merge and the claim lock (a second push of a branch name is refused) take effect at the moment of the push, with no runner, and Symphony already uses them.

And Actions is not where most of the time goes. Measured today, GitHub turns an event into a running job in about 3 to 4 seconds. The waits a person feels are the board's queue, a median of 21 seconds and up to 57 in a copy, and the work itself: the required check takes 100 seconds in a copy and 300 in the template, and a Claude session takes minutes on any host.

Recommendation, cheapest first:

1. Free, no server, in the code we already own: shorten the two waits that were measured. Split scripts/check.sh into parallel jobs (the copy's own standards suite already runs six groups side by side in about 15 seconds each), and look in symphony-protocol at whether a burst of board runs can collapse into one, since each run reads the whole state and the runs queued behind it only repeat it. Together they would take the slowest path from minutes to well under one, with nothing new to host or secure.
2. For near-instant board updates, the one route that exists is still the webhook edge of rust-coordinator.md, section 2: SymphonyBoard's webhook on, pointed at a Cloudflare Worker with one Durable Object per repository, reacting in under a second, with Actions kept as the fallback sweep and as the only place the check and Claude run. It works on a free personal account (an App installs there like anywhere) and costs nothing on Workers Free for a handful of repositories, or $5 a month on Workers Paid. It reverses the standing decision "no server of ours" and widens what a leaked key can reach (below), so it is the owner's decision alone.
3. Sandboxes belong to the sessions, not the backend. If the owner wants the protection the sandboxes give, Claude Code has its own sandbox for its shell commands on macOS and Linux (recalled, not re-read this session), and Docker Sandboxes run Claude Code too; either fences a local session, and neither changes how Symphony coordinates.

## 1. Where the time goes, measured

Measured on 2026-10-20 around 19:45 UTC from the REST API's /actions/runs and /actions/runs/{id}/jobs, over the last 100 runs of each repository, skipped runs left out. Lead is from the run's creation to its job's creation, which is where a concurrency group holds a job; queue is from the job's creation to a runner starting it.

A private copy of the owner's made on 2026-10-20, whose board runs (the template skips its own):

| Job | n | Lead, median (range) | Queue, median (range) | Setup and checkout | Job, median (range) |
| --- | ---: | --- | --- | --- | --- |
| Board / board | 22 | 21 s (0 to 57) | 3 s (2 to 4) | 2 s | 13.5 s (10 to 25) |
| Checks / check | 12 | 7.5 s (2 to 62) | 3 s (0 to 4) | 3 s | 101.5 s (up to 114) |
| standards / each of six groups | 7 each | 1 s | 3 s | 2 to 3 s | 14 to 18 s |
| automerge, tidy, template init, settings | 1 to 3 each | 1 s | 3 s | 0 to 4 s | 5 to 25 s |

OpenSpineConsortium/symphony-template:

| Job | n | Lead, median | Queue, median | Job, median (range) |
| --- | ---: | --- | --- | --- |
| Checks / check | 18 | 7 s | 3 s | 299 s (to 323) |
| Docs / build | 4 | 0 s | 3 s | 322.5 s (248 to 335) |
| Settings / apply, Sync / offer, Notebooks / run | 1 to 2 each | 0 to 1 s | 3 s | 5 to 38 s |

What this says:

- GitHub's own overhead is about 3 seconds for a runner and 2 to 3 for setup and checkout, as on 2026-10-19. A backend of our own would save those 5 to 6 seconds a hop.
- The board's queue is real: the copy's board waited a median of 21 seconds, up to 57, behind earlier board runs in its single concurrency group, because one merge or one claim fires several events at once. This is the measurement step 1 of rust-coordinator.md asked for, taken without a burst on purpose. The board's run itself takes 10 to 25 seconds, so a person sees the board change about 15 to 85 seconds after acting.
- The template's check has grown from 160 to 230 seconds on 2026-10-19 to about 300 today, and the docs build takes about as long. Those are work, which a faster host shortens only by being a faster machine.

## 2. What the sandboxes are, and why they do not replace Actions

- GitHub Copilot's local sandbox, generally available since 2026-10-07, wraps the commands Copilot CLI, the Copilot app and VS Code's Agent Host run on the person's machine in the operating system's own isolation, at no extra cost; it starts switched off (`/sandbox enable`), and an enterprise can require it. Copilot's cloud sandbox runs a session in an isolated, ephemeral Linux VM on GitHub's infrastructure and was in public preview, not generally available, on 2026-10-20. Both serve Copilot only.
- Docker Sandboxes (sbx, released March 2026) run any coding agent, Claude Code among them, in a microVM with its own kernel on the person's computer, brokering its network through a proxy on the host that can inject a credential so the agent never sees it; the CLI is free, with organization governance a paid subscription (third-party reports, not read on Docker's own pricing page).

None of them listens for GitHub's events, holds a repository's settings or posts a check, so none can stand where board.yml, workers.yml or ci.yml stand. They answer a different question, whether an agent's command can damage the machine it runs on, which in Symphony's Actions jobs is already answered by the job's own throwaway VM.

## 3. What GitHub has, by plan

Read on 2026-10-20 from the github/docs repository's content files (docs.github.com is unreachable from the session):

| Feature | What it gives | Free personal account |
| --- | --- | --- |
| Actions, GitHub-hosted runners | the only event-driven compute GitHub has | yes; free on public repositories, minutes from the plan on private ones |
| Larger runners | more CPU and RAM, so a faster check | no: "only available for organizations and enterprises using the Team or Enterprise Cloud plans" |
| Self-hosted runner | the runner wait can drop, and the check runs on any machine | yes; needs a machine kept on, and is safe only on a private repository (the grid's runner chain, docs/research/wsu-grid-and-github-actions.md, is one) |
| Rulesets | instant enforcement at push time | public repositories on Free; private ones need Pro, Team or Enterprise Cloud |
| Push rulesets | refuse a push by path, size or file type | Team plan, private and internal repositories only |
| Merge queue | serialised merges tested together | public repositories owned by an organization, or private ones on Enterprise Cloud; not a personal account |
| Webhooks | events delivered to a server within GitHub's 10-second answer limit; no automatic redelivery | yes, but they need a server to receive them |
| GitHub Agentic Workflows | Markdown compiled to an Actions workflow | runs on Actions, so no faster (docs/research/workflow-languages.md) |

The owner's plan to leave GitHub Enterprise makes the merge queue on private repositories and push rulesets unavailable to a personal account, so neither is a foundation to build on.

## 4. What the Apps' webhooks could replace, workflow by workflow

A webhook only delivers an event; whatever answers it is a server of ours. SymphonyBoard and Symphony Setup have their webhooks off, and their permissions decide only what such a server could write. Sorted by what the 24 workflows of the template at 4e364ac do, read from their triggers and steps:

| Kind | Workflows | Could a webhook edge take it? |
| --- | --- | --- |
| Short API writes on an event | board.yml, tidy.yml, queue.yml, add-worker.yml, template-init.yml, settings.yml | yes, in under a second; these are where the edge would be felt, the board above all |
| Dispatchers that start a Claude run | workers.yml, coordinator.yml, claude.yml, agents.yml, drive-organize.yml, pool.yml | the dispatch only; the Claude run stays in Actions on the repository's own token |
| Builds and checks of the code | ci.yml (the required check), docs.yml, notebooks.yml, papers.yml | no: they need a checkout and minutes of CPU, which a Worker cannot give |
| Scheduled and on-demand jobs | metrics.yml, protocol.yml, sync.yml, drive-sync.yml, digest.yml, token.yml | no gain: nobody waits on them |
| The grid | grid.yml, grid-gate.yml | no: they run on the grid's own runner chain |

So an edge would take six workflows and the front of six more, and leave the twelve that do real work where they are. GitHub natively already covers part of the first row: delete-branch-on-merge removes a merged pull request's branch, leaving tidy only issues closed without a merge, auto-merge lands a ready pull request with no workflow, and the claim lock is GitHub refusing a second push of a branch name.

## 5. The webhook edge, weighed again

The design, costs and credential rule are in rust-coordinator.md, sections 2 to 4, and are not repeated here. Against the owner's four measures:

- Latency: under a second from event to board, against 15 to 85 seconds measured today. The check and Claude are unchanged, since they stay in Actions.
- Power: equal for the board's deterministic work (labels, comments, renames, the board branch, the deal); it cannot run Claude, which must stay on each repository's own token in Actions under Claude Code's terms.
- Protection: GitHub's rulesets and required checks protect the same way whoever writes, so nothing is lost; a missed delivery needs a sweep, which Actions' six-hourly board run already is.
- Security: worse in one way. Today a workflow writes with a GITHUB_TOKEN scoped to one repository and one run. An edge holds the App's private key, which mints a token for every installation, so a leak of the Cloudflare account reaches every adopted repository. The control panel's sign-in Worker already runs on the same account, but it holds no App key.

### What moving costs, and what it does to correctness

The owner's follow-up at 19:53 UTC: "how much trouble to move to a cloudflare worker? do i lose any guarantee of correctness?" Inferred from the design above and the protocol's text; nothing measured or built.

The work, about five pull requests in symphony-app beside the sign-in Worker, with the deploy-on-merge workflow it already has: a receiver that checks the webhook's signature and answers inside 10 seconds; App authentication (a JWT from the App's key, an installation token per repository); one Durable Object per repository that runs the board's step; a Cron Trigger that reconciles every repository and redelivers failed deliveries; and the board workflow changed to stand back while the edge is healthy. The one-time steps for the owner would be the App's webhook URL and secret and the App's key as a Worker secret; GitHub's API can set an App's webhook URL and secret with the App's own JWT, so the deploy workflow could likely set them, which was not tried.

The language decides the risk. The protocol is a stdlib-only Python library, and Cloudflare runs Python Workers through Pyodide; whether that runs the library unchanged inside a Durable Object was not checked. If it does, the same code runs and symphony-protocol's tests and validation harness keep covering it. If the logic has to be ported to JavaScript or Rust, it is a second implementation, and until the harness checks it against the same oracle it carries none of the guarantees the Python library earned (F1 to F18 were found that way).

What stays the same, whatever runs the board: the guarantees GitHub itself enforces. The claim lock (GitHub refuses the second push of a branch name), the rulesets, the required check, the push guard in each session and the merge gate do not depend on Actions, so no move can weaken them.

What changes:

- Better: one Durable Object per repository runs one step at a time, a single writer, so the board's queue and the race of a waiting run cancelled by a newer one (F12) go away by construction.
- Worse unless handled: GitHub never redelivers a failed webhook by itself, where an Actions run is started for every event; the protocol survives a lost event only because each step reads the whole state again, so the edge must stay level-triggered and keep the sweep, with Actions' six-hourly board run as the last fallback.
- New: while both the edge and the fallback can write, there are two writers again, so the board branch must be updated with an expected-head check (git's own compare-and-swap on a ref) and the fallback must not write while the edge is healthy.
- To be re-specified: the Release section dates a push by "the run that a push to the branch started" and by the run's start; an edge has no run, so those rules need their edge equivalent, written into symphony-protocol and checked by its harness before the edge is trusted to release a claim.

### Realistic latency, path by path

The owner asked next (20:00 UTC) for realistic reductions. The board's job in the copy, step by step over its last eight successful runs: set up and checkout 1 to 3 s, fetching the old board 0 to 1 s, rendering (the GitHub API calls that read issues, branches and pull requests and write renames and comments) 4 to 13 s, median 5, and writing the board branch 1 to 2 s. An edge still makes those API calls, so it saves the queue, the runner and the setup, not the rendering. Webhook delivery is taken as about a second, which is typical but not measured here and carries no promise from GitHub.

| Path | Today, measured | Free fix (no queue build-up, in Actions) | Webhook edge, estimated |
| --- | --- | --- | --- |
| Act on GitHub to the board showing it (claim, label, merge) | median about 38 s (21 queued, 3 runner, 13.5 job); 15 to 87 s | median about 17 s; 13 to 30 s | about 7 to 9 s; up to about 15 s |
| A label to a worker's Claude session starting | about 5 to 10 s before Claude's own start-up | the same | saves the same 5 to 10 s, invisible beside a session of minutes |
| A push to the required check's result | 100 s in the copy, 300 s in the template | about 30 to 60 s if split into parallel jobs (inferred from the copy's six standards groups, 14 to 18 s each) | no change: the check stays in Actions |

So the edge's real gain is on one path, the board, from about 38 s to about 8 s at the median and from 87 s to about 15 s at worst, and most of the worst case is removed already by the free fix. Making the rendering itself faster (fewer calls, GraphQL batching, reading only what an event changed) would help either host equally.

So the move is a few days of thread work if Python Workers run the library, and it loses no guarantee GitHub enforces. The protocol's own guarantees carry over only if the same library runs and the harness is extended to the edge's delivery and timing.

## 6. The owner's decisions

1. Whether to start step 1: a template pull request splitting the check into parallel jobs, and a symphony-protocol pull request letting a burst of board runs collapse. Free, no server, ordinary pull requests.
2. Whether to lift "no server of ours" for the webhook edge of step 2, knowing it puts the App's key on Cloudflare.

## 7. Step 1 taken, 2026-10-20

The owner said at 20:26 UTC that the free fixes "seem like no brainers", and the thread made them in one pull request:

- The check in parts: ci.yml runs a job parts, five legs side by side (scripts/check.sh without its tests, and the tests cut into four by tools/test_shard.py, longest first by the seconds tests/durations.json records), and the required job check waits for them and fails unless every leg passed. Measured locally on 4 CPUs, the tests took 360 s in one run; the four parts come to about 168, 61, 61 and 61 s, so the template's check is held by its one longest module, tests/test_filled_copy.py, which runs three copies' own checks, and a copy's check by about a quarter of its tests.
- The board's line: the concurrency group moved from the workflow to the job, so a run whose job is skipped (every push to a claim branch, a fork's pull request) no longer waits in it; and a run stands back when a newer run whose job will run waits behind it, except a run a push to a claim branch started (a branch made, or a pull request's synchronize), which dates that push at its start so no claim is released in the run its push started. A merge's burst then costs one full run, not four.

Measured on the pull request's own run in the template (GitHub-hosted runners, 2026-10-20 20:49 UTC): the parts started together; rest took 13 s, parts 2 to 4 took 39 to 47 s, and part 1, tests/test_filled_copy.py alone, took 210 s, after which the job check took 9 s; the check finished 222 s after its parts began, against 299 s for the single job before (median of 18). The template stays bound by the copies' own checks that test makes; a copy, which skips that test, should finish in about its slowest part, under a minute against 100 s. The board's change is measured from a copy's runs once the sync brings it.

## Sources read

- GitHub REST API: /actions/runs and /actions/runs/{id}/jobs on OpenSpineConsortium/symphony-template and on the owner's private copy, 2026-10-20.
- github/docs content: about-rulesets.md (rulesets and push rulesets by plan), gated-features/merge-queue.md, actions/larger-runner-permissions.md, webhooks/using-webhooks/handling-failed-webhook-deliveries.md.
- GitHub changelog, through search results: "Local sandboxing for GitHub Copilot now generally available" (2026-10-07) and "Cloud and local sandboxes for GitHub Copilot now in public preview" (2026-06); docs.github.com's "About cloud and local sandboxes", by its search summary.
- Docker Sandboxes, through search results: docs.docker.com's guide to running Claude Code in a Docker Sandbox and third-party write-ups; not read on Docker's own site.
- docs/research/rust-coordinator.md and docs/research/workflow-languages.md in this repository.
