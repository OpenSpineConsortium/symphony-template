# The same CI for every contributor

Source: the project thread "Same CI for every contributor", 2026-10-22, opened by the owner's question of 04:23 UTC: "please make sure you require all contributors to openspineconsortium projects to follow the stringest CI i am using, is that a product of the repo or my claude instructions or both?" Every ruleset below was read through GitHub's API (GET repos/OpenSpineConsortium/<repository>/rulesets and each ruleset by id) between 04:25 and 04:40 UTC that day; the organization's own endpoints answer a session 403, so the organization's ruleset was read through the repositories it applies to.

## The answer: both

What the owner's sessions do comes from two places. GitHub enforces the repository's part on everyone who opens a pull request, person or session, and only the organization's owners can step past it. The Project's instructions, the "Rules" the owner wrote for the owner's own Claude sessions, bind those sessions alone: a person such as a collaborator, or a Claude session on their own account and Project, never reads them.

Enforced by the repositories (everyone):

- The default branch takes changes only by pull request, with no forced push and no deletion (each repository's ruleset "Protect the default branch").
- The required check "check", taken from GitHub Actions (integration 15368) where the ruleset pins it: bash scripts/check.sh with the template's tests, the claim protocol check for a claude/<issue> pull request, spine-datasets' dataset review (tools/dataset_review.py, inside its check), SchwingNet's gate and standards beside it.
- The organization ruleset "Require owner approval to merge" (id 25608346, made 2026-10-22 02:02 UTC, on every repository's default branch): one approval given after the last push, stale approvals dismissed, organization owners bypassing always. It binds a collaborator and not the owner or the sessions acting under the owner's login.
- GitHub's rule that a branch be up to date is off everywhere on the owner's order of 2026-10-20 (the overlap check at advise takes its place, docs/memory/the-overlap-check.md), so it is no part of "the strictest CI" and was not brought back.

Only in the owner's Claude instructions before this change (the owner's sessions alone):

- An adversarial review before each substantive pull request.
- One pull request per change, from the thread's own branch (the claim protocol holds a claude/<issue> branch to one issue, but nothing held a pull request to one change).
- Commit what a session finds under docs/research/ with its README line before it stops (.claude/rules/research.md says the same for sessions here, and nothing checks it).
- Run bash scripts/check.sh before a pull request; this one is enforced anyway, since CI runs the same script as the required check.

The Claude-side hooks (the push guard, the board at session start) run only in a Claude Code session with this repository's .claude/ settings; GitHub's rulesets stand behind the push guard for the default branch, and the claim protocol check stands behind it for claim branches.

## Repository by repository

| Repository | Own ruleset on the default branch | Required checks | Organization approval rule |
| --- | --- | --- | --- |
| symphony-template | Protect the default branch | check (pinned to Actions) | yes |
| SchwingNet | Protect the default branch | check (pinned), gate, standards (every group green) | yes |
| spine-datasets | Protect the default branch | check | yes |
| symphony-protocol | Protect the default branch, Repository-admin bypass | check | yes |
| coordbench | Protect the default branch | check | yes |
| symphony-start | Protect the default branch | check | yes |
| beethoven-qa | main: checks before merge, organization-admin bypass, no pull request rule of its own | gate, plugin, standards | yes |
| spine-program | Protect the default branch | none | yes |
| openspineconsortium.github.io (the site) | none | none | yes |
| hpcworker | none | none | yes |

The organization's other repositories (the Beethoven ones, flowbench, symphony-app, symphony-marketplace, symphony-extension and the older research repositories) were not read in this thread; the organization's approval rule reaches them all, since it targets every repository.

## Gaps

1. The adversarial review was instruction-only. Closed here: tools/review_record.py runs in the required job check (ci.yml) and fails a pull request marked ready whose body has no section "## Adversarial review" of at least a sentence, or still has the template's placeholder; drafts, bots' pull requests and those opened before 2026-10-22 05:00 UTC pass, so the work already in review is not stopped. A copy of the template takes it with its next sync of ci.yml and tools/, or by the same change by hand.
2. Three repositories require no check at all (spine-program, the site, hpcworker): a pull request there merges on the approval rule alone. The site has no CI to require (docs/memory says its build is checked by hand); spine-program and hpcworker have none either. Requiring a check there first needs a check to exist.
3. The organization's approval rule was checked for whether it holds the auto-merge the workflows arm, and it does not so far: SchwingNet #88, whose auto-merge github-actions[bot] armed, merged at 04:07 UTC under the owner's name, as did the owner's own armed pull requests in symphony-template (#360, #362, #363). A pull request a collaborator opens waits for one approval from someone else with write access, which in practice is the owner, since a Claude session may not approve.
4. One change per pull request and the research commit cannot be read off a diff reliably; CONTRIBUTING.md states them for everyone, and the review record is where a reviewer says when a pull request carries two changes.

## Why not one organization ruleset with a required workflow

GitHub's native way to put one check on every repository is an organization ruleset with the rule "Require workflows to pass before merging", naming a workflow in a public repository (available-rules-for-rulesets.md, "Using a workflow file": a public workflow can run in any repository of the organization). It was set aside for now, from GitHub's own documentation (troubleshooting-rules.md, "Troubleshooting ruleset workflows"): a ruleset workflow does not run on events triggered by GITHUB_TOKEN, so every pull request a workflow opens with it (protocol.yml's sync, add-worker.yml, the promoter's record pull requests where they use it) would wait for a check that never comes; it blocks direct pushes, which template-init's first commit and the board's and metrics' branch writes make on their own branches, so it must never target more than default branches; it can block creating a repository from the template unless it is in Evaluate mode or someone with bypass makes it; and it runs only on opened, synchronize and reopened, so editing a body would not re-run it. A session cannot write an organization ruleset (403 on the organization's endpoints, and every ruleset write refused), SymphonyBoard holds no organization Administration, and giving a public App that permission would ask every installation of it for it, so it would be the owner's own import under the organization's Settings, Rules. The required check "check" already reaches every repository a collaborator works in; the review record rides in it.
