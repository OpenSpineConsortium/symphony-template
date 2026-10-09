# Turning on @claude in issues and pull requests

Writing @claude on an issue, a pull request or a review runs a Claude Code
session in Actions (.github/workflows/claude.yml): it reads CLAUDE.md and
the rules like every other session, answers, fixes, or takes the work the
comment asks for. Until the one secret below exists, the workflow ends at
its first step with a pointer and does nothing, so nothing here is
required.

## No API billing

The workflow authenticates with a subscription OAuth token, not an API
key: runs draw on the main account's Claude plan (Pro, Max, Team or
Enterprise) and bill nothing. That keeps the project's rule intact; the
token lives only in the repository's Actions secrets, which are settings,
not repository content, so the rule that no file holds a credential holds
too.

## Steps, once, by the main account

1. On a machine where Claude Code is signed in to the main account, run
   `claude setup-token` and approve it in the browser. It prints a token
   good for about a year and saves it nowhere.
2. Put the token in the repository secret CLAUDE_CODE_OAUTH_TOKEN, under
   https://github.com/{{REPO}}/settings/secrets/actions.
3. Nothing else. The workflow is already on {{DEFAULT_BRANCH}}; the next
   @claude mention runs it.

## What a run costs

- A run spends the main account's own usage: the five-hour window and the
  weekly limit, shared with that account's interactive sessions and
  routines. The workflow caps each run (--max-turns, a job timeout), but
  mentions are still deliberate asks, not decoration.
- Keep usage credits off on the main account unless overage billed at API
  rates is wanted; with them on, a run past the limits bills quietly.
- A pull request from a fork gets no secrets, so @claude does not run
  there; an account working in this repository pushes claim branches, not
  forks (docs/agents/PROTOCOL.md).

## Keeping the token

Treat the token like a password: it is the main account's subscription.
It expires after about a year; run `claude setup-token` again and replace
the secret. To turn @claude off, delete the secret, and the workflow is a
quiet no-op again.
