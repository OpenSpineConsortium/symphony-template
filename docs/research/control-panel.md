# The Symphony control panel and what Symphony costs

The research notes of the thread "Symphony control website", item 7 of the owner's handoff of
2026-10-15 (docs/checkpoints/2026-10-15b/handoff.md). Written 2026-10-16 and kept current as the
work goes on; every figure names its source and the day it was read. The owner asked on
2026-10-16 that research notes accumulate in this repository rather than in replies, so this file
is the record and the thread's replies only point at it.

## The ask

Item 7, in the owner's words: "Interactive UI website with native claude browser to drive the
symphony environment (add repos, monitor CI, tasks, board, add workers, also with the option of
interacting through prompts) and direct comparison of money spent on this site versus
competitors (particularly notsorry)".

"notsorry" is unsorry, agenticsnz/unsorry, the swarm that proves theorems in Lean with
volunteers' own agents and coordinates them in GitHub Actions: it is the one system in the
taxonomy of 2026-10-15 that shares Symphony's shape (coordination as Actions jobs, no server, a
first-push-wins claim), and the taxonomy's manual walks it through as its worked example
(docs/checkpoints/2026-10-15b/taxonomy/spec.md, section 5.1; manual.md, section 5). No project
named "notsorry" was found on GitHub; the spelling is taken as a slip for unsorry.

## The answer in short

- Built, in four pull requests, three merged on 2026-10-16 (the table under Where it lives): the control panel at
  /symphony/control/ and the cost page at /symphony/cost.html on the site, one script behind
  both; the stateless sign-in service in symphony-app; version 8 of the Apps' privacy statement
  in symphony-start; this note and a memory fact in the template.
- Works today, with nothing deployed: a person makes a fine-grained GitHub token, pastes it into
  the page, and drives any repository of theirs that carries the topic symphony from the browser,
  as themselves. A Claude driving a browser reads the same page: every state is a sentence under
  the summary line and every action is a named button.
- Waits on the owner: deploying the sign-in service (a Cloudflare Worker) and giving the App a
  client secret and two callback URLs, after which one more pull request on the site sets two
  constants and "Sign in with GitHub" appears. The steps, each with its link and what to click,
  are in symphony-app's signin/README.md and under What waits on the owner below.
- The money: a Symphony repository pays one flat Claude plan for its workers in Actions ($20,
  $100 or $200 a month) and, on a public repository, nothing for the compute, since standard
  runners are free there and the coordination makes no model call. The other ways of running
  coding agents on GitHub meter every token: an API key (gh-aw's Claude engine, claude-code-action
  with a key) at Anthropic's list prices, GitHub Copilot's coding agent at the same list prices in
  AI credits past a plan's included ones, unsorry at whatever each volunteer pays for their own
  runs, and OpenAI's Codex at OpenAI's rates. The worked example below prices 300 runs a month:
  $210 of Sonnet 5.5 tokens at the list, which Symphony covers with a $100 plan while the runs fit
  its windows.

## Where it lives

| Repository | Files | Pull request |
| --- | --- | --- |
| OpenSpineConsortium/openspineconsortium.github.io | tools/pages/symphony/control/index/body.html, tools/pages/symphony/cost/body.html, assets/js/symphony-panel.js, assets/css/control.css, tools/build_site.py (two nodes), README.md; the built pages symphony/control/index.html and symphony/cost.html | #20, merged 2026-10-16 |
| OpenSpineConsortium/symphony-app | signin/worker.js, signin/test_worker.mjs, signin/README.md, scripts/check.sh | #14, merged 2026-10-16 |
| OpenSpineConsortium/symphony-start | PRIVACY.md, version 8 (rendered by the site at /symphony/apps-privacy.html) | #44, merged 2026-10-16 |
| OpenSpineConsortium/symphony-template | docs/research/control-panel.md (this file), docs/memory/the-control-panel.md and its index line | #95, merged last |

