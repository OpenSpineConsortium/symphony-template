# WSU grid files in the Folders tab

Source: the thread "WSU grid files in Folders", 2026-10-20, from the owner's message of 20:52 UTC in the
SchwingNet thread: where are the videos, can they be watched without downloading them since they are all
on the WSU grid, and could the control panel's Folders tab become a real-time view of the grid's files,
through the browser or through passwordless, VPN-less ssh "like the VS Code extension". Nothing here is
built. Read on the day: Wayne State's knowledge base through search results only (tech.wayne.edu and
services.wayne.edu do not resolve from the cloud session), the articles "How to SSH to the Grid in Visual
Studio Code" (tech.wayne.edu/kb/high-performance-computing/hpc-tutorials/500049), "How to connect to the
Grid OnDemand" (500191), "How to manage your files OnDemand" (services.wayne.edu article 20233) and "How
to Setup Globus" (article 20224); other universities' VS Code pages (Florida, UConn, Oregon State, Utah);
Globus Connect Server v5's HTTPS access guide (docs.globus.org). What the grid itself has shown comes from
docs/research/wsu-grid-and-github-actions.md. Every claim not read on the day is marked inferred or the
author's knowledge, to be checked before it is relied on.

## The short answer

Updated the same evening: the owner's test showed Globus's web app browses and plays the grid's files
with no VPN (section "Globus works", below), so Globus, not the tunnel, is the recommended route; what
follows is the first answer, kept as written.

Three ways already exist on Wayne State's side, and none needs a new server of ours:

1. Today, on the VPN: Grid OnDemand's Files menu (https://ondemand.grid.wayne.edu, Files, Home
   Directory) browses the home and the lab volume, and its View opens a file in the browser, where Chrome
   plays an MP4 as it streams (the player is the browser's; that OnDemand serves the file inline is the
   author's knowledge of Open OnDemand, to check). It needs GlobalProtect, which is what the owner wants
   to be rid of.
2. With no VPN, no password and no key: a VS Code Remote Tunnel started by `code tunnel` inside a Slurm
   job, opened at https://vscode.dev/tunnel/<name>/<folder> in any browser, phone included, signed in
   with the owner's own GitHub account. It is the "VS Code extension" route the owner names, and the
   recommendation below.
3. Bulk copies: Globus, whose collection wsugrid#globus is Wayne State's own, with a Globus ID and the
   AccessID; it moves files, and plays nothing unless the collection has HTTPS access switched on.

The Folders tab's part is small: a "WSU grid" place that opens the tunnel at the folder asked for, and,
for finished videos meant to be shown, a copy into OneDrive, where the tab's existing Graph preview plays
them. A grid listing drawn inside the tab itself would need a web service reachable from the browser,
which the grid does not have (below).

## What the grid allows

- The login node, warrior, may run nothing heavy. Wayne State's own VS Code article says that VS Code
  connected the ordinary way runs its server on warrior "even if you start an interactive job", that
  computationally intensive processes there are prohibited, that the user is warned, and that such
  processes are killed. Its fix is to ssh only to a compute node where the user has a job running, "even
  for basic functions like reading and editing files", through an ssh config that a Wayne State script
  writes on warrior, with an ed25519 key made on the grid. So Wayne State endorses VS Code on a compute
  node inside a job; the tunnel route keeps to that rule.
- The same article gives VS Code 1.98 as the last version that works with the grid's operating system:
  newer VS Code servers need a newer C library than EL7's (the author's knowledge of why). A tunnel run
  inside an Apptainer image of a current Ubuntu, as the runner chain already runs GitHub's runner, avoids
  the limit (inferred, to measure).
- Grid OnDemand is reached only over the VPN, or from a static address that hpc@wayne.edu allows.
- grid.wayne.edu:22 answers from the internet, and a key alone signs in from outside the VPN (the owner's
  test of 2026-10-17). A password sign-in also asks the Google Authenticator code.
- A batch job can hold a long outbound connection: Claude Code's Remote Control registered from an sbatch
  job on 2026-09-29, and the compute nodes reach the internet directly.
- No Wayne State page found on the day says whether the grid may hold PHI, or whether a dev tunnel from a
  job is acceptable. Both are questions for hpc@wayne.edu and, for PHI, the IRB.

## The routes weighed

