# The board comes first

Before any change in this repository:

1. Fetch: `git fetch origin`. The session-start hook does this once; do it again before you push.
2. Read the board and docs/agents/PROTOCOL.md (how work is claimed). The board is the file STATE.md on the branch `board`, rewritten by the board workflow; read it with `git fetch origin board && git show origin/board:STATE.md`. The session-start hook prints it at the start of every session; docs/agents/STATE.md on the default branch only describes its layout.
3. Check the claim on the issue you mean to take: a branch `claude/<issue>` on origin, or a file `docs/agents/claims/<issue>.md` on the default branch, means another account has it. Pick another.

One issue, one branch `claude/<issue>`, one pull request. Claim with the claim skill (.claude/skills/claim) before the first change to any other file, and open the draft pull request at once.

Never push to a branch another account claimed. Never force-push the default branch or any branch that is not your own claim; after a rebase, your own claim branch takes `git push --force-with-lease`, and nothing else ever does. When the board comments "main moved" on your pull request, rebase on the default branch and push again. An issue labelled blocker is claimed like any other, and nobody fixes it in parallel.

A hook enforces the push rules before they can be broken: tools/guard_push.py, wired in .claude/settings.json, refuses a push to the default or board branch, a plain --force anywhere, and --force-with-lease outside your own claude/ branch. A refusal is the rule working, not an obstacle; the answer is a pull request, a rebase or another branch, never a way around the hook. Branch protection on GitHub (docs/setup/github.md) stands behind it.
