---
name: signin-worker-deploy
description: How the control panel's sign-in Worker reaches Cloudflare, and why GitHub can answer it 429
metadata:
  type: project
  modified: 2026-10-20T17:04:41.572Z
---

Since symphony-app #62 (2026-10-20), a push to main that changes signin/worker.js runs .github/workflows/deploy-signin.yml, which uploads the Worker through Cloudflare's API with the one secret CLOUDFLARE_API_TOKEN ("Edit Cloudflare Workers" template), keeping its bindings (scripts/deploy_signin.py). greg never pastes code into Cloudflare again; until the secret is set the run ends green with a notice.

GitHub's login endpoints rate-limit by IP, and Workers share Cloudflare's egress IPs, so /exchange can get 429 from other sites' traffic. The Worker resends on 429 (never on 5xx, since a code or refresh token may be spent), and so does the panel (exchangeCode, checks C4/C5, mutants m81-m83).

**Why:** greg (2026-10-20): no manual steps for him, ever.
**How to apply:** any new Cloudflare service gets the same deploy-on-merge workflow, not a paste step.

Health check: symphony-app signin-health.yml (#74) runs after every deploy, every 6 h and by hand. It asks the live Worker what the page asks, then lists the Worker's calls of the last hours from Cloudflare analytics and Workers Logs: time, route, status and Origin. When a browser says "could not be reached", run this first to see whether the call reached the Worker. On 2026-10-21 at 01:28 UTC every call was answered.