| Route | VPN | Credential | Live navigation | Plays video in the browser | Build |
|---|---|---|---|---|---|
| OnDemand Files | Yes | AccessID, password, code | Yes | Yes, the browser's player | None |
| VS Code tunnel in a job | No | The owner's GitHub sign-in to the tunnel, once per tunnel | Yes, vscode.dev's explorer | Yes, VS Code's built-in media preview (inferred, to test) | A job script in hpcworker, a link in the Folders tab |
| VS Code Remote-SSH to a compute node | No | The key the owner's test proved, plus Wayne State's config | Yes | Yes, in VS Code desktop | None on our side; desktop only, not the browser |
| Globus web app | No | Globus ID | Yes, its file manager | Only with HTTPS access on the collection, and as a download | None |
| Grid to OneDrive copy | No, to watch | A Microsoft Graph sign-in held on the grid | Of what was copied | Yes, the Folders tab's existing preview | A copy step; one Entra setting |
| A file service of ours behind a tunnel, listed in the Folders tab | No | The tunnel's sign-in in the browser | Yes, inside the tab | Yes | A service, its auth and CORS; no native piece covers the gap |
| The ssh gate from Actions | No | The gate key, held as an environment secret | No: each call is a workflow run of a minute or more, and the gate takes one word a minute | No | A new word in tools/grid_gate.sh |

Why the tunnel and not the others. OnDemand is the native answer but needs the VPN. Remote-SSH is native
and VPN-less too, and right for editing code on the owner's PC, but it is the desktop app, not a page the
control panel can open, and it needs Wayne State's config copied to each machine. Globus is for moving
data, not looking at it. A copy into OneDrive is the right home for a finished video the owner will show
or share, not for navigating a volume of corpora, and copying data out of the grid is what the PHI
question below asks about. A file service of our own is what "Native first" rules out while the tunnel
covers the need. The ssh gate is built for one word a minute and keeps workflow code away from the
account's files, so turning it into a file browser would undo what it was made for.

