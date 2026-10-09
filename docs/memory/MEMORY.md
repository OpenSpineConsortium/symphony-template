# Memory index

One line per fact under docs/memory/: a dash, the fact's title as a link to its file, a colon and one line saying what it is. CLAUDE.md imports this file into every session; a fact's own file is read when its line says it matters. Add or correct a fact with the remember skill (.claude/skills/remember): one file, one line here, in the same pull request as the change it came from. This index stays under 200 lines and 25 KB, a limit of this project's own: an imported file loads whole into every session's context, and Claude Code's guidance for an instruction file is under 200 lines. `scripts/check.sh` fails when a fact is missing here or a line names a file that is not there.

- [CI runs Python 3.12](ci-python-is-3-12.md): the checks run on GitHub's 3.12, so tools and tests use no API newer than that; test with python3.12 where it exists.
- [@claude runs on the main account's subscription](claude-mentions-run-on-the-main-accounts-subscription.md): mentions run .github/workflows/claude.yml on the token from `claude setup-token`, spending plan limits, never an API key.
- [How this repository works](how-this-repository-works.md): the repository is the shared plane for every Claude account and session; what lives where.
- [Team mode](team-mode.md): a lead plans an epic into pre-assigned tasks, members work them in parallel and land by auto-merge; the lead integrates; switched on by CLAUDE_TEAM with CLAUDE_WORKER.
- [The plan ladder](the-plan-ladder.md): which GitHub and Claude plans unlock what, verified 2026-10-09; public repo means free Actions and enforced protection, no payment method means a hard cap.
