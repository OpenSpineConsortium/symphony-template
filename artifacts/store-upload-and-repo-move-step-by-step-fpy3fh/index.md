# Store upload and repo move, step by step

Oct 8, 2026 · @greg

## Before you start

Step 1 is done. Start at Step 2: upload by hand once, fill in the listing, submit, then set the secrets and the switch, so nothing is created twice. Refreshed on 2026-10-08 for release 0.2.0.773, which carries its import and export scripts itself, so the extension needs no Allow User Scripts switch and the remote-code answer is No: every text to paste below is the one in main's `docs/store/LISTING.md` today. Stop at any step and the rest waits.

**Before you press Submit for review, put cswap on PyPI.** The test instructions tell the reviewer to install it with uv tool install claude-swap-cloud, which works only once it is published. On pypi.org, signed in: Account, Publishing, Add a new pending publisher, GitHub, with PyPI project name claude-swap-cloud, owner OpenSpineConsortium, repository claude-swap-cloud, workflow publish.yml, environment pypi. Then push the tag v0.27.0b1 from main (git tag v0.27.0b1 then git push origin v0.27.0b1), or tell the thread to push it. The Publish to PyPI run builds the bytecode-only wheels and publishes them; https://pypi.org/project/claude-swap-cloud/ then shows the version.

You need:

- The zip. CI builds it on every merge to main and keeps the newest at https://github.com/OpenSpineConsortium/claude-swap-cloud/releases/latest/download/claude-swap-cloud-chrome.zip (the README links it; sign in to GitHub, the repository is private): upload that one, since it is exactly what CI will send to the store later. Today that is release 0.2.0.773, 124,457 bytes, SHA-256 starting 2e1e2de2, which I rebuilt from the same commit and got the same bytes. The folder `claude-swap/store-upload` in this project's files holds the same zip as `claude-swap-cloud-0.2.0.773-chrome.zip`, beside the six images and the four texts, all refreshed from main today.
- The Google account that already publishes Beethoven on the Chrome Web Store, signed in to the developer dashboard at https://chrome.google.com/webstore/devconsole. A second developer registration is not needed; the item goes under the same publisher.
- On GitHub: you as an owner of the OpenSpineConsortium organization (for the secrets and the variable in claude-swap-cloud's Settings).
- About forty minutes in all: the listing about twenty, the secrets about twenty. Review by the store takes days and needs nothing from you.

## Step 1. Move the two repositories to OpenSpineConsortium

Done on 2026-10-06; on 2026-10-07 you renamed the repository claude-swap-cloud. Nothing here is left to do, and the steps below stay only as the record of how it was done.

Before pressing anything, check two things on github.com:

- OpenSpineConsortium holds no repository called claude-swap or claude-swap-privacy. A transfer into a name that is taken is refused; rename or delete the placeholder first.
- You are listed under the organization's **People** as an owner. Owners can always receive a transfer.

The transfer, for each repository:

1. Open the repository on GitHub and press **Settings** (the repository's own tab, right of Insights).
2. Stay on **General** and scroll to the end, the red-framed **Danger Zone**. On the line **Transfer ownership**, press **Transfer**.
3. Under **New owner**, choose **Select one of my organizations** and pick **OpenSpineConsortium**.
4. Read the warning box once. One line applies: a private repository moved into a Free organization loses branch protection rules and GitHub Pages. claude-swap has no Pages site; a protection rule on main, if you ever set one, is dropped and can be set again afterwards.
5. Type the repository's name in the confirmation box and press **I understand, transfer this repository**. The page reloads at the new address; GitHub moves the data in the background, which can take a moment.
6. Do the same for claude-swap-privacy.

What moves with each repository: the code and its history, the branches, pull requests, issues, releases, stars and watchers, and the Actions secrets, webhooks and deploy keys. That is why the secrets of Step 7 are created after the move: once, in their final place. Earlier workflow runs and Actions variables are not promised by GitHub's page; neither exists here yet. GitHub holds claude-swap as a standalone private repository, not as a fork of realiti4's, so no fork rule applies to the move.

After the move, in this order:

1. On your PC, in the clone: `git remote set-url origin https://github.com/OpenSpineConsortium/claude-swap.git`. The old address redirects for now, but the redirect ends the day a repository of the old name is created, so do not rely on it.
2. The Claude GitHub App: open https://github.com/apps/claude/installations/select\_target, choose OpenSpineConsortium, and if it says **Only select repositories**, add claude-swap and claude-swap-privacy. The app is already installed there for beethoven-extension; only the two repositories need adding.
3. This project: in its settings, under Repositories, replace the two Gregory-Schwing-MD-PhD addresses with the organization's. Until then, threads here cannot reach the moved repositories.
4. Done on 2026-10-06: both repositories moved, pull request #22 (every address in the repository, PRIVACY.md version 4) merged, and PRIVACY.md version 4 copied to claude-swap-privacy.

CI minutes now come from the organization's Actions quota: 2,000 a month on a Free organization, 3,000 on Team. A full claude-swap run (Ubuntu, Windows, macOS and the store zip) costs about 72 of them, because Windows minutes count double and macOS minutes ten times; the release workflow alone runs on Ubuntu and costs a few. Without a payment method on the organization, runs stop when the quota is spent and start again the next month.

## Step 2. Create the item and upload the package

The item is born from the zip; everything else is typed into it afterwards. Have the zip on your computer: the newest build from main at https://github.com/OpenSpineConsortium/claude-swap-cloud/releases/latest/download/claude-swap-cloud-chrome.zip (today release 0.2.0.773, SHA-256 starting 2e1e2de2), or the same file from the project's `claude-swap/store-upload` folder. The item starts at that version, 0.2.0 followed by the commit count, so every later build from main is above it.

1. Open https://chrome.google.com/webstore/devconsole, signed in as the publishing account. The left side shows **Items**.
2. Press **New item** (top right of the Items page).
3. Drop the zip onto the upload box, or **Browse files** and choose it. Wait for the upload to finish; the dashboard then opens the new item's draft.
4. Read the header: the store took the name **Claude Swap Cloud** and the summary from the package's manifest; neither is typed. The item's id is in the page address, the 32 letters after /item/. Copy it somewhere: it is needed in Step 6 (the bridge) and Step 7 (the `CWS_ITEM_ID` secret).
5. Press **Save draft** before going on; a draft can be left for days.

If the upload is refused, the message names the manifest field at fault; the zip in the set passed the packager's checks (Manifest V3, six permissions, one host permission, four icons), so a refusal here is new information worth pasting into the thread.

## Step 3. The Store listing tab, field by field

Twelve fields, in the order the tab shows them; each takes one file from the upload set or one text from below. The texts are also in `LISTING.md` in the set, so you can copy from either.

| # | Field | What goes in |
| --- | --- | --- |
| 1 | Description | the text block below, whole |
| 2 | Category | **Productivity** |
| 3 | Language | **English** |
| 4 | Store icon (128 x 128) | `store-icon-128.png` |
| 5 | Global promo video | leave empty |
| 6 | Small promo tile (440 x 280) | `promo-tile-440x280.png` |
| 7 | Screenshots (1280 x 800) | `screenshot-01-importing.png`, then `screenshot-02-stops-and-tells.png`, then `screenshot-03-done.png` |
| 8 | Marquee promo tile (1400 x 560) | `marquee-1400x560.png` (optional; upload it) |
| 9 | Official URL | leave as **None** (it accepts only a site verified in Search Console) |
| 10 | Homepage URL | `https://github.com/OpenSpineConsortium/claude-swap-privacy` |
| 11 | Support URL | `https://github.com/OpenSpineConsortium/claude-swap-privacy/issues` |
| 12 | Mature content | **No** |

The two URLs name the public companion repository claude-swap-privacy, because claude-swap-cloud is private: the store opens these links without signing in.

Field 1, Description (copy all of it):

```
Claude Swap Cloud moves your claude.ai Projects between your own Claude accounts.

cswap, the command line this extension belongs to, switches Claude Code between your accounts on your computer without logging out, and lets you run them side by side. Claude Swap Cloud does the same for what lives in the cloud: your Projects. That includes the redesigned Projects, one ongoing conversation where Claude coordinates threads that run as cloud sessions and share the project's repositories, instructions and memory, as well as the regular Projects with their knowledge files and chats. A Project belongs to the account that made it, and claude.ai has no way to move it to another. Claude Swap Cloud copies it: export it from one account, sign in as the other, import it.

Three buttons in the side panel, always in the same place. Open the project on claude.ai, signed in as the account that has it, and press Export this project: your computer's own Save As window opens for where the export goes (one .tar file), and the extension runs its export script on the project's page and saves the project there through cswap. Press Sign out and reload: the tab makes claude.ai's own sign-out request and goes to the sign-in page, where you sign in as the other account yourself. Give the copy a name if you want one and press Import: your computer's own Open window appears; open the export to copy (the .tar just saved, or any export cswap made), and cswap queues the import and the extension runs it in the same tab, into whichever account you signed in as. Any export on your computer can be imported this way at any time, so a move can be picked up at any step. The command line works too: cswap project-move import --to NUM queues an import that the extension picks up in the claude.ai tab signed in as that account, after checking that it is.

What comes across. From a Claude Code project: its name, icon and colour, description, instructions, files, model and effort settings, and its repositories and linked folders where the new account may use them; its conversation, threads and session transcripts, as files the new project's Claude can read, since claude.ai cannot create those live; and, for each of its running sessions, the cswap teleport line that carries that session on under the new account. Its memory, what its Auto memory panel shows, comes across when claude.ai lets the export read it: written into the new project's own memory at the same paths where claude.ai takes it there, and otherwise as a file the new project's Claude can read, in a folder of its own; the import's last line names any memory that went to that folder. From a regular project: its name, description, instructions, knowledge files and documents, with every chat and the project memory added as documents. The import always makes a new, private project, and a copied Claude Code project arrives paused until you press Resume on its page; nothing in either account is changed or deleted.

What it shows you, in the side panel:
- the three buttons, always in place (a press at the wrong moment is answered with why), a name for the copy, and the line to type when an import could not be queued;
- the job, the account it imports into or exports from, and the script's status line;
- the gate: one request at a time, a fixed spacing before each write (none by default before a read), and a countdown for every wait;
- Resume, Skip this step, Cancel and Confirm, each only when it applies;
- a log you can filter and save.

What it does when the site pushes back:
- When claude.ai asks the browser to pass a check, signs you out, or the tab is signed in as another account, the import stops and the panel says what happened and what to do. Nothing is retried on its own; you press Resume.
- When the site asks it to slow down, the full wait is honoured, never shortened.

What it never does: it does not handle passwords, tokens or your sign-in, add or remove request headers, switch accounts, run on any site but claude.ai, or send anything to the developer. The only cookie it looks at is claude.ai's lastActiveOrg, which names the organization the site is showing, read by the import when your account belongs to more than one so the copy goes there. Beside the scripts' own requests it asks claude.ai only which account the tab is signed in to (and, for an export, the account's list of projects, to name the one the tab shows), and makes claude.ai's sign-out request when you press Sign out and reload, reading nothing of that answer but whether it worked. There are no analytics. The log never keeps request bodies or cookies, and names each request by its path. Every script it runs is in its package; nothing is downloaded. cswap's registry is read only for an account named on the command line, never for a credential; the Save As and Open windows are your computer's own, opened by cswap, which keeps only the folder the last one used.

Requires the cswap command line from Claude Swap Cloud (Python 3.12 or newer; uv tool install claude-swap-cloud, or pipx install claude-swap-cloud) and a one-time cswap bridge install --register, which lets Chrome talk to cswap on your computer; the side panel's Setup section shows each line to type, with this extension's id filled in.

Claude Swap Cloud is an independent tool. It is not made, endorsed or sponsored by Anthropic, and it is not an Anthropic product. "Claude", "Claude Code" and "claude.ai" are Anthropic's marks, used here only to say which site and which product the extension works with.
```

Press **Save draft** at the end of the tab. Look at each image once in the dashboard's preview before moving on; the three screenshots show a made-up account and project, by design.

## Step 4. The Privacy tab

Every box here is a text from `LISTING.md`; paste each whole. The remote-code answer is No, since every script the extension runs is in the package; if review asks about it anyway, section 3 of `SUBMISSION.md` in the set holds the reply.

**Single purpose** (one box):

```
Copy a claude.ai Project between the user's own Claude accounts, from the user's own claude.ai tab and under the user's control: export the signed-in account's project to the user's computer through cswap and import it into another of the user's accounts, or import a project the user exported with the cswap command line into the signed-in account.
```

**Permission justification**, one box per permission the dashboard lists:

nativeMessaging:

```
Talks to cswap's own program on the user's computer (the native host com.claude_swap.bridge, registered by the user with "cswap bridge install --register"). It hands the extension the import job the user queued and the export's files one at a time, and receives the import's progress for the command line. For a copy made from the side panel it also opens the computer's own Save As window for where the export goes and takes the export's files piece by piece as the script writes them, saving them in that one .tar on the user's computer; and it opens the computer's own Open window for the export to import, reads the export the user opened and queues its import into the account the user is signed in as. The extension never learns what was chosen in those windows beyond the export's own path. At the user's request it ends a job that another browser profile left behind, so a new one can start. No code passes through it, and nothing is downloaded. It connects to no other native host.
```

scripting:

```
Runs the extension's own page helper and then its import script, or for a copy made from the side panel its export script, in the user's claude.ai tab, in the extension's isolated world, with chrome.scripting.executeScript and files from the package: only when the user has queued an import or pressed Export this project or Import. The scripts are the same ones the cswap command line offers to paste into the console by hand; the extension saves the paste. Nothing is fetched or evaluated.
```

storage:

```
Keeps the current job's state (for a copy made from the side panel, also the project list the page read to name the tab's project, and the id of the file window the job waits on), the settings, and a bounded log (at most 20,000 records, dropped after 72 hours by default) in chrome.storage.local, so the side panel can show them and a job survives a service worker restart. No credentials or request bodies are stored.
```

sidePanel:

```
The side panel is the extension's only page: it shows the job's progress and waits, holds the Resume, Skip this step, Cancel and Confirm controls, and the three buttons of a copy: Export this project, Sign out and reload, and Import, with a name for the copy; where the export goes and which export to import are chosen in the computer's own Save As and Open windows.
```

alarms:

```
Wakes the service worker to continue a scheduled wait (a fixed spacing before a write, or a Retry-After the site asked for) and to check for a queued job, because a Manifest V3 worker cannot keep a timer alive across its own restarts.
```

notifications:

```
Shows one desktop notification when a job stops and needs the user (a check to pass, a sign-in, a step to send again or skip), when it is done or has failed, when an export made from the side panel is done (saying what to press next), and when its import could not be queued. Can be turned off in the side panel's settings.
```

Host permission, https://claude.ai/\*:

```
The import, and an export made from the side panel, happen on claude.ai and nowhere else: a content script reports whether the tab shows a check or the sign-in page and, when the user presses Sign out and reload, makes claude.ai's own sign-out request in that tab (it reads nothing of the answer but its status, and then the tab goes to the sign-in page for the user to sign in); the import or export script runs in the claude.ai tab the user is signed in to. The extension requests no other site.
```

**Are you using remote code?** Answer **No**: the page helper and the import and export scripts are files in the package, and nothing is fetched or handed over to be run. The dashboard asks nothing more; if review asks, this is the answer:

```
No remote code. The page helper and the import and export scripts are files in the package (src/page.js, src/project-import.js, src/project-export.js), injected with chrome.scripting.executeScript({ files }) in the extension's isolated world. The native host passes data only (the job, the export's files, the progress), never code. There is no eval or new Function.
```

**Data usage**: tick exactly four boxes. **Personal communications**: the conversations of the project being copied (its chats, or a Claude Code project's conversation and threads), read from claude.ai into the export or uploaded from it as files of the new project. **Web history**: the address (without its query) and the title of the claude.ai pages the extension runs on, to know which project the tab shows and whether a check or the sign-in page is showing, kept on the user's computer. **Personally identifiable information**: the email address of the claude.ai account the tab is signed in to, read to check it is the account the user named, or, for a copy made from the side panel, to record the account the project came from and the one it goes into. **Website content**: the project being copied (its files, text, conversations and memory), and, for a copy made from the side panel, the names of the projects the signed-in account can see. Leave every other type unticked: health, financial and payment, authentication information, location, user activity.

**Certifications**: tick all three (no sale or transfer to third parties outside the approved use cases; no use unrelated to the single purpose; no use for creditworthiness or lending).

**Privacy policy URL**: `https://github.com/OpenSpineConsortium/claude-swap-privacy/blob/main/PRIVACY.md`. The store opens it without signing in, and the companion repository is public, so it answers. The file there is version 15, the same bytes as the PRIVACY.md inside the zip and on main (checked on 2026-10-08).

Press **Save draft**.

## Step 5. The Distribution and Test instructions tabs, then submit

**Distribution tab**:

- Payments: **Free**.
- Visibility: **Unlisted** to start, as the listing is written (anyone with the link installs; nothing shows in search). Public can follow later with no new review of its own. Private, the way Beethoven is published, works as well: it then wants the testers' Google Group address, and only its members can open the listing.
- Regions: **All regions**.

**Test instructions tab**:

- Username and Password: leave both empty; the extension has no account of its own.
- Additional instructions (the box takes 500 characters; this text is 403):

```
Needs Python 3.12+ and the cswap command line: uv tool install claude-swap-cloud (or pipx install claude-swap-cloud). Open the side panel: Setup shows the register line with this item's id. Open a small Project on claude.ai, press Export this project and save the .tar; then press Import and open it. One account is enough: the copy goes into the account signed in. Scripts are minified, not obfuscated.
```

One thing to expect: the reviewer installs cswap from PyPI as the text says, so publish it first (the PyPI step at the top). If review writes back that it could not test the extension, SUBMISSION.md section 4 has the answer: offer a short screen recording of an export and an import of a small project, made with the uploaded build.

**Submit**:

1. **Save draft**, then **Submit for review** (top right). The dashboard asks whether to publish automatically once review passes; say yes, so nothing waits on you.
2. The item's status becomes **Pending review**. Review of a first item with `nativeMessaging` and `scripting` usually takes several days; you get an email either way.
3. A reviewer may write back about the remote-code answer. The reply is written: section 3 of `SUBMISSION.md` in the set, "The scripts are in the package". Paste it into the dashboard's reply box; nothing in the package needs to change for it.
4. Once it says **Published**, the listing is at `https://chromewebstore.google.com/detail/<item id>`; an Unlisted item opens only from that link.

## Step 6. Once the item exists: its id and the bridge

The id exists from the moment the draft is saved in Step 2; review does not change it. Two things use it.

1. **The bridge on each computer.** The copy installed from the store has the store's id, not the pinned id of the unpacked folder, and Chrome lets a native host talk only to the extension ids its registration names. So on every computer that installs from the store, once, on the command line:

   ```
   cswap bridge install --register --extension-id <the item id>
   ```

   `cswap bridge status` then shows that id as the registered one. The side panel's Setup section prints this exact line with the copy's own id filled in, so a person who installs from the store copies it from there. One registration names one id: a profile with both the unpacked copy and the store copy connects whichever was registered last.
2. **Your own PC.** Only if you install the store copy there: run that line in PowerShell with the id. Until then your PC keeps the unpacked copy, which stays registered and works as before.
3. **The secret.** The same id is `CWS_ITEM_ID` in Step 7.

Nothing in the repository needs the id. A later change can teach cswap the store id by itself (a constant beside the pinned one in `bridge.py`, both in `allowed_origins`), so that the line above is no longer needed; it is not written yet.

## Step 7. The five CWS\_ secrets

The release workflow talks to the store with five values, kept as repository secrets in claude-swap-cloud. Nothing prints them: the workflow passes them by name to one step, and the script reads them from the environment and never writes them anywhere.

| Secret | What it is | Where it comes from |
| --- | --- | --- |
| `CWS_PUBLISHER_ID` | the publisher's id | the dashboard, **Publisher**, **Settings** (older dashboards show it on the **Account** page in the left menu) |
| `CWS_ITEM_ID` | the item's id | Step 2, the 32 letters from the item's address |
| `CWS_CLIENT_ID` | an OAuth client's id | the Google Cloud console, part A |
| `CWS_CLIENT_SECRET` | that client's secret | the same screen |
| `CWS_REFRESH_TOKEN` | a long-lived token of your account for that client | the OAuth Playground, part B |

**A. The OAuth client (Google Cloud console, once)**

1. Open https://console.cloud.google.com signed in as the publishing Google account. In the project picker at the top, **New project**: name it `cswap-store` (any name does), **Create**, then select it.
2. Left menu **APIs & Services**, **Library**: search `Chrome Web Store API`, open it, press **Enable**.
3. Left menu **Google Auth Platform** (older consoles say **OAuth consent screen**), **Get started**: App name `cswap-store`, User support email your address, **Next**; Audience **External**, **Next**; Contact email your address, **Next**; agree, **Create**.
4. Still in Google Auth Platform, open **Audience**: under **Test users**, **Add users**, your own email, **Save**. Then on the same page press **Publish app** and confirm, so the status reads In production, before making the token in part B: a token made while the app is in Testing stops working seven days after you authorized it. Google says up front that it may not give a verified status to an app with the store's write scope and that unverified status does not block the API; the app is never submitted for verification, and nobody but you signs in to it.
5. **Clients**, **Create client**: Application type **Web application**, Name `cswap-store`; under **Authorized redirect URIs** press **Add URI** and paste `https://developers.google.com/oauthplayground`; **Create**.
6. A box shows the **Client ID** and the **Client secret**. Copy both now; the secret is shown in full only at this moment (the client's page masks it later, and **Reset secret** makes a new one). They are `CWS_CLIENT_ID` and `CWS_CLIENT_SECRET`. Do not download the JSON into the repository.

**B. The refresh token (OAuth 2.0 Playground, once)**

1. Open https://developers.google.com/oauthplayground with the same Google account.
2. Press the gear icon at the top right, tick **Use your own OAuth credentials**, paste the client id and the client secret, close the box.
3. In **Step 1** on the left, in the box **Input your own scopes**, paste `https://www.googleapis.com/auth/chromewebstore` and press **Authorize APIs**.
4. Choose the publishing account. The screen **Google hasn't verified this app** is expected for your own client: press **Advanced**, then **Go to cswap-store (unsafe)**, then **Continue** (or **Allow**).
5. Back in the Playground, **Step 2**: press **Exchange authorization code for tokens**. Copy the **Refresh token**; the access token beside it expires within the hour and is not needed. That is `CWS_REFRESH_TOKEN`. If the Refresh token box is empty, this client was authorized before (Google returns a refresh token only on the first authorization): remove the app at https://myaccount.google.com/permissions and start again from step 3.

**C. Into GitHub (five times)**

1. Open https://github.com/OpenSpineConsortium/claude-swap-cloud, **Settings**, in the left sidebar under Security **Secrets and variables**, then **Actions**. Stay on the **Secrets** tab.
2. **New repository secret**: **Name** `CWS_PUBLISHER_ID`, **Secret** its value, **Add secret**.
3. Repeat for `CWS_ITEM_ID`, `CWS_CLIENT_ID`, `CWS_CLIENT_SECRET` and `CWS_REFRESH_TOKEN`. The names are exact, upper case with underscores. The list afterwards shows five names and no values.
4. To change one later (a new refresh token, say), press the pencil on its line, paste the new value, **Update secret**. The old value is gone; nothing else changes.

**D. A check from your PC, optional**

In PowerShell, in the clone, with the five values set for that window only:

```
$env:CWS_PUBLISHER_ID = "..."; $env:CWS_ITEM_ID = "..."; $env:CWS_CLIENT_ID = "..."; $env:CWS_CLIENT_SECRET = "..."; $env:CWS_REFRESH_TOKEN = "..."
node release-kit/store/publish.mjs --status
node release-kit/store/publish.mjs --upload --zip $HOME\Downloads\claude-swap-cloud-chrome.zip --dry-run
```

Run it in the clone after `git pull`, since the script moved to `release-kit/store/` with the release kit. `--status` reads the item's state (what is published, what is in review, the last upload) and so proves the five values work; `--upload --zip <the zip> --dry-run` prints the requests an upload would make and sends nothing (point `--zip` at wherever the zip is). Neither prints a secret. The line that set them stays in PowerShell's history: run `Clear-History` afterwards, or skip this check and read the store job's log in Step 8 instead.

Two things to leave alone: the item's **Verified CRX Uploads** opt-in in the dashboard (the API then wants a signed .crx, which the script does not make) and the client's redirect URI (the Playground's address is the only one it needs). To switch the store off from the GitHub side, delete the five secrets: the store step then says "Not configured" and stays green. Deleting the client in the Cloud console instead leaves the secrets in place and makes the step fail until they go too. Google deletes an OAuth client unused for six months (an email comes 30 days before) and a refresh token unused for six months stops working; a release every few months keeps both alive, and parts A and B make new ones if not.

## Step 8. The switch, and the first automatic release

The GitHub release with the zip is made on every merge to main that changes the extension, whatever this variable says; with the five secrets in place, the variable turns the store part on. Start with `upload`, which only replaces the item's draft; move to `publish` once a run has gone through cleanly.

1. In the repository on GitHub: **Settings**, **Secrets and variables**, **Actions**, the **Variables** tab (next to Secrets), **New repository variable**. Name `CWS_ON_PUSH`, value `upload`. **Add variable**.
2. A dry run first, with no code change: **Actions**, the workflow **Release the extension** in the left list, the **Run workflow** button on the right, tick **upload**, leave **publish** unticked, **Run workflow**. Two jobs run, release / package and release / store. The store job's log ends with the store's answer: "The store accepted the package as the item's new draft (version 0.2.0.\<number>)." The dashboard's item now shows that draft; the GitHub release extension-v0.2.0.\<number> holds the zip and its SHA-256.
3. From then on, every merge to main that changes the extension (its manifest, sidepanel.html, src/, icons/, PRIVACY.md, the packager or the release kit) does the same on its own. The version is the manifest's 0.2.0 with the commit count as a fourth number, so each build is above the last; raise the manifest's version only when you mean a new release line.
4. To submit for review automatically too, change the variable's value to `publish`. Every such merge then goes to review at once, so test on a branch first; the hand test is `TEST_BEFORE_UPLOAD.md` in the set. To stop the store part, delete the variable or set it to `off`; CI still tests every push and still keeps each build as a release.

Runs never overlap: a second merge while one is being released waits, and a third replaces the waiting one, so the store always gets the newest.

## When something is refused

Each message below is the exact text a run or the dashboard shows, and nothing is retried on its own; you decide.

| What you see | Where | What to do |
| --- | --- | --- |
| "Not configured: CWS\_... is not set. Nothing was sent to the store." | the `store` job's log, run green | Add the named secret (Step 7); the names are case-sensitive. |
| "Could not get an access token (HTTP 400: invalid\_grant)" | the `store` job, run red | The refresh token expired or was revoked. A consent screen left in Testing gives seven-day tokens: set its audience to production (Step 7), make a new token in the Playground and update `CWS_REFRESH_TOKEN`. |
| "The store refused the upload (HTTP 400: Version number in manifest must be greater than ...)" | the `store` job, run red | The version is not above the published one; it happens when a tag repeats a version a push already released. Merge to `main` again, or raise `version` in `extension/manifest.json`. |
| "The store is still processing the package after 5 minutes. Nothing was submitted" | the `store` job, run red | The draft was taken. Later, **Run workflow** with **publish** ticked, or submit in the dashboard. |
| The `store` job failed after the release was made | Actions | **Re-run failed jobs**, or **Run workflow** on `main` with **upload** ticked; a re-run attaches the files to the release that exists. |
| A rejection email from the store | your inbox and the item's page | It names the policy. For the remote-code question, reply with section 3 of `SUBMISSION.md`; for anything else, paste the email in the thread and the fix is a pull request plus a new upload. |
| "Bridge not connected" in the side panel after installing from the store | the extension | The bridge is registered for the unpacked id. Run the register line from Step 6 with the store id. |
| A push to `main` sent nothing to the store | Actions, no run or a skipped run | No run at all: the merge touched nothing the zip holds. A run with the release made and the store job skipped: the variable is unset or `off`. |
