# The control panel's Dependencies and Folders tabs

Source: the thread "Control panel sign-in", 2026-10-18, written at the owner's checkpoint of 13:02 UTC. It follows control-board-graph.md (the research behind Dependencies) and drive-sync.md (the design behind Folders), and records where the two tabs stand, so the next session carries them on without asking again.

## What they are

- Dependencies (the owner's choice 6 in control-board-graph.md): a console tab after Tasks, data-tab "dependencies", that draws a repository's epics, sub-issues and blocked-by links with Mermaid in the browser, from GitHub's own sub-issue and dependency data, with no graph code of ours.
- Folders: a console tab after Share, data-tab "folders", that links a repository to OneDrive folders the owner ticks, as drive-sync.md describes. OneDrive only: Google Drive waits for a route with no API key, since the owner refused the Google Picker's browser key.
- The sign-in Worker gains /drive routes for Microsoft's sign-in, whose redirect URI is exactly https://openspineconsortium.com/symphony/control/ with its trailing slash.
- Each tab adds lines to the Apps' privacy statement (symphony-start PRIVACY.md), and each takes the next version after main's when it merges; 18 is symphony-start #57's.

## Where the work stands

Every branch is pushed, and each pull request opens with its own "Checkpoint 2026-10-18" line. None is merged.

- Site #36 (claude/graph-section): Dependencies, with master #48 merged; its review's folds partly applied.
- Site #37 (claude/folders-page): Folders, with master #48 merged; its review's fold stopped partway.
- symphony-app #19: the Dependencies checks, with mutants g45 and g46 not yet proved to bite.
- symphony-app #20: the Worker's /drive routes.
- symphony-app #21: the Folders checks.
- symphony-start #51 and #52: the statement's lines for each tab.
- symphony-protocol #51: the board's Dependencies section, a draft held until 0.5.1 is cut.

Site master moved on after #48 (site #49 to #54), so each site branch merges master again, is rebuilt against symphony-start main and has its checks rerun before it merges. The order is the statement first, then the site and the checks together; for Folders, the Worker's routes are deployed and the owner's Microsoft clicks are done before the tab is useful.

## The owner's one-time clicks, still to come

1. Register the Microsoft app: https://entra.microsoft.com/#view/Microsoft_AAD_RegisteredApps/ApplicationsListBlade, press "New registration", name it SymphonyBoard Folders, choose personal and work or school accounts, set the Web redirect URI to https://openspineconsortium.com/symphony/control/ and press Register. Under "Certificates & secrets" press "New client secret"; under "API permissions" add Microsoft Graph's delegated Files.ReadWrite and offline_access. WSU's tenant may need IT's consent.
2. In Cloudflare, https://dash.cloudflare.com/, open Workers & Pages, then symphony-signin, then Settings, then "Variables and Secrets": add MICROSOFT_CLIENT_ID as text and MICROSOFT_CLIENT_SECRET as a secret, then paste the merged worker.js from symphony-app #20 and press Deploy.
