# Sharing a repository from the control board

The notes of the thread "Share from control board" of the claude.ai Project "symphony2", 2026-10-18.
The owner's ask, in his words: "I definitely want to be able to share my repo from the control
board, by native google, microsoft, github, or email, where the first three can grant that person
direct permission to join as a collaborator on the project if their github is linked to that
respective social account". The second half of his message, how OneDrive fits, belongs to the
thread "Word revisions from OneDrive" (drive-sync.md beside this file).

The sources are GitHub's own documentation, read from the github/docs repository on 2026-10-18
(content/authentication/keeping-your-account-and-data-secure/about-authentication-to-github.md,
data/reusables/organizations/invite_to_org.md and invite_to_team.md, the repository access page
managing-teams-and-people-with-access-to-your-repository.md) and its REST data files
(src/rest/data/fpt-2022-11-28/collaborators.json, orgs.json, users.json and
src/github-apps/data/fpt-2022-11-28/server-to-server-permissions.json, which say which App
permission each endpoint needs). Nothing below was tried against a live invitation yet.

## The answer in short

GitHub never tells a service which Google or Microsoft account a GitHub user has linked, so the
"if their GitHub is linked" test cannot be run as asked. What GitHub does do comes to the same
thing by another road: a social login on GitHub is an email address on the account, and GitHub
delivers an invitation sent to an email address to the account that holds it. So the console asks
for the person's Google or Microsoft address (or their GitHub username), and GitHub does the
matching when the person accepts.

1. Linked accounts are not visible. GitHub's social login is Google or Apple only; there is no
   Microsoft sign-in to link at all. A social login is kept as an email address on the account
   ("you can add your social login email to the account"). No REST endpoint lists a user's sign-in
   methods. The "social accounts" endpoints (GET /users/{username}/social_accounts) are the
   profile's links to other sites, such as a Twitter page, which anyone can type and nobody
   verifies; they prove nothing. GET /user/emails lists the emails of the signed-in person only,
   never of someone else, and search finds a user by email only where they made it public.
2. Inviting by email works only into an organization. POST /orgs/{org}/invitations takes
   `email` ("which can be an existing GitHub user") or `invitee_id`, a `role` and `team_ids`, and
   needs the App's organization permission Members (write) and a signed-in organization owner. The
   person joins the organization and, through the team, the repository. GitHub's own team page
   says the same: "type their username or email address ... will be added to the team once they
   accept".
3. Inviting a collaborator to one repository takes a username only. PUT
   /repos/{owner}/{repo}/collaborators/{username} has no email form, and it needs the App's
   repository permission Administration (write), which the project decided the main App never
   holds on anyone's repository. It is the only route for a repository a person owns rather than
   an organization, and the only one that makes an outside collaborator rather than a member.
4. GitHub's own page needs no permission at all. The console can open
   https://github.com/OWNER/REPO/settings/access, where the owner presses "Add people" and types a
   name; the organization's invitation page takes "the username, full name, or email address".
   That is one click more and holds nothing.
5. "Native Google, Microsoft and email" sharing needs no key. A link that opens Gmail's compose
   window (https://mail.google.com/mail/?view=cm&to=...&su=...&body=...), Outlook on the web's
   (https://outlook.office.com/mail/deeplink/compose?to=...&subject=...&body=...), a mailto: link,
   and the browser's own share sheet (navigator.share, which on a phone offers every app the person
   has) each send the repository's link and the invitation from the owner's own mail. Picking the
   person from Google or Microsoft contacts would need an OAuth client and the contacts scope
   (Google's People API, Microsoft Graph's People.Read), the registration and review that Drive is
   still waiting on (drive-sync.md); typing or pasting the address needs neither.

## What the console's Share tab does

One rail button and one panel, as every section joins the console (control-panel-console.md),
built in openspineconsortium.github.io#45 with the first route below and checked in Playwright's
Chromium against a stubbed GitHub API.

- A field that takes a GitHub username or an email address, the role (read, triage, write,
  maintain), and four ways to send: Gmail, Outlook, email, and the device's share sheet. Each sends
  a short message with the repository's link and, where an invitation was made, GitHub's
  invitation page (https://github.com/OWNER/REPO/invitations for a repository,
  https://github.com/orgs/ORG/invitation for an organization).
- Grant access, in the order that holds the least:
  - Today, with nothing new held: a button that opens the repository's access page on GitHub,
    with the name or address copied, for the owner to paste into "Add people".
  - With the owner's one-time click to add Members (write) to SymphonyBoard: for a repository of
    an organization, an email or username becomes an organization invitation into a team that
    holds the repository. The team must already exist with the repository on it, since attaching a
    repository to a team needs Administration (write) too; Symphony Setup, which holds
    Administration for the adoption's one run, can make that team then, one per repository.
  - Only if the owner reverses the decision that the main App never holds Administration: a
    username becomes a direct collaborator invitation, on a personal repository too.

## What it costs and what it changes

- Members (write) on SymphonyBoard is asked of every organization that installs it, and an
  invitation by email makes the person a member of the organization, not an outside collaborator,
  so they see its other members and any repository the organization opens to all members. On a
  paid organization each member takes a seat. A free organization's members cost nothing.
- Each new thing the App holds or does goes into the Apps' privacy statement (symphony-start
  PRIVACY.md) before it ships: an invitation names a person's email, which GitHub keeps and the App
  does not. The no-permission route holds nothing and changes no statement.
- None of this is a Microsoft or Google login on GitHub's side: the person still needs a GitHub
  account, made with Google, Apple or a password, and accepts the invitation from it.

## Open

- Whether GitHub's repository "Add people" search matches an email address that is not public,
  as the organization's page says it does, is inferred, not seen.
- Whether Symphony Setup's adoption run should make a per-repository team, which the Members
  route needs.
- The owner's choice among the three routes.
