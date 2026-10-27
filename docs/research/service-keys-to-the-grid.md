# Service keys to the grid by GitHub secret

Source: the thread "Dataset finalization", 2026-10-23, in the project symphony_3. Read from SchwingNet's grid/README.md (item 3, the token files), grid/platform-fetch.sbatch, grid/run-platform-fetch.sh, tools/fetch_sources.py and tools/wandb_log.py at SchwingNet main 7708538, and from hpcworker's tools/grid_gate.sh at main 7987179.

The owner sent a new Kaggle key for the grid because the old account was gone, which is why RSPECT #88's fetch had failed. A cloud session cannot reach the grid's shell or the Actions secrets API. So he chose to keep each key as a secret of the environment grid, sent to the grid by a gate word ("all my keys should go that route").

## Where each key lives on the grid

SchwingNet's jobs read each key from a file only the owner can read, and refuse a file anyone else can read.

| Service | File | Line |
| --- | --- | --- |
| Kaggle | ~/.fluorocap/credentials.env | KAGGLE_API_TOKEN=... |
| PhysioNet | ~/.netrc | machine physionet.org login ... password ... |
| Hugging Face | ~/.hf/token.env | HF_TOKEN=... |
| Redivis | ~/.redivis/token.env | REDIVIS_API_TOKEN=... |
| Zenodo | ~/.zenodo/token.env | ZENODO_TOKEN=... |
| W&B | ~/.wandb/token.env | WANDB_API_KEY=... |
| RSNA RATIC | ~/.rsna/ratic_link | the presigned link alone |
| Elsevier | ~/.elsevier/token.env | ELSEVIER_API_KEY=... and ELSEVIER_INSTTOKEN=... |
| Semantic Scholar | ~/.fluorocap/credentials.env | S2_API_KEY=... |

Kaggle's own page says to use ~/.kaggle/access_token. SchwingNet's fetches do not read that file. They read KAGGLE_API_TOKEN from ~/.fluorocap/credentials.env (load_token in grid/platform-fetch.sbatch, and kaggle_token in tools/fetch_sources.py). An earlier reply in this thread named the wrong file.

## The route

1. A key is a secret of the environment grid, under the name docs/setup/grid.md's "Service keys" table gives.
2. The action key of .github/workflows/grid-accounts.yml (admin only) hands its step only the secret the input name picks, masks it, and sends it over ssh's standard input.
3. hpcworker's gate word `key NAME` (hpcworker #36) reads one line with a time limit and checks it against the key's shape. It then writes the line into the fixed file, 0600 in a 0700 folder, keeping every other line. It refuses links and files that belong to another account.

The key never appears in a word, a log, the gate's answer or the branch grid.

## Elsevier and Semantic Scholar (2026-10-27)

Source: the thread "Get full texts through Elsevier key" in the project symphony_4, 2026-10-27, for the owner's word of 23:00 UTC: add Elsevier to the key route, write a fetch that runs as a grid job, reads the key from a file only he can read and keeps the text on the grid, test both, and list the papers it cannot get.

- The owner saved ELSEVIER_API_KEY and ELSEVIER_INSTTOKEN on 2026-10-25 as organization Actions secrets, with repository access "Private and internal repositories" (his words in the thread "Flesh out Panjabi, rewrite in PyMC" at 22:46 UTC on 2026-10-27). A job of grid-accounts.yml reads an organization secret as it reads the environment's, so the action key reaches them without a copy in the environment grid. The recommended access is Selected repositories, SchwingNet and symphony-template.
- The action key's name elsevier sends the key, one space and the token, or the key alone where no token is saved; s2 sends S2_API_KEY, Semantic Scholar's key, which the thread of 22:55 UTC advised him to save the same way. No session can see whether a secret is saved, since the proxy refuses the secrets API; a send whose secret is missing stops before the gate with "the secret for NAME is not set".
- hpcworker's gate word key elsevier writes both lines of ~/.elsevier/token.env, every other line kept, and replaces both on each send, so a token no longer sent does not stay behind; key s2 writes S2_API_KEY into ~/.fluorocap/credentials.env beside the Kaggle lines, the store spine-program's literature tools (spine_data_review's sdr/creds.py) already read on the owner's machine.
- Elsevier's terms for the token, from its 2026-10-16 e-mail (spine-program 13_aidas_program/memory/elsevier-grant-and-terms.md): server side in a password-protected environment, never in browser code or an address bar, HTTPS only, the key in the header X-ELS-APIKey and the token in X-ELS-Insttoken. The file is mode 600 in a 700 folder of the owner's grid home, and SchwingNet's fetch sends the values in those headers alone.
- What the fetch got and what it could not is SchwingNet's docs/research/literature-on-the-grid.md, kept there since its findings belong to SchwingNet's private work.

