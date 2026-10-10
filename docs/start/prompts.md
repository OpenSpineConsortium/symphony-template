# Prompts to paste

Each block is one message for a Claude Code session on the repository: `claude` in your clone, a cloud session at https://claude.ai/code, or a thread of the account's Project. Every session already reads CLAUDE.md, the protocol, the memory index and the board, so the prompts stay short. Put the issue's number for N, the repository for ORG/NAME and your own account's label where account:main stands.

## Work

**Claim the next issue,** when one session works at a time; it takes blockers first, then the lowest-numbered unclaimed issue in the Queue:

```
Read the board, take the next issue as docs/agents/routines/worker.md's steps 2 to 5 say, claim it with the claim skill and carry it to a ready pull request. If the push of claude/<issue> is refused, another session holds it: take the next one. Do not merge.
```

**Claim issue N,** when several sessions run at once, so none waits on a refused push:

```
Claim issue N with the claim skill and carry it to a ready pull request, as docs/agents/PROTOCOL.md says; work on the branch claude/N, not this session's own branch. If the push of claude/N is refused, another session holds the issue: say so in one line and stop. Do not merge.
```

**Add this line in a cloud session,** whose GitHub proxy refuses gh's GraphQL commands:

```
gh issue and gh pr are refused here, so add the labels, post the plan and open the draft pull request with your GitHub tools or gh api (repos/ORG/NAME/issues/N/labels, repos/ORG/NAME/issues/N/comments, repos/ORG/NAME/pulls); if you cannot mark the pull request ready, say so and stop.
```

**Add this line on any account but the main one,** so the board says whose claim it is:

```
My account label is account:alice and the claim file's Account line is alice.
```

**Run the worker once,** to see what the routine will do before you schedule it:

```
Do what the prompt in docs/agents/routines/worker.md says, once, as it stands, with my account label account:main.
```

**Make the worker routine,** in the account's Project conversation, so it runs as the Project's threads: paste the prompt from docs/agents/routines/worker.md, then:

```
Run this every hour, a few minutes past the hour.
```

**Split a piece of work into issues,** so parallel sessions each get files no other session touches:

```
Split the work below into one Task issue per piece, each with a Goal, an Acceptance line and the Files likely touched, labelled todo, with no two issues touching the same file; where two pieces meet, write the interface between them into both. Show me the list before you open them. The work:
```

**Rebase after "main moved",** the one forced push the protocol allows:

```
The board says main moved on my pull request: git fetch origin, rebase claude/N on origin/main, run bash scripts/check.sh, and push with --force-with-lease.
```

## Keep what you learned

**Checkpoint,** so the next session or account starts where this one stopped:

```
Write a checkpoint with the checkpoint skill and commit it on this pull request's branch.
```

**Remember a fact for every account,** since a Project's own memory is private to its account:

```
Remember this with the remember skill, in this pull request: <the fact, in one sentence>
```

**Show the whole board,** since the session hook prints only its first 120 lines (`/sdlc:board` where the plugin brings it):

```
/board
```

## Review

**Review a pull request,** a second reading before the owner merges:

```
Review pull request #N: read the issue it closes and the plan in its claim file, check that the diff does what the issue asks and nothing else, that bash scripts/check.sh passes on its branch and that it finishes as docs/agents/PROTOCOL.md says. Leave your findings as one review comment. Do not push and do not merge.
```

**Or ask @claude on the pull request itself,** which runs in Actions on the main account's token:

```
@claude review this pull request against the issue it closes and docs/agents/PROTOCOL.md; comment, and do not push.
```

## Benchmark

**The smoke test,** in a cloud session on OpenSpineConsortium/coordbench with the environment from [benchmark.md](benchmark.md); one agent session, the cheapest proof the whole chain works:

```
Run coordbench's smoke test: bash bench/cooperbench/setup.sh, then bash bench/cooperbench/prepare_task.sh pallets_click_task 2068, then env -u ANTHROPIC_API_KEY python3 coordbench/run.py run --arm solo --repo pallets_click_task --task 2068 --features 1,6 --driver claude-cli --name smoke-solo, then python3 bench/cooperbench/report.py --run solo=smoke-solo. Show me the timings line and the report, and stop. Do not run judge.py's model sections.
```

**The pilot,** six arms on one task, about 66 agent sessions:

```
Run bash bench/cooperbench/pilot.sh pallets_click_task 2068 pilot in the background; if it stops at the two-hour limit, run it again, since finished pairs are kept. When it ends, show me ~/cooperbench/logs/pilot-report.md and remove the task's image with docker rmi akhatua/cooperbench-pallets-click:task2068.
```
