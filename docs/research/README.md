# Research

This folder holds the project's running research programmes: for each, the question, the instrument that measures it, the measurements taken with it and what they found, kept beside each other so that a reader can go from a claim to the record it rests on and to the command that made it, which reproduces it wherever what it read is kept. One folder per programme, with a README that says where the programme stands. docs/history/ is for what a piece of work found and settled; a programme lives here while its questions are open, and a settled finding goes to docs/history/ or, when every session should know it, to docs/memory/.

Three rules hold in every programme, taken from OpenSpineConsortium/coordbench, where the project measured coordination first:

- A measurement is taken by code, deterministic and tested, from records the work leaves behind; a model judges only when the owner runs it on purpose, and never on an API key.
- A run that spends tokens or money waits for the owner's word and the number: how many runs, of what, at about what cost. Nothing here starts a run by itself; a schedule, where one exists, is a fallback and never the only trigger.
- A record carries counts, bytes, seconds and tokens, with tool names and model names, and never a path, a command, a prompt, a title or any text of a conversation, so it can be committed and shared. Transcripts and logs stay where they were written.

Programmes:

- [beyond-cooperation](beyond-cooperation/README.md): what one agent spends, context, tool calls, reading and time, and how to spend less, measured with tools/profile.py.

The threads at work on 2026-10-16 (agentic workflow benchmarks, the control website's cost comparison, Symphony on the WSU grid, the Claude token setup wizard, the Beethoven worker opening, the integration of outside code bases) each add their programme or note here in their own pull request as it lands.

## Notes

A note is one finished piece of research, a study, a comparison, a deep-research run or a fact-check, kept here across checkpoints so it accumulates in the repository rather than in one account's Project (.claude/rules/research.md). Each opens by naming its source: the thread, the date and the doc, artifact or upload it came from.

- [Symphony in brief](symphony-in-brief.md): the tl;dr of 2026-10-14, how Symphony works, what it guarantees and does not, and where it sits against CooperBench and other agent coding work; its numbers are those of that evening.
- [Native git plus DeLM for agents that reuse verified results](git-and-delm-for-verified-results.md): the deep research of 2026-10-15 on git notes keyed by tree, compare-and-swap refs and merge-tree as the primitives for parallel agents that reuse verified results, DeLM's check receipt as the key worth taking, a proposed coordbench arm, and why a run with no stored credential rules out DeLM's harness and coordbench's drivers as they stand.
- [Symphony versus competitors](symphony-versus-competitors.md): the comparison of 2026-10-16, built on the taxonomy spec and manual and exported from its Claude Doc, with its placement figure (symphony-versus-competitors-figure.svg): who Symphony is compared with, two head-to-head tables, seven claims where it is better by design, each graded, nine places where it is not or not yet, what not to claim, and a paragraph for each audience.

## Research kept elsewhere in this repository

Written before this folder existed and left where its links point:

- docs/checkpoints/2026-10-14/handoff-page/: RESEARCH-scale.md, DESIGN-runtime.md, DESIGN-qa-gate.md, PLAN.md and free-or-paid.md, the files of the handoff page of 2026-10-14.
- docs/checkpoints/2026-10-14b/notes/ (gh-aw against Symphony, read both ways) and docs/checkpoints/2026-10-14b/plans/gh-aw-migration-plan.md.
- docs/checkpoints/2026-10-14c/notes/readiness-research-2026-10-14.md, with the coordbench review notes under docs/checkpoints/2026-10-14c/notes/, 2026-10-14d/notes/, 2026-10-14e/notes/ and 2026-10-15/notes/.
- docs/checkpoints/2026-10-14c/deep-lane/ and docs/checkpoints/2026-10-14e/deep-lane/: the validation harness's deep lane, its review findings and the scripts that ran it.
- docs/checkpoints/2026-10-15b/taxonomy/: the spec and the manual of the coordination landscape, with the research notes and the reference work behind them; and docs/checkpoints/2026-10-15b/protocol-fixes/: the protocol fixes' third-review findings.
- docs/history/split-research/ and docs/history/crowdsourcing/research.md: the research behind the split into five repositories and behind crowd mode.

## Research in the project's other repositories

- OpenSpineConsortium/coordbench: docs/research.md (CooperBench's paper, read and verified), PARITY.md, bench/cooperbench/PLAN.md (the pre-registered run) and bench/cooperbench/results/curse-of-coordination-notes/ (the experiment's notes and figures).
- OpenSpineConsortium/symphony-protocol: validation/ (DESIGN.md, GUARANTEES.md and the harness's findings).
- OpenSpineConsortium/spine-program: 01_carm_level_detection/grants/aidas_2027/ (the grant's record, evidence and review notes).

## Outside git, by link

A Claude Doc or an artifact belongs to one account and is read by link; what a session could export is above.

- "Symphony versus competitors" (https://claude.ai/code/artifact/a1cb9900-9020-49ec-8d96-6781a0d3a523), a Claude Doc of 2026-10-16 built on the taxonomy spec and manual; it supersedes "Symphony in brief" where the two differ, and its copy is the note above.
- The taxonomy spec (https://claude.ai/code/artifact/9ed6238d-6b5e-4a7e-acb5-df360435c19c) and manual (https://claude.ai/code/artifact/c42e4d26-b238-4834-bb7b-318ae086152c), Claude Docs of the other account; their Markdown copies are under docs/checkpoints/2026-10-15b/taxonomy/.
- The handoff page of 2026-10-14 (https://claude.ai/artifact/XQj71up9dbJhwSStCVUe9T); its files are under docs/checkpoints/2026-10-14/handoff-page/.