They merged in the order symphony-start (the site renders its privacy statement), the site,
symphony-app, then the template, each with a merge commit once its check was green, on the
owner's standing permission; the site has no check of its own beyond its build.

## What the panel does

The parentheses in the ask, one by one, and how each is done through GitHub's REST API as the
signed-in person, with nothing of ours in between.

- Add repos: "Find my Symphony repositories" lists the person's repositories (up to 300) and
  keeps those whose About carries the topic symphony, which an adoption sets; a repository named
  by hand that lacks the topic gets the two presses that set Symphony up on it, the App's install
  link preselected for that one repository and the front door's form. `?repo=OWNER/NAME` in the
  address lands on one repository.
- Board: STATE.md on the branch board, read as raw text and rendered by a small Markdown renderer
  of the page's own, which escapes every character first and allows only headings, paragraphs,
  lists, tables, code, bold and http links; the branch's commit date says when it was written.
- Tasks: the open issues sorted by the protocol's labels into the Queue, Given to workers,
  Claimed, In review, Blocked, Blockers and Epics; "Queue a task" opens an issue labelled todo in
  the shape the Task form writes (Goal, Acceptance, Files likely touched); a select on each queued
  issue gives it to a registered worker by adding its worker:<name> label, making the label when
  it is missing.
- Prompts: "Ask Claude" opens an issue, or comments on one, mentioning @claude, which the
  repository's claude.yml answers on its own Claude token.
- Add workers: the registry under .github/symphony/workers/ is listed, and "Add the worker"
  opens an "Add a worker" issue in the form's shape, which add-worker.yml turns into the pull
  request that registers it; the page never takes a credential for a worker.
- Monitor CI: the latest Actions runs with their outcomes, the open pull requests with the state
  of every check on each head, and four buttons that start the workers, the board, the checks and
  the metrics by workflow_dispatch; a Merge button becomes pressable on a ready pull request whose
  checks have all passed, asks once more, and merges with a merge commit.
- Cost: the cost page reads METRICS.json on the branch metrics (the economics and coordination
  blocks the metrics workflow writes) and sets what the last 30 days cost at API list prices
  beside the flat plan, beside the same tokens under each competitor, and feeds a calculator
  whose inputs the person can change.

## Design decisions

1. A static page that calls GitHub's API as the person, plus a small stateless sign-in service
   through the App's user token. The owner decided this shape on 2026-10-13 (CLAUDE.md, Durable
   decisions: "the control panel is a site page with a small stateless sign-in service acting
   through the App's user token"). Nothing of ours sees the repository's data; the site has no
   server, and the service holds one secret and keeps nothing.
2. Two ways to sign in. A fine-grained personal access token works with nothing deployed and
   needs no permission from the App, so the panel is usable from the day it merges. "Sign in
   with GitHub" gives a user-to-server token of SymphonyBoard, scoped to the App's permissions
   intersected with the person's own access, and appears only once the script's SIGNIN_SERVICE
   and CLIENT_ID are set, which waits on the owner's deployment.
3. Never a Claude token. The page never asks for one, holds one or sends one; the workers run on
   the token the repository holds as its secret. This is the project's one fundamental rule.
4. The GitHub token lives in the browser only: sessionStorage by default (gone when the tab
   closes), localStorage when "Keep me signed in" is ticked, and the tick is off by default so
   that a shared computer forgets. "Forget the token" drops it and, for a signed-in token, asks
   GitHub through the service to revoke it.
5. The sign-in service exchanges the code with PKCE: the page makes a secret for each sign-in,
   sends GitHub its hash, and sends the secret with the code, so a code stolen from an address
   bar is worth nothing to anyone else; the Origin check on top keeps other sites' scripts out.
   The service bounds every request body in bytes, answers only the site's origin, returns only
   the five token fields, and takes an optional rate-limit binding.
6. The issue bodies the page writes are in the exact shape GitHub gives the two issue forms, so
   the existing workflows (add-worker.yml, the board, the workers) read them as if the forms had
   been used, and no workflow changes.
