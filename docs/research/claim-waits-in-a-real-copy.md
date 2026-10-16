# How long a claim waits: the three waits measured in a real copy

Measured on 2026-10-16 in the thread "Protocol fixes toward 0.5.0", for item 5 of part 2.1 of the 2026-10-15b handoff, the measurement pass, which is three pull requests: the API calls of one board run (symphony-protocol#38, whose figures are the library README's "What a board run costs"); these three waits, the claim-to-first-pull-request, open-to-merge and first-review medians from a real copy; and retry on GitHub's rate limits in the library, which comes next. No Claude Doc, artifact or upload lies behind this note: the figures come from GitHub's API, read by the template's own collector, tools/metrics.py, on a repository where real sessions claim real issues. The readiness research of 2026-10-14 had found the three waits defined by the field metrics and no figure for them recorded anywhere (docs/checkpoints/2026-10-14c/notes/readiness-research-2026-10-14.md).

## The answer

On OpenSpineConsortium/spine-program, over the 30 days to 08:29:47 UTC on 2026-10-16:

| Wait | Pull requests | Median | p90 | Middle half | Longest |
| --- | --- | --- | --- | --- | --- |
| Claim to first pull request | 38 | 84 s | 90 s | 54 s to 86 s | 17,496 s (4.9 h) |
| Open to merge | 37 | 576 s (9.6 min) | 12,921 s (3.6 h) | 474 s to 1,618 s (27 min) | 18,660 s (5.2 h) |
| First review | 0 | none | none | none | none |

A session's draft pull request opens about a minute and a half after its claim commit, and the pull request merges about ten minutes after it opens, a quarter of them after more than 27 minutes and a tenth after more than three and a half hours. Nothing reviewed any pull request there, so the third wait has no value on this copy.

## Where the figures come from

- The copy. spine-program runs the protocol from the template's files, .github/workflows/board.yml, metrics.yml, protocol.yml and tidy.yml, with tools/VENDORED naming sdlc-protocol 0.4.1 at 438844f; its sessions claim an issue by pushing the branch claude/<n> and open the draft at once, as docs/agents/PROTOCOL.md says. Of the 39 pull requests opened in the window, 38 came from claim branches; of the 37 merged in it, 36.
- The record. The copy's own metrics workflow wrote METRICS.json to its branch metrics at 08:29:47 UTC (the record's generated_at), over the 30 days before; the medians and p90s above are that record's durations_seconds.
- The recomputation. The template's collector, tools/metrics.py at main 918193e, run on the copy with `--now` at the record's time, wrote the same six figures, in 265 calls of the session's own token and none of the copy's GITHUB_TOKEN. It is a newer collector than the copy's, and it counts 41 claims where the copy's counted 38 and 6 sessions where it counted 7; the waits are the same.
- The counts and the spread. The column of pull requests, the middle half and the longest come from the short script under "How to measure again", which takes the same lists the collector takes its medians from (claim_waits, merge_waits and review_waits) and only counts and sorts them. The medians and p90s are the collector's, which its tests hold; the script is not tested.

## What each wait measures there

- Claim to first pull request: from the claim's time, the earliest author date among the pull request's commits, which on a claim branch is the claim file's own commit, to the draft's opening, once for each claim whose pull request opened in the window. It is what a claim costs in a session's time: the claim commit, its push, the labels, the plan as a comment and the draft. The middle half of the claims took 54 to 86 seconds and the shortest 8; one draft opened 4.9 hours after its claim commit.
- Open to merge: from the opening to the merge, for each pull request merged in the window. Since a claim opens its draft at once, this is the work itself, from the draft to a green check and the merge, and not a wait the protocol adds. The check passed on its first run on every pull request whose first run counted (the record's first_check_pass_rate is 1.0, with 130 check runs passed and none failed), and every pull request that ended in the window merged (merge_rate 1.0).
- First review: from the opening to the first review by anyone but the author. None of the 42 pull requests changed in the window carries a review of any kind, the author's own included: the copy's sessions merge once the check is green, on the owner's standing permission. The wait can be measured only on a copy where someone, or something, submits reviews.

## What the figures do and do not say

- One copy and one month, the work of two people's sessions, with up to five pull requests at work at one moment (the record's parallel block): a sample of one, not a figure for copies in general.
- The waits are the pace of Claude Code sessions, not of a person.
- 84 seconds is the claim's cost in a session's wall time, measured where it had only been defined. With the board's calls per run, it answers the time half of the question the taxonomy spec asks as R3, what one coordination step costs (docs/checkpoints/2026-10-15b/taxonomy/spec.md), for this one copy.
- Work beside other work was no slower here: the record's coordination block, which splits the merged pull requests into 6 done alone and 30 done beside other open work, gives open-to-merge medians of 593 and 584 seconds, a latency ratio of 1.02.

## How to measure again

1. Read the copy's own record: `gh api 'repos/OpenSpineConsortium/spine-program/contents/METRICS.json?ref=metrics' --jq .content | base64 -d`.
2. Recompute it at the record's time with the template's collector, from a checkout of the template and with GITHUB_TOKEN set to a token that may read the copy: `python3 tools/metrics.py collect --repo OpenSpineConsortium/spine-program --out METRICS.json --now 2026-10-16T08:29:47Z`.
3. The counts and the spread, from the same checkout with the same token, by this script, which printed the table's figures in 233 calls:

```python
import os, statistics, sys
sys.path.insert(0, "tools")
import metrics

window = metrics.Window.ending(metrics.parse_time("2026-10-16T08:29:47Z"), 30)
api = metrics.Budgeted(os.environ["GITHUB_TOKEN"], "OpenSpineConsortium/spine-program")
facts, _claims, _comments, _rest = metrics.read_repository(api, window)
opened = [f for f in facts if window.holds(metrics.time_of(f.pull, "created_at"))]
merged = [f for f in facts if window.holds(metrics.time_of(f.pull, "merged_at"))]
for name, values in (("claim to first pull request", metrics.claim_waits(opened)),
                     ("open to merge", metrics.merge_waits(merged)),
                     ("first review", metrics.review_waits(opened))):
    ordered = sorted(values)
    quartiles = statistics.quantiles(ordered, n=4, method="inclusive") if len(ordered) > 1 else ordered * 3
    print(f"{name}: n={len(ordered)} median={metrics.median_seconds(ordered)} p90={metrics.p90_seconds(ordered)}"
          f" quartiles={[round(q) for q in quartiles[::2]]} longest={ordered[-1:]}")
print(f"{len(facts)} pull requests read, {sum(len(f.reviews) for f in facts)} reviews, {api.calls} calls")
```

A later window moves every figure. The copy's metrics workflow replaces its branch metrics with one new commit each time it runs, so the record of 08:29:47 UTC goes with the next run and this note keeps its figures; the recomputation with `--now` at that time gives them again from GitHub for as long as nothing changes on the pull requests it reads, a review added to one of them included.
