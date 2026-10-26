# The grid word `schwingnet bordercall <stage>`

The thread "Finish CNS slides with junction predictor", 2026-10-26. No link: the owner's prompt
was written into the project chat and the work is in SchwingNet and bordercall, both private.

## What the word is

`schwingnet-bordercall-<stage>`, stage `pilot` or `full`, is a fixed job word of
.github/workflows/grid-accounts.yml's action `job` (scripts/grid-accounts.sh), passed through
hpcworker's gate to SchwingNet's grid/gate.sh as the word `bordercall <stage>`, where it queues
one CPU batch job. The owner's count of 2026-10-25 23:56 UTC is two CPU jobs, a pilot over a
few hundred countable cases first and then the full corpus; the gate refuses `full` until the
pilot's report ends well, refuses a stage it does not know, and queues no second job of a
stage while one is live. Everything the job does, and what it found, is SchwingNet's
(docs/research/bordercall-corpus.md there), confidential until the filing.

## Why a word of its own

The anomaly route of SchwingNet #391 went through the same pass-through (#491 here, 2026-10-25)
as `anomaly <stage>`; the bordercall measurements are a job of their own, with their own stages
and their own refusal rules, so they take a word of their own rather than a stage of the anomaly
word, and the regex in scripts/grid-accounts.sh names it beside `anomaly`. The test
tests/test_grid_accounts.py holds the accepted spellings (`schwingnet-bordercall-pilot`,
`schwingnet-bordercall-full`) and the refused ones (no stage, a capital, two stages, a space).

## What remains the owner's

Sending the word. The status word (`schwingnet-status`) is read first, once, as the standing
grid rule says, and `update` goes first after hpcworker's side of the pass-through merges, so
the gate's clone carries the new word before it is asked for.
