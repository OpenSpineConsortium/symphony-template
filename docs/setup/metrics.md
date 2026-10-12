# Field metrics

OpenSpineConsortium/coordbench measures ways of coordinating coding agents on CooperBench's task pairs, this template's claim protocol among them. Field metrics measure the same protocol where it is really used, in this repository, so the benchmark's numbers can be set beside what happens in practice. Only aggregates are kept: counts, durations, outcome rates and how often each kind of communication error appears. No code, no text, no title, no login, no branch name and no repository name ever goes into the files, and nothing leaves the repository unless the repository installed the Symphony App, whose collector reads two files and nothing else. Sharing is on by default and has one switch, below.

Two pieces do the work, both in tools/metrics.py:

- `collect` runs every day in .github/workflows/metrics.yml, with GitHub's own GITHUB_TOKEN and no other secret, and writes METRICS.json to the branch `metrics`.
- `judge` runs only when a maintainer runs it, on their own machine, with their own gh and their own Claude Code on their own subscription, and writes JUDGE.json, which `--push`, or `push` afterwards, adds to the same branch.

## What is computed, and from where

The window is the 30 days that end when the run starts. "The window's pull requests" are those GitHub changed in it: created, merged, closed, reviewed, commented on or pushed to. Everything is read from GitHub's REST API, and every identity, number and text the code reads stays in the run's memory.

