# Dependabot and unowned pull requests across the organization

Source: the thread "Unowned PR sweep" of the claude.ai Project "symphony_2", 2026-10-22, which merged the pull requests the handoff listed with no owner and every open Dependabot pull request in the organization's repositories.

## What was merged and how it was checked

- symphony-template #318, symphony-protocol-canary #5 (the copy taking symphony-protocol 0.5.1, a release already published, so no release and no approval gate was touched) and #6 (create-github-app-token 1 to 3, the version the template's own template-init already uses), spine-datasets #5 and #6, and test #2 and #3 merged on their green checks.
- symphony-app #82 had no check run because its branch conflicted with main in signin/panel-checks/README.md (GitHub runs no pull_request workflow on a conflicted pull request); main was merged in keeping both the Runs tab's line and the Grid tab's newer one, and its check passed.
- spine-program #216, the sync's offer of the board's files, has no check workflow in that repository; its copy was verified against tools/VENDORED (0.6.1, 19 files match), every workflow parsed as YAML and its Board run was green.
- beethoven-vscode has no CI at all; #16, #18 and #19 (npm patch and minor bumps) each passed `npm ci`, the typecheck and the 120 unit tests in a clone, and main passed the same after all three merged.

## What keeps a Dependabot pull request red in SchwingNet

SchwingNet carries beethoven-qa, whose supply-chain standard fails any new or changed `uses:` line that is not pinned to a full commit, while Dependabot writes the bumped tag (`actions/checkout@v7`). Every Dependabot pull request there therefore fails "standards (every group green)" until someone pins the line to the tag's commit with the tag as a comment, as the rest of its workflows are. A repository that carries beethoven-qa gets the same failure on every future bump; Dependabot keeps a pin if the line is already pinned, so pinning the remaining tag references once ends it.

## The template behind its copies

The copies had taken actions/checkout v7 in grid.yml and grid-accounts.yml and actions/download-artifact v8 in pool.yml and workers.yml while the template still held v4 and v7; the template was brought to the same versions in this thread's pull request. Both bumps are compatible with how these workflows use them: the grid's runner already runs setup-python v7 on the same Node, and download-artifact v8 still unzips the zipped artifacts upload-artifact v7 writes, failing only on a digest mismatch.
