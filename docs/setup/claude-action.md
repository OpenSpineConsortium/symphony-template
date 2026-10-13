# Turning on @claude in issues and pull requests

Writing @claude on an issue, a pull request or a review runs a Claude Code
session in Actions (.github/workflows/claude.yml): it reads CLAUDE.md and
the rules like every other session, answers, fixes, or takes the work the
comment asks for. The same secret runs the workers registered to run in
Actions and the coordinator workflow (both below). Until the one secret
below exists, each of these workflows says so in its run and does nothing
more, so nothing here is required. In crowd mode
(docs/setup/crowdsourcing.md) none of this page applies: the repository
holds no Claude token, and the workflows never start while the repository
variable CLAUDE_CROWD is true.

## No API billing

The workflow authenticates with a subscription OAuth token, not an API
key: runs draw on the main account's Claude plan (Pro, Max, Team or
Enterprise) and bill nothing. That keeps the project's rule intact; the
token lives only in the repository's Actions secrets, which are settings,
not repository content, so the rule that no file holds a credential holds
too.

## Steps, once, by the main account

One OAuth flow does everything: on a machine where Claude Code is signed
in to the main account, run `/install-github-app`, pick this repository,
and approve the browser flow it opens. It installs the Claude GitHub App
and writes the repository secret CLAUDE_CODE_OAUTH_TOKEN itself, so no
token is ever copied by hand. The workflow is already on
{{DEFAULT_BRANCH}}; the next @claude mention runs it.

By hand, where that command is not at hand:

1. Run `claude setup-token` and approve it in the browser. It prints a
   token good for about a year and saves it nowhere.
2. Put the token in the repository secret CLAUDE_CODE_OAUTH_TOKEN, under
   https://github.com/{{REPO}}/settings/secrets/actions.

## What a run costs

- A run spends the main account's own usage: the five-hour window and the
  weekly limit, shared with that account's interactive sessions and
  routines. The workflow caps each run (--max-turns, a job timeout), but
  mentions are still deliberate asks, not decoration.
- Keep usage credits off on the main account unless overage billed at API
  rates is wanted; with them on, a run past the limits bills quietly.
- A pull request from a fork gets no secrets, so @claude does not run
  there; an account working in this repository pushes claim branches, not
  forks (docs/agents/PROTOCOL.md).

## Workers in Actions, optional

A worker in Actions is one file under .github/symphony/workers/ that says
"runs": "actions" (docs/agents/WORKERS.md), and
.github/symphony/workers/README.md lists its settings. Add one with the
"Add a worker" issue form,
https://github.com/{{REPO}}/issues/new?template=worker.yml, whose
workflow opens the pull request that adds the file where the repository
lets GitHub Actions open pull requests ("Allow GitHub Actions to create
and approve pull requests" under Settings, Actions, General, which
scripts/setup-repo.sh and the front door's Setup App turn on;
docs/setup/github.md, section 8), and otherwise answers with the link
that opens it in one press; or add the file by hand in a pull request of
its own. Once it merges,
.github/workflows/workers.yml runs every such worker on this token, one
run per worker, in parallel: every six hours, whenever an issue is
queued or given to one of them, and again while a worker still has
work, up to the "rounds" its file allows in a row. Before any Claude
session starts, a cheap step on GitHub's own token (tools/team.py) deals
the open work among them, by area first, so no two race for one issue
and a worker with nothing to do costs seconds of a runner and no plan
usage. Each worker's model and turns per run come from its file. Run the
workflow from its own page with "Run workflow", naming one worker or
none for all, to try it once; delete a worker's file by pull request to
stop it. A worker whose file says "lands": "auto-merge" turns on
auto-merge for its finished pull request, which needs "Allow
auto-merge" under Settings, General; turning off "Require branches to be
up to date" in the default branch's rules saves a run per worker each
time another lands. Give each worker its own name, after its job: a
routine and a worker in Actions under one name would each take the
other's claims for their own.

## The coordinator workflow

The same token runs the part of the coordinator that needs judgement,
.github/workflows/coordinator.yml (docs/agents/WORKERS.md); the board's
own run does the rest, releasing idle claims and telling open work that
overlaps, on GitHub's token alone. Label an issue epic and Claude plans
it into tasks that each own their files, given to the registered workers
whose area fits, or to the open queue where none is registered, and
starts the workers in Actions; the epic then loses the label todo, and
the board lists each task given to a worker under "Given to workers",
out of the Queue, so nobody else takes it. A worker that labels its task
blocked calls the coordinator to settle what it needs. When an epic's
last task closes, the coordinator checks the default branch as a whole,
since every task can pass alone while the whole fails, and fixes what the
pieces broke together on a pull request that lands by auto-merge, so
"Allow auto-merge" is needed here too. Every week it runs the
coordinator prompt, docs/agents/routines/coordinator.md, which splits
requests into issues and tidies the shared memory. Nothing turns it on
but the token, and no coordinator routine is needed beside it.

CLAUDE_ALLOWED_TOOLS, a repository variable, replaces the tools the
sessions of claude.yml, workers.yml and coordinator.yml may use when a
project's checks need more than git, gh, python3 and scripts/check.sh;
the workers themselves are files, not variables. Every worker in
Actions and the coordinator draw on the main account's one usage window,
so three workers in Actions spend it about three times as fast as one
session, and a Max plan suits several of them better than Pro.

## Keeping the token

Treat the token like a password: it is the main account's subscription.
It expires after about a year; run `claude setup-token` again and replace
the secret. To turn @claude off, delete the secret, and the workflow is a
quiet no-op again, as are the workers in Actions and the coordinator
workflow, which run on the same secret.
