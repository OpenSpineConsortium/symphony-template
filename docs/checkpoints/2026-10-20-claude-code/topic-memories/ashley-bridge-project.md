---
name: ashley-bridge-project
description: Ashley Bridge = university-agnostic HPC worker framework (hpcworker) + browser extension over Open OnDemand that surfaces a Claude Code worker in claude.ai via Remote Control; repo Desktop/ashley-bridge, GitHub GregorySchwing/ashley-bridge (private); built 2026-09-29; research report in ashley/docs/research/reports
metadata:
  type: project
---

**What it is (decided 2026-09-28/29):** the port of Ashley's best parts into (1) `framework/` (`hpcworker`,
bash + Python 3 stdlib; site profile JSON per university; Slurm/PBS/LSF adapters; probe job; worker job
running `claude remote-control` under a pty in tmux inside the Apptainer image; always-on chain via
`--dependency=afterany`; one-sitting `claude login`; never deletes outside its run dirs; refuses
destructive commands under CLAUDECODE) and (2) `extension/` (WXT MV3, Chrome/Edge side panel, Firefox
MV2, Safari untested; ONLY a content script on the student's Open OnDemand origin granted at click
time; Shell WebSocket bootstrap for one sbatch; Files JSON mailbox for status.json/connection.json;
no cookies/tabs/claude.ai permissions; audit chokepoint with 60 s scheduler floor; signed kill-list;
Ashley's Ed25519 keys and clickwrap ported). The claude.ai side is Anthropic's own Remote Control:
the worker's `environment_url` (`https://claude.ai/code?environment=env_...`) is what the green
"Open in Claude" button opens. The two prior PDFs' claude.ai-interception design was rejected
(Consumer Terms).

**Why:** Greg's directive 2026-09-28: bring the HPC Claude worker to claude.ai, university-agnostic,
as easy as "open the OnDemand tab, start a persistent worker, open claude.ai". The one manual step
that stays is Anthropic's paste-code login (monthly) plus the one-time consent, both the student's
own acts; the extension never handles them.

**How to apply:** read `ashley-bridge/CLAUDE.md`, `docs/RESEARCH_REPORT.md` (build spec),
`docs/OPEN_QUESTIONS.md`. Tests: `HPCW_PYTHON=python bash framework/tests/run.sh`; in `extension/`:
`npx tsc --noEmit && npx vitest run && npm run build`. Mock portal: `node extension/mock-ood/server.mjs`.
Wayne profile points `claude_config_dir` at `~/.ashley/claude` (Ashley's login). Push with
`bash tools/push_via_grid.sh` from the bridge repo. Related: [[ashley-extension-project]],
[[ashley-compliance-boundary]], [[grid-ashley-deletion-2026-09-28]].

**v2 flow (2026-09-29 morning, commit in ashley-bridge):** icon click = connect + side panel; options page on
right-click; step machine with one button; sign-in sitting in the panel (`hpcworker claude login --plain`,
AUTH-URL tab, one paste box, code never logged/stored); consent marker `~/.hpcworker/consent` written on the
data statement; framework VERSION 2 deployed to the grid; TERMS_VERSION 2. Live-portal facts: WSU OOD shell
host default -> warrior; uploads disabled (PUT works); Job Composer JSON present; /rnode 404 (mailbox mode);
a missing file downloads as 200 text/html (existence must come from the directory listing); cold PUN gives a
500 once. Untested by a human: the v2 flow end to end. Load unpacked from extension/.output/chrome-mv3.

**Tester key (2026-09-29):** site key lid L-kBUmEepmm5D8 for wayne.edu, valid to 2027-03-28, in ~/.ashley-vendor/licenses/; any wayne.edu portal user; revoke when the pilot ends. Bridge extension 2.0.0 honours site keys. Tester package: Desktop/Ashley Bridge for testers. First tester: Ashley (Ashleykschehr@gmail.com), instructions e-mailed by Greg.

**Store kit (2026-09-29 afternoon, ashley-bridge a74de0c, extension 3.0.0):** public pages live at
https://openspineconsortium.com/ashley/bridge/ (privacy v4, agreement v3) and the signed kill-list at
/ashley/bridge-killlist.json (k1; signer `ashley/tools/license/ashley-license.mjs sign-killlist|verify-killlist`;
pages via `tools/site_bridge_build.py`; `extension/test/killlist.live.test.ts` trips when anything is withdrawn).
Store texts and click-by-click in `docs/store/LISTING.md` + `SUBMISSION.md`; screenshots in
`extension/store-assets/`; reviewer key L-Dw8z5-3R4RAK (username st1234, to 2027-03-28). Facts fixed after review:
kill-list is fetched only after acceptance (so PRIVACY's sentence holds); LICENSE v3 dropped the activation ping /
error reports Bridge never had; `normaliseOrigin` refuses Anthropic hosts. Greg opens the store accounts (CWS $5 +
2SV, Edge Partner Center, AMO); once live, students install from the stores with no developer mode. Not yet: a human
run of 3.0.0 against the live portal; k1.pem is unencrypted; Safari deferred.

**No keys in Bridge (Greg, 2026-09-29 afternoon, binding):** "the user name to key complexity should be completely removed";
the grid sign-in identifies the person (the extension reads the signed-in account name the OnDemand dashboard shows,
never a cookie, never a typed name) and the access service answers whether that account is approved (the same
allowlist the Ashley admin console manages; request page -> Greg approves -> next icon click works). No licence keys,
no skeleton/site keys, no paste box; the kill-list withdraws versions only. Tester site key L-kBUmEepmm5D8 and reviewer
key L-Dw8z5-3R4RAK retired. Ashley VS Code keeps its own key flow unless Greg says otherwise. Being built as 4.0.0
(LICENSE v4, PRIVACY v5, Firefox data_collection personallyIdentifyingInfo, Worker route access_check with CORS).

**4.0.0 built and proven (2026-09-29 evening, ashley-bridge 835e1b4, ashley a5cd818, site c79229f):** access_check
route live; extension approval flow e2e-proven against the real service (st1234 approved -> online 17/17; zz9999 ->
Ask for access); LICENSE v4 / PRIVACY v5 / TERMS_VERSION 4; framework 3 on the grid (7-day resume, `<site>-<run>`
session name). Laptop-off property: the worker is a Slurm job chain (afterany successor, `--continue`), started over
ssh alone it registered env_01CgWERV6rm8gb61NvaBcn9s; the portal is needed only to start/stop/restart. Tester package
4.0.0 has no key. Next: Greg opens the store accounts (docs/store/SUBMISSION.md); a human run against the live portal.

**Repos and releases (2026-09-29 evening):** the organisation's PRIVATE copy https://github.com/OpenSpineConsortium/ashley-bridge
(created by API with WSL's stored GitHub credential; the grid token has no org rights) mirrors the personal
GregorySchwing/ashley-bridge. Push both: `bash tools/push_via_grid.sh` (personal, grid token) and
`wsl -e bash -lc 'bash /mnt/c/.../ashley-bridge/tools/push_org.sh'` (org, WSL credential). Release v4.0.0 on both
with chrome/edge/firefox/safari/sources zips + SHA256SUMS (also in `release/4.0.0/`); edge.zip == chrome.zip bytes;
safari.zip is converter input only. README has the developer build and release steps; `npm run zip:all`.

**Shared copy (5.0.0, 2026-09-29 night, ashley-bridge 4c6eada):** Greg's rule "Claude Code is the gas, the Ashley code
is the car": the framework lives in the lab's read-only shared dir `/rs/rs_grp_oschome/shared/ashley/hpcworker/current`
(published by `tools/deploy_shared.sh`; flip `current`; never delete), a student's account gets only a launcher +
marker + profile + PATH block (`hpcworker install --shared`); per-user upload is the fallback for sites without a
shared dir; framework 5, agreement v5, privacy v6. Updates for students = Greg publishes to the shared dir; the
extension updates itself only through the stores. GitHub cannot be an update channel for students (private repo, no
token). Students must be in group oschome (only ab5188, go2432 today). Greg's account is converted: do not load an
unpacked 4.0.0 on it. Releases v5.0.0 on both repos; `docs/store/TEST_BEFORE_UPLOAD.md` for hand tests.

**Beethoven (2026-09-29 night, binding):** the public product name is **Beethoven** (Greg first said "Claude for the
Grid", warned about Anthropic's mark, chose Beethoven). Browser extension 7.0.0 = Beethoven (agreement v6, privacy v7,
TERMS_VERSION 6); public pages LIVE at https://openspineconsortium.com/beethoven/ (index, privacy, terms, support,
request, services.json, killlist.json); access service second name https://beethoven-access.openspineconsortium.workers.dev
(same Worker code/KV/secrets; ashley-service kept for installed copies); the old /ashley/bridge/ redirects. Greg then
asked for the OLD NAME EVERYWHERE to become Beethoven (VS Code edition -> "Beethoven for VS Code" under a NEW Marketplace
id; grid CLI/folders with symlinks; key prefixes with dual acceptance; vendor folder; site area /ashley -> /beethoven with
redirects) -- the global workflow script is in the scratchpad (rename-beethoven-global.js), to run after the extension
integration finishes. **Ashley Schehr is a person (tester, awards on the website): never rename her.**
**Repos (2026-09-30):** ONLY the organisation copies exist going forward: https://github.com/OpenSpineConsortium/beethoven
(was ashley-bridge; GitHub redirects) and https://github.com/OpenSpineConsortium/beethoven-vscode (the ashley repo). Push
with `tools/push_org.sh` from WSL in each repo (the grid token has no org rights; push_via_grid.sh retired). The personal
GregorySchwing/ashley and GregorySchwing/ashley-bridge must be deleted BY GREG (my tokens lack admin rights); their
content is on the org copies (ab1e1fa/05efbf6 verified). Admin token rotated 2026-09-30 (the old one was sent to Resend
once by mistake); Resend key installed; test e-mail delivered (200). Website restructure (home = Beethoven only, tabs as
pages, onboarding primer with "Is the female pelvis relatively wider?") running as a workflow.

**Website rebuilt (2026-09-30, site commit 816e9c4, live):** openspineconsortium.com is generated by
`openspineconsortium.github.io/tools/build_site.py` (ONE navigation definition; body files in tools/pages/; renders
the Beethoven agreement/privacy from ashley-bridge's LICENSE.txt/PRIVACY.md; copies release/<ver> zips to
/beethoven/downloads/; stamps every asset ?v=<utc>; its own link/parse/coverage checks). Never hand-edit generated
HTML; never run the retired ashley-bridge site builder. Home page (= /beethoven/) is only: headline, the claude.ai
diagram (Claude servers / Wayne State grid -> up to Claude, left to H200), the needs line, the request form, four
browser cards (Direct download until a store URL is set in BROWSERS), the trademark line. Tabs: Home, Onboarding,
Research, Data & Tools, People; Get Involved -> /beethoven/request.html. GitHub Pages "Enforce HTTPS" turned on.
Greg dislikes: long technical text on product pages, off-theme pages, one giant page; wants apple.com restraint.

**Global rename done (2026-09-30; beethoven-vscode 0475b63, beethoven fb97c2c, site be44925):** vendor folder is now
`C:/Users/grego/.beethoven-vendor` (the old `.ashley-vendor` is a junction to it; scripts read BEETHOVEN_VENDOR_DIR then
ASHLEY_VENDOR_DIR); vendor tool `tools/license/beethoven-license.mjs` (ashley-license.mjs is a wrapper). Grid: command
`beethoven` (alias `ashley`), `~/.beethoven` (`~/.ashley` is a link), shared framework at
`/rs/rs_grp_oschome/shared/beethoven/hpcworker/current` (the old `shared/ashley` is a link), framework 7, Claude sign-in
at `~/.beethoven/claude`. Keep the links until builds older than Beethoven 8.0.0 / Beethoven for VS Code 4.0.0 retire.
Prefixes: verifiers accept ASHLEY1/BEETHOVEN1 and ASHLEYREV1/BEETHOVENREV1, but issuers keep the OLD prefix
(Worker var KEY_PREFIX=ashley, tool --prefix) because shipped 4.0.0-7.0.0 and VS Code 3.0.0 accept only those; never
re-sign killlist.json with the new prefix yet. Next browser build is 8.0.0. VS Code edition = "Beethoven for VS Code"
4.0.0, NEW Marketplace id openspineconsortium.beethoven (Greg uploads; then Unpublish, never Remove, the old id).
Do not run Ashley VS Code 3.0.0's "Install on the grid" or "repair" on the grid again (it writes v6 scripts through the links).

**Access control model (2026-09-30, Greg, binding):** distribution ONLY through a PRIVATE Chrome Web Store listing (Google
Group of trusted testers that Greg maintains; no Edge/Firefox/Safari, no public downloads anywhere; the site's
downloads folder is purged from git history). One approved AccessID = ONE browser installation: the extension sends its
random install id with each approval check; the service binds the first and refuses others ("other_installation") until
Greg moves or withdraws it by e-mail link or admin.mjs reset-seat; clients without an install id get "update_required".
Approval kinds: grants extension+lab, or lab only. Request portal on the site: AccessID, name, WSU e-mail, Google account
(for the listing invitation), purpose text, optional CV (KV, 12-month TTL, signed view link), WSU mailbox proof by
one-click e-mail when MAIL_STUDENTS=1 (needs Resend domain verification first). Refused on principle and by Chrome's
policy: obfuscation, hardware fingerprinting, MAC hashing, hidden tracking; the earlier asks for those were declined and
Greg accepted the installation-id model instead. Framework 8 writes a CLAUDE.md grid guide into each worker workspace.

**8.0.0 released (2026-09-30 midday):** beethoven c05f595 + release v8.0.0 (Chrome zip only; no grid-side tool inside;
install_id seats), beethoven-vscode cb6b143 (service v2: seats, grants, request portal with CV, mailbox proof behind
MAIL_STUDENTS; REQUIRE_INSTALL_ID "0" until everyone runs 8.0.0), site 3f805f4 = HISTORY PURGED (all packages ever
published removed from every commit; tree unchanged; backup bundle in the scratchpad; old tip 648e151). The site has NO
downloads any more; Chrome private listing only (Google Group "Beethoven-users", Greg maintains; consumer Groups have
no API; a Workspace adapter exists behind GROUP_MODE for later). Follow-up running: Move-link guard, st1234 exemption
localhost-only, decision links tied to the request version, mailbox required + lifecycle (submitted/confirmed/decided/
invited/installed), Done-invited link + daily reminder, admin page, framework 9 = Slurm client inside the worker.
Greg's pending items: create Beethoven-users group; Chrome private upload of 8.0.0; Resend domain DNS at Spaceship
(then MAIL_STUDENTS=1); delete GregorySchwing/ashley and ashley-bridge (needs his token: file
.beethoven-vendor/github_admin_token); after everyone is on 8.0.0 set REQUIRE_INSTALL_ID=1 and deploy both names.

**9.0.0 released (2026-09-30 night):** beethoven 782e648 + private release v9.0.0. 9.0.0 = 8.0.0 with the site theme (bundled Newsreader + IBM Plex), the worker-rack icon and THIRD_PARTY_NOTICES.md in the package; same permissions, agreement v7, privacy v8. The upload is 9.0.0, NOT 8.0.0. Store kit: release/9.0.0/store-kit/ (numbered in dashboard order) + docs/store/PASTE.md (text for every field). Store images rebuild with extension/store-assets/src/build_assets.mjs --pw <scratchpad pw/node_modules/playwright> using Node 22 at /c/Users/grego/tools/node22 (node is not on PATH in Git Bash or PowerShell). Store icon = the package 128 with transparent padding (the store refuses alpha only on screenshots and tiles). Not uploaded to the store or YouTube; Official URL waits on Greg's Search Console verification file; Resend still waits on his Verify press.

**2026-10-01:** Resend verified openspineconsortium.com; student mail is ON (wrangler.toml MAIL_STUDENTS "1", vendor mail_from = access@openspineconsortium.com), both Worker names deployed, beethoven-vscode b7a4929. A request now goes first to <AccessID>@wayne.edu for confirmation; that confirm e-mail has not been exercised live with a real unapproved student yet (unit tests only). Greg reports Official URL (Search Console file googlec3911e7fb095977e.html is live at the site root) and Trusted testers (the Beethoven-users group) done in the Chrome dashboard. The dashboard also has a Test instructions tab (Username, Password, Additional instructions) that the older docs said did not exist; texts drafted by workflow wf_9d34b0f6-356.

**10.0.0 released (2026-10-01 early):** beethoven f8d2e88 + private release v10.0.0; 9.0.0 was NEVER submitted and must not be uploaded. 10.0.0 fixes two defects observed in a running browser on 9.0.0: (1) Chrome was asked for a site permission on claude.ai before the refusal (typed into the setup page's Connect field); now refused before any prompt, any scheme, leftover grants removed at start; (2) the agreement's Accept button enabled without scrolling; now needs scroll-to-end or both texts opened in tabs, record says which (opened_in_tab). Store kit release/10.0.0/store-kit (12-test-* files = the dashboard's Test instructions tab: Username 96 chars 'None: Beethoven has no account...', Password empty, 490-char instructions; limits 100/100/500); docs/store/PASTE.md has changed host-permission and activeTab justifications that must be re-pasted. Reviewers get release/10.0.0/reviewer/beethoven-mock-portal.zip, never the sources zip. Service beethoven-vscode 9ba36d2: reviewer mock account st1234 approved only at a localhost portal; public GET /allowlist returns an empty list (list at GET /admin/allowlist with the admin token); services.json (both) no longer names allowlist (site 9c47d38 published first; Worker deploy scheduled about 70 min later so VS Code clients refresh their 1 h cache). Open: Greg must supply the notice address (postal + e-mail, not university or hospital) for the support page before submitting; remove the st1234 approval once the store review has passed; next LICENSE/PRIVACY versions should name the new record fields and say 'no site permission on claude.ai'; VS Code privacy v5 still says it fetches the approved list. Lesson: never type a git stash into a probe command (I stashed the service tree by accident and popped it back; tests confirmed intact).

**2026-10-01 09:00 UTC:** the service (9ba36d2) is DEPLOYED under both names and verified live: public /allowlist answers an empty list; st1234 approved at portal localhost from two installation ids; st1234 refused at ondemand.grid.wayne.edu with no seat and no conflict; the three approved records intact. Remaining before Submit: Greg's notice address on the support page.

**11.0.0 in progress (2026-10-01):** redesign of the first run and a home panel per Greg's brief ([[beethoven-first-run-ux]]). Spec: scratchpad v11/SPEC.md (also the basis of docs/V11_CONTRACT.md); build workflow wf_ff1e10ef-b1c (contract, then cluster tool framework 10, extension core, pages, mock+e2e harness, texts LICENSE v8 / PRIVACY v9; verify; integrate; final screenshots in scratchpad v11/final/shots). Facts established on the grid: the portal ondemand.grid.wayne.edu signs in with HTTP Basic (401 WWW-Authenticate: Basic at /pun/sys/dashboard/), so the browser keeps the sign-in until it closes and the extension can work from its background with no portal tab; Greg's worker took 6 min in the reqp queue; Greg's own account has a grid-side key (id_rsa 2022) and the grid makes none automatically, so a student with no key will probably get a password prompt from the portal's Shell app: 11.0.0 adds a one-time guided 'hpcworker login-setup' step, UNPROVEN on the real grid until a keyless student (Ashley, hy9698) tries it. Decisions taken: one tick agreement with optional Show terms, no install-time host permission, no GitHub line, Beethoven never types the university password. Not done until I review the screens: store images, store docs, website, release/11.0.0, framework 10 deploy to Ceph. 10.0.0 has not been submitted to the store as far as I know.

**11.0.0 committed (2026-10-02):** beethoven 95d7eea pushed (extension 11.0.0, framework 10, LICENSE v8, PRIVACY v9). Proven on the mock only. Framework 10 is NOT deployed: its lib/relay.py ran python3 on warrior for the whole Claude sign-in, and warrior's banner bans python by name; workflow wf_c8583091-ebe is replacing it with a shell relay. Deploy with tools/deploy_shared.sh only after that passes. Still out of date: store docs and images (10.0.0), website terms/privacy pages (v7/v8), no release/11.0.0 or GitHub release yet.

**12.0.0 released (2026-10-02):** beethoven 8af64d6 pushed; private pre-release v12.0.0 (package, three bridge installer zips, store kit, mock zip, sums); site 9fdbc13 published (LICENSE v9, PRIVACY v10, reviewers and support pages); framework 11 DEPLOYED to the grid (current -> v11). 12.0 = the direct way by ssh without the VPN tried first (bundled script bridge: PowerShell on Windows, Perl on mac/Linux, installed once by the student, nativeMessaging permission), the sign-in sheet for AccessID+password+code, a browser key (non-extractable by default, Hello/Touch ID opt-in), the gate and restricted key line in framework 11, the phone route with QR codes, VPN/OnDemand path as fallback. No browser-only bridge exists (Secure Shell exposes no byte stream; Cloudflare terms exclude a Worker relay); relay and store-extension providers are stubs. BLOCKER on the real grid: framework 11's browser-key check refuses because three CephFS scaffold folders above the volume are world-writable without sticky and owned by root or another lab (/.rs/volumes/rs_grp_hpc_allusers_readonly, /.rs/volumes/rs_grp_oschome, /.rs/volumes/rs_grp_oschome/rs_vol_oschome); only C&IT can chmod +t them (or the lab moves the shared copy, or the check is relaxed). I set +t on the three go2432-owned folders (the volume root uuid dir, shared, shared/beethoven). Also still open: Greg's tests G1 (key sign-in off-VPN), G2 (phone paste), G3 (real Hello/Touch ID); store screenshots are 9.0.0's; the 11.0 e2e scenarios 0-12 were not re-run on 12.0.0; Decision list in docs/V12_STATUS.md; the worker's renewal job sat PENDING >12 h on reqp (partition is the lever).

**2026-10-02 late:** framework 12 deployed (7c8a484): folders above the lab's copy owned by others (CephFS scaffold) are notes, not refusals; browser-key check now passes on the grid with four notes for C&IT. Ashley (hy9698): her 12.0.0 installation was refused other_installation because Greg's Move link bound an older 10.0.0 install id; I reset her seat; her next panel open binds the current installation. Greg's admin token is the file C:/Users/grego/.beethoven-vendor/admin_token (never paste it in chat). All of Greg's non-Beethoven grid jobs were cancelled at his request; the worker renewal 40523658 still PENDING on reqp (QoS requeue priority 100) while secp has 47 idle nodes (QoS secondary priority 200): recommended switching the worker's partition_cpu_batch/qos_batch to secp/secondary (his decision). Greg asked for no more extensive browser-scenario testing.
