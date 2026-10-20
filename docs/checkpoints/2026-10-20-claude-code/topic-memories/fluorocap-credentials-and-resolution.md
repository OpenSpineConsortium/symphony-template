---
name: fluorocap-credentials-and-resolution
description: "Credential store for FluoroCap harvesters (~/.fluorocap on WSL, never printed) and the publisher-original refetch that fixes panel resolution without credentials"
metadata: 
  node_type: memory
  type: project
  originSessionId: e44eca96-f48c-494d-ba1f-7dae68bdf06d
  modified: 2026-09-14T20:32:55.024Z
---

Set up 2026-09-14 after the corpus QC found the median panel 231 px on its short side.

**Credential store**: `~/.fluorocap/credentials.env` on WSL (mode 600, outside every repo), template
`tools/credentials.template.env`, loader `tools/fluorocap_creds.py` (`init` / `check`; check prints names and
pass/fail only). Cookie jars under `~/.fluorocap/cookies/`, Instagram session at `~/.fluorocap/instagram_session`.
User-facing checklist: `docs/CREDENTIALS_SETUP.md`. Never echo a value, never commit a filled copy.

**Resolution fix that needs no credentials**: `tools/fluorocap_refetch_hires.py` replaces PMC figures with the
publisher's copy by deterministic URL rules. Measured gains on corpus figures: Cureus 16x, MDPI 9-20x, Elsevier
CDN 12x, Frontiers 6x, Springer/BMC/Nature 4x. SAGE/Atypon, Wiley, LWW and JNS block bots (403/202); those need
the WSU proxy cookie or the publishers' TDM APIs. Run from WSL (`~/fluorocap_tools`), output `raw_hires/` and
`refetch_hires.jsonl` in `~/FluoroCap_wsl`; `--apply` swaps winners into `raw/` keeping `<file>.pmc`.

**Why:** the user asked for institutional access, Instagram/Facebook logins and API keys to fix image size; the
biggest gain turned out to be free, and the credentialed routes carry real risk (publishers block a whole
university range for bulk downloads; Meta disables accounts used for automated collection).

**How to apply:** try the credential-free refetch first; for closed journals prefer the Elsevier/Springer/Wiley
TDM APIs over proxy scraping; Instagram only on a dedicated account. Grid IP 141.217.x.x is inside WSU's range
(IP-authenticated access untested because LWW blocks non-browser clients). See [[fluorocap-dataset]],
[[fluorocap-repo-private]].

**Learned 2026-09-15 (rounds one to three):** LWW and Medknow open copies (10.1097, 10.4103) resolve to
www.ovid.com with no login; their image API caps at 1200 px (`/width/1200.jpg` returns a lossless PNG). AME
figures sit in the `imgSource=` query of an image renderer on cdn.amegroups.cn. The Korean M2PI journals
(e-neurospine, asianspinejournal, jkns) serve the full-size figure from `/upload/thumbnails/`, and medrang
originals are the thumb URL without `/thumb/`. Hindawi (10.1155) lives on Wiley (proxy + TDM), figure number
is the `.00N` suffix. Never exclude "thumb" from candidate URLs; never route CDN fetches through the proxy after
a proxy 404 (that alone lost AME and M2PI in rounds one and two). SNI (surgicalneurologyint.com) times out;
Synapse (`-l.jpg`) and Dove originals are only ~500-750 px, so their PDF route matters. The trial-ledger
option is `--ledger`. Rounds: `~/round2.sh`, `~/round3.sh` on WSL (frozen); markers ROUND2_DONE / ROUND3_DONE.
