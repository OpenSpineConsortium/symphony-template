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

Kaggle's own page says to use ~/.kaggle/access_token. SchwingNet's fetches do not read that file. They read KAGGLE_API_TOKEN from ~/.fluorocap/credentials.env (load_token in grid/platform-fetch.sbatch, and kaggle_token in tools/fetch_sources.py). An earlier reply in this thread named the wrong file.

## The route

1. A key is a secret of the environment grid, under the name docs/setup/grid.md's "Service keys" table gives.
2. The action key of .github/workflows/grid-accounts.yml (admin only) hands its step only the secret the input name picks, masks it, and sends it over ssh's standard input.
3. hpcworker's gate word `key NAME` (hpcworker #36) reads one line with a time limit and checks it against the key's shape. It then writes the line into the fixed file, 0600 in a 0700 folder, keeping every other line. It refuses links and files that belong to another account.

The key never appears in a word, a log, the gate's answer or the branch grid.
