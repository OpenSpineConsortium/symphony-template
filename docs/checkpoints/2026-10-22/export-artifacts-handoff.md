# Handoff: exporting the other accounts' artifacts (2026-10-22, 04:05 UTC)

Thread "SchwingNet video demo plan", session https://claude.ai/code/session_01Pc1tx7LutSxyU1XKXSV5Qc, written when the account ran out of usage. The thread's grid and SchwingNet handoff is part 5 of handoff.md beside this file; this file covers only the artifact export the owner asked for at 03:55 UTC ("I have 4 other accounts I want to do the same for").

## Done

- .claude/skills/export-artifacts/SKILL.md: the procedure for one account. It lists that account's own artifacts, skips any link already named in artifacts/README.md here or in SchwingNet, and copies each artifact into artifacts/. Symphony, Beethoven and grid work go here; spine and SchwingNet work, and anything that might be patent material, go to SchwingNet. It lands one pull request per repository and merges it once green. Share is set to "Anyone with the link" through Claude in Chrome only when the owner asks, and never for SchwingNet material.
- CLAUDE.md's Skills line, artifacts/README.md, docs/memory/artifacts-are-kept-as-files.md and its index line now name the skill.
- All of it is in symphony-template pull request #363, a draft from the branch claude/project-thread-0koxce. CI was running when the account stopped. `bash scripts/check.sh` passed locally without the tests.

## Left to do

1. A session on any account: read pull request #363's checks. If any are red, fix them. If all are green, mark it ready and merge it on the standing permission.
2. A three-lens review of the skill (tool mechanics, safety, the four-account run) was running as workflow wf_89c1eb1c-e82 and died with the account. Run it again, or read the skill against the Artifact tool's own description, and fix what it finds in a follow-up pull request.
3. Then, on each of the owner's four other accounts:
   - open https://claude.ai/code;
   - start a session on OpenSpineConsortium/symphony-template, with OpenSpineConsortium/SchwingNet selected too;
   - type `/export-artifacts`. Add "and share them" only with Claude in Chrome connected and signed in to that same account.
