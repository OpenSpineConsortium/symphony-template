# Team mode: a lead and its members

Team mode runs several Claude members on one piece of work at once, the
way the best-scoring arm of CooperBench's own later ablation did: a team
with a lead, a shared task list and a shared scratchpad (62%, against 56%
for coop on a shared git remote, 48% solo and 26% for agents that could
only message each other; one model, 50 task pairs, one seed, not peer
reviewed). The ablation's team mode is cooperbench/CooperBench's
src/cooperbench/team_harness/prompt.py; this page is the same idea on
GitHub's own primitives, and the claim protocol (PROTOCOL.md) holds
throughout.

| CooperBench team mode | Here |
| --- | --- |
| The lead's PLAN.md: who owns which files, the interfaces between them | The plan the lead writes into the epic issue |
| A task list pre-seeded with one task per member | Sub-issues of the epic, labelled todo and agent:<member> |
| Claiming a task | Pushing its branch claude/<issue>, as for any claim |
| The shared scratchpad and messages | Comments on the epic |
| The shared git remote: fetch and merge each other's branches | Every claim branch is on origin; finished work merges to the default branch on a green check |
| The lead's integration checklist | The lead's last pass over the integrated default branch |

## The lead (the chief of staff)

Labelling an issue `epic` starts it (.github/workflows/claude-lead.yml).
The lead reads the epic and the code, then plans to avoid collisions: at
most one task per member, each owning a disjoint set of files, and where
two tasks meet, the interface between them written into both, so each
member can build against it before the other lands. It returns the plan
as JSON; tools/team.py, not Claude, writes it into the epic, opens the
tasks pre-assigned to the members named in CLAUDE_TEAM, and starts them.
When the last task closes, the lead runs once more, to integrate: it
checks the default branch as a whole (`bash scripts/check.sh` and the
tests the epic names), fixes on its own claim branch whatever the pieces
broke together, and closes the epic. Integration is the point of the
job: every task can pass alone while the whole fails.

## The members

Each member (.github/workflows/claude-worker.yml, one leg per name in
CLAUDE_TEAM, in parallel) asks tools/team.py what to do and runs Claude
only when there is something: its own claim that needs work, else its
pre-assigned task, else any unassigned todo. A member:

1. reads the epic's plan first and stays inside the files its task owns;
2. claims its task as PROTOCOL.md says, with its name on the claim file's
   Account line;
3. looks at its peers' branches on origin while it works, so its code
   meets theirs at the agreed interfaces instead of colliding with them;
4. brings the default branch in by merging it when it has moved, which
   needs no forced push;
5. when stuck on something only a peer or the lead can settle, labels its
   task `blocked` and says what it needs on the epic;
6. finishes as PROTOCOL.md says and turns on auto-merge, so the pull
   request lands by itself once the check named "check" passes.

A leg that still has work dispatches itself again, up to CLAUDE_MAX_ROUNDS
rounds in a row (6 if unset); the six-hourly schedule picks up whatever is
left. A claim that only waits for its checks or its merge costs no run.

## Turning it on

docs/setup/claude-action.md, "Team mode", lists the switches: the
repository variables CLAUDE_TEAM (the members, as a JSON list such as
["w1","w2","w3"]) and CLAUDE_WORKER, "Allow auto-merge" in the
repository's settings, and the Claude GitHub App with the subscription
token. Every member and the lead draw on the same subscription's usage
window, so a team of three spends it about three times as fast as one
session; a Max plan suits a team better than Pro.
