# Where the Actions minutes went on 2026-10-25

Source: the thread "Write project handoff for new account" in the claude.ai project "symphony3", 2026-10-25. At 16:03 UTC the owner wrote that the organization was out of GitHub Actions minutes, with its spending budget at $0. The numbers below come from the Actions jobs API of OpenSpineConsortium/SchwingNet and OpenSpineConsortium/symphony-template for that day, read by the session at about 16:10 UTC. GitHub's billing API is refused to a session, so billed minutes are estimated the way GitHub bills them: each job's run time, rounded up to a whole minute. Skipped jobs and self-hosted runners are left out. The price is $0.006 a minute for a Linux 2-core runner past the included quota (docs/setup/free-or-paid.md, verified 2026-10-13).

## What stopped

Once the included minutes were used up, GitHub started no job on its own runners. Each job ended at once with no runner and no steps, and the annotation "The job was not started because recent account payments have failed or your spending limit needs to be increased". Nothing went green, so nothing merged. The board, @claude, the research loop and the grid words stopped as well, since grid-accounts.yml and grid-gate.yml run on ubuntu-latest before they reach the grid. A run that failed this way does not restart when minutes return; it is run again with `gh api -X POST repos/OWNER/NAME/actions/runs/ID/rerun-failed-jobs`.

At 16:26 UTC the owner chose a capped budget on a card. The other two options were a free self-hosted runner and waiting for the monthly reset. The cap is set on the organization's billing page under Budgets and alerts, or, where the $0 limit sits on the enterprise, on the enterprise's Billing and licensing page.

## Where the minutes went

SchwingNet ran about 4,330 billed minutes that day, and symphony-template about 1,250, so about $33 at the overage price. SchwingNet had run between 1,300 and 2,500 workflows a day since it began on 2026-10-20.

| Repository | Workflow | Billed minutes | Minutes of work | Runs |
|---|---|---|---|---|
| SchwingNet | gate, on pull requests | 1,572 | 1,535 | 78 |
| SchwingNet | gate, on main | 459 | 446 | 26 |
| SchwingNet | standards | 834 | 288 | 104 |
| SchwingNet | Checks | 645 | 471 | 152 |
| SchwingNet | Board | about 305 | about 160 | about 540 |
| SchwingNet | Docs | 151 | 119 | 113 |
| SchwingNet | Owner OK | 92 | 6 | 95 |
| symphony-template | Checks | 812 | 484 | 70 |
| symphony-template | Docs | 199 | 186 | 70 |
| symphony-template | Owner OK | 74 | 5 | 38 |

The table sums the jobs of the runs the session read at 16:10 UTC. Some of the gate's runs were missing from that read: the gate's own run list for the whole day has 85 runs on pull requests and 28 on main, about 1,760 and 540 minutes counted by run, and the paragraphs below use that list.

## Why

Four causes account for most of it.

- **A prover re-proving code nobody changed.** SchwingNet's gate runs CrossHair and Z3 over the package, and that lane was 31 of a run's 32 minutes. Its verdict depends only on the package, its gated tests, its configuration, its locked environment and the pinned beethoven-qa. Yet 76 of the day's 85 pull-request runs were on pull requests that changed none of those files, and they spent about 1,480 minutes. Only 2 of the 33 pull requests gated that day touched what the lane reads. Most changed research notes, dataset records, tools, grid scripts or the template's own tests.
- **Whole-minute rounding of short jobs.** GitHub bills each job by the whole minute. The standards workflow ran six groups of about 15 seconds each as jobs of their own, beside a seventh that waited for them and a Scorecard report, so a run cost eight billed minutes for under three of work. Owner OK's two jobs of a few seconds each cost two minutes for every pull request event.
- **Runs cancelled part-way.** 45 of the 85 pull-request gate runs, and 15 of the 26 on main, were cancelled by a newer push after running for a while. Their minutes are billed and their result is thrown away, about 730 minutes.
- **A burst of issues.** About 90 issues opened at 13:00 UTC started over 1,000 runs in an hour. Board, Experiment, Figure re-run, Workers and Tidy each start on every issue event. Most of these runs skip their job, but each that runs costs at least a minute.

