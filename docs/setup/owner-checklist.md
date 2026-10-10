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
admin rights on the repository; a cloud session cannot run it, having
neither gh nor admin rights. The script creates the ruleset
docs/setup/ruleset-main.json unless one of that name is already listed
for the repository, turns on "Automatically delete head branches" and
"Allow auto-merge", turns on secret scanning and then push protection
(and says so and carries on where the plan or the visibility offers
neither: a Free organization's private repository has no Secret
Protection), creates or updates the seven labels from the one list in
tools/template_init.py, sets each variable given as `--var NAME=VALUE`,
and with `--token` stores the secret CLAUDE_CODE_OAUTH_TOKEN from gh's
hidden prompt, so the token is never on a command line, in a file or on
the screen. Each step prints one line; run it again at any time, and
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

## One-click links

Each opens the exact page; the sections below say what to do there.

- Install the Claude GitHub App: https://github.com/apps/claude/installations/new
- The same, with this organization and repository preselected (the form GitHub documents for an app's install URL, with the ids the API reports for OpenSpineConsortium/sdlc-template, not tried live from a session): https://github.com/apps/claude/installations/new/permissions?suggested_target_id=285817514&repository_ids[]=1411163972
- Connect GitHub to Claude: https://claude.ai/settings/connectors
- Claude Code in the cloud (sessions, environment settings): https://claude.ai/code
- How cloud environments, variables and network access work: https://code.claude.com/docs/en/cloud-environments
- The repository's rulesets (New ruleset, Import): https://github.com/OpenSpineConsortium/sdlc-template/settings/rules
- The repository's general settings (auto-delete, auto-merge): https://github.com/OpenSpineConsortium/sdlc-template/settings
- Secret scanning and push protection: https://github.com/OpenSpineConsortium/sdlc-template/settings/security_analysis
- New repository secret: https://github.com/OpenSpineConsortium/sdlc-template/settings/secrets/actions/new
- New repository variable: https://github.com/OpenSpineConsortium/sdlc-template/settings/variables/actions/new
- Organization secrets and variables (shared by every repository of the organization): https://github.com/organizations/OpenSpineConsortium/settings/secrets/actions
- Organization rulesets (applied to every repository of the organization): https://github.com/organizations/OpenSpineConsortium/settings/rules
- claude.ai Projects: https://claude.ai/projects

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
   must have write access to OpenSpineConsortium/sdlc-template.
3. **The Claude GitHub App** (github.com/apps/claude) must be installed on
   the OpenSpineConsortium organisation with access to sdlc-template, so
   cloud sessions can push. An organisation owner installs it once; a new
   account reuses it.
4. **Start a cloud session** at claude.ai/code on
   OpenSpineConsortium/sdlc-template, on the default network access level,
   and type "continue". main's .claude/session.md sends the session to the
   branch claude/10 and its checkpoint.

That is all the code work needs. Running agents on benchmark tasks needs
section 2 as well.

## 2. To run the experiment (agents on CooperBench tasks)

The experiment now lives in its own repository,
OpenSpineConsortium/coordbench, and runs in a cloud session opened
there; these steps are the same for it.

1. **Make a subscription token** on your own computer, signed in to the
   Claude account whose usage the run should draw on:
   `claude setup-token`. It prints a long-lived OAuth token (about a year).
2. **Put it in the cloud environment, not the repository**: in a claude.ai/code
   session, open the environment menu in the session's title bar, Edit,
   and add an environment variable named `CLAUDE_CODE_OAUTH_TOKEN` with the
   token as its value. A session sees only variables that existed when it
   started, so start a **new** session after adding it.
3. **Do not set `ANTHROPIC_API_KEY`** anywhere in that environment:
   CooperBench's adapter prefers it over the token, and it bills the API.
4. **Optional, for the last 7 of the 50 pairs**: under the same Edit,
   Network access, add these allowed domains (keep "allow package
   managers" ticked): `openaipublic.blob.core.windows.net` (tiktoken),
   `huggingface.co` (outlines 1706), `pypi.nvidia.com` (llama_index). The
   tasks' containers would then still need those downloads baked into
   their images (coordbench's bench/cooperbench/README.md says why);
   without this step the run covers the 42 pairs that grade.
5. Nothing on GitHub is needed for the experiment. The session starts
   Docker inside its own container (coordbench's
   bench/cooperbench/setup.sh); images come from mirror.gcr.io because
   Docker Hub rate-limits the cloud host; the disk holds about one large
   task image at a time; a session's background command stops after two
   hours, so runs go one task at a time.

Cost, for planning: about $0.43 of usage per agent session at API prices;
the 42 gradable pairs over four arms are about 294 sessions (about $125 of
plan usage, spread over several usage windows); a pilot on one task is
about 42 sessions.

## 3. The repository's GitHub settings (sdlc-template and every copy)

`bash scripts/setup-repo.sh` does 1 to 4 in one run (above). By hand,
under Settings of the repository, as docs/setup/github.md describes:

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
5. **Template**: sdlc-template is already marked as a template repository.

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
   `COORDINATOR_TRIGGER_TOKEN`.

## 5. A claude.ai Project per account (optional)

docs/setup/claude-project.md: one thin Project per account, this repository
as its only resource, its instructions, description and memory left blank;
the repository's CLAUDE.md and docs are the one source. Projects are in
beta on Pro and Max.

## 6. The other repositories

The template is one of five repositories under OpenSpineConsortium;
docs/project.md says what each is for. Sessions built the other four but
could not finish setting them up: the push guard refuses any push to a
branch named main, so each got its first branch under another name, and
the session's git proxy refused to push a tag. In this order:

1. **Rename each default branch to main**, as an admin of the
   repository, in sdlc-protocol (now `wip/extract`), coordbench (now
   `claude/split`) and sdlc-marketplace (now `claude/init`); sdlc-app
   already has main, and its first change is pull request
   OpenSpineConsortium/sdlc-app#1, to merge first. On each branches page,
   https://github.com/OpenSpineConsortium/<name>/branches, the default
   branch's menu, Rename branch. GitHub redirects the old name, and the
   default branch keeps being the default under its new name.
2. **Release sdlc-protocol 0.1.0**: create the release v0.1.0 on the commit
   f139a079d881ff245511625e443f6eff1318c727, the one tools/VENDORED names
   (Releases, Draft a new release, a new tag v0.1.0 on that commit; or
   `gh release create v0.1.0 --repo OpenSpineConsortium/sdlc-protocol
   --target f139a079d881ff245511625e443f6eff1318c727 --title
   "sdlc-protocol 0.1.0"`). Coordbench, the plugin and the App are to be
   re-vendored from that tag.
3. **Register the GitHub App** from a clone of sdlc-app, on your own
   computer, as an owner of the organization:
   `python3 scripts/register.py --org OpenSpineConsortium`, which names it
   OpenSpine SDLC (slug openspine-sdlc): App names are global across GitHub
   and "sdlc" belongs to the account @sdlc, so if a name is taken, add
   `--name "<another>"`. Install the App
   on the organization (Install App; "All repositories" also covers a copy
   made later), then set the variable `SDLC_APP_ID` and the secret
   `SDLC_APP_PRIVATE_KEY` with the commands register.py prints; set them
   at the organization with `--visibility all` for copies to have them on
   their first push. .github/workflows/template-init.yml then makes the
   App's token, so a new copy's first commit starts its Checks and its
   Board; without the two settings it runs on GITHUB_TOKEN as before.
4. **Merge #12**, the push guard's newline fix.
5. **Then a session marks #13 ready**: it deletes docs/agents/claims/10.md
   in that commit, as docs/agents/PROTOCOL.md (Finish) requires, and you
   merge it.

Nothing is to be done for sdlc-marketplace in this repository:
.claude/settings.json names the marketplace but enables no plugin, because
the plugin runs the same hooks this repository's settings already run, and
enabling it here would run each of them twice; the plugin is for
repositories not made from the template (its README says how to install it).

## 7. Where things stand

- main: the template, released; .claude/session.md points at the work.
- claude/10, draft pull request #13 (issue #10): the claim protocol
  vendored from sdlc-protocol 0.1.0 under tools/sdlc_protocol, with
  tools/board.py, check_protocol.py and team.py as shims over it;
  experiment/ moved out to OpenSpineConsortium/coordbench; the App's token
  in template-init. Its .claude/session.md is the full checkpoint. It
  stays a draft until #12 is merged (section 6, step 4).
- claude/11, pull request #12 (issue #11): the push guard's newline fix
  alone, rebased on main, 52 lines over main, ready for review.
- sdlc-protocol, coordbench, sdlc-marketplace and sdlc-app: built and
  pushed on the branches section 6 names, waiting on its steps.
- The main account's weekly Claude usage resets on 2026-10-15 at 11:00 UTC.
