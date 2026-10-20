---
name: ashley-extension-project
description: "Ashley = the grid + Claude Code VS Code extension at Desktop/ashley; v3.0.0 (Trial + Full Edition agreements, access by approval, click-to-fix, sandbox kit) built 2026-09-28; read docs/CHECKPOINT_2026-09-28.md first; keys in ~/.ashley-vendor; what still needs Greg"
metadata:
  node_type: memory
  type: project
  originSessionId: 0599380b-0d32-4e19-b5be-65bdd1017566
  modified: 2026-09-28T13:41:28.897Z
---

**Read first:** `C:\Users\grego\OneDrive\Desktop\ashley\docs\CHECKPOINT_2026-09-28.md` (top section
"CURRENT STATE"). Repo `Desktop\ashley`, branch main, private remote
https://github.com/GregorySchwing/ashley, pushed with `bash tools/push_via_grid.sh` (the grid's
GITHUB_TOKEN never leaves the grid; the clone is 700 and deleted after). Build with the portable
Node 22 at `C:\Users\grego\tools\node22`.

**State 2026-09-28 evening (v3.0.0, commits through the 3.0.0 release):** two agreements (Trial
Edition free for approved AccessIDs, LICENSE.txt; Full Edition LICENSE-FULL.txt shown when a non-trial
key is registered), wizard = Wayne State sign-in then automatic access key from the Cloudflare access
service (`tools/intake/`, approved list + request page + admin page; DEPLOYED 2026-09-28 at https://ashley-service.openspineconsortium.workers.dev on Cloudflare account go2432@wayne.edu; deploy from WSL with ~/node22, `tools/intake/deploy.sh`; admin token in ~/.ashley-vendor/admin_token; `tools/intake/admin.mjs`), service
addresses from `services.json` on the support site, click-to-fix rows, Windows Sandbox kit
(`tools/sandbox/`, feature not enabled on Greg's PC), PUBLISHED on the VS Code Marketplace 2026-09-28 20:24 UTC as `OpenSpineConsortium.ashley` 3.0.0
(publisher `openspineconsortium` under the personal Microsoft account gregoryamdg@gmail.com; uploaded
through the web management page because a new Azure DevOps org now needs an Azure subscription, so no
PAT; updates = next integer VSIX via the page's Update; verified-domain badge not before 2026-12-21). Grid sign-in relay `grid/login_relay.sh` waiting on asx1 for Greg's code.

**State 2026-09-28 midday (v2.0.0):** extension id `openspineconsortium.ashley` (installed in Greg's VS
Code); per-person Ed25519 license keys (`grid/license.js`; issuer `tools/license/ashley-license.mjs`;
vendor folder `C:\Users\grego\.ashley-vendor` with release key `k1` and trial key `trial`; Greg's
own license `L-02dodeGmoygG`, lab edition, valid to 2027-09-28, in `~/.ashley-local` and
`~/.ashley/license.key` on the grid); first-run SIGNING dialog (terms version 3: four un-prechecked boxes with recorded labels, typed name, "Accept and Continue", opt-out error reports; the record gates the daemon, MCP server and CLI too; no arbitration, see [[ashley-compliance-boundary]]); Claude
sign-in only through Claude Code's own flow (see [[ashley-compliance-boundary]]); trial/report
service in `tools/intake/` (Cloudflare Worker, not yet deployed); CI + triage workflows, CODEOWNERS,
CONTRIBUTING, ENGINEERING, SECURITY, PRIVACY; release via `node tools/release.mjs` (checks + signed
SHA256SUMS in `dist/release/<v>/`; bundles readable, no maps, because the Marketplace has pulled
minified extensions); listing fields ready (`pricing: Trial`, site links, telemetry.json); support
site pages in `docs/site/`, staged but NOT committed in `openspineconsortium.github.io/ashley/`
until Greg supplies the notice address. Twelve wizard steps; last = "Sign in to Claude on the grid".

**Still needs Greg:** the notice address for the support page and publishing the site; the
Checklist B items in the checkpoint (LLC, E&O insurance, copyright registration, MI sales tax or
a merchant of record, EAR self-classification, COI disclosure, a GitHub token with `workflow`
scope for branch `workflows-pending`); `Ashley: Sign in to Claude on the grid` (then phone access via `Ashley: Phone
access`, which asks him to answer Remote Control's consent in a terminal); the Wayne State sign-in in
the university tenant; deploying the intake Worker (trials, reports); the three written answers
(Anthropic, WSU OTC, counsel); a second student account.

**Traps that cost time here:** inline bash heredocs collapse `\\n`/`\\d` in Python and JS (write
patch scripts with the Write tool, run by path); a quoted `'~/x'` over ssh makes a literal `~`
folder; `claude mcp add-json` refuses an existing name; `--resume` looks only in the running
`CLAUDE_CONFIG_DIR/projects`; Linux-only tests run in the container via `tools/grid_tests.sh`
(17 pass there); the release check must guard against source maps (1.0.0 shipped them).
Related: [[grid-apptainer-module-works]], [[grid-slurm-inside-apptainer]], [[windows-ssh-to-grid]].

**Grid Claude account since 2026-09-29 05:02:** Greg re-signed in on the grid with his personal Google-linked Claude account (gregoryamdg@gmail.com, Max), not the WSU-e-mail one; consent recorded by Claude Code; Ashley phone host environment env_01BSwGFbdvjXwTG56B86GYnm. Licence identity is the AccessID (go2432), independent of the Claude account e-mail; the wizard text 'the account you made with your WSU e-mail' is a suggestion, not a check.
