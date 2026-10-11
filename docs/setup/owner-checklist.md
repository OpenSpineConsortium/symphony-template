# Owner's checklist: every authorization, secret, token, variable and setting

Everything a person (not a session) has to set up so the work continues
on any account, gathered in one place on 2026-10-09 from the sessions that
built it. Sessions cannot do these steps themselves: they need the owner's
own accounts. Never paste a token into a chat or commit one to the
repository; each one goes only where this page says.

## One command for the GitHub side

Every repository setting of section 3 and the variables of section 4 are
one run of `bash scripts/setup-repo.sh` from a clone, on your own
computer, with the GitHub CLI signed in (`gh auth login`) as a user with
admin rights on the repository; a cloud session cannot run it: gh is
installed there, but its GitHub proxy refuses gh's GraphQL commands, and
the session has no admin rights. The script creates the ruleset
docs/setup/ruleset-main.json unless one of that name is already listed
for the repository, turns on "Automatically delete head branches" and
"Allow auto-merge", turns on secret scanning and then push protection
(and says so and carries on where the plan or the visibility offers
neither: a Free organization's private repository has no Secret
Protection), creates or updates the seven labels from the one list in
tools/template_init.py, sets each variable given as `--var NAME=VALUE`,
and with `--token` stores the secret CLAUDE_CODE_OAUTH_TOKEN from gh's
hidden prompt, so the token is never on a command line, in a file or on
the screen, and last prints any line of .github/CODEOWNERS that GitHub
cannot resolve. Each step prints one line; run it again at any time, and
nothing is done twice. The ruleset goes in whatever the plan, but on
GitHub Free a private repository's ruleset is written and not enforced
(docs/setup/tiers.md); the script says so when the repository is private.

Two things it cannot do. The token itself: only `claude setup-token`,
run by you and signed in to the account whose subscription the runs
should draw on, makes one, so the script asks you to run that in another
terminal and paste the result (or run `/install-github-app` in Claude
Code instead, which installs the app and stores the secret in one OAuth
flow, docs/setup/claude-action.md). And anything outside the repository:
the Claude GitHub App's installation, the organization's rulesets,
secrets and variables (below), the cloud environment's variable
(section 2) and the claude.ai Projects (section 5) are pages you open,
from the links that follow.

A project worked by volunteers on their own Claude accounts takes another
command instead, and none of the token, variable or auto-merge steps on this
page: `python3 scripts/crowd.py setup ORG/NAME --area AREA`, then, after
reading the pull request it opens, `python3 scripts/crowd.py finish
ORG/NAME`. docs/setup/crowdsourcing.md, Part 1, says what each does and what
is left by hand; setup-repo.sh refuses to run once crowd mode is on, or
when it cannot tell, since it would turn auto-merge on and can store a
token.

## One-click links

Each opens the exact page; the sections below say what to do there.

