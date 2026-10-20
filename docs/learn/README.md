# Learn by doing

Four short lessons teach Symphony by running it. Each takes about ten minutes, needs no Claude account, no key and no GitHub sign-in, and works at a terminal or in Google Colab. They are written for students and new users who have never used git's branches or GitHub's pull requests in a team: every step says what to type, what you should see, and why it matters.

They live in the public library, [symphony-protocol's lessons/](https://github.com/OpenSpineConsortium/symphony-protocol/tree/main/lessons), with their Colab notebooks beside them in its notebooks/, so there is one copy, anyone can open it, and Colab needs no sign-in. That repository's required check runs every command the lessons show and compares its output with the page, and makes the notebooks from the lessons, so what you read is what the code does.

| Lesson | You learn | Features it uses | Colab |
| --- | --- | --- | --- |
| [1. Claim your first task](https://github.com/OpenSpineConsortium/symphony-protocol/blob/main/lessons/01-first-claim.md) | how two people can never take the same task | claim branches, claim files | [Open](https://colab.research.google.com/github/OpenSpineConsortium/symphony-protocol/blob/main/notebooks/01-first-claim.ipynb) |
| [2. When Symphony says no](https://github.com/OpenSpineConsortium/symphony-protocol/blob/main/lessons/02-push-guard.md) | which pushes are refused, and what to do instead | the push guard | [Open](https://colab.research.google.com/github/OpenSpineConsortium/symphony-protocol/blob/main/notebooks/02-push-guard.ipynb) |
| [3. Read the board](https://github.com/OpenSpineConsortium/symphony-protocol/blob/main/lessons/03-read-the-board.md) | where to find your next task, and what comes first | the board: Queue, Given to workers, Blockers | [Open](https://colab.research.google.com/github/OpenSpineConsortium/symphony-protocol/blob/main/notebooks/03-read-the-board.ipynb) |
| [4. Two students, one file](https://github.com/OpenSpineConsortium/symphony-protocol/blob/main/lessons/04-overlaps.md) | how work that touches the same file lands in order | Overlaps | [Open](https://colab.research.google.com/github/OpenSpineConsortium/symphony-protocol/blob/main/notebooks/04-overlaps.ipynb) |

To run one at a terminal, clone symphony-protocol and follow the lesson from the top of that clone. In Colab, open it from the table and choose Runtime, then Run all. The demo Codespace ([capabilities.md](../start/capabilities.md), Try it in a minute) has git and Python installed if you would rather not install them.

A lesson is changed in symphony-protocol, by a pull request there, never here.

## Living documents

This site is a living document in two ways, both enforced by the required check, `bash scripts/check.sh`, so a pull request that breaks one cannot merge:

- **The reference follows the code.** The site's Reference page is made from each module's docstring and each script's opening comment, as Javadoc is made from comments, and `python3 tools/living_docs.py check` fails a module or script that has none.
- **The tests accumulate.** Every test any pull request has added stays in [tests/](../../tests/) and runs on every pull request and push ([ci.yml](../../.github/workflows/ci.yml)). Run them again at any time with `python3 -m unittest discover -s tests`, or from the CI workflow's Run workflow button on GitHub. The site's Tests page lists each test file and its results from the run that built it.

## Publishing the site

[docs.yml](../../.github/workflows/docs.yml) builds the site on every push to the default branch with `python3 tools/living_docs.py site`, and publishes it with GitHub Pages where Pages deploys from GitHub Actions and the repository variable `SYMPHONY_DOCS` is `pages`, so a site the owner publishes some other way is never overwritten. Pages needs admin rights to turn on, which the workflow's own token lacks, so `bash scripts/setup-repo.sh` makes both settings with the rest of a new repository's, and on an internal or private repository limits the site to the repository's readers, or makes none where GitHub cannot limit it. By hand: the repository's Settings, Pages, Build and deployment, Source: GitHub Actions; then Settings, Secrets and variables, Actions, Variables, New repository variable `SYMPHONY_DOCS` with the value `pages`. A repository whose plan offers no Pages keeps the built site as the run's artifact.

The next push to the default branch publishes it, or run the Docs workflow from the Actions tab (Run workflow). On an internal or private repository, Pages is visible only to people who can read the repository (inferred from GitHub's rules for Pages on such repositories). To preview the site locally: `python3 tools/living_docs.py site _site`, then open `_site/index.html`.
