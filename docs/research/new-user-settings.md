# What a new user still sets by hand

Source: the thread "New user setup" in the symphony2 Project, 2026-10-18, answering the owner's question of that day: "i want as few manual settings changes required for users, im assuming all of the settings changes i made will be made by the setup app for new users?" Read against symphony-start's scripts/setup.py and scripts/adopt.py at its main of 2026-10-18, the template's scripts/setup-repo.sh and docs/setup/, the owner's to-do lists of 2026-10-14e, 2026-10-15b and 2026-10-16, and GitHub's own documentation and REST description (github/docs and github/rest-api-description on raw.githubusercontent.com, the same day).

## The answer in short

Mostly yes. Every per-repository setting the owner changed by hand on his own repositories is applied by Symphony Setup in the adoption run, or made by the run itself. What the owner did as the Apps' owner is done once for everyone and never reaches a user. What is left for a new user is four things: one of them, letting GitHub Actions open pull requests in an organization, is likely refused for every new organization and can only be automated by giving Symphony Setup an organization-wide permission, which is the owner's call; the other three need the user's own sign-in or have no API an App may call.

## Each change, and who makes it for a new user

Applied for every new user by the adoption run (symphony-start's setup.py with Symphony Setup's token, or adopt.yml with SymphonyBoard's):

- The default branch's ruleset (docs/setup/ruleset-main.json; in mode existing without the required check).
- "Automatically delete head branches" and "Allow auto-merge".
- The topic symphony.
- Secret scanning, then push protection, where the plan and the visibility offer them (a Free organization's private repository has neither; nothing can turn them on there).
- "Allow GitHub Actions to create and approve pull requests" on the repository, in mode new, wherever the owner's organization does not hold it off (below).
- The six labels, the issue "Set up this project", and the first commit of an empty repository.
- SymphonyBoard's permissions, Actions, Secrets, Variables and the Codespaces ones the Tokens page uses: a new user accepts them once on the install page; only an existing installation is asked again when the owner adds one.

The owner's one-time steps as the Apps' and the products' owner, which no user repeats: each App's permissions, Setup URL with Redirect on update, callback URLs, client secret, description and logo; the sign-in Worker on Cloudflare; the privacy statement; the environment release in symphony-protocol and bench in coordbench; the Chrome Web Store credentials and CWS_ON_PUSH; the grid gate; the owner's own Claude slots. None of these is a user's setting.

Still left to each new user or organization:

1. "Allow GitHub Actions to create and approve pull requests" in an organization. GitHub's documentation says a new organization does not allow it by default and a new repository in an organization inherits the organization's setting; the repository's own setting is then refused with 409, which setup.py records as forbidden and the adoption's pull request turns into the exact organization page to tick (scripts/adopt.py, policy_words). Inferred from the documentation, not seen in a run: the owner's own organization had it allowed. A personal account's repository takes the box from the run. Without it nothing breaks: protocol.yml brings each release as an issue with a one-press link, and add-worker.yml answers with a link. Automating it needs Symphony Setup to hold the organization permission Administration (write), which PUT /orgs/{org}/actions/permissions/workflow requires, and would change the policy for every repository of that organization.
2. The Claude token and the Claude GitHub App. The token comes only from the user's own Claude sign-in (claude setup-token, the token wizard, or the Tokens page's "Add a Claude account"), and the Claude GitHub App, which claude-code-action's token exchange needs, is Anthropic's App, whose install no other App can chain. `/install-github-app` in Claude Code does both in one flow (docs/setup/claude-action.md). Both stay one step for the user, and only for the workflows that run Claude; the board, the check and the claims run without them.
3. Codespaces for an organization's members, which only the Tokens page's "Add a Claude account" needs in an organization. PUT /orgs/{org}/codespaces/access is not enabled for GitHub Apps in GitHub's REST description, so no App can set it; a personal account needs nothing.
4. Issue types and a Projects table (docs/setup/github.md, section 9), optional and display only. POST /orgs/{org}/issue-types is open to an App with the organization permission Issue types (write), so the run could make Goal, Epic and Task given that permission; a project can be made through GraphQL, but its views and hidden fields have no API, so the table stays a few clicks either way.

## What this thread does about it

Every remaining automation needs Symphony Setup to hold a new organization permission, which only the owner can add on the App's page and which each adopter would be asked to accept. The thread put the choice for item 1 to the owner, recommending to keep Symphony Setup on the one repository: an App asking for an organization's Administration is one many owners will refuse to install, the box is optional, and the pull request already names the page. Item 4 waits for the same decision. Items 2 and 3 have no API and stay as they are.
