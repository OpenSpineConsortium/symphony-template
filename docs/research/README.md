# Research

This folder holds the project's running research programmes: for each, the question, the instrument that measures it, the measurements taken with it and what they found, kept beside each other so that a reader can go from a claim to the record it rests on and to the command that made it, which reproduces it wherever what it read is kept. One folder per programme, with a README that says where the programme stands, and one file per finished note. A programme lives here while its questions are open and stays here when they are settled, as a note does; a pull request that settles a finding for good may move it to docs/history/, the longer record, and a fact every session should know becomes a memory in docs/memory/ that points here (.claude/rules/research.md).

Three rules hold in every programme, taken from OpenSpineConsortium/coordbench, where the project measured coordination first:

- A measurement is taken by code, deterministic and tested, from records the work leaves behind; a model judges only when the owner runs it on purpose, and never on an API key.
- A run that spends tokens or money waits for the owner's word and the number: how many runs, of what, at about what cost. Nothing here starts a run by itself; a schedule, where one exists, is a fallback and never the only trigger.
- A record carries counts, bytes, seconds and tokens, with tool names and model names, and never a path, a command, a prompt, a title or any text of a conversation, so it can be committed and shared. Transcripts and logs stay where they were written.

Programmes:

- [beyond-cooperation](beyond-cooperation/README.md): what one agent spends, context, tool calls, reading and time, and how to spend less, measured with tools/profile.py, with MAST's failure taxonomy as the outcome side.
- [flowbench](flowbench/README.md): the workflow as a plug-in, on SWE-bench Verified: whether Symphony's flow (an issue claimed by its branch, a draft pull request, a review by three lenses, an answer to every finding) resolves as many issues as the owner's map-reduce script and as one agent alone, and at what cost in tokens and time; these notes say where it stands, and the benchmark itself, the design, the pre-registered plan, the parity with SWE-bench row by row and a tested harness that scores through SWE-bench's own harness in the published images, rehearsed end to end, is its own repository, OpenSpineConsortium/flowbench; no agent has run on the owner's tokens yet, and the pilot waits for the owner's word.

## Notes

A note is one finished piece of research, a study, a comparison, a deep-research run or a fact-check, kept here across checkpoints so it accumulates in the repository rather than in one account's Project (.claude/rules/research.md). Each opens by naming its source: the thread, the date and the doc, artifact or upload it came from.

