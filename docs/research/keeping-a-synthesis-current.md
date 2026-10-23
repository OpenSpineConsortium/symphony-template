# Keeping a synthesis current

The thread "SchwingNet textbook and critique reviews", 2026-10-23. A synthesis of the artifacts of the owner's accounts had been made in a private repository (SchwingNet #120, #136, #155): an inventory record per artifact, topic clusters, and the statements and figures two artifacts give differently, each with a reader's verdict. It took a day of reads by hand, and the owner asked for it to keep itself current: "make it extensible so i can update it as new knowledge is added or new datasets are added? do something clever with like dynamic updating, dynamic concept checking" (SchwingNet #166, pull request #167). The synthesis and everything it holds stay in that repository under its confidentiality rule; this note keeps the process alone: the shape that was built, how it was reviewed, what failed, and what to keep, so the next synthesis that must stay current is built the same way or better.

## The shape

1. A stamp says what every record was read from, by content and never by date: for each source folder the git tree of that folder at the commit its record was read at, for each structured record the hash of its bytes, and what was already known when the stamp was made, the quotes a text did not hold then and the checks already seen. A tree that differs from the stamp is a source that changed, whoever changed it and however; a date would have missed a rewrite that kept the date.
2. A look with no model runs on a push that changes a source, daily, and by hand. The daily run takes what no push started it for: the sources kept in another repository, and every change a merge by GitHub's auto-merge landed, since the repository arms auto-merge with the workflow token and GitHub starts no workflow for an event that token caused. It sets today's trees and hashes beside the stamp and names what is new, changed or gone; checks every verdict's and every record's quotes against today's texts by script, so a verdict whose words its page no longer holds is found without a reader; and checks every text against a ledger of settled figures, the counts the structured records give and the figures the verdicts settled, each with the words that say what it is a figure of. What it finds is written into one issue, rewritten in place, opened only when there is something to say and closed only when the look finds nothing at all.
3. A model reads only what the look cannot settle: a new or changed source, read into its record and then set against its cluster and the figures, and every stale or new verdict, read by a skeptic, a re-checker told to overturn the skeptic, and a judge where the two disagree, the same ladder the hand-made verdicts went through. Research notes and structured records are checked by script alone. A run reads at most a few sources and a set number of verdict items, a day takes a set number of runs that a repository variable can change within a ceiling, a variable switches every read off while the look still runs, and three failed runs in a row pause the runs a push or the schedule starts.
4. What a run read lands in one pull request, rebuilt each run as one commit on the default branch, opened by the organization's App so that the owner's tap on the deployment gate is asked for (owner-ok-deployment-gate.md), and merged by itself once green. A Reject is kept: no run builds on a pull request whose gate failed on its head. Where the default branch's rules do not require the gate, the pull request is a draft for a person to mark ready.
5. No code that is not on the default branch runs beside a secret. A run lays onto the default branch only the files a join writes, the records, the pages and the stamp, from the open pull request, and runs the default branch's tools; a pull request that changes anything else is named foreign and not built on. The job that learns which secrets are set checks nothing out, and the sessions' jobs name the model's token alone.
6. Every record is written in the layout its first reading wrote, so a run's diff holds only what changed; every text a run writes goes through the repository's scrub of what its rules keep out, and an answer holding an e-mail address, a phone number or a credential's shape is refused; and a run gives one answer whatever the hash seed, since `python3 -I` draws a new one in every process: nothing whose order reaches a result is a set left unsorted, and a test runs the checks under several seeds.

## How it was reviewed

The owner asked for adversarial reviews of this work ("not for this super important work, please do adversarial reviews in this thread, this is a new account"). Three reviewers each read it by one lens, in an agent of its own: the tools for correctness, the workflow for security, and the documents against the code. They made ten, six and fifteen findings. Each was fixed with a test of its own where it was in code, and then a mutation check broke each of twenty fixes in turn and ran the tests, which caught all twenty: a test that passes with its fix broken proves nothing.

The kinds of fault they found, without the research:

- A quote matched by any window of it, as a long quote extracted with broken spacing must be, hides an edit inside the rest of it; a quote found only by a window is now found in part, and a verdict resting on one is read again when its source changes.
- States that could never clear: a gone source tracked by its old tree, checks that no text gives any more kept as unseen, and a verdict that landed on a row already there counted as not come back, so the issue never closed or every run failed.
- A run made without one of the two repositories overwrote the stamp's word for that repository's sources; a run that cannot see everything now writes nothing.
- A cascade: a row a concept check made produced concepts of its own.
- A model's answer reaching a pull request's body and the pages as live Markdown, tags and images included; a guard applied to the records and the verdicts but not to the finders' candidates; and one injected text able to reach other sources' rows through a shared batch.
- Unmerged code run beside the secrets, and a bot's pull request merging without the tap, since a job skipped because the job it needs failed reports as skipped, which a required check takes as passing.
- An unbounded pattern whose cost grew with the square of a line's length.
- Documents stating the code more strongly than it does: a default limit written as a fixed number, "opens a pull request" where runs add to one, "stamps only what was read" where every record's hash is stamped, a closing condition looser than the code's.

The session that resumed the work after a checkpoint found two more. A failed read of the gate's check runs counted as not rejected, so a Reject the run could not see would have been built on; every read that gates safety now fails closed. And the model's token the reads need is the repository's one token for every workflow that runs the model, so setting it for these reads also lets the mention workflow, the coordinator and any registered worker run; the documents and the owner's setup steps now say so, since an exception to a rule against keeping credentials covers every reader of that credential, not only the one it was asked for.

## What failed

- The owner's weekly usage reached 92 percent in the middle of the work, and a handoff committed on the branch carried the exact next steps; the resumed session followed it and found two of its statements wrong, a status it called clean that was not and a setup step that left out what else the secret enables. A handoff is a claim like any other, checked before it is relied on.
- Five tests broke from the fixes themselves, none from a bug: a list of fixes should carry the tests each fix changes.
- Files left open came to light only once the tests ran with warnings as errors; every tool now closes what it opens.
- One mutant ran a command the test meant to refuse, and it rewrote the real records in the working tree; a test that drives a command line patches the part that writes, so a regression cannot reach real files.
- A cd into a subfolder in one shell call moved the session's working directory for the calls after it; every command takes absolute paths and git -C.
- The first look after the work merged never ran. GitHub's auto-merge landed the pull request, armed by the repository's workflow with the workflow token, so the push that was to start the look started nothing, and no other workflow on the default branch ran either. The session started the look by hand, and the documents, which had promised a look within minutes of every change, now say that an auto-merged change waits for the daily run.

## What to keep

- Stamp by content, never by date; compare trees and hashes.
- Script first: a look with no model on every change, and the model only where the look finds work, under limits a person sets and can switch off.
- One pull request, rebuilt as one commit on the default branch, opened by an App so the owner's gate holds, with a Reject kept.
- From an unmerged branch, take data and never code.
- Fail closed on every read that decides whether something may merge or be built on.
- A secret's reach is every workflow that reads it; say so when asking for it.
- A push trigger fires only for a push a person or an App makes. Where auto-merge is armed with the workflow token, what must follow every merge needs a daily run behind it, or an App's token behind the arming; check the runs list after the first merge rather than trusting the trigger.
- A test for each fix, then a mutation check that breaks each fix, then the documents read against the code by a reader of their own.