7. Words and named buttons. Every state is a sentence (the summary line, "No open pull
   request.", "Written 3 minutes ago"), every action is a button with a name, and errors say
   what GitHub answered and what to do, so a Claude driving a browser needs no screenshot
   reading.
8. The merge needs two presses and a token with Contents: Read and write; a draft, a failed
   check or a check still running keeps the button off. A wrong merge is the one action on the
   page that cannot be undone.
9. The cost page's price table is kept in the script beside the template's own
   (tools/economics.py) with the date it was read, and every price names its source at the foot
   of the page; where the two tables differ the page says which date each is of.

## The cost comparison

### How each system charges

Read at each source on 2026-10-15 (the Sources section); every row is what the system itself
says.

| System | Where the agents run | Compute | Inference | Who pays |
| --- | --- | --- | --- | --- |
| Symphony | GitHub Actions on the repository's subscription token; people's own sessions | Standard runners, free and unlimited on a public repository; 2,000 minutes a month on Free and 3,000 on Pro and Team for a private one, then $0.006 a minute | One Claude plan for the Actions workers (Pro $20, Max 5x $100, Max 20x $200 a month); past the plan's five-hour and weekly windows, usage credits at API list prices | The repository's owner, one plan |
| An API key in Actions (gh-aw's Claude engine; claude-code-action with a key) | GitHub Actions | The same minutes | Every token at Anthropic's list prices; gh-aw says the subscription token "is not supported" | The key's owner, per token |
| GitHub Copilot coding agent (the Claude and Codex agents on GitHub) | Actions runners under GitHub's service | Actions minutes | AI credits at $0.01 each; a plan includes some (Pro $10 with 1,500, Pro+ $39 with 7,000, Max $100 with 20,000), then metered; Claude at Anthropic's list prices | The Copilot subscriber, per token |
| unsorry | The board, the dispatcher and the reaper in Actions; the agents on volunteers' machines | Free in a public repository's Actions | Each volunteer's own claude -p, Codex or Gemini runs, on their plan or their key | The volunteers |
| OpenAI (openai/codex-action, openai/symphony) | Actions, or a daemon of the user's | Actions minutes, or the host | An OpenAI API key is required; OpenAI's rates | The key's owner |

### The prices

- Claude plans (claude.com/pricing, read 2026-10-15, monthly billing): Pro $20, Max 5x $100,
  Max 20x $200. The allowance is published as a multiple of Free per five-hour window, with
  weekly limits on top, not as a token count; past the limits, usage credits bill at the API
  prices (support.claude.com, "Manage usage credits for paid Claude plans").
- Anthropic's API list prices per million tokens, read from platform.claude.com/docs/en/about-claude/pricing
  on 2026-10-15: input, cache write kept five minutes, cache write kept an hour, cache read,
  output. Sonnet 5.5: 2, 2.5, 4, 0.10, 10. Opus 5.5: 4, 5, 8, 0.20, 20. Fable 5.1: 10, 12.5, 20,
  0.25, 50. Haiku 5.5: 0.10, 0.125, 0.20, 0.01, 0.50.
- Claude Code in Actions on a subscription: "If you authenticate with an OAuth token, runs use
  your Claude subscription instead of API billing" (code.claude.com/docs/en/github-actions).
- GitHub Actions (github/docs, content/billing/concepts/product-billing/github-actions.md at
  commit 12691d2, read 2026-10-15): free and unlimited standard runners on public repositories;
  2,000 minutes a month on Free and 3,000 on Pro and Team for private ones; a Linux 2-core
  runner $0.006 a minute from 2026-01-01.
- GitHub Copilot (github/docs, content/copilot/concepts/billing-and-usage/individuals/billing.md
  and data/variables/copilot.yml at 12691d2; content/copilot/reference/copilot-billing/models-and-pricing.md):
  usage-based since 2026-06-01, AI credits at $0.01, the plans' included credits as above, and
  Claude priced at Anthropic's list prices; third-party coding agents consume Actions minutes and
  AI credits (about-third-party-coding-agents.md).
- gh-aw's Claude engine (github/gh-aw, docs/src/content/docs/engines/claude.md at dc91dbe, read
  2026-10-15): "Claude subscription OAuth tokens such as CLAUDE_CODE_OAUTH_TOKEN are not
  supported".
- OpenAI: openai/codex-action's README requires an API key as a secret.
- unsorry (agenticsnz/unsorry at 029d328b, read 2026-10-15): ADR-004 for the claims on one shared
  branch, reaper.yml and queue-dispatcher.yml for the coordination in Actions, swarm/agent.sh for
  each volunteer's own runs.

### A worked example

The calculator's defaults: 10 runs a day for 30 days, 10 runner minutes a run, and a run of
1,745,000 tokens (20,000 input, 100,000 cache writes at the five-minute rate, 1,600,000 cache
reads, 25,000 output), the shape of a Claude Code run that re-reads a cached context. Cache
writes are priced at the five-minute rate, which an API key gets by default; on a subscription
the cache lives an hour.

| Model | Tokens a run | Tokens a month, 300 runs | Copilot Pro ($10 + 1,500 credits) | Copilot Pro+ ($39 + 7,000) | Copilot Max ($100 + 20,000) |
| --- | --- | --- | --- | --- | --- |
| Sonnet 5.5 | $0.70 | $210 | $205 | $179 | $110 |
| Opus 5.5 | $1.40 | $420 | $415 | $389 | $320 |
| Fable 5.1 | $3.10 | $930 | $925 | $899 | $830 |
| Haiku 5.5 | $0.04 | $13 | $10 | $39 | $100 |

Against those, Symphony's bill for the same 300 runs is the plan alone, $100 a month on Max 5x,
while the runs fit the plan's windows, and $0 of compute on a public repository; on a private
repository on GitHub Free the 3,000 runner minutes exceed the 2,000 included by 1,000, which is
$6 (none on Pro or Team, whose 3,000 cover them), and every row above pays the same minutes. An
API key pays the Tokens a month column; Copilot pays its plan plus the tokens past its credits;
unsorry's volunteers pay the Tokens a month column between them; OpenAI's figure depends on
OpenAI's price list, outside the table. Whether 300 such runs fit a plan's windows is not
published as a token count, so the page says so and gives the tokens' list price as the most the
usage credits could add.

### What the measured figures are

A Symphony repository records what its work cost beside the work: each session's commits carry a
Symphony-Usage line and each Claude run in Actions leaves a usage artifact, and metrics.yml sums
them into METRICS.json on the branch metrics (docs/memory/field-metrics.md). Signed in, the cost
page reads that file as the person and shows the economics block (the pull requests ended and
merged, the tokens by kind, the time at work, the estimate at list prices, the coordinator's
share, the dollars per merged pull request) and the coordination ratios (alone against parallel:
tokens and dollars per merge, latency, throughput, first check passed, commits per merge,
failures per pull request, over 1 where parallel did better), prices the measured tokens under
each competitor, and can hand the measured window to the calculator. The page states the date
the template's table priced the record by (economics.prices_as_of) beside its own.

One difference found while comparing the tables: tools/economics.py prices Sonnet 5.5's cache
reads at 0.20 per million (PRICES_AS_OF 2026-10-06), and Anthropic's page of 2026-10-15 says 0.10;
the page's table has 0.10. The fix to the template is a follow-up pull request of its own (under
Follow-ups).

