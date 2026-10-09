# Memory index

One line per fact under docs/memory/: a dash, the fact's title as a link to its file, a colon and one line saying what it is. CLAUDE.md imports this file into every session; a fact's own file is read when its line says it matters. Add or correct a fact with the remember skill (.claude/skills/remember): one file, one line here, in the same pull request as the change it came from. This index stays under 200 lines and 25 KB, a limit of this project's own: an imported file loads whole into every session's context, and Claude Code's guidance for an instruction file is under 200 lines. `scripts/check.sh` fails when a fact is missing here or a line names a file that is not there.

- [How this repository works](how-this-repository-works.md): the repository is the shared plane for every Claude account and session; what lives where.
