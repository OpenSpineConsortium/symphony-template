---
name: handoff
description: Use when told the account's weekly limit is at 90 percent (the handoff hook says so), when the owner asks to hand off or swap accounts, or before a grid worker moves to another account, to write the handoff a fresh account resumes from.
---

# Write the handoff for the next account

A handoff is one committed page under docs/checkpoints/<date>/ that a session on another Claude account reads first and resumes from, in the shape of docs/research/handoff-2026-10-23.md: each piece of open work, where its own record is, its state at this minute and its next steps. Nothing of the conversation crosses accounts, and no prompt cache does either, so this page and what it names are all the next account has. The hook (tools/handoff.py hook) says when it is due, once per window; the owner may also ask for it in words, which is the only trigger a cloud session on claude.ai has.

1. Stop starting new work. Finish or park what is mid-flight: commit and push each branch by name, as the claim skill does, so nothing lives only in this container.
2. Land what was found: research under docs/research/ with its README line (.claude/rules/research.md), and memory under docs/memory/ (.claude/rules/memory.md), in their own pull requests or the work's. The handoff names those files and never carries them.
3. Write the skeleton: `python3 tools/handoff.py new`. It prints the path and fills in what git knows (the branch, what is not pushed, what is not committed).
4. Fill every part it marks `<!-- fill -->`: the pull requests with their states; one item per piece of open work, with where its record is (an issue, a claim branch, a research note, a grid job by its Slurm id and the status word that reads it) and its next steps numbered; the owner's own steps with exact links and what to click, or "Nothing." Plain prose, ASCII and LF, no secret, token, e-mail or tool output. A Project thread writes its own work; the coordinator writes one page for every thread, as the 2026-10-23 handoff was.
5. Checkpoint too (.claude/skills/checkpoint), so `.claude/session.md` and the marked block of CLAUDE.md agree with the page.
6. Commit the page on the thread's branch and open its pull request; run `bash scripts/check.sh`; merge once green on the owner's standing permission. A page that is not on the default branch is not found by the next session's start.
7. Record it: `python3 tools/handoff.py done <path>`. It refuses a page with a part still to fill, keeps the nudge quiet for this window, and on the grid tells hpcworker that the worker may move now.
8. Tell the person in one short reply: the page's link, and that the next account may start. Then stop: anything more spends the window the handoff was written to save.

On the next account, the session-start hook names the newest handoff of the last three days; read it, then the board, and carry the work on.
