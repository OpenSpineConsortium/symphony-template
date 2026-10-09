# Owner's checklist: every authorization, secret, token, variable and setting

Everything a person (not a session) has to set up so the work continues
on any account, gathered in one place on 2026-10-09 from the sessions that
built it. Sessions cannot do these steps themselves: they need the owner's
own accounts. Never paste a token into a chat or commit one to the
repository; each one goes only where this page says.

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
   their images (experiment/README.md says why); without this step the run
   covers the 42 pairs that grade.
5. Nothing on GitHub is needed for the experiment. The session starts
   Docker inside its own container (experiment/setup.sh); images come from
   mirror.gcr.io because Docker Hub rate-limits the cloud host; the disk
   holds about one large task image at a time; a session's background
   command stops after two hours, so runs go one task at a time.

Cost, for planning: about $0.43 of usage per agent session at API prices;
the 42 gradable pairs over four arms are about 294 sessions (about $125 of
plan usage, spread over several usage windows); a pilot on one task is
about 42 sessions.

## 3. The repository's GitHub settings (sdlc-template and every copy)

Under Settings of the repository, as docs/setup/github.md describes:

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
   Variables), each optional:
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

## 6. Where things stand

- main: the template, released; .claude/session.md points at the work.
- claude/10, draft pull request #13 (issue #10): the experiment kit and
  coordbench; its .claude/session.md is the full checkpoint and
  experiment/coordbench/REVIEW.md the 28 findings to fix first.
- claude/11, draft pull request #12 (issue #11): the push guard's rewrite,
  work in progress.
- The main account's weekly Claude usage resets on 2026-10-15 at 11:00 UTC.
