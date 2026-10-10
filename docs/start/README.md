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

sdlc-template is internal to its enterprise, so only the enterprise's members can open it and press "Use this template". Anyone else needs a public copy, which the template's owner publishes with `python3 scripts/crowd.py publish-template` ([crowdsourcing.md](../setup/crowdsourcing.md), Part 1, step 2, route A). Below, TEMPLATE_OWNER/TEMPLATE_NAME is that copy, or OpenSpineConsortium/sdlc-template itself for a member.

## Pick your path

| You want | Page | You need |
| --- | --- | --- |
| One person, one account, a new project | [solo.md](solo.md) | Claude Pro or Max, a GitHub account, git and gh |
| Many cloud sessions on one project at once, on one account or several | [parallel.md](parallel.md) | solo.md done; each account's own plan |
| Several people, each on their own account; or a team of agents in Actions | [team.md](team.md) | solo.md done; each person's own plan |
| Volunteers on their own accounts, in an organization | [crowd.md](crowd.md) | a GitHub organization, a public copy of the template |
| The protocol in a repository you already have | [existing-repo.md](existing-repo.md) | Claude Code, gh, admin on the repository |
| Measure coordination on CooperBench's tasks | [benchmark.md](benchmark.md) | Claude Pro or Max, a cloud environment of your own |
| Change the rules themselves, everywhere at once | [protocol.md](protocol.md) | write access to sdlc-protocol |

## Accounts and tokens

Each line belongs to one account and never leaves it: Anthropic's Consumer Terms forbid sharing account credentials, so nothing here is shared, pooled or committed, and no file in a repository holds any of it.

| What | Made where | Stored where | Held by | Needed for |
| --- | --- | --- | --- | --- |
| claude.ai sign-in | `claude` (a browser sign-in), or claude.ai | your machine and claude.ai | each person, their own | everything |
| GitHub connection for cloud sessions | https://claude.ai/code, Sign in with GitHub | Anthropic, encrypted with your claude.ai account; never in the session's VM | each person, their own | cloud sessions, Projects, routines |
| The Claude GitHub App on the repository | https://github.com/apps/claude/installations/new | the repository's or the organization's GitHub Apps settings | the repository's admin, once | cloud sessions on the repository (a private one needs it), Projects, routines' GitHub triggers |
| gh sign-in | `gh auth login` | your machine | each person, their own | setup-repo.sh, crowd.py, the claim skill on your machine |
| CLAUDE_CODE_OAUTH_TOKEN | `claude setup-token`, on your machine | the repository's Actions secrets | the main account, one per repository | @claude, the Actions worker, team mode |
| COORDBENCH_CLAUDE_TOKEN | `claude setup-token`, on your machine | Environment variables of your own personal cloud environment | each person who runs the benchmark, their own | coordbench's agents |
| COORDINATOR_TRIGGER_URL and COORDINATOR_TRIGGER_TOKEN | the coordinator routine's API trigger, Generate token | the repository's Actions secrets | the main account | the board waking the coordinator when it changes |
| SDLC_APP_ID and SDLC_APP_PRIVATE_KEY | sdlc-app's scripts/register.py | an Actions variable and secret, on the repository or the organization | the owner | a copy's first workflows; the protocol's sync |
| ANTHROPIC_API_KEY | nowhere | nowhere: keep it unset | nobody | nothing; on your machine it would outrank your sign-in and bill the API |

A cloud session needs no token in its environment for project work: it runs on your own sign-in and reaches GitHub through its proxy. Only the benchmark puts one there, because the agents it starts need it.

## The quickest path, about five minutes

You need Claude Pro or Max, signed in at https://claude.ai/code with GitHub connected (Sign in with GitHub), and read access to the template. Branch rules, secret scanning and @claude come later, in [solo.md](solo.md), steps 3 and 6; until then nothing but the session's push guard stops a push to the default branch.

1. Make the repository: open https://github.com/new?template_owner=TEMPLATE_OWNER&template_name=TEMPLATE_NAME&owner=@me&visibility=public, name the repository and create it. You should see the new repository with the template's files.
2. Wait a minute or two, then open https://github.com/ORG/NAME/issues. You should see the issue "Set up this project", opened by the first push's init workflow, and seven labels at https://github.com/ORG/NAME/labels.
3. Install the Claude GitHub App on it: in "Set up this project", follow the link "install the app", which has your repository already chosen, and install. You should see Claude at https://github.com/ORG/NAME/settings/installations. On an organization, an organization owner may need to approve it.
4. Open a task at https://github.com/ORG/NAME/issues/new?template=task.yml, for example the title "Task: write the goal" with the goal "docs/project.md says what this project makes, for whom and what done looks like". You should see it labelled todo, as issue #2 in a new repository.
5. Open https://claude.ai/code?repositories=ORG/NAME, paste the prompt below with your issue's number, and send it. Within minutes you should see the branch `claude/2`, a draft pull request saying "Closes #2", and the claim on the board at https://github.com/ORG/NAME/blob/board/STATE.md.

```
Claim issue 2 with the claim skill and carry it to a ready pull request, as docs/agents/PROTOCOL.md says; work on the branch claude/2, not this session's own branch. gh issue and gh pr are refused in a cloud session, so add the labels, post the plan and open the draft pull request with your GitHub tools or gh api. Do not merge.
```

From there: [solo.md](solo.md) finishes the setup, and [parallel.md](parallel.md) starts several such sessions at once.
