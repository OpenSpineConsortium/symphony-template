# The Dollar-per-Feature Ladder

Oct 9, 2026 · @greg

An agent-driven software team on this template runs whole for $17 a month, and every dollar above that rung buys a named feature; the ladder below was verified against GitHub's and Anthropic's own pages on Oct 9, 2026.

## The pitch

Three numbers carry the argument. **$17 a month** runs the whole machine: one Claude Pro seat, billed annually, beside a public repository on GitHub Free, where Actions on standard runners are free without limit and branch protection is enforced at no charge. **$0** is the guaranteed GitHub bill at that rung, by construction rather than by discipline: with no payment method stored, GitHub blocks usage at the quota instead of billing, and a public repository never draws on the quota at all. **3,000** is the number of included private-repo CI minutes on both the $4 GitHub Pro plan and the GitHub Team plan: identical. Above the bottom rung, money buys governance and usage, never compute, until the one real capacity jump at Enterprise (50,000 minutes).

The ladder is front-loaded. The product below runs complete at the bottom rung; each rung above it buys a short, named list of genuine features. That is the whole pitch: spend nothing that does not buy a name on the list.

## The product: a shared project that lives in a repository

The product is a GitHub template repository ([OpenSpineConsortium/sdlc-template](https://github.com/OpenSpineConsortium/sdlc-template)) that makes one repository the shared plane of a multi-account, agent-driven software project. The instructions, the goal, the shared memory and the work protocol are files; CLAUDE.md imports them, so every Claude Code session on every account assembles the same context from a fresh clone. The board is a file on its own branch, rewritten by a workflow from the live issues, branches and pull requests. Work moves by a claim protocol: one issue, one branch, one pull request, claimed by the first push of a branch name GitHub will refuse to a second account. The claude.ai Project each account makes is a bare link to the repository; its own fields stay blank, so nothing copies, drifts or needs a credential.

Three pull requests, built and verified tonight, turned the protocol's prose into mechanism:

- [Enforcement and @claude (#3)](https://github.com/OpenSpineConsortium/sdlc-template/pull/3): a hook that refuses forbidden pushes before they run, instant document checks on every edit to the instructions or memory, a shared permission allowlist, a /board command, branch tidying for the one case GitHub has no setting for, and @claude on issues and pull requests, authenticated by a subscription OAuth token rather than an API key.
- [The machine-checked protocol and the Actions worker (#5)](https://github.com/OpenSpineConsortium/sdlc-template/pull/5): the claim protocol enforced inside the required CI check (a draft must carry its claim file, a ready pull request must have deleted it and must close its issue), and an opt-in scheduled worker that takes queue issues to pull requests on the same subscription token, behind a free deterministic gate.
- [The tier page and the economy fix (#7)](https://github.com/OpenSpineConsortium/sdlc-template/pull/7): the verified plan ladder as a setup page and a memory fact, plus the one change the numbers demanded, the board's cron fallback cut from hourly to six-hourly, saving a private repository about 630 billed minutes a month.

All three pass CI, including the new protocol check validating itself against its own pull request.

## The ladder: what each rung unlocks

Monthly prices at annual billing where it exists; every GitHub gate verified against [GitHub's billing reference](https://docs.github.com/en/billing/reference/product-usage-included) and [ruleset docs](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets), every Claude price against [claude.com/pricing](https://claude.com/pricing), on 2026-10-09.

| Rung | 1 person, $/mo | 5 people, $/mo | What the rung genuinely adds |
| --- | --- | --- | --- |
| GitHub Free (public repo) + Claude Pro | 17 | 85 | The whole template: unlimited free CI on standard runners, enforced branch protection and rulesets, @claude and the worker on the Pro account's one-year setup-token |
| + GitHub Pro, $4 (personal account) | 21 | n/a | Enforced protection on a private personal repository, 3,000 included CI minutes; nothing else |
| GitHub Team + Claude Team standard | n/a | 120 | Private org repos with enforced protection, push restrictions and bypass lists, push rulesets, org-wide rulesets, Claude Code on every seat under SSO and one bill |
| + premium seats or Max, where a seat hits limits | 100-200 solo (Max) | +80 per premium seat | Usage only: 5x-20x the window, no new features anywhere in this upgrade |
| GitHub Enterprise Cloud + Claude Enterprise | custom | custom | 50,000 CI minutes (16.7x Team), enterprise-level rulesets, internal repos; Claude's administered shared workspace (pricing not publicly verifiable) |

The chart below plots the three priceable rungs against team size; the vertical gap between the bottom line and the others is the entire cost of governance.

&#91;embedded content: GitHub billing reference and claude.com/pricing, verified 2026-10-09; Team rungs start at 2 seats\]

## Tier 1, economy: $17 a month all in

One Claude Pro seat and a public repository on GitHub Free run everything the template has. The GitHub bill is zero by construction: public repositories pay nothing for Actions on standard runners, branch protection and rulesets enforce for free, and an account with no stored payment method cannot be surprise-billed, because GitHub halts usage at the quota instead of charging. Claude Pro's `setup-token` (a one-year OAuth credential, sanctioned for CI from the cheapest paid plan up) powers both @claude mentions and the scheduled worker with no API billing; runs draw on the Pro account's five-hour window and weekly limit.

For a private repository, the $4 GitHub Pro plan is the one purchase that earns its keep: enforced protection on personal private repositories plus 3,000 included minutes, the same allotment Team gets. The template's deterministic CI spends those minutes slowly: the check suite runs about a minute per pull request event, and the board's six-hourly fallback costs about 120 minutes a month.

What this tier cannot buy at any price on a personal account: server-side push restrictions and bypass lists, which belong to organizations. The template's push-guard hook and machine-checked protocol stand in for them, honestly but client-side.

## Tier 2, team: the organizational fences

GitHub Team ($4 a person) plus Claude Team standard seats ($20 a person, annual) is the first rung where the server, not a hook, enforces the social rules. The genuine adds, none replicable below this rung: enforced protection on the organization's private repositories; push restrictions with bypass lists, so a push to main or to another account's claim branch is refused by GitHub itself; push rulesets that block files by path and size across the whole fork network; one organization-wide ruleset protecting main and the board branch in every repository the project ever adds (a capability that moved down from Enterprise in June 2025); and Claude Code on every Team seat under SSO and central billing, each account running its own worker with its own label on the board.

Two people cost $48 a month; each additional person adds $24. Claude Max ($100 or $200, monthly only) belongs on this rung only as the solo alternative: it multiplies usage 5x-20x and adds no feature, so it is the right spend exactly when one person's weekly limit, not a missing capability, is the constraint. The same logic prices premium Team seats ($100): buy them per person, only where a seat actually hits its limit.

## Tier 3, scale: enterprise, with the unknowns named

GitHub Enterprise Cloud is the ladder's only large capacity jump: 50,000 included minutes (16.7x Team), enterprise-level rulesets that sit above organizations, and internal repositories with push rulesets. Claude Enterprise adds the administered shared workspace: SSO and admin controls over a shared plane that is native rather than git-backed. Honesty requires two flags. Claude Enterprise's pricing is custom and could not be verified from public pages (a circulating $20-per-seat figure was adversarially refuted), and its shared-Project feature delta over Team likewise survived no verification, so this tier is a direction, not a quote: price it in a sales conversation, against the two tiers above that are fully priced.

What stays true at this rung: the repository remains the only shared plane that is versioned, pull-request-reviewed and machine-checked, so the template loses none of its point at scale. Native sharing buys back exactly one cost the repository plane accepts everywhere: the latency of a git fetch between a change and every session seeing it.

## The zero-inference core

The template's running costs stay near zero because every always-on part is deterministic, and every part that thinks is gated behind a deliberate act:

- Costs nothing, ever: native GitHub settings (auto-delete merged branches, branch protection, secret scanning), the push-guard and document-check hooks (they run inside the developer's session, not in CI), and all CI on a public repository.
- Costs CI minutes only on private repositories, and little: the check suite (about a minute per pull request event), the board rebuild on events, the six-hourly board fallback (about 120 minutes a month, cut from about 750 when it was hourly), and the tidy workflow (one run per closed issue).
- Costs Claude plan usage only when summoned: an @claude mention is a deliberate ask; the scheduled worker is off until a repository variable turns it on, and even then a free GITHUB\_TOKEN step checks the queue first, so an empty queue costs seconds of a runner and no tokens at all.

The design rule behind all of it: a native setting beats a workflow, a workflow beats inference, and inference runs only when a person or a queued issue asked for it. Ubuntu runners everywhere; Windows bills at roughly 1.7x, macOS at roughly 10x.

## Shared projects without Enterprise

The template approximates Claude Enterprise's shared workspace on any paid plan by making the repository the workspace. Instructions, goal and memory load identically into every account's sessions from the clone, so a merged pull request changes what every seat reads at once, with review, history and machine checks that a native shared Project does not have. The claude.ai Project on each account stays a bare link; nothing syncs, so nothing drifts and no cross-account credential exists anywhere.

The one cost accepted in exchange is synchronization latency: a session sees a change after a git fetch, not at the instant it lands, and the board trails events by a workflow run. For an asynchronous, pull-request-shaped workflow this latency is minutes and almost always already spent by the time a human looks. What genuinely does not replicate: real-time co-presence in one context window, org-wide admin and audit over conversations, and centrally administered data controls. Those are what an Enterprise conversation should be about, not shared instructions, goals or memory, which the $17 rung already shares better than a copied field would.

## Turning it on

1. Merge the stack in order: [#3](https://github.com/OpenSpineConsortium/sdlc-template/pull/3), then [#5](https://github.com/OpenSpineConsortium/sdlc-template/pull/5), then [#7](https://github.com/OpenSpineConsortium/sdlc-template/pull/7). Each is a draft with green CI; say the word and I mark them ready (for #5 and #7 that means deleting their claim files, exactly as the new protocol check requires).

- [x] Merge #3, #5, #7 in order (done 2026-10-09; the merges closed issues #2, #4 and #6, the tidy workflow deleted all three claim branches, and main's CI is green)
- [ ] Main account runs `claude setup-token` and stores it as the repository secret CLAUDE\_CODE\_OAUTH\_TOKEN (enables @claude; everything else already works without it)
- [ ] Optional: set repository variable CLAUDE\_WORKER=true to turn on the scheduled worker
- [ ] Per docs/setup/github.md: protect the default branch, require the check named "check", turn on "Automatically delete head branches", secret scanning and push protection
- [ ] Pick the tier profile in docs/setup/tiers.md and flip only its named settings
- [ ] Re-instantiate the test repository from the updated template rather than back-porting (sdlc-template-test came from an older layer)

## Verification

The numbers above come from a 103-agent research run (2026-10-09): 21 sources fetched, 95 claims extracted, the top 25 adversarially verified by three independent votes each; 23 confirmed, 2 refuted, none left unverified. Both refutations changed the design:

- Refuted: "GitHub overage auto-bills on every plan." In fact, no stored payment method means a hard stop at the quota, which is what makes the economy tier's $0 ceiling a guarantee rather than a hope.
- Refuted: "Claude Enterprise costs $20 a seat." Enterprise pricing is custom and unverified, so this report refuses to price the scale tier.

Still open, deliberately not asserted anywhere above: merge-queue plan gating, CODEOWNERS enforcement limits, secret-scanning availability per plan, Claude Enterprise's shared-Project feature delta, and whether Team-plan org rulesets can require workflows in practice (the June 2025 changelog says yes; the docs flag lags).

Primary sources, all opened and read: [GitHub product usage included](https://docs.github.com/en/billing/reference/product-usage-included) · [GitHub Actions billing](https://docs.github.com/en/billing/concepts/product-billing/github-actions) · [About protected branches](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches) · [About rulesets](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets) · [Org rulesets for Team plans](https://github.blog/changelog/2025-06-16-organization-rulesets-now-available-for-github-team-plans/) · [claude.com/pricing](https://claude.com/pricing) · [Claude Code authentication](https://code.claude.com/docs/en/authentication) · [Claude Code with Pro/Max](https://support.claude.com/en/articles/11145838-use-claude-code-with-your-pro-or-max-plan) · [Claude Code with Team/Enterprise](https://support.claude.com/en/articles/11845131-using-claude-code-with-your-team-or-enterprise-plan) · [Claude Code GitHub Actions](https://code.claude.com/docs/en/github-actions)
