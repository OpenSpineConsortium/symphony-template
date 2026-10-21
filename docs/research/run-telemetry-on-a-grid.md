# Run telemetry on a grid, and what a private repository's docs site shows

Source: the thread "SchwingNet witness frames and W&B", 2026-10-21, building the evaluation step of a confidential training project in a repository adopted from this template (its own pull request carries the code; nothing of that project's method is written here).

## Weights and Biases from Slurm compute nodes

- What was asked: runs visible on the W&B website as soon as training starts, with the key the grid already holds, and never a key in a repository.
- What holds: W&B reads its key from WANDB_API_KEY, from ~/.netrc's api.wandb.ai entry that `wandb login` writes, or from whatever file the caller loads into the environment; a step can name where the key is by name only (env, file, netrc, none) and never read its value, except to hand a mode-600 token file's one line to its own process.
- A compute node may have no route out. `wandb.init(mode="online")` then waits; with `settings=wandb.Settings(init_timeout=60)` it raises a CommError after a minute (measured in a cloud container whose proxy refuses api.wandb.ai). The failed start keeps the run id in W&B's local service, so a second `init` with the same id fails with "run ID ... is in use" until `wandb.teardown()` frees it; the offline fallback takes an id of its own, since the failed online start may have registered the first one.
- Offline runs land under `<dir>/wandb/offline-run-*`; `wandb sync` pushes them from any machine with a route out (a Slurm login node), and leaves a `.synced` file in each, so a step-by-step push never uploads one twice.
- The push needs only the wandb package: a small pixi environment with wandb alone runs it on a login node, where an environment pinned to a CUDA build may refuse to install for the missing `__cuda` virtual package and costs gigabytes.
- Nothing W&B does should stop a long run: every call wrapped, logging stopped for the step on a failure, and the reason said on the flow's last line and in the run's ledger. Error text from W&B goes into committed files only after its first line is kept, whitespace collapsed, table bars replaced and anything key-shaped (32 or more letters, digits, dashes and underscores) redacted.

## A private repository's docs site may not be private

- The template's living docs (docs.yml, tools/living_docs.py) publish a Reference page made from every tool's docstring, besides the lessons, once Pages deploys from Actions and SYMPHONY_DOCS is pages.
- GitHub keeps a Pages site to the repository's readers only with access control, an Enterprise Cloud feature; on other plans a private repository's site is public (docs/research/github-plans-and-visibility.md has the plans). The owner plans to leave Enterprise.
- So in a copy whose tools describe confidential work, turning the site on publishes those docstrings. That project's evaluation page is therefore written into the repository and read on GitHub, never put on the site; a copy that holds confidential method should leave SYMPHONY_DOCS unset, or the site's Reference page should leave the copy's own tools out, until access control is confirmed on its plan. Whether SchwingNet's Pages is on could not be read from the session (the proxy refuses the Pages API).