- [Symphony in brief](symphony-in-brief.md): the tl;dr of 2026-10-14, how Symphony works, what it guarantees and does not, and where it sits against CooperBench and other agent coding work; its numbers are those of that evening.
- [Native git plus DeLM for agents that reuse verified results](git-and-delm-for-verified-results.md): the deep research of 2026-10-15 on git notes keyed by tree, compare-and-swap refs and merge-tree as the primitives for parallel agents that reuse verified results, DeLM's check receipt as the key worth taking, a proposed coordbench arm, and why a run with no stored credential rules out DeLM's harness and coordbench's drivers as they stand.
- [Symphony versus competitors](symphony-versus-competitors.md): the comparison of 2026-10-16, built on the taxonomy spec and manual and exported from its Claude Doc, with its placement figure (symphony-versus-competitors-figure.svg): who Symphony is compared with, two head-to-head tables, seven claims where it is better by design, each graded, nine places where it is not or not yet, what not to claim, and a paragraph for each audience.
- [The Symphony control panel and what Symphony costs](control-panel.md): the notes of the thread "Symphony control website" (item 7 of the 2026-10-15b handoff), written 2026-10-16 and kept current as the work goes on: the ask, the answer in short, where the panel lives and what it does, its design decisions, the cost comparison, the checks and reviews, and what waits on the owner.
- [Outside code bases](outside-code-bases.md): the assessment of 2026-10-16, in the thread "Integrating outside code bases", of the four code bases the owner named (delm-agent-plugin, Claim Plane, HyperAgent, autonomous-software-agent) and of the git-native candidates in the note above: none taken as a library and no code copied, DeLM's check receipt and Claim Plane's pre-write admission measured first as coordbench arms, Claim Plane's published gain matched by its own serial arm, and the order the steps wait in.
- [The token wizard's checks](token-wizard-checks/README.md): the probes, the wrap fuzz and the mutants the thread "Claude token setup wizard" and its reviewers ran against scripts/tokens.py on 2026-10-16, each with the commit it was written against and what it showed there, kept so that a later session can run them again.
- [The token wizard](token-wizard.md): the notes of the thread "Claude token setup wizard" (item 11 of the 2026-10-15b handoff), written 2026-10-16: how Claude tokens were taken before, what claude setup-token and gh do, why scripts/tokens.py runs the sign-in behind a pseudo-terminal of its own and stores each account's token as an Actions secret without showing it, the checks, the two adversarial review passes and what changed for them, and what stays open.
- [Beethoven's worker and Claude projects](beethoven-worker-opening.md): the notes of the thread "Beethoven worker opening" (item 9 of the list the owner gave the project chat on 2026-10-15), written 2026-10-16: why a Claude project cannot take the session Beethoven's worker starts and reaches the worker only through its own Work locally, what the worker runs today, what claude.ai's documentation says, the owner's goal feature by feature, what Beethoven 21.0.0 changes, and what is not yet measured on the grid.
- [The WSU grid and GitHub Actions](wsu-grid-and-github-actions.md): the study of 2026-10-16, in the thread "Symphony on the WSU grid" (item 10 of the 2026-10-15b handoff), of whether Beethoven can run Symphony's Actions on Wayne State's grid and bring the logs back: the answer, a self-hosted runner served as a chain of Slurm jobs that points from the grid out; what was measured and where; the two directions weighed; what was built, in hpcworker and here; what the grid has not yet shown; and the ssh gate, which waits on the owner's test that a key alone signs in from outside the VPN.
- [How long a claim waits](claim-waits-in-a-real-copy.md): the measurement of 2026-10-16, in the thread "Protocol fixes toward 0.5.0" (item 5 of part 2.1 of the 2026-10-15b handoff, the second of the measurement pass's three pull requests), of the field metrics' three waits on a private copy of the owner's, from the copy's own metrics record, recomputed by the template's collector: 84 seconds from a claim commit to its draft, a lower bound on what a claim costs, and 9.6 minutes from opening to merge, by median over the copy's first four days, with no review to measure; where the figures come from, what they do and do not say, and how to measure again.

## Research kept elsewhere in this repository

Written before this folder existed and left where its links point:

- docs/checkpoints/2026-10-14/handoff-page/: the files of the handoff page of 2026-10-14, RESEARCH-scale.md, DESIGN-runtime.md, DESIGN-qa-gate.md, PLAN.md, free-or-paid.md and the patch template-crowd-number-of.patch.
- docs/checkpoints/2026-10-14b/notes/ (gh-aw against Symphony, read both ways) and docs/checkpoints/2026-10-14b/plans/gh-aw-migration-plan.md.
- docs/checkpoints/2026-10-14c/notes/readiness-research-2026-10-14.md, with the coordbench review notes under docs/checkpoints/2026-10-14c/notes/, 2026-10-14d/notes/, 2026-10-14e/notes/ and 2026-10-15/notes/.
- docs/checkpoints/2026-10-14c/deep-lane/ and docs/checkpoints/2026-10-14e/deep-lane/: the validation harness's deep lane, its review findings and the scripts that ran it.
- docs/checkpoints/2026-10-15b/taxonomy/: the spec and the manual of the coordination landscape, with the research notes and the reference work behind them; and docs/checkpoints/2026-10-15b/protocol-fixes/: the protocol fixes' third-review findings.
- docs/history/split-research/ and docs/history/crowdsourcing/research.md: the research behind the split into five repositories and behind crowd mode.

## Research in the project's other repositories

- OpenSpineConsortium/coordbench: docs/research.md (CooperBench's paper, read and verified), PARITY.md, bench/cooperbench/PLAN.md (the pre-registered run) and bench/cooperbench/results/curse-of-coordination-notes/ (the experiment's notes and figures).
- OpenSpineConsortium/flowbench: DESIGN.md, PLAN.md (the pre-registered run) and PARITY.md, with the harness they describe; the programme's notes are docs/research/flowbench/ here.
- OpenSpineConsortium/symphony-protocol: validation/ (DESIGN.md, GUARANTEES.md and the harness's findings).
- OpenSpineConsortium/spine-program: 01_carm_level_detection/grants/aidas_2027/ (the grant's record, evidence and review notes).

## Outside git, by link

A Claude Doc or an artifact belongs to one account and is read by link; what a session could export is above.

- "Symphony versus competitors" (https://claude.ai/code/artifact/a1cb9900-9020-49ec-8d96-6781a0d3a523), a Claude Doc of 2026-10-16 built on the taxonomy spec and manual; it supersedes "Symphony in brief" where the two differ, and its copy is the note above.
- The taxonomy spec (https://claude.ai/code/artifact/9ed6238d-6b5e-4a7e-acb5-df360435c19c) and manual (https://claude.ai/code/artifact/c42e4d26-b238-4834-bb7b-318ae086152c), Claude Docs of the other account; their Markdown copies are under docs/checkpoints/2026-10-15b/taxonomy/.
- The handoff page of 2026-10-14 (https://claude.ai/artifact/XQj71up9dbJhwSStCVUe9T); its files are under docs/checkpoints/2026-10-14/handoff-page/.