How the tunnel works. `code tunnel` is VS Code's own command-line tool, one static binary. Run in a job,
it signs in once with a GitHub or Microsoft account by a device code (a code shown in the job's log,
entered at https://github.com/login/device), registers the machine by a name with Microsoft's dev tunnels
service, and keeps one outbound connection open. Only the account that registered it can open it, at
https://vscode.dev/tunnel/<name>; a path after the name opens that folder. Nothing listens on the node and
no port is opened (the author's knowledge of VS Code's documentation, to check). The tunnel lasts as long
as the job; the next job reuses the stored sign-in from the account's home, mode 0600, the same place
Claude Code's sign-in already sits.

What the Folders tab would do. A "WSU grid" entry beside OneDrive in the tab's places, which opens
https://vscode.dev/tunnel/<name>/rs/rs_grp_oschome/<folder> in a new tab when the tunnel is up and says how
to start it when it is not. How it starts, on Beethoven's existing button, is the next section. The tab is
the explorer thread's work and sits in the Phone home screen thread's shell, so its change goes through the
coordinator.

## Building on Beethoven's Connect GitHub Actions

The owner pointed out, at 21:01 UTC, that Beethoven already has a button that connects the grid and
GitHub Actions both ways. It is *Connect GitHub Actions* under Settings, *For your lab lead*, added in
beethoven-extension#18 (22.0.0) and carried in 23.0.0: one press types hpcworker's cli.json line
grid-gate-setup into the portal's shell, which runs `tools/grid_runner.sh --gate-setup`, so the ssh gate
(a key whose forced command takes start, status or stop, held as the environment secret GRID_GATE_KEY)
is set up with nothing run on the owner's computer (docs/research/wsu-grid-and-github-actions.md, "The
gate's setup as a button"). That is the native starting point, and the tunnel route fits on it in two
pieces, each a copy of a pattern that already works:

1. Starting and stopping the tunnel goes through the gate already set up. Two more words for
   tools/grid_gate.sh, tunnel-start and tunnel-stop, queue and cancel one job of hpcworker's own that runs
   `code tunnel` under a fixed name, size and wall time the gate's line names, as the runner chain's size
   is named there. The Folders tab's "WSU grid" place runs grid-gate.yml with the word, through the
   panel's existing workflow-run action, and opens the vscode.dev link once status says the job runs. The
   gate still never runs a workflow's code: the job runs one fixed program. No new key, secret or setting.
2. The tunnel's one GitHub sign-in is a second button beside the first, *Connect browser access*, which
   types `code tunnel user login --provider github` into the portal's shell and shows the owner the device
   code there. The code must never pass through an Actions log: whoever enters a device code first owns
   the tunnel, and every writer of the repository can read a run's log, so the sign-in stays in the portal
   shell, as the gate's own setup does.

Why not ride the runner chain itself, grid.yml, for the listing. A grid.yml job runs inside GitHub's
runner image with `--containall --no-mount bind-paths`, so it sees neither the home nor the lab volume:
that is what keeps a workflow's code away from the account's gh and Claude sign-ins. Binding the volume
in would give every writer's workflow the corpora, and each listing would still be a queued workflow run
returning an artifact, not a stream. The chain stays for computing; the tunnel is for looking.

What this changes: hpcworker (the two words, the job, the cli.json line), beethoven-extension (the
button, whose merge is a Chrome Web Store submission and so waits on the owner's word), grid-gate.yml
here (the two words in its choice list), and the site's Folders tab (the place and its link). The gate's
rule of one call a minute and its refusals stay as they are.

## The owner's OnDemand test, 2026-10-20

At 21:24 UTC the owner reported his first test of Grid OnDemand's Files on the VPN: browsing worked; the
.mkv files, the container the YouTube downloads came in, did not play; .tsv and .html files were shown as
plain text; a folder of about a million files froze the page; and a video that did play sat in a large
black frame, like a cathode-ray television. He then set the order of routes: native Wayne State OneDrive
access to the grid's files first, if it exists, the tunnel second, the VPN last.

What follows from it. Chrome plays MP4 (H.264) and WebM but not Matroska, so a browser view of the raw
downloads needs an MP4 made on the grid, whatever the route; the cut clips' preview.mp4 already is one.
At 21:30 UTC the owner said he wanted OneDrive only if Wayne State connects it to the grid natively. It
does not: OneDrive cannot reach the grid's storage, Microsoft makes no OneDrive client for Linux, and
anything there would be a copy (rclone's OneDrive backend, signed in as SymphonyBoard Folders, was drafted
and dropped the same minute). The one native link that might exist is Globus's OneDrive connector, a paid
add-on to an institution's Globus subscription; whether Wayne State's wsugrid#globus has it is a question
for hpc@wayne.edu. So the tunnel is the route, the VPN the fallback. The black frame is not yet explained:
the video's own letterbox, or OnDemand's viewer page.

## Globus works, 2026-10-20

At 21:43 UTC the owner searched Globus's collections: Wayne State lists OSIRIS Data collection, WSU-TMP
Data collection, wsugrid#globus and Share_wsugrid#globus, all on the endpoint "wsugrid#globus GCSv5.4",
subscribed, and no OneDrive collection, so Wayne State has no Globus OneDrive connector. At 21:46 UTC he
opened wsugrid#globus at https://app.globus.org/file-manager, went to a cut clip's preview.mp4 and played
it in the browser with no VPN, after one click to authenticate to the collection. So the collection has
HTTPS access switched on, and Globus's web app is a native, VPN-free browser and player for the grid's
files, under Wayne State's own setup and the owner's own sign-in, with nothing built.

This moves the recommendation. The Folders tab's "WSU grid" place becomes a link that opens Globus's file
manager at a folder (the file manager takes the collection and the path in its address), which needs no
token, no App and no step from the owner; the VS Code tunnel, built and tested in hpcworker on the same
day, adds only editing and a terminal over it, and waits on the owner's choice. Chrome still plays no
.mkv through Globus or any route, so an MP4 copy of the raw downloads remains a grid job for the owner's
word. Whether Globus's HTTPS access is allowed for PHI depends on the collection being High Assurance,
which is not known; until then the same rule holds as for the tunnel: public and de-identified data only.

## Globus as the Folders tab's own backend, 2026-10-20

At 22:00 UTC the owner asked for Globus as a second drive in the Folders tab beside OneDrive, "consistent"
in look, "as high speed transfer and streaming as possible", opening a file on a double click (Globus's
file manager opens one only from a side button), and "with as few intermediate steps as possible". Built
the same evening on the site (assets/js/symphony-panel.js, the control page's body file and control.css;
the site pull request is named in the thread), with six checks GL1 to GL6 and nine mutants in symphony-app's
signin/panel-checks/e2e2/folders.test.mjs. The design, and what was read for it from the Globus JavaScript
SDK's sources (globus/globus-sdk-javascript v6.4.0) and Globus's own static data portal
(globus/static-data-portal), since docs.globus.org does not resolve from the cloud session:

- The sign-in is the page's own: Globus Auth takes a native app ("thick client", no secret) with PKCE,
  and answers a browser's token exchange, so no route on the sign-in service was needed, unlike
  OneDrive's. The page sends the browser to https://auth.globus.org/v2/oauth2/authorize with client_id,
  response_type=code, redirect_uri (the console's own address), scope, state, code_challenge (S256) and
  access_type=offline, which asks for refresh tokens, and exchanges the code at /v2/oauth2/token,
  form-encoded, with code_verifier, client_id and redirect_uri and ?include_consented_scopes=true. The
  answer holds one token per service: the sign-in's own (resource_server auth.globus.org) and, under
  other_tokens, the Transfer API's (transfer.api.globus.org) and the collection's HTTPS server's (the
  collection's id). Each has its own refresh_token, renewed at the same endpoint with
  grant_type=refresh_token; an access token lasts two days, a refresh token until six months unused.
- The scopes: openid profile urn:globus:auth:scope:transfer.api.globus.org:all for the first sign-in; a
  mapped collection on Globus Connect Server 5.4 then refuses the listing with 403 ConsentRequired and
  required_scopes naming its data_access scope as the Transfer scope's dependent,
  urn:globus:auth:scope:transfer.api.globus.org:all[*https://auth.globus.org/scopes/<collection>/data_access],
  and the page goes to Globus Auth once more with those and https://auth.globus.org/scopes/<collection>/https
  for the HTTPS server. With the collection's id known beforehand (the constant GLOBUS_KNOWN in the
  script, blank until the owner gives it) the first sign-in carries all three and the second trip is gone.
- The listing: GET https://transfer.api.globus.org/v0.10/operation/endpoint/<collection>/ls?path=...
  &show_hidden=false&limit=2000, answering DATA_TYPE file_list with absolute_path, DATA (each entry with
  name, type dir or file, size, last_modified as "2026-10-20 10:00:00+00:00", permissions, user, group,
  link_target) and the undocumented length and total; filter=name:~*word* narrows one folder by name, since
  the API lists one folder at a time and searches nothing. The collection is found by
  /v0.10/endpoint_search?filter_scope=all&filter_fulltext=wsugrid%23globus and read at
  /v0.10/endpoint/<id>, whose https_server and default_directory the tab keeps. A folder of a million
  files is cut at 2,000 entries, which the list says.
- Opening a file: a double click opens https_server + the file's path, encoded once per segment, in a
  new tab, as Globus's own portal does with its Open button; the collection's server asks for a Globus
  sign-in there the first time and keeps a session cookie, then streams the file straight from the grid's
  data node to the browser with HTTP range requests, so a video seeks without loading whole, and nothing
  is written anywhere unless ?download is asked, which the Download verb asks. The page proxies nothing,
  so the speed is the data node's uplink and the person's own connection, with no hop of ours.
- The preview pane plays a video or a sound from the same address with a video element, and fetches a
  text, an image or a PDF (up to 50 MB) into the page with the collection's own bearer token.
- Read-only: the command bar's writing verbs, the menus' and the ticks are off on Globus; Track stays
  OneDrive's. Both drives are kept on the browser per GitHub account (OneDrive under the login, Globus
  under login|globus), each a root in the folder tree, a press on the other switching; Forget Globus
  leaves OneDrive.
- Globus issues new collection domains under gaccess.io since July 2025; wsugrid#globus keeps its
  data.globus.org one, and the tab reads https_server from the collection document, hardcoding none.

What was not measured, since the cloud session cannot reach globus.org (the proxy answers 403): whether
the collection's HTTPS server allows the page's origin (CORS) for the preview pane's fetch, which the
double click never needs; whether a video element plays from the address without the first sign-in
click in a tab (the pane falls back to an Open in a new tab button on an error); and the exact filter
syntax of ls, taken from the SDK's types and Globus's documentation as remembered. The owner's two
one-time steps: register this page at https://app.globus.org/settings/developers as a thick client
whose redirect is https://openspineconsortium.com/symphony/control/ and give its client UUID, and read
wsugrid#globus's UUID from its Overview tab in the file manager; both go into the script's constants.

The adversarial review of the first build (the same evening) found thirteen things, all fixed before the
pull request: the collection was matched on display_name alone and fell back to the search's first hit,
so a stranger's lookalike collection could have been opened (now an exact match on either name, else no
collection); a fetched PDF was shown in a frame that was same-origin with the console and allowed
scripts, so a file named .pdf but typed text/html by the server could have read the page's storage (now
retyped by this page's own choice and framed with no script); a consent hop taken on its own after every
return could bounce the page between the two sites for good (now once per collection per sitting, then a
button); one refused refresh token forgot the whole connection (now only the Transfer API's does); every
download but the first was blocked by the browser (now one per press, said); the tree walked the
cluster's root and every folder above home (now it starts at the home folder); the active drive was
recorded under an empty login; names reached the message area through the link-maker (now as text);
Authorization followed redirects (now redirect: error); and three smaller inconsistencies in the head
and the status bar. The list's error now says why and links the fixes: the same folder in Globus's own
file manager (app.globus.org/file-manager?origin_id=<collection>&origin_path=<folder>), Connect Globus
again, the consents page and Globus's status; and since Globus moves and streams files only, the same
place names Beethoven for a shell, a job or Claude Code on the grid, with the page that says what it
does, the Chrome Web Store listing to install it and OnDemand on the VPN as the portal, as the owner
asked at 22:21 UTC (links and error messages when it is broken, the theme, the text size, which A- and
A+ already scale, and help for a person without the Beethoven extension).

Globus is files only (listing, streaming, transfers, sharing; Globus Compute runs functions, not a
shell), so an interactive terminal on the grid without the VPN stays the VS Code tunnel's (above), built
and parked in hpcworker, or OnDemand's shell on the VPN.

## Live on the grid, 2026-10-21

The owner registered the page at Globus on 2026-10-21 (a native app, "Symphony control panel", a thick
client with the console page as its redirect and the Apps' privacy statement as its privacy URL; site
#120 carries the client id, site #119 the collection's) and signed in: the Transfer API listed his home
folder on wsugrid#globus, 1221 entries, as go2432@wayne.edu, read-only, with OneDrive still connected
beside it. One thing the mock had not shown: the collection's endpoint document gives default_directory
as the placeholder "{server_default}", which the Transfer API resolves but the page had shown as the
folder's name; a placeholder (any value with a brace, like "/~/") is now no path, and the first listing's
absolute_path says where home is.

His next words were about the look, not the plumbing: the head read as one long sentence beside a
globe, and he asked for the drives mounted "like something Apple would have for mounting multiple cloud
accounts", consistent with the rest of the panel, and in the Workers tab's card shape. So the head now
carries an accounts strip: one card per drive kept on the browser, in the console's card shape (12 px
radius, the theme's line, a 3 px inset accent in the drive's colour, the one shown lit in teal), with the
drive's mark, its name and whose it is ("Greg (personal)", "go2432@wayne.edu, read-only"); a press on
the other card switches to it, an eject control on the lit one forgets it (the head's own Forget button,
moved into the card, its words kept for a screen reader), and a dashed card adds a drive. The Add a
cloud drive dialog lists the drives as rows, each with its mark, its name and a word on it, as a
system's add-account sheet does. The words that say whose drive it is stay, in one small line under the
head, since every state of the panel is written in words. The strip's radii, borders and hover colours
read the Panel design system thread's tokens (--ds-radius, --ds-border, --ds-surface, --ds-hover-border,
--ds-hover-bg) with the old values as fallbacks, so it looks the same before and after that thread's
shared classes land, and takes them when they do. The checks FS1 and GL1 to GL7 and the whole Folders
file hold it, and the Folders mutants were run against it.

## PHI and the patent

- A dev tunnel's traffic passes through Microsoft's relay. VS Code's documentation describes it as
  end-to-end encrypted over ssh (the author's knowledge, to check), but no source found on the day says
  dev tunnels are under Microsoft's HIPAA business associate agreement. Until the IRB or Wayne State's
  privacy officer says otherwise, the tunnel is for de-identified data and the public corpora, and PHI is
  viewed through OnDemand on the VPN, which keeps it on Wayne State's network
  (docs/research/phi-with-microsoft-365.md).
- A copy into the owner's Wayne State OneDrive stays under Microsoft 365's agreement, if Wayne State allows
  PHI there, which that note says is the privacy officer's to answer.
- Globus handles PHI only on a High Assurance subscription and collection (the author's knowledge); whether
  wsugrid#globus is one is not known.
- The SchwingNet videos are confidential until the provisional is filed. A tunnel opened only by the
  owner's account and a Wayne State OneDrive are both private to him; nothing here makes them public.

## What is not yet measured

- `code tunnel` on a compute node: on EL7 directly, or inside an Apptainer image, and whether the stored
  sign-in survives from one job to the next.
- Whether Wayne State accepts a dev tunnel from a job (ask hpc@wayne.edu), and whether its Entra policies
  block the tunnel's Microsoft sign-in, as Utah's do; a GitHub sign-in avoids that (Utah's page).
- vscode.dev playing a fluoroscopy MP4 through the tunnel, and how fast it starts on the lab volume.
- Whether OnDemand's View serves an MP4 inline so it plays in place.
- Whether wsugrid#globus has HTTPS access switched on: it has (the owner's test, above).

## What waits on the owner

- The choice of route (the thread's card), and his word before the beethoven-extension merge.
- For the tunnel: one GitHub device-code sign-in when the first job prints its code, and Wayne State's word
  on tunnels if he wants it first.
- For a OneDrive copy from the grid: whether PHI or confidential renders may go there.
