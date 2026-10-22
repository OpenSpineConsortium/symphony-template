# Handoff: exporting the other accounts' artifacts (2026-10-22, 04:05 UTC)

Thread "SchwingNet video demo plan", session https://claude.ai/code/session_01Pc1tx7LutSxyU1XKXSV5Qc, written when the account ran out of usage. The thread's grid and SchwingNet handoff is part 5 of handoff.md beside this file; this file covers only the artifact export the owner asked for at 03:55 UTC ("I have 4 other accounts I want to do the same for").

## Done

- .claude/skills/export-artifacts/SKILL.md: the procedure for one account. It lists that account's own artifacts, skips any link already named in artifacts/README.md here or in SchwingNet, and copies each artifact into artifacts/. Symphony, Beethoven and grid work go here; spine and SchwingNet work, and anything that might be patent material, go to SchwingNet. It lands one pull request per repository and merges it once green. Share is set to "Anyone with the link" through Claude in Chrome only when the owner asks, and never for SchwingNet material.
- CLAUDE.md's Skills line, artifacts/README.md, docs/memory/artifacts-are-kept-as-files.md and its index line now name the skill.
- All of it is in symphony-template pull request #363, a draft from the branch claude/project-thread-0koxce. CI was running when the account stopped. `bash scripts/check.sh` passed locally without the tests.

## Left to do

1. A session on any account: read pull request #363's checks. If any are red, fix them. If all are green, mark it ready and merge it on the standing permission.
2. The three-lens review of the skill finished: 38 findings, 6 of them high, written out in export-artifacts-review.md beside this file. Among the high ones: SchwingNet needs add_repo with push access and a clone; the sort can send patent material here and behind a public link; and a Docs export comes back as base64 that has to be decoded, not retyped. Apply them all in one pull request before anyone runs the skill, and above all before "and share them".
3. Only then, on each of the owner's four other accounts:
   - open https://claude.ai/code;
   - start a session on OpenSpineConsortium/symphony-template, with OpenSpineConsortium/SchwingNet selected too;
   - type `/export-artifacts`. Add "and share them" only with Claude in Chrome connected and signed in to that same account.
