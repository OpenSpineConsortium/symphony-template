Stale-branch statistics: tools/staleness.py reads GitHub's history into per-pull-request catch-ups, redone check runs and stale wall-clock, and .github/workflows/staleness.yml adds a record to the branch staleness after every merge.

The record (STALENESS.json, SNAPSHOTS.jsonl, REPORT.md on the branch
staleness) is rebuilt from GitHub's own timelines and the check
workflow's runs, so it needs no server and no Claude run. Each snapshot,
taken when a pull request merges into the default branch, keeps GitHub's
word on every open pull request (behind, dirty, mergeable) and whether
the up-to-date rule is on, which dates a change of the rule without the
ruleset history an administrator alone may read. A catch-up is a merge
of the default branch into a branch; a run is redone when its head is a
catch-up; a branch is a claim when it is claude/<issue>. The findings of
2026-10-20 and what history cannot recover are in
docs/research/stale-branch-failures.md.