## Checks and reviews

- The service: `node --test signin/test_worker.mjs`, 15 tests that drive the handler with a fake
  GitHub (the description, the preflight, the exchange with and without a verifier, the refresh,
  the revoke, foreign and malformed origins, bad bodies, the byte bounds, a missing setting, a
  rate-limit binding, GitHub refusing or unreachable); symphony-app's scripts/check.sh runs them
  where node is on the path, as on GitHub's runners (`PYTHON=python3.12 bash scripts/check.sh`
  passed).
- The privacy statement: symphony-start's `bash scripts/check.sh`, 300 tests, passed.
- The site: `python3 -X utf8 tools/build_site.py` builds and `--check-only` reports 0 problems
  (49 pages; the one note is older and about the Beethoven pages' link depth).
- The pages: a Playwright test outside the repositories (the site has no test runner) drives
  both pages against a mocked api.github.com: sign-in with the tick and without, the summary
  line, the board's rendering with a hostile script tag escaped, queueing a task in the form's
  shape with the label todo, giving an issue to a worker, adding a worker in the form's shape,
  starting the workers, the two-press merge with Cancel, a repository without the topic and its
  preselected install link, the cost page's measured rows and calculator, Forget the token, and a
  refused token. It passes against the built pages of 2026-10-16.
- Two adversarial reviews, as the handoff requires before a substantive pull request, one of
  the pages and one of the service and the privacy statement; what each found and what was done:
  - The pages: a loader of one repository could write into the next after a switch (every loader
    now checks the state it started for); the summary stayed at "Reading..." when a read failed
    (it now says what is known and names each failed read); the merge confirmed with a browser
    dialog (now a second press with Cancel); the cost table's wording implied the template and
    the page share one table (each names its own date); the cost page called minutes free on a
    private repository (it reads the repository's visibility and says which); "Keep me signed
    in" was on by default (off); giving an issue to a worker could label the wrong one (scoped);
    an escaped pipe broke a board cell (unescaped in the cell); the issue list's cut at five
    pages, the pull requests' at two and the discovery's at 300 were silent (each says "at
    least"); a board over 1 MB was unreadable through the JSON contents API (read raw); the
    queued task's label was assumed (the answer's labels are checked, and the page says when
    GitHub dropped todo); an archived repository was not said (it is); the Copilot pricing link
    was the wrong page (models-and-pricing.md); a label was made with no colour (one colour for
    worker labels); dead code; a 429 was explained as a 403 (its own words).
  - The service and the statement: the "keep" tick was lost across the OAuth redirect (kept in
    the sign-in state); the cost page could start a sign-in from an unregistered callback (both
    pages are callbacks, and the README says so); the refresh token was kept but unsaid (said);
    two reads were unlisted in the statement (listed); Cloudflare keeps Workers Logs on by
    default (the README's step 2 turns them off, and the statement says the host's logs are off);
    no PKCE (added, required); a failed refresh left the page signed in with a dead token (it
    signs out and says why); the body reader had no byte bound (4,096 bytes, counted as read);
    no rate limit (an optional binding, 429 past it); the statement contradicted itself on what
    the service sees (rewritten); ALLOWED_ORIGIN with a path or a slash broke the check silently
    (normalized, 503 until it is a bare origin); a null body, a code in the URL with no state, a
    non-JSON answer from GitHub and two refreshes in flight each had a wrong answer (each has its
    own); no way to revoke (POST /revoke, pressed by Forget the token); index.html in the
    callback (stripped); GitHub unreachable answered 500 (502 with words).
  - The reviewer's own probe script, 13 checks written against the pages before the rewrite
    (repository switching mid-load, a failed read said in words, the 300-issue cut, the merge
    button on a draft and on a failed check, a hostile board, an escaped pipe, the fallback
    without Actions: read, a private repository's minutes, sharing off and a missing record,
    the tab-only token, a dropped todo label, a hostile ?repo=, an archived repository), was
    rerun after the rewrite with its fixtures served as raw text, as the page now reads files,
    and its failed-read check pointed at the summary line, where the failure is now said: all
    13 pass.

## What waits on the owner

Each step is in symphony-app's signin/README.md with its link and what to click; in short:

1. Make the Worker on Cloudflare (https://dash.cloudflare.com/, Workers & Pages, Create,
   Create Worker, name symphony-signin, Deploy; Edit code, paste signin/worker.js, Deploy) and
   copy its address.
2. On the Worker's page, Settings, Observability: turn Workers Logs off.
3. On https://github.com/organizations/OpenSpineConsortium/settings/apps/symphonyboard: note
   the Client ID; Generate a new client secret; add the two callback URLs
   https://openspineconsortium.com/symphony/control/ and
   https://openspineconsortium.com/symphony/cost.html; leave the wildcard box unticked, "Expire
   user authorization tokens" ticked, "Request user authorization (OAuth) during installation"
   unticked and the Setup URL as it is; Save changes.
4. On the Worker's page, Settings, Variables and Secrets: GITHUB_CLIENT_ID (text),
   GITHUB_CLIENT_SECRET (secret), ALLOWED_ORIGIN = https://openspineconsortium.com (text);
   Deploy.
5. Give a session the Worker's address and the Client ID: one pull request on the site sets
   SIGNIN_SERVICE and CLIENT_ID, and "Sign in with GitHub" appears.
6. Optional: add "Actions: Read and write" to the App's permissions, so that a signed-in token
   lists runs and starts workflows; without it the panel falls back to the default branch's
   check runs and says so, and a fine-grained token needs nothing from the App.

Until then the pages work with a fine-grained token: https://github.com/settings/personal-access-tokens/new,
the repositories Symphony runs in, and under Repository permissions Actions Read and write,
Checks Read-only, Contents Read and write, Issues Read and write, Pull requests Read and write.

## Follow-ups

- tools/economics.py: Sonnet 5.5's cache-read price 0.20 to 0.10 and PRICES_AS_OF to 2026-10-16,
  the day the page was read again (its footnote: cache hits on Opus 5.5 and Sonnet 5.5 are 0.05
  times the input price, Sonnet 5's 0.1 times), in the pull request after #95; done.
- The constants pull request on the site, once the owner gives the Worker's address and the
  Client ID.
- The Playwright test lives outside the repositories; the site has no test runner, and adding
  one is a proposal, not a change (the writing rule on dependencies).
- Not built, by the owner's choice of shape: a hosted server, an account pool, anything that
  touches a Claude token.

## Sources

- The owner's handoff: docs/checkpoints/2026-10-15b/handoff.md, item 7; the shape of the panel:
  CLAUDE.md, Durable decisions (2026-10-13).
- The taxonomy: docs/checkpoints/2026-10-15b/taxonomy/spec.md (section 5.1) and manual.md
  (section 5), for unsorry as the nearest system.
- Prices and terms: claude.com/pricing (2026-10-15); support.claude.com, "Manage usage credits
  for paid Claude plans"; platform.claude.com/docs/en/about-claude/pricing (2026-10-15);
  code.claude.com/docs/en/github-actions; github/docs at commit 12691d2 (2026-10-15):
  content/billing/concepts/product-billing/github-actions.md,
  content/copilot/concepts/billing-and-usage/individuals/billing.md, data/variables/copilot.yml,
  content/copilot/reference/copilot-billing/models-and-pricing.md,
  content/copilot/concepts/agent-capabilities/about-agents/about-third-party-coding-agents.md;
  github/gh-aw at dc91dbe, docs/src/content/docs/engines/claude.md; openai/codex-action's
  README; agenticsnz/unsorry at 029d328b.
- Platforms: Cloudflare's Workers Logs page (on by default for new Workers, seven days of
  invocation logs) and the rate-limiting binding's page
  (developers.cloudflare.com/workers/runtime-apis/bindings/rate-limit/), read 2026-10-16;
  GitHub's App docs on callback URLs (exact match, up to ten, the Setup URL apart) and on
  user-to-server tokens (eight hours, a six-month single-use refresh token), read from
  github/docs on 2026-10-16.
