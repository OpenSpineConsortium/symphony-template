Field metrics: .github/workflows/metrics.yml writes the protocol's aggregates, never a name or any text, to METRICS.json on the branch metrics daily with GITHUB_TOKEN alone; a maintainer's judge adds App F counts as JUDGE.json; .github/sdlc-metrics or the variable SDLC_METRICS turns sharing off.

tools/metrics.py collect reads the last 30 days of pull requests, reviews,
check runs, claude/<n> branches and comments from the REST API and writes
counts, medians and 90th percentiles in seconds, and two rates, under the
keys docs/setup/metrics.md lists and no other; tests/test_metrics.py fails
when a key, a name, a title, a branch or a body from its fixtures reaches
the file. Off from the file or the variable writes {"schema":
"sdlc-metrics/1", "sharing": "off"} and calls no API.

The branch metrics is written like board: one commit from the files alone,
pushed with --force-with-lease naming the commit the run fetched, so the
JUDGE.json a maintainer pushed meanwhile is kept, never lost; a ruleset
must leave the branch out, and CI's push trigger leaves it out. The judge
(`python3 tools/metrics.py judge`) runs only on a maintainer's machine, with
their own gh and their own `claude -p` on their own subscription, refuses
while ANTHROPIC_API_KEY is set, sends each pull request's conversation
(people as A, B, C) only to that local claude, keeps codes only, and pushes
JUDGE.json as an ordinary commit the push guard lets through.

Two conventions the counts rest on: the coordinator routine starts each
release comment with `<!-- sdlc-coordinator: claim-released -->` (both
coordinator prompts carry it), and the board's "main moved" comment says
"conflicting with" for a conflict; change either and metrics.py with it.
OpenSpineConsortium's collector, in sdlc-app, reads only the two files at
the ref metrics of repositories that installed the OpenSpine SDLC App and
stores them under a salted hash of the repository.
