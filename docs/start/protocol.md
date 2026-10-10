# Change the protocol once, everywhere

The claim protocol's rules (the labels, the claim, the board, the protocol check, team mode's clerk, the push guard, the merge gate) live in one place, [OpenSpineConsortium/sdlc-protocol](https://github.com/OpenSpineConsortium/sdlc-protocol), and four repositories run a copy of it: this template under tools/sdlc_protocol, coordbench, the plugin marketplace and the GitHub App. A change is made there and nowhere else; one merge to its main carries it to every copy as a pull request that each repository's own check decides. A hand edit of a copy fails that repository's check, since the copy is held to the sha256 of every file in its VENDORED record and, on CI, to the library's own files. [ECOSYSTEM.md](https://github.com/OpenSpineConsortium/sdlc-protocol/blob/main/ECOSYSTEM.md) says which repository takes which modules.

## Steps

1. **Branch in sdlc-protocol.**

   ```bash
   gh repo clone OpenSpineConsortium/sdlc-protocol
   cd sdlc-protocol
   git switch -c my-change
   ```

2. **Change the module and its tests, and run the checks.** One test module per module, `tests/test_<module>.py`. A rendered string (the board, the guard's refusals, the gate's answers, the VENDORED record) is part of the interface: change one only on purpose, and say so in the pull request. When a module's imports or ecosystem.json change, rewrite the map. A new release raises `__version__` in sdlc_protocol/__init__.py and `version` in pyproject.toml together, which the tests hold equal. Then run the module's own tests (here the board's), the map and the whole check:

   ```bash
   python3.12 -m unittest tests.test_board -v
   python3 scripts/architecture.py
   bash scripts/check.sh
   ```

   You should see the suite pass and check.sh end without a problem; it holds every file to ASCII with LF endings and ECOSYSTEM.md to what architecture.py writes.

3. **Open the pull request.**

   ```bash
   git push -u origin my-change
   gh pr create --fill
   ```

   You should see the check `check` and one job per consumer, `downstream (sdlc-template)`, `downstream (coordbench)`, `downstream (sdlc-marketplace)` and `downstream (sdlc-app)`: each vendors your change into that repository's main and runs its own check there, so a change that would break a consumer is red before it merges.

4. **When a downstream job is red on purpose,** because a consumer pins the old output in a test or calls a function that changed, that consumer goes first: in a clone of it, vendor your branch and answer the change in a pull request of its own, merge that, then re-run this pull request's downstream jobs. From the consumer's clone, with your branch checked out in ../sdlc-protocol:

   ```bash
   git switch -c answer-my-change
   python3 ../sdlc-protocol/scripts/vendor.py . --consumer OpenSpineConsortium/CONSUMER
   ```

   CONSUMER is that repository's name, as the job names it. Then change the test or the code that pinned the old behaviour, run that repository's own `bash scripts/check.sh`, and open its pull request.

   The sync cannot carry such a change for you: it rebuilds its branch from the consumer's main on every run. sdlc-protocol's README, "A change a consumer must answer", has the order.

5. **Merge with a merge commit, not a squash,** so the commit each consumer's record names stays the last one that changed the package, and the sync finds the consumer you answered in step 4 already up to date.

6. **Watch the sync.** The push to main starts the workflow Sync at https://github.com/OpenSpineConsortium/sdlc-protocol/actions/workflows/sync.yml (also weekly, and by hand with Run workflow, or `gh workflow run sync.yml --repo OpenSpineConsortium/sdlc-protocol`). You should see one row per consumer in the run's summary: up to date, or the pull request `sdlc-protocol/sync` it opened or updated there, as the App OpenSpine SDLC, and whether auto-merge is armed. On the template, coordbench and the marketplace it lands by itself once that repository's required check is green (the one-time setup below, step 4), and on the marketplace the same commit raises the plugin's version, so the merge is also the plugin's release. The sync does not arm auto-merge for sdlc-app, which ecosystem.json gives `"auto_merge": false` and whose settings leave auto-merge off, so its owner merges that pull request.

7. **Tag the release, and bring it into repositories made from the template.** After the merge, with the version from step 2: `git tag vX.Y.Z MERGE_COMMIT && git push origin vX.Y.Z`. A repository made from the template is not on the sync's list, so its owner brings each release in by hand, from its own clone with sdlc-protocol beside it, and lands it by pull request:

   ```bash
   git switch main && git pull
   git switch -c sdlc-protocol-vX.Y.Z
   git -C ../sdlc-protocol fetch --tags && git -C ../sdlc-protocol checkout vX.Y.Z
   python3 ../sdlc-protocol/scripts/vendor.py . --consumer OpenSpineConsortium/sdlc-template
   bash scripts/check.sh
   git add tools
   git commit -m "Vendor sdlc-protocol vX.Y.Z"
   git push -u origin HEAD
   gh pr create --fill
   ```

   You should see a line beginning `vendor: replaced the copy and its record`, `checks ok` after the check, and the new pull request's address at the end; merge it once its check is green.

## The sync's one-time setup, by the owner

Until the variable SDLC_APP_ID is set on sdlc-protocol, the sync skips itself, stays green and says in its summary what is missing. Once, in this order:

1. Install the App OpenSpine SDLC on all five repositories, at https://github.com/organizations/OpenSpineConsortium/settings/installations (Configure, then All repositories or the five chosen).
2. Give sdlc-protocol the App's id and key, from a clone of OpenSpineConsortium/sdlc-app, whose .sdlc-app.env scripts/register.py wrote, so the key goes through a pipe and never onto the screen:

   ```bash
   gh variable set SDLC_APP_ID --repo OpenSpineConsortium/sdlc-protocol --body 5258276
   python3 scripts/register.py --print-key | gh secret set SDLC_APP_PRIVATE_KEY --repo OpenSpineConsortium/sdlc-protocol
   ```

3. Allow auto-merge on the consumers the sync arms it for:

   ```bash
   gh api -X PATCH repos/OpenSpineConsortium/sdlc-template -F allow_auto_merge=true
   gh api -X PATCH repos/OpenSpineConsortium/coordbench -F allow_auto_merge=true
   gh api -X PATCH repos/OpenSpineConsortium/sdlc-marketplace -F allow_auto_merge=true
   ```

4. Require the check `check` on each consumer's main with a ruleset (Settings, Rules, Rulesets, New ruleset, Import a ruleset, docs/setup/ruleset-main.json), so auto-merge has something to wait for; on sdlc-protocol require `check` and, if you like, the downstream jobs.
