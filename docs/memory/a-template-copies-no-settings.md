"Use this template" copies files only; the SymphonyBoard App applies the GitHub side on its own through .github/workflows/settings.yml, with Symphony Setup and scripts/setup-repo.sh only the fallbacks where the App cannot hold the permissions.

A copy of the template arrives with no ruleset, no toggle, no label, no
secret and no variable, and GITHUB_TOKEN can set none of them. The owner
decided on 2026-10-20 that no person sets them by hand again ("I NEVER WANT
TO NEED TO MANUALLY ... SET REPO SETTINGS AGAIN", and "WHY WOULD I RATHER
JUST NOT USE THE FUCKING GITHUB APP I DEVELOPED FOR THIS SPECIIC PURPOSE!
... MAKE SURE THE SETUPAPP IS ALWAYS SECONDARY"): so the SymphonyBoard App,
installed on the organization's repositories, is the primary path, and its
Administration is used for the settings as well as the Share tab. Its
token, minted from the variable SDLC_APP_ID and the secret
SDLC_APP_PRIVATE_KEY that template-init already uses, runs
scripts/setup-repo.sh in .github/workflows/settings.yml on the push
template-init makes, on a change to the ruleset's file and by hand, and weekly and when the repository is made public only for the environment and the Pages site a plan or a private repository held back, so it never undoes what the owner turned off: the
ruleset of docs/setup/ruleset-main.json with any checks the copy adds,
the pin of "check" to GitHub Actions, delete-branch-on-merge and
auto-merge, the topic symphony, secret scanning and push protection,
"Allow GitHub Actions to create and approve pull requests", the
environment token-store, Pages with SYMPHONY_DOCS, and the labels. A
permission the installation has not accepted (Pages) is a refusal in the
run's summary, never a failed run. The ruleset is made once and left as
it is after. Symphony Setup, the front door's second App, is the fallback
for an adoption where SymphonyBoard cannot hold the permissions;
setup-repo.sh from a clone the last resort; a crowd repository takes
`python3 scripts/crowd.py setup` instead, and setup-repo.sh refuses to run
there. The Claude token still comes from the owner's own `claude
setup-token` or `/install-github-app`. An organization on Team or above
can also preship organization rulesets (docs/setup/ruleset-org.json);
docs/setup/owner-checklist.md has the plan each needs.