## What was changed

- **SchwingNet's gate** asks GitHub for the newest commit of main it passed on a push. It runs the symbolic lane only where a change touches a path that lane reads since that commit: src/, tests/schwingnet/, vendor/, conftest.py, pyproject.toml, pixi.toml, pixi.lock or the workflow itself. Every other lane still runs. It also runs the lane in full once a day on main, by hand, and wherever the comparison cannot be made. Expected saving: about 1,800 of SchwingNet's 2,030 gate minutes a day. The change was written and tested in the thread, with eight scripted cases, actionlint and zizmor. It goes to SchwingNet by pull request from the thread's branch once SchwingNet #392 merges.
- **beethoven-qa 8.0.0** (beethoven-qa #13) runs the six standards groups as steps of the one required job, standards (every group green), and Scorecard on main and by hand only. That takes a run from eight billed minutes to about three, about 500 minutes a day in SchwingNet. A repository takes it with `python -m beethoven_qa vendor --into . --ref v8.0.0 --kit`. Since #13 changes a workflow file, the kit's automerge would arm it with GITHUB_TOKEN, whose merge starts no push workflow, so release.yml would not tag v8.0.0. It is merged by a person or a session once green.
- **Docs on the owner's call.** The Docs workflow rebuilt the site on every merge, about 350 billed minutes that day (151 in SchwingNet and 199 here). A daily build was first left out, since the owner's standing rule is that a schedule is never the only trigger. At 17:25 UTC the owner decided instead that Docs builds only when the owner starts it: docs.yml here and in SchwingNet keep only workflow_dispatch, with no push and no schedule. A page the site shows is then as old as its last run.
- **Checks on a head already checked.** SchwingNet's Checks re-ran in full on 39 of its 124 pull-request runs, on a head already checked: an edited body, a pull request marked ready or turned back to draft. Only the protocol and review-record checks read the body. On those three events each part of the template's Checks now asks GitHub first, with tools/earlier_pass.py and the run's own token (actions: read), whether the newest earlier run on the same head passed every part, and skips its work where it did. Only the newest counts, by when its latest attempt started, so an edit that changed the base branch, a re-run, or a run cancelled or still going, lets no older pass stand in for it. The parts are judged as one, since which tests a part runs comes from GitHub's test merge, and a moved base branch can move a failing test from one part into another (found by an independent review after #485 merged, and fixed in the pull request after it). A part then costs one billed minute instead of its tests, and the job check still holds the body to its rules. An edit that changes the base branch, any other event and any answer GitHub does not give run the parts in full. The earlier run checked the test merge with the base branch as it stood then, which is all a re-run on these events could add, and the check is not required to be up to date anyway. SchwingNet's Checks, one job, takes the same step by the name of its step that runs check.sh.

## Left as it is, and why

- **symphony-template's Checks in five parts.** Joining the parts would save the rounding on each, about 300 minutes a day. But it gives back the wall time the parts were split to save (docs/research/faster-backend-than-actions.md).

## What would cut more, not yet done

- The kit's pre-push hook runs the whole gate before every push, about 16 minutes of a session's time, even for a change to a note. beethoven-qa's own CI spends about 31 minutes on CrossHair per run. The same scope belongs in beethoven-qa, as an option of its gate command, so the hook and every consumer's CI read it from one place. beethoven-qa 9.0.0 (beethoven-qa #14, open on 2026-10-25) does it by module: `gate --base`, or BEETHOVEN_QA_BASE, which the kit's hook sets to auto, proves only the modules the change reaches, and none for a change to documents, data, tests or workflows.
- symphony-template's Docs build runs the whole test suite again for its Tests page, about 7 minutes a build, on the commit Checks has just tested. It could read Checks' results instead.
- Sessions that open many issues at once could open them in a quieter way, or the workflows that start on every issue event could leave the issue events they never act on.