| Key | What it is | Read from |
| --- | --- | --- |
| counts.claims | Distinct issues N with a pull request from `claude/N` among the window's, or a branch `claude/N` whose head commit was made in the window | /pulls, /branches, /commits/{sha} |
| counts.pull_requests_opened | Pull requests created in the window | /pulls |
| counts.merged | Pull requests merged in the window | /pulls |
| counts.closed_unmerged | Pull requests closed without a merge in the window, among them a released claim's, which GitHub closes when the board renames its branch (docs/agents/PROTOCOL.md, Release) | /pulls |
| counts.reviews | Reviews submitted in the window on the window's pull requests, by anyone but the pull request's author (GitHub files an author's reply in a review thread as a review of their own); a reply in a review thread by anyone else is filed as a review too, and counts as one | /pulls/{n}/reviews |
| counts.changes_requested | Those reviews that asked for changes and still stand: a changes-request dismissed since shows as dismissed, and is not counted | /pulls/{n}/reviews |
| counts.check_runs_passed | Check runs that finished in the window, with the conclusion success, on the commits of the window's pull requests that were made in the window, every attempt on each (GitHub lists the latest attempt of each check alone unless asked for all, which would hide a failure behind its re-run) | /pulls/{n}/commits, /commits/{sha}/check-runs?filter=all |
| counts.check_runs_failed | The same with the conclusion failure or timed_out; neutral, skipped, cancelled, stale and action_required count as neither | /pulls/{n}/commits, /commits/{sha}/check-runs?filter=all |
| counts.conflicts_seen | Pull requests seen in conflict with the default branch: open ones GitHub reports as `dirty` now, and any the board's "main moved" comment called conflicting in the window (a pull request only behind is no conflict) | /pulls/{n}, /issues/comments |
| counts.released_claims | Claims released in the window, by the coordinator's release comments: those whose first line is `<!-- sdlc-coordinator: claim-released -->` (docs/agents/routines/coordinator.md, step 2) and whose author is the repository's owner, a member or a collaborator, the ones the board acts on; only that line is looked for. A release comment on an issue that had another less than a day before is the same release said again, and counts once | /issues/comments |
| counts.contributors | How many different people did something in the window on its pull requests: created one, submitted a review on one, or made a commit on one, by its author or committer date; a pull request enters the window on any change, so each person is dated by their own act, not by the pull request's. Apps and bots are left out, and a commit with no GitHub account counts by its author's email, so an agent that commits under one name counts once | /pulls, /pulls/{n}/reviews, /pulls/{n}/commits |
| durations_seconds.claim_to_first_pull_request_median, _p90 | From each claim to its first pull request opened in the window | /pulls/{n}/commits |
| durations_seconds.open_to_merge_median, _p90 | From opening to merging, for pull requests merged in the window | /pulls |
| durations_seconds.first_review_median, _p90 | From opening to the first review by someone other than the author, for pull requests opened in the window that have one | /pulls/{n}/reviews |
| rates.merge_rate | merged / (merged + closed_unmerged) | the counts |
| rates.first_check_pass_rate | Of the pull requests opened in the window, the share whose first head commit's counted check runs all passed, every attempt among them, so a check that passed only when run again did not pass first | /pulls/{n}/commits, /commits/{sha}/check-runs?filter=all |

How the choices were made:

- The claim's time. GitHub's REST API never says when a branch was made. A claim branch's first commit adds the claim file and nothing else (docs/agents/PROTOCOL.md), so the claim's time is the earliest author date among the pull request's commits: that commit's. Author dates survive a rebase; committer dates do not.
- The first head commit. GitHub keeps no record of the head a pull request was opened with, so it is the newest of its commits committed by the time it opened, with a minute's grace for a fast clock. When a rebase has replaced them all, the pull request stays out of first_check_pass_rate. On a `claude/N` pull request opened at once, as the protocol asks, the first head is usually the claim commit.
- Check runs. They are read on every commit of the window's pull requests made in the window, not on the head alone: the default branch takes only a pull request whose check passed, so a merged pull request's head is green by construction, and the failures its earlier heads had would never be seen. And every attempt on a commit is read (filter=all), where GitHub's listing shows the latest attempt of each check alone, so a failure that a re-run fixed is still the failure it was.
- Conflicts come from two places because each misses some: GitHub computes `dirty` only for an open pull request and only as it stands now, and the board's comment marks the moment the default branch moved under one. Both are counted once per pull request.
- The budget. A run costs, per pull request of the window, one REST call for its commits, one for its reviews, one for the check runs of each of its commits made in the window, one more for the head it was opened with when that was made before the window, and while it is open one for its detail, or two when GitHub has not computed its mergeability yet; one per claim branch without a pull request in the window; and one per hundred pull requests, branches and comments listed. GITHUB_TOKEN has 1,000 requests an hour for the whole repository, which the board's runs share, so the run reads from each answer how many are left and stops before it would leave fewer than 300 for the board: it says so, with the calls it made and when the hour's budget comes back, writes nothing, and the workflow run fails; the branch keeps its last record, and the next run, the daily one or one by hand once the hour has turned, writes again when it fits. The log of a run that fits says how many calls it took. It runs once a day at 03:43 UTC, before OpenSpineConsortium's collector reads the branch at 04:17, by hand from the Actions tab or with `gh workflow run metrics.yml --repo OWNER/NAME`, and on a push to the default branch that changes .github/symphony-metrics (the switch, below).
- Medians are rounded half up to whole seconds; the 90th percentile is the nearest rank, the smallest value at or above nine tenths of them. A wait against the clock (a later event dated earlier) is left out. Rates are rounded to four places. Where a value has nothing to measure it is null.

## The files

On the branch `metrics`, which holds nothing else. METRICS.json, here with sharing on:

```json
{
  "schema": "sdlc-metrics/1",
  "generated_at": "2026-10-10T03:43:12Z",
  "window_days": 30,
  "sharing": "on",
  "protocol_version": "0.2.0 f530a66",
  "counts": {
    "claims": 4,
    "pull_requests_opened": 3,
    "merged": 1,
    "closed_unmerged": 1,
    "reviews": 3,
    "changes_requested": 1,
    "check_runs_passed": 3,
    "check_runs_failed": 1,
    "conflicts_seen": 2,
    "released_claims": 1,
    "contributors": 4
  },
  "durations_seconds": {
    "claim_to_first_pull_request_median": 7200,
    "claim_to_first_pull_request_p90": 10800,
    "open_to_merge_median": 86400,
    "open_to_merge_p90": 86400,
    "first_review_median": 7200,
    "first_review_p90": 7200
  },
  "rates": {
    "merge_rate": 0.5,
    "first_check_pass_rate": 0.3333
  }
}
```

protocol_version is the release and short commit of the vendored protocol, from tools/VENDORED's first line. With sharing off the file is this, and nothing more:

```json
{
  "schema": "sdlc-metrics/1",
  "sharing": "off"
}
```

JUDGE.json, only after a maintainer has run the judge and pushed its file:

```json
{
  "schema": "sdlc-judge/1",
  "generated_at": "2026-10-10T18:02:40Z",
  "model": "claude-sonnet-5-5",
  "prompt_variant": "appF-7",
  "conversations": 18,
  "counts": {
    "C1a": 2,
    "C1b": 1,
    "C2": 0,
    "C3a": 1,
    "C3b": 0,
    "C4a": 0,
    "C4b": 3
  },
  "groups": {
    "unresponsiveness": 3,
    "hallucination": 1,
    "repetition": 3
  }
}
```

conversations is how many pull request conversations got a readable answer; each counts under at most one code, as App F labels at most one category per conversation, and many under none.

## How each measure lines up with the benchmark's

coordbench's PARITY.md lists every measure CooperBench takes, by row, with how coordbench takes it. CooperBench runs two agents on one task pair with hidden tests and merges their two patches once at the end; a project here runs any number of people and agents through issues, claim branches and pull requests against its own checks, so most field measures are the protocol's own and few have a CooperBench twin. Plainly:

| Field measure | Benchmark measure | How they compare |
| --- | --- | --- |
| counts.conflicts_seen | CooperBench's conflict rate (PARITY.md row 55, from row 54's naive-merge conflict flag); the sdlc arm's merge_conflicts (row 135, coordbench's own) | Equivalent in what it asks, different in how: CooperBench asks whether git conflicts when it merges the two final patches; the field counts pull requests that met the default branch in conflict, as the sdlc arm's gate meets them. Divide by pull_requests_opened for a rate; the benchmark divides by pairs. |
| counts.claims, pull_requests_opened, merged | The sdlc arm's claims, prs_opened and merges (row 135, coordbench's own) | Same events; CooperBench has no claims or pull requests. |
| durations_seconds.open_to_merge_* | The sdlc arm's time_to_first_merge_seconds; CooperBench's pair duration_seconds and median task time (rows 30 and 32) | Different clocks: the field measures each pull request from opening to merge, the benchmark the pair from its start. |
| counts.contributors | The number of agents in a run (row 15; CooperBench runs 2, 3 or 4) | A count of people and commit identities, not of configured agents. |
| JUDGE.json counts and groups | App F's communication errors (rows 66 to 75): C1a, C1b and C2 under Unresponsiveness, C3a and C3b under Hallucination, C4a and C4b under Repetition | The same seven codes, names and groups, and App F's text word for word (variant appF-7, coordbench's default) except its Output paragraph. Three differences: the conversation is a pull request's description, comments, review comments and reviews, among people, agents and bots, not two agents' messages; the answer is the codes alone, so coordbench's check that two quotes are found verbatim cannot run, and the field's counts are the judge's labels without it, so they can only be as many as coordbench would accept from the same model, or more; and the judge model is the maintainer's Claude, coordbench's one unavoidable deviation too (row 66). |
| counts.reviews, changes_requested; durations first_review_* | none | CooperBench has no review. |
| counts.check_runs_passed, check_runs_failed; rates.first_check_pass_rate | none | These are the project's own checks, not hidden tests; CooperBench's feature passed and tests_passed (rows 2 and 3) run held-out tests on the merged patches, which a project does not have. |
| counts.released_claims; durations claim_to_first_pull_request_* | none | CooperBench has no claims; coordbench's sdlc arm logs claim and pr_opened events but reports no wait between them. |
| rates.merge_rate | none | CooperBench's success (rows 0 and 1) is both features' tests passing on the merged patches, which the field cannot run; a merge here says only that the project's own rules let it land. |

Not measured in the field at all: pair success and the coordination gap (rows 0, 1 and 8), cost and tokens (rows 24 to 29), messages and turns (rows 36 to 47) and the failure symptoms and causes (rows 76 to 88), since each needs the agents' own logs or patches, which never leave a project.

## What is never collected

No source code, diff or file name; no issue, pull request, comment or commit text; no title, label name or branch name; no login, name or email; no URL, issue number or pull request number; no repository name. The identities and numbers the code reads to count are dropped with the run. The judge's conversations go only to the maintainer's own local claude process, which asks the model on the maintainer's own account as any of their Claude Code sessions does, and only the counts are written. A repository appears in OpenSpineConsortium's data only as a salted hash.

The branch `metrics` is as visible as the repository: in a public repository anyone can read the two files, which hold aggregates only.

## The switch

Sharing is on unless one of these says off; off from either wins.

- The file .github/symphony-metrics on the default branch: its first word is `on` or `off`. A missing file means on; any first word but `on`, or a file that cannot be read, means off. Change it by pull request like any file:

  ```
  printf 'off\n' > .github/symphony-metrics
  git add .github/symphony-metrics && git commit -m "Turn field metrics off"
  ```

- The repository variable SDLC_METRICS, which the workflow hands to the tool: `off` (any word but `on`) turns sharing off whatever the file says, and it needs no pull request:

  ```
  gh variable set SDLC_METRICS --repo OWNER/NAME --body off
  ```

With sharing off the run writes `{"schema": "sdlc-metrics/1", "sharing": "off"}` and makes no API call, so the collector sees only that. The run comes at once after a merge of off, since the workflow starts on a push to the default branch that changes .github/symphony-metrics; the variable starts no run, so after setting it run the workflow once by hand:

```
gh workflow run metrics.yml --repo OWNER/NAME
```

Either way the off record is on the branch before the collector's daily read at 04:17 UTC. The daily run alone, at 03:43, would leave the last on record there for the collector to read once more, with any JUDGE.json beside it.

Disabling the workflow (`gh workflow disable metrics.yml --repo OWNER/NAME`) does not stop sharing: the branch keeps what it last held, and the collector reads an on record left there every day as that day's. To stop both, in this order: turn the switch off, run the workflow once so the branch holds the off record (or delete the branch `metrics`), and only then disable it.

## Running the judge

On your own computer, in a clone of the repository, with gh signed in as you (`gh auth login`) and Claude Code signed in to your own subscription (`claude`, then /login). The judge refuses to run while ANTHROPIC_API_KEY is set, since claude would then bill the API, which this project never does, and just the same while ANTHROPIC_AUTH_TOKEN, CLAUDE_CODE_USE_BEDROCK, CLAUDE_CODE_USE_VERTEX or CLAUDE_CODE_USE_FOUNDRY is set, since each sends the conversations to an API or a cloud account and bills it; the refusal names the variable to unset. ANTHROPIC_BASE_URL alone, which would send them to a gateway, is dropped from claude's environment, and a dry run says so when it is set. Try the judge before running it whole:

```
unset ANTHROPIC_API_KEY
python3 tools/metrics.py judge --dry-run
python3 tools/metrics.py judge --limit 20
```

Then judge and push in one go, or judge, read JUDGE.json and push it afterwards; `push` never judges again:

```
python3 tools/metrics.py judge --push
```

```
python3 tools/metrics.py judge
python3 tools/metrics.py push
```

- `--dry-run` reads the window's pull requests with gh and prints, for the first conversation, exactly what would go to the model (the command, the system prompt and the conversation on stdin) and the JUDGE.json a run would write; it calls no model, writes no file and pushes nothing.
- A run asks your claude once per pull request conversation (twice when the reply is not JSON), with `claude -p --output-format json`, the conversation on stdin and App F as the whole system prompt, read from a file (`--system-prompt-file`) in the temporary folder claude runs in, which holds nothing else, so no project's CLAUDE.md is read; with no tool, no MCP server, no settings and so no hook, no skill and no saved session. Claude Code may still read your own user instructions; the one mode that skips them, `--bare`, signs in only with an API key. Each call spends your plan's usage; `--limit` caps the number of pull requests, newest first, and `--model` picks the model (default claude-sonnet-5-5, coordbench's default). A model name is letters, digits, dots, dashes and underscores, at most 64, with an optional `[tag]` after them, the shape the collector keeps; anything else, such as a cloud model ARN with an account number in it, is refused, because the name goes into JUDGE.json as it is. When claude fails (signed out, an unknown model, a usage limit), the judge stops, repeats what claude said, and writes nothing.
- People are named A, B, C in each conversation in the order they first speak, and mentions of them become the same letters; apps and bots are "bot". The protocol's own automated comments are left out: the board's "main moved" and "idle" comments and the coordinator's release comments, known by their markers (`<!-- sdlc-board: main-moved SHA -->`, `<!-- sdlc-board: idle -->`, `<!-- sdlc-coordinator: claim-released -->`), which are posted again and again by design, so App F would read them as spammy repetition that nobody wrote. The model is told to answer with codes alone, and anything else a reply carries is dropped before counting.
- `--push` commits JUDGE.json onto the branch `metrics` of origin as an ordinary commit on top of what is there, keeping METRICS.json exactly as it is, and pushes it with a plain push, which the push guard (tools/guard_push.py) lets through; when the workflow rewrote the branch in between, the judge reads it again and tries once more. The commit message ends with `[skip ci]`, so a workflow the repository starts on every push stays off a tree of two JSON files. The next run of the workflow keeps JUDGE.json. JUDGE.json names no repository, so the push can only go to origin, and origin must be the repository judged: the judge compares the two before it reads a pull request and refuses `--push` when they differ (a clone of another project, or a fork clone whose gh default is the upstream), so a mismatch costs nothing; run it in a clone of the repository judged.
- `push` sends a JUDGE.json already written (`--out`, default ./JUDGE.json) after the same origin check, without judging again: after a push the judge gave up on, which its last words name, or after a run kept without `--push` so the file could be read first. `--repo` names the repository the file was judged for, as `judge --repo` did. The file must be one the judge wrote, since the branch takes its aggregates and nothing else.
- `--repo`, `--window-days` and `--out` change what the defaults say (the repository gh sees here, 30 days, ./JUDGE.json, which .gitignore keeps out of commits).

## Who reads the files

OpenSpineConsortium's collector lives in the private repository OpenSpineConsortium/symphony-app. Once a day, at 04:17 UTC, after this repository's run at 03:43, it lists the repositories that installed the Symphony App, reads METRICS.json and JUDGE.json at the ref `metrics` of each and no other path, keeps only those whose sharing is on, and stores each day's files under HMAC-SHA256 of the repository's node id with a salt only the collector holds, never under the repository's name. A repository whose switch is off shows the collector `"sharing": "off"` and nothing more. A repository without the App is never read; its branch `metrics` is written all the same and stays the project's own record.

## The branch and the rules

.github/workflows/metrics.yml writes the branch the way the board's workflow writes `board`: one commit built from the files alone, which replaces the branch with `--force-with-lease` naming the commit the run read, so a judge's push that landed meanwhile makes the lease fail, and the run reads the branch again, keeps the new JUDGE.json and tries once more. It replaces only a branch that holds nothing but METRICS.json and JUDGE.json: a branch `metrics` with any other file is the project's own, there before the workflow came (a repository that adopted the template, or an owner who started one), and replacing it would lose it, so the run prints those files, pushes nothing and fails. Rename that branch (`git branch -m metrics NAME` in a clone, then push NAME and delete `metrics`, or the repository's branches page) and the next run starts a branch `metrics` of its own. A ruleset must therefore target only the default branch, as docs/setup/github.md says for `board`: one over all branches would refuse the run's push and leave the metrics stale. CI's push trigger leaves the branch out (.github/workflows/ci.yml), since the judge's push, made with a person's credentials, would otherwise start the checks on a tree that holds two JSON files, and the judge's commit message ends with `[skip ci]`, which keeps any other workflow a repository starts on every push off that tree too.

The workflow is skipped in the template repository itself, wherever the marker folder .template/ still is, and in a fork, since a fork made with gh or the API carries the original's branch `metrics`, frozen on the day it was made, and a run there would write metrics of the fork's own beside the original's JUDGE.json. It names no secret but GITHUB_TOKEN, so it runs in crowd mode as anywhere (docs/setup/crowdsourcing.md), and the judge, like everything else there, runs on the maintainer's own Claude account.