- Install the Claude GitHub App: https://github.com/apps/claude/installations/new
- The same, with this organization and repository preselected (the form GitHub documents for an app's install URL, with the ids the API reports for OpenSpineConsortium/symphony-template, not tried live from a session): https://github.com/apps/claude/installations/new/permissions?suggested_target_id=285817514&repository_ids[]=1411163972
- Connect GitHub to Claude: Sign in with GitHub at https://claude.ai/code; your connectors, to disconnect it: https://claude.ai/customize/connectors
- Claude Code in the cloud (sessions, environment settings): https://claude.ai/code
- How cloud environments, variables and network access work: https://code.claude.com/docs/en/cloud-environments
- The repository's rulesets (New ruleset, Import): https://github.com/OpenSpineConsortium/symphony-template/settings/rules
- The repository's general settings (auto-delete, auto-merge): https://github.com/OpenSpineConsortium/symphony-template/settings
- Secret scanning and push protection: https://github.com/OpenSpineConsortium/symphony-template/settings/security_analysis
- New repository secret: https://github.com/OpenSpineConsortium/symphony-template/settings/secrets/actions/new
- New repository variable: https://github.com/OpenSpineConsortium/symphony-template/settings/variables/actions/new
- Organization secrets and variables (shared by every repository of the organization): https://github.com/organizations/OpenSpineConsortium/settings/secrets/actions
- Organization rulesets (applied to every repository of the organization): https://github.com/organizations/OpenSpineConsortium/settings/rules
- Projects in Claude Code: https://claude.ai/code/projects/browse

A template copies files only, never settings, secrets or variables: the
command above sets the repository's, and the next section says what an
organization can set once for every repository it makes.

## What an organization can set once for every repository it makes

Three things an organization sets once reach every repository it makes
afterwards, copies of this template included, with no step in the new
repository; each needs the plan named. Checked against GitHub's own
documentation and REST description on 2026-10-09; where a sentence
could not be read from a primary source, it says so.

- **Organization rulesets** need GitHub Team or Enterprise; a Free
  organization has none. A ruleset targets all repositories (`~ALL`),
  the repositories matching a name pattern, or a chosen list; the first
  two are evaluated against the organization as it stands, so a
  repository made later from the template is covered without a step (by
  construction; the documentation never says "new repositories" in so
  many words). docs/setup/ruleset-org.json is ruleset-main.json in the
  shape the organization level needs, the repository_name condition
  beside ref_name, targeting `~ALL`: import it at the organization's
  rules page (New ruleset, Import a ruleset). Only the organization's
  owners can edit it afterwards; a repository's admins may add rulesets
  of their own, which aggregate with it, and the one command above
  skips its own ruleset when one of that name is already listed. Whether
  the import page accepts the repository-shaped file and asks for
  targets was not verified, which is why the second file exists.
- **Organization Actions secrets and variables** can be made on any
  plan, with a policy of all repositories, private repositories only, or
  a chosen list; "all" and "private only" cover a repository made later,
  a list does not until the repository is added. On GitHub Free a private
  repository cannot read them at all, so there they serve only the
  organization's public repositories. From the command line:
  `gh secret set CLAUDE_CODE_OAUTH_TOKEN --org ORG --visibility all` and
  `gh variable set CLAUDE_WORKER --org ORG --visibility all --body true`;
  gh's default visibility is "private", which on a Free organization
  would make the value readable nowhere. One organization-wide
  CLAUDE_CODE_OAUTH_TOKEN means every repository draws on the main
  account's subscription; Claude Code's own documentation suggests an API
  key for a secret shared across repositories, which this project's rule
  of no API billing rules out.
- **Settings as code**, a settings file an app applies, is not a GitHub
  feature but one of two community apps. github/safe-settings keeps every
  repository's settings in one admin repository of the organization and
  applies them when a repository is created, but needs a GitHub App of
  your own and your own hosting (no hosted instance exists, and whether
  GitHub supports it as a product is unverified). The Repository Settings
  App (repository-settings/app, formerly probot/settings) is hosted and
  reads .github/settings.yml from each repository, but it makes anyone
  with push rights an admin in effect, and whether it writes rulesets
  rather than branch protection is unverified. Both need an app
  installation, a new dependency, so by .claude/rules/writing.md it is an
  issue first: "Settings as code", opened by the session that wrote this
  page. The native equivalents are the two bullets above and, for secret
  scanning and push protection, the organization's security
  configurations.

One observation for the owner to confirm: the API reports this
repository's visibility as "internal", which GitHub offers only to
organizations owned by an enterprise account, so the organization's plan
may not be the Free plan this page otherwise assumes, and the Team-and-up
items above may already be open to it.

## 1. To continue the work on a new Claude account

1. **Claude plan.** A Pro or Max subscription on the new account. No API
   key and no API billing anywhere: everything runs on the subscription.
   Keep "extra usage" (usage credits) off unless overage billed at API
   rates is wanted; with it off, work simply stops at the plan's limit.
2. **Connect GitHub to Claude** on the new account: claude.ai, Settings,
   Connectors, GitHub (or claude.ai/code prompts for it). The GitHub user
   must have write access to OpenSpineConsortium/symphony-template.
3. **The Claude GitHub App** (github.com/apps/claude) must be installed on
   the OpenSpineConsortium organisation with access to symphony-template, so
   cloud sessions can push. An organisation owner installs it once; a new
   account reuses it.
4. **Start a cloud session** at claude.ai/code on
   OpenSpineConsortium/symphony-template, on the default network access level,
   and type "continue": the session reads main's .claude/session.md, the
   last checkpoint, first. docs/start/prompts.md has the sentences for
   the everyday moves.

That is all the code work needs. Running agents on benchmark tasks needs
section 2 as well.

## 2. To run the experiment (agents on CooperBench tasks)

The experiment now lives in its own repository,
OpenSpineConsortium/coordbench, and runs in a cloud session opened
there; these steps are the same for it.

1. **Make a subscription token** on your own computer, signed in to the
   Claude account whose usage the run should draw on:
   `claude setup-token`. It prints a long-lived OAuth token (about a year).
2. **Put it in the cloud environment, not the repository**: at
   https://claude.ai/code, select the cloud icon showing the current
   environment's name, in the row above the message box, then Cloud, and
   Add cloud environment (or hover an environment and select its
   settings icon to edit it), and add the line
   `COORDBENCH_CLAUDE_TOKEN=<the token>` under Environment variables,
   not Network secrets. The environment withholds a variable named
   `CLAUDE_CODE_OAUTH_TOKEN` from the session, since it runs the
   session's own Claude Code, so coordbench reads the alias and copies
   it to that name for its agents. A running session keeps the values it
   last read, so start a **new** session after adding it
   (docs/start/benchmark.md has the whole run).
3. **Do not set `ANTHROPIC_API_KEY`** anywhere in that environment:
   CooperBench's adapter prefers it over the token, and it bills the API.
4. **Optional, for the last 7 of the 50 pairs**: in the same dialog, set
   Network access to Custom and add these allowed domains (keep "Also
   include default list of common package managers" ticked):
   `openaipublic.blob.core.windows.net` (tiktoken), `huggingface.co`
   (outlines 1706), `pypi.nvidia.com` (llama_index). The tasks'
   containers would then still need those downloads baked into their
   images (coordbench's bench/cooperbench/README.md says why); without
   this step the run covers the 42 pairs that grade.
5. On GitHub the experiment needs only the account connected at
   claude.ai/code, which every cloud session needs, and a fork of
   coordbench (or Write on it) to push a results page to, with the Claude
   GitHub App installed on the repository the session pushes to
   (https://github.com/apps/claude/installations/new, Only select
   repositories), unless GitHub was connected with `/web-setup`: a session
   connected through the App pushes with the App's token, which writes
   only where the App is installed. The session starts Docker inside its
   own container (coordbench's bench/cooperbench/setup.sh); images come
   from mirror.gcr.io because Docker Hub rate-limits the cloud host; the
   disk holds about one large task image at a time; a session's background
   command stops after 30 minutes, or two hours at most when started with
   that timeout, so runs go one task at a time.

Cost, for planning: about $0.43 of usage per agent session at API prices;
the 42 gradable pairs over four arms are about 294 sessions (about $125 of
plan usage, spread over several usage windows); a pilot on one task is
about 42 sessions.

## 3. The repository's GitHub settings (symphony-template and every copy)

`bash scripts/setup-repo.sh` does 1 to 4 and checks 5 in one run
(above); a repository adopted through the front door with its Setup App
installed has 1 to 4 done by that run, as its pull request's section
Settings says. By hand, under Settings of the repository, as
docs/setup/github.md describes:

1. **Rules**: Rules, Rulesets, New ruleset, Import a ruleset, and choose
   docs/setup/ruleset-main.json (protects the default branch, requires the
   check named "check").
2. **General**: tick "Automatically delete head branches". For team mode
   also tick "Allow auto-merge", and optionally untick "Require branches
   to be up to date" in the ruleset.
3. **Code security**: turn on secret scanning and push protection.
4. **Labels**: a copy gets them from template-init (todo, claimed,
   in-review, blocker, account:main, epic, blocked). The template
   repository itself has none; add them by hand only if this repository's
   own issues should be labelled.
5. **Code owners**: open .github/CODEOWNERS on GitHub and see that no
   line is marked as an error. template-init names the owner there, or in
   an organization's copy the person who made it, since GitHub asks a user
   or a team for review and never an organization; a copy made by an app
   still names the organization, so change that line by pull request
   (docs/setup/github.md, section 7).
6. **Template**: symphony-template is already marked as a template repository.
7. **Field metrics**: nothing to set. .github/workflows/metrics.yml writes
   the project's aggregates to the branch `metrics` once a day, which
   OpenSpineConsortium's collector reads only where the Symphony App
   is installed; the word off in .github/symphony-metrics, or the repository
   variable `SDLC_METRICS` = `off`, turns sharing off. Like `board`, the
   branch must stay outside every ruleset (docs/setup/metrics.md).

## 4. Claude inside GitHub Actions (optional; @claude, the worker, team mode)

1. **The token as a repository secret**: run `/install-github-app` in
   Claude Code on your computer, as the main account. One OAuth flow
   installs the Claude GitHub App and stores the repository secret
   `CLAUDE_CODE_OAUTH_TOKEN`. By hand instead: `claude setup-token`, then
   Settings, Secrets and variables, Actions, New repository secret
   `CLAUDE_CODE_OAUTH_TOKEN`. Replace it when it expires (about a year).
   docs/setup/claude-action.md has the details.
2. **Repository variables** (Settings, Secrets and variables, Actions,
   Variables, or `scripts/setup-repo.sh --var NAME=VALUE`), each optional:
   - `CLAUDE_WORKER` = `true`: the scheduled worker in Actions. Pick it or
     the worker routine in a claude.ai Project, not both.
   - `CLAUDE_TEAM` = a JSON list of member names, as `["w1","w2","w3"]`:
     team mode (docs/agents/TEAM.md); needs `CLAUDE_WORKER` too, and
     "Allow auto-merge" above.
   - `CLAUDE_MAX_ROUNDS` (default 6): how many rounds a member runs in a row.
   - `CLAUDE_ALLOWED_TOOLS`: replaces the tools the Actions sessions may use.
3. **Coordinator routine** (optional, once a second account joins):
   docs/agents/routines/coordinator.md. Its API trigger's address and bearer
   token go into the repository secrets `COORDINATOR_TRIGGER_URL` and
   `COORDINATOR_TRIGGER_TOKEN` only while every writer of the repository is
   you, since any writer's workflow can read them and each fire spends the
   main account's usage; otherwise leave the trigger out
   (docs/start/team.md, steps 1 and 6), and the hourly schedule and the
   pull request events carry the routine.

## 5. A claude.ai Project per account (optional)

docs/setup/claude-project.md: one thin Project per account, this repository
as its only resource, its instructions, description and memory left blank;
the repository's CLAUDE.md and docs are the one source. Projects are in
beta on Pro and Max.

## 6. The other repositories

The template is one of five repositories under OpenSpineConsortium;
docs/project.md says what each is for, and symphony-protocol's
[ECOSYSTEM.md](https://github.com/OpenSpineConsortium/symphony-protocol/blob/main/ECOSYSTEM.md)
maps which of them copies which of the library's modules. The first
round of setting them up is done. Checked on 2026-10-10: each of the
four has main as its default branch, symphony-protocol has the release tag
v0.1.0 on f139a079d881ff245511625e443f6eff1318c727, and #12 and #13 are
merged. The App Symphony Dev (slug symphony-dev, id 5258276) is
registered, and its id and key are set on this repository.

### The sync: one push to symphony-protocol reaches every repository

A change to the protocol is made in symphony-protocol alone. Its CI runs each
consumer's own check on the change before it merges (the jobs
`downstream (<name>)`), and the push to its main starts its workflow
Sync, which vendors the change into each consumer and opens the pull
request `symphony-protocol/sync` there, as the App, with auto-merge on where
the repository allows it. Nobody copies anything by hand. Until the
variable below is set, the sync skips itself, stays green and says in its
run's summary what is missing. Once, in this order:

1. **Install the App on all five repositories**: the organization's
   settings, GitHub Apps, Symphony, Configure, and choose "All
   repositories" or add symphony-protocol, symphony-template, coordbench,
   symphony-marketplace and symphony-app
   (https://github.com/organizations/OpenSpineConsortium/settings/installations).
   The sync's token is scoped to one consumer at a time, and the App
   needs no permission beyond the ones it was registered with (contents
   and pull requests, write).
2. **Give symphony-protocol the App's id and key**, the same values this
   repository has. From a clone of symphony-app, whose .sdlc-app.env
   register.py wrote, so the key goes through a pipe and never onto the
   screen:

   ```
   gh variable set SDLC_APP_ID --repo OpenSpineConsortium/symphony-protocol --body 5258276
   python3 scripts/register.py --print-key | gh secret set SDLC_APP_PRIVATE_KEY --repo OpenSpineConsortium/symphony-protocol
   ```

   Where the two are already set at the organization with `--visibility
   all`, symphony-protocol, being public, has them, and this step is done.
3. **Allow auto-merge on the three consumers the sync arms it for**.
   `bash scripts/setup-repo.sh` turns it on here (section 3); these
   commands do it for all three, and change nothing where it is on already:

   ```
   gh api -X PATCH repos/OpenSpineConsortium/symphony-template -F allow_auto_merge=true
   gh api -X PATCH repos/OpenSpineConsortium/coordbench -F allow_auto_merge=true
   gh api -X PATCH repos/OpenSpineConsortium/symphony-marketplace -F allow_auto_merge=true
   ```

   The sync does not arm auto-merge for symphony-app, which ecosystem.json
   gives `"auto_merge": false` (docs/start/protocol.md, step 6), so you
   merge the App's sync pull request yourself.
4. **Require the check `check` on each consumer's main**, with a ruleset,
   so auto-merge waits for it to be green. Here
   docs/setup/ruleset-main.json already does (section 3); the same file
   imports into coordbench, symphony-marketplace and symphony-app (their Settings,
   Rules, Rulesets, New ruleset, Import a ruleset); on symphony-app the check
   then gates your own merge (step 3). On symphony-protocol require `check`
   and, if you like, the `downstream (<name>)` jobs, so a change that
   breaks a consumer cannot merge there.
5. **Land the pull requests that brought the sync**, one per repository
   from the branch `claude/festive-edison-al7xu2`, the four consumers'
   first. symphony-protocol's `downstream` jobs vendor its change into each
   consumer's main and run that consumer's check there, and until a
   consumer's own pull request has merged, its tests on main still read
   the old record of one line and fail. Then symphony-protocol's, with a merge
   commit rather than a squash, so the commit the consumers' records name
   stays the last one that changed the package and the first sync finds
   every consumer up to date. Push symphony-protocol's branch first all the
   same: each consumer's CI clones symphony-protocol and fails when the clone
   has no commit of the one its VENDORED names, which until the library's
   pull request merges is on that branch alone. The consumers' branches
   change their .github/workflows/ci.yml, so they go up with a token that
   has the workflow scope.
6. **Release symphony-protocol 0.2.0** once its pull request is merged
   (done on 2026-10-10, as v0.2.0, under the library's name of the day):
   `gh release create v0.2.0 --repo OpenSpineConsortium/symphony-protocol
   --target <the merge commit> --title "sdlc-protocol 0.2.0"`.
7. **Run the sync once by hand** to see it work: symphony-protocol's Actions
   tab, Sync, Run workflow. Its summary has a row per consumer: up to
   date, or the pull request it opened or updated and whether auto-merge
   is on.

Afterwards, a sync pull request that waits because main moved under it
(the ruleset requires a branch to be up to date) needs no hand: the next
push to symphony-protocol, the weekly run or Run workflow rebuilds the branch
on the consumer's main as it then is.

Nothing is to be done for symphony-marketplace in this repository:
.claude/settings.json names the marketplace but enables no plugin, because
the plugin runs the same hooks this repository's settings already run, and
enabling it here would run each of them twice; the plugin is for
repositories not made from the template (its README says how to install it).

## 7. Where things stand

- main: the template, with the claim protocol vendored from symphony-protocol
  under tools/sdlc_protocol and tools/board.py, check_protocol.py, team.py
  and guard_push.py as shims over it; experiment/ moved out to
  OpenSpineConsortium/coordbench; the App's token in template-init.
- The sync of section 6 and symphony-protocol 0.2.0, whose record lists the
  sha256 of every copied file and each consumer's check holds its copy
  to, came as one pull request per repository from the branch
  `claude/festive-edison-al7xu2`, to land in the order of section 6,
  step 5.
- The main account's weekly Claude usage resets on 2026-10-15 at 11:00 UTC.
