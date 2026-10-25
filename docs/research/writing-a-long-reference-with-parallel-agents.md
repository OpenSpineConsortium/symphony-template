# Writing a long reference with parallel agents

The thread "Finish the SchwingNet textbook", 2026-10-24. The book itself and its method files stay in the private SchwingNet repository (docs/research/artifact-textbook/writing/ there); this note keeps only what carries to any project: how one session wrote and reviewed a reference of thirty-two chapters, about 6,000 words each, with subagents, and what that taught. No number or content of the book is here.

## The shape that worked

- One writer brief and one reviewer brief, both files every agent reads first, with the house rules in one place: each chapter's closing sections, the grades a statement may carry (Measured, Reported, Inferred, Unverified), which part may hold what, how people are named, and how an unsettled figure is quoted. A rule that lives only in a prompt drifts between agents; a rule in the brief does not.
- A short prompt per chapter that names the chapter's entry in the plan and its sources, and nothing else.
- A lint script every agent runs on its own chapter before it reports: the closing sections present, every link resolving inside the repository, every grade one of the four, the length under a ceiling, and the shapes of private data (addresses, logins, machine paths). Agents fix what the lint names, so the coordinator reads only reports.
- A writer and a separate reviewer for every chapter. The reviewer is told to check each statement against the source it cites and to mend the chapter in place, and reports counts by kind of fault and the three most serious faults.
- A cross-book pass after the per-chapter reviews: recurring figures checked in every chapter for the same value, grade and unsettled mark. Single-chapter reviews cannot see this, and it found faults in fourteen chapters.
- Then the project's own mechanical check (here, the site build's check of every chapter against a ledger of settled figures) read entry by entry. It flagged 144 passages, of which 11 were real: a script's flags are a list for a reader, not a list of edits.

## What the reviews found

The faults were the same kinds in almost every chapter, in this order of frequency: a figure the record holds open quoted as current; a grade above what its source supports (a figure copied from a summary page graded as measured); a misreading of the record (two things merged into one, a plan read as built, a range that takes in items it should not); content in a part of the book where the rules forbid it; gendered pronouns for a person whose pronouns are not stated. Writers told about a fault kind in their prompt made it less often, so the brief should name each kind once a review has found it.

A reviewer can be wrong too: one reported that no source held a figure's fraction, and the source cited held it. A reviewer's claim that something is missing is checked before it changes other chapters.

## The budget

- At most eight agents at a time, the owner's choice; one over the cap happened once, from launching before a finished agent's notice arrived, so a count of running agents is kept by the coordinator and checked before each launch.
- A writer took about 5 to 10 minutes and a reviewer 4 to 11, each about 220 to 330 thousand tokens of context at its last turn (which is context, not spend: docs/memory/subagent-token-figures-are-context-not-spend.md).
- A commit script that lints, adds only the book's folders, commits with the session's trailers and pushes kept every finished chapter on the branch within a minute. Since it adds the whole folder, it also committed chapters still being edited; harmless on a draft branch, but a commit that must hold only finished work names its files.

## Pitfalls met

- A lint that resolves links against a fixed path needs a real checkout there: a symbolic link to a clone broke path resolution, and a git worktree at that path fixed it. Tools kept for reuse take the repository root from their own location instead.
- A weekly usage limit stopped every agent mid-chapter once; the handoff written then was stale by the time the work resumed (drafts it called unfinished were finished), so a resumed thread reads the branch before the handoff's list.
