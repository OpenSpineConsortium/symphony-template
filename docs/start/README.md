# Start here

This folder is the way in. It says what the five repositories are, which path fits what you want to do, which accounts and tokens each path needs, and the quickest way to see the whole thing work. Every page is a short list of blocks to copy, each with the settings page it touches and what you should see when it worked. [links.md](links.md) has every settings page as one list of links, and [prompts.md](prompts.md) the sentences to paste into a session.

In the blocks, ORG/NAME is your repository (ORG is the user or the organization that owns it) and N an issue's number. Bash blocks run on macOS, Linux or WSL; PowerShell blocks run in Windows itself. On Windows, run the bash blocks in WSL, since the scripts and the hooks need bash and python3.

## The five repositories

| Repository | What it is |
| --- | --- |
| [OpenSpineConsortium/sdlc-template](https://github.com/OpenSpineConsortium/sdlc-template), internal | The template a project is made from: the instructions, the memory, the board, the workflows and the hooks that every Claude session on the project reads. |
| [OpenSpineConsortium/sdlc-protocol](https://github.com/OpenSpineConsortium/sdlc-protocol), public | The claim protocol as one Python library with no dependencies; every other repository runs a copy of it, so a rule is written once. |
| [OpenSpineConsortium/coordbench](https://github.com/OpenSpineConsortium/coordbench), public | The benchmark that compares ways of coordinating Claude Code agents on CooperBench's task pairs, this protocol among them. |
| [OpenSpineConsortium/sdlc-marketplace](https://github.com/OpenSpineConsortium/sdlc-marketplace), public | The Claude Code plugin `sdlc`: the skills, the board command and the hooks, for a repository not made from the template. |
| OpenSpineConsortium/sdlc-app, private | The GitHub App OpenSpine SDLC, whose token starts a new copy's first workflows and opens the protocol's sync pull requests. |

How they fit: sdlc-protocol holds the rules, and its sync workflow carries every merged change to the other four as a pull request that each one's own check decides. A project is made from sdlc-template and coordinates through GitHub alone: an issue is a task, the first push of a branch `claude/<issue>` is the claim, the board (the file STATE.md on the branch `board`) is the shared state, and a pull request is the handoff. That is why any number of sessions, on any number of accounts, can work one repository at once without talking to each other: GitHub refuses the second push of a claim branch, so two sessions never hold the same issue. [ECOSYSTEM.md](https://github.com/OpenSpineConsortium/sdlc-protocol/blob/main/ECOSYSTEM.md) in sdlc-protocol draws the map: which modules each repository copies and how a change reaches each.

sdlc-template is internal to its enterprise, so only the enterprise's members can open it and press "Use this template". Anyone else needs a public copy, which the template's owner publishes with `python3 scripts/crowd.py publish-template` ([crowdsourcing.md](../setup/crowdsourcing.md), Part 1, step 2, route A). A public copy publishes the template's files and history, so it is made only with the template's owner's agreement. Below, TEMPLATE_OWNER/TEMPLATE_NAME is that copy, or OpenSpineConsortium/sdlc-template itself for a member.

## Pick your path

| You want | Page | You need |
| --- | --- | --- |
| One person, one account, a new project | [solo.md](solo.md) | Claude Pro, Max, Team or an Enterprise seat with Claude Code; a GitHub account; git, gh and Python 3.12 or later |
| Many cloud sessions on one project at once, on one account or several | [parallel.md](parallel.md) | solo.md done; each account's own plan |
| Several people, each on their own account; or a team of agents in Actions | [team.md](team.md) | solo.md done; each person's own plan |
| Volunteers on their own accounts, in an organization | [crowd.md](crowd.md) | a GitHub organization, a public copy of the template |
| The protocol in a repository you already have | [existing-repo.md](existing-repo.md) | Claude Code, git, gh, Python 3.12 or later, admin on the repository; the files the plugin cannot ship, from the template, from a public copy of it, or, while there is no copy, from the template's owner, as step 1 says |
| Measure coordination on CooperBench's tasks | [benchmark.md](benchmark.md) | Claude Pro, Max, Team or an Enterprise seat with Claude Code; GitHub connected at claude.ai/code; a cloud environment of your own; a fork of coordbench, or Write on it, with the Claude GitHub App installed on the repository the session pushes to, unless you connected GitHub with `/web-setup` |
| Change the rules themselves, everywhere at once | [protocol.md](protocol.md) | a fork of sdlc-protocol; Write on it stays the owner's alone, since its Actions hold the App's key, which any writer could read |

## Accounts and tokens

Each line belongs to one account: Anthropic's Consumer Terms forbid sharing account credentials, so nothing here is pooled or committed, and no file in a repository holds any of it. A repository's Actions secret stays with its account only while that account's owner is the repository's one writer: any writer can run a workflow of their own that reads it, and every writer's @claude comment runs on CLAUDE_CODE_OAUTH_TOKEN. So the secrets come out of the repository before anyone else gets Write ([team.md](team.md), step 1). In an organization, its owners have admin on every repository it owns, and a base permission of write makes every member a writer, from the moment a repository is made: a copy made there may hold CLAUDE_CODE_OAUTH_TOKEN only when you are the organization's only owner and its base permission is read or none. Otherwise leave out `--token` and @claude ([solo.md](solo.md), steps 3 and 6), or make the copy in an organization you alone own.

| What | Made where | Stored where | Held by | Needed for |
| --- | --- | --- | --- | --- |
| claude.ai sign-in | `claude` (a browser sign-in), or claude.ai | your machine and claude.ai | each person, their own | everything |
| GitHub connection for cloud sessions | https://claude.ai/code, Sign in with GitHub | Anthropic, encrypted with your claude.ai account; never in the session's VM | each person, their own | cloud sessions, Projects, routines |
| The Claude GitHub App on the repository | https://github.com/apps/claude/installations/new | the repository's or the organization's GitHub Apps settings | the repository's admin, once | cloud sessions on the repository (a private one needs it to clone, and any one for the session's push, unless GitHub is connected with `/web-setup`), Projects, routines' GitHub triggers, @claude, the Actions worker, team mode |
| gh sign-in | `gh auth login` | your machine | each person, their own | setup-repo.sh, crowd.py, the claim skill on your machine |
| CLAUDE_CODE_OAUTH_TOKEN | `claude setup-token`, on your machine | the repository's Actions secrets | the main account, one per repository, only while its owner is the repository's one writer | @claude, the Actions worker, team mode |
| COORDBENCH_CLAUDE_TOKEN | `claude setup-token`, on your machine | Environment variables of your own personal cloud environment | each person who runs the benchmark, their own | coordbench's agents |
| COORDINATOR_TRIGGER_URL and COORDINATOR_TRIGGER_TOKEN | the coordinator routine's API trigger, Generate token | the repository's Actions secrets | the main account, only while its owner is the repository's one writer | the board waking the coordinator when it changes |
| SDLC_APP_ID and SDLC_APP_PRIVATE_KEY | sdlc-app's scripts/register.py | an Actions variable and secret: on sdlc-protocol, for the sync; on an organization, for its copies' first push, only where the owner alone writes every repository the organization owns, since the visibility that reaches a copy from its first push (all, or private, gh's default) also puts the key into every copy a member makes there, where that member is admin | the owner; the key comes out of a repository others write to | the first workflows of a copy made in an organization only the owner writes to (any other copy runs its init on GITHUB_TOKEN; its Checks start with its first pull request and its Board with the first issue or pull request a person opens); the protocol's sync |
| ANTHROPIC_API_KEY | nowhere | nowhere: keep it unset | nobody | nothing; on your machine it would outrank your sign-in and bill the API |

A cloud session needs no token in its environment for project work: it runs on your own sign-in and reaches GitHub through its proxy. Only the benchmark puts one there, because the agents it starts need it.

## The quickest path, about five minutes

You need Claude Pro, Max or Team, or an Enterprise seat with Claude Code, signed in at https://claude.ai/code with GitHub connected (Sign in with GitHub; on Team and Enterprise an Owner first turns on the GitHub connector at https://claude.ai/admin-settings/connectors), and read access to the template. Branch rules, secret scanning and @claude come later, in [solo.md](solo.md), steps 3 and 6; until then nothing but the session's push guard stops a push to the default branch.

1. Make the repository. A member of the template's enterprise makes it private, in an organization of the enterprise, whose plan already enforces branch rules and offers auto-merge on a private repository: https://github.com/new?template_owner=OpenSpineConsortium&template_name=sdlc-template&owner=OpenSpineConsortium&visibility=private, with another organization of the enterprise in place of `owner=OpenSpineConsortium` if that is where you make repositories. An organization's owners write every repository it owns, and an organization secret reaches a copy from its first push, so before you create it read "Accounts and tokens" above: the copy holds no subscription token unless you are the organization's only owner, and the organization must not hold the App's key for all its repositories or all its private ones (the SDLC_APP_PRIVATE_KEY row); if it does, ask an organization owner to limit it to a list of repositories they alone write, or remove it, first. Anyone else makes it from the public copy: https://github.com/new?template_owner=TEMPLATE_OWNER&template_name=TEMPLATE_NAME&owner=@me&visibility=public. Name the repository and create it. You should see the new repository with the template's files.
2. Wait a minute or two, then open https://github.com/ORG/NAME/issues. You should see the issue "Set up this project", opened by the first push's init workflow, and seven labels at https://github.com/ORG/NAME/labels.
3. Install the Claude GitHub App on it: in "Set up this project", follow the link "install the app", which usually has your repository already chosen (if not, pick it), and install. You should see Claude at https://github.com/ORG/NAME/settings/installations. On an organization, an organization owner may need to approve it.
4. Open a task at https://github.com/ORG/NAME/issues/new?template=task.yml, for example the title "Task: write the goal" with the goal "docs/project.md says what this project makes, for whom and what done looks like" and the acceptance "bash scripts/check.sh passes and the owner agrees"; the form does not submit without an Acceptance. You should see it labelled todo, as issue #2 in a new repository.
5. Open https://claude.ai/code?repositories=ORG/NAME, paste the prompt below with your issue's number, and send it. Within minutes you should see the branch `claude/2`, a draft pull request saying "Closes #2", and the claim on the board at https://github.com/ORG/NAME/blob/board/STATE.md.

```
Claim issue 2 with the claim skill and carry it to a ready pull request, as docs/agents/PROTOCOL.md says; work on the branch claude/2, not this session's own branch. gh issue and gh pr are refused in a cloud session, so add the labels, post the plan and open the draft pull request with your GitHub tools or gh api. Mark the pull request ready with your GitHub tool update_pull_request (draft false), not gh api, which cannot change a draft; if you have no such tool, say so and stop before you delete the claim file. Do not merge.
```

From there: [solo.md](solo.md) finishes the setup, and [parallel.md](parallel.md) starts several such sessions at once.
