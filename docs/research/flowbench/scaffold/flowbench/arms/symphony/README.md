# The symphony arm

The issue under the claim protocol, kept locally for one instance: the
worker claims it as the branch claude/1 of the workspace, commits the
fix there and writes the pull request's description; a reviewer reads
the branch's diff through the same three lenses the script arm's
reviewers use (the same prompt file, held equal by tests/test_arms.py);
the worker answers every finding, changing the code or saying why not.
The patch is the branch's diff against the commit the workspace started
at, as for every arm.

## What is not here yet

The protocol's gate: in the design, the required check runs the
repository's tests of the modules the diff touches, the merge gate merges
on a green check, and the protocol library (sdlc_protocol.gate over its
bare-git adapter, vendored as coordbench vendors it for its sdlc arm)
decides what a worker may push and when the pull request lands. The
scaffold runs the three stages in order with no gate between them, so
what it measures today is the protocol's shape (a claim, a pull request,
a review by lenses, an answer to every thread), not its enforcement. The
gate wiring is coordbench's sdlc arm's, to be carried over before a
measured run; until then PARITY.md's rows for this arm say "shape only".

The other half of the design, symphony-github, runs the same flow on
GitHub itself with the template's workers in Actions, one scratch
repository per instance; it is designed and not scaffolded, since it
needs the repository and the owner's account slots first.

## One round

One review round: work, review, answer. A second round (the reviewer
reads the answers and asks again) is a repeat of the review and answer
stages, which stages.json can list twice under names of its own
(review-2, answer-2) once the first round's numbers say it is worth its
cost.
