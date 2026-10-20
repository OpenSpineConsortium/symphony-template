# Publishing part of a repository

GitHub sets visibility for a whole repository, never for a file or a folder, so a project that is part open and part proprietary keeps everything in its private repository and publishes the open part into a public one. This repository does that with one manifest, [.github/symphony/public.json](../../.github/symphony/public.json), which is the whole record of what leaves: a file it does not list never reaches a public repository, and `bash scripts/check.sh` fails while it lists a file that is not there or one under its `private` globs.

## What runs

- **Export.** [export.yml](../../.github/workflows/export.yml) runs on every push to the default branch. For each export it stages exactly the listed files, plus whatever the export's `build` writes, then opens or updates one pull request in the public repository from the branch `symphony/export/<name>`, made with the SymphonyBoard App's token for that repository alone. The public repository's own checks and merge rules decide it.
- **Import.** [import.yml](../../.github/workflows/import.yml) runs weekly and by hand. For an export marked `"import": true`, it copies the public repository's versions of the listed files back and opens a pull request here from `symphony/import/<name>`, so what a crowd improves there comes home through this repository's own checks. Generated output and every unlisted path never come back, so a contributor in the public repository can never touch a proprietary file.
- **Copies.** Each export names its `source`, the one repository it runs in, so a repository made from this template, which carries the manifest too, exports nothing until its owner writes exports of its own.

[tools/public_export.py](../../tools/public_export.py) holds the rules, and its docstring shows a manifest's fields.

## The exports today

| Export | From | To | Why |
| --- | --- | --- | --- |
| notebooks | the lessons, through `python3 tools/living_docs.py publish` | [OpenSpineConsortium/symphony-protocol](https://github.com/OpenSpineConsortium/symphony-protocol), `notebooks/*.ipynb` | Colab opens a public notebook for anyone with no GitHub sign-in, and this repository is internal |

## Other ways, and why not

- Git submodules put a private repository inside a public one, but a contributor without access hits a clone error, and the private part's history is still a separate repository to keep in step.
- Internal visibility opens a repository to an enterprise's members only, never to the public.
- CODEOWNERS and rulesets decide who must review and who may push, not who may read.
- Google's Copybara and Meta's ShipIt do what export and import do here, with a server or a tool of their own; this repository adds no dependency (.claude/rules/writing.md), so the same idea is a manifest, a script and two workflows.
