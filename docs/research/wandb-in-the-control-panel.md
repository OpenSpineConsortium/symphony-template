# Weights and Biases in the control panel

Source: the thread "W&B tab in the control panel", 2026-10-21, after the owner's ask "can you add wandb tracking/viewing as a tab under control panel? essentially integrate the wandb account i made into the style of the control panel". The code is the site's W&B tab (OpenSpineConsortium/openspineconsortium.github.io, assets/js/symphony-panel.js) and the sign-in service's route /wandb/graphql (OpenSpineConsortium/symphony-app, signin/worker.js, with its checks in signin/panel-checks/e2e2/wandb.test.mjs).

## Native first: what W&B offers

- Embedding: W&B lets a report be embedded in another page as an iframe, and only a public report; the runs of a private project cannot be shown that way, and an iframe would bring wandb.ai's own look, which the ask ruled out.
- The API: W&B's GraphQL endpoint, https://api.wandb.ai/graphql, is what W&B's own Python client reads (wandb/apis/public in github.com/wandb/wandb: the viewer and its teams, `models(entityName:)` for projects, `project.runs(first:, order: "-created_at")` with state, heartbeatAt, historyLineCount and summaryMetrics, `run.historyKeys`, and `run.sampledHistory(specs:)`, one list per spec of `{"keys": ["_step", key], "samples": n}`). The client sends the API key as HTTP Basic with the user `api`.
- Cross-origin reads: nothing W&B publishes says the endpoint answers a browser on another origin. It could not be measured from here: the cloud session's proxy and the owner's device shell both refuse wandb.ai, and Claude in Chrome was not connected. So the page does not count on it.

## What was built, and why

- The page reads W&B through the sign-in service, which already exists and deploys on merge: POST /wandb/graphql takes the key, a query and its variables, passes them to W&B as W&B's client does, and keeps nothing. It answers the site's origin alone, refuses any query that names a mutation or a subscription anywhere (so a fault of the page cannot change or delete a run through it), and caps a body at 16 KB and an answer at 4 MB, read as it streams. A 401 is said as W&B refusing the key; a 403 is passed on as W&B's word, since it may be a project the key may not read or a guard in front of W&B, and the page keeps the key.
- The key lives on the person's browser, under their GitHub login, as the Folders tab keeps a drive's connection (localStorage symphony_panel_wandb), until Forget W&B or Forget the token. It is pasted once from https://wandb.ai/authorize; nothing else could fetch it without the person, since the grid's copy in ~/.netrc must never be copied about, and a secret on the service would show one person's runs to everyone signed in. The key can do on W&B whatever its owner can; the page only reads with it.
- The tab lists the account's and its teams' projects, SchwingNet first where it is there (SchwingNet's tools/wandb_log.py logs there, the entity being the key's default), the newest thirty runs with state, last heard and last numbers, and for the run pressed a chart of each of up to four numeric metrics, loss first, chosen by chips, drawn in the panel's own teal with a crosshair readout. A running run is read again every fifteen seconds while the tab is shown, others every minute, and nothing while another tab is shown. wandb.ai is a link away for media, tables, artifacts and reports.

## What is not yet measured

- Whether api.wandb.ai answers a browser on openspineconsortium.com directly. If it does, the hop through the service could go; it costs one Worker request per read, well inside the free plan at one read a quarter minute.
- The live answer of W&B to the service's requests: the checks mock W&B as its Python client describes it, and the first real reading is the owner's first Connect.
