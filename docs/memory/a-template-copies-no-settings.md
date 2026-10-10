"Use this template" copies files only; the owner sets the GitHub side with scripts/setup-repo.sh, and an organization on Team or above can preship the rules and the secrets.

A copy of the template arrives with no ruleset, no toggle, no label, no
secret and no variable, and only a person with admin rights can set them.
tools/template_init.py makes the labels and opens the setup issue on the
first push; the rest is one run of `bash scripts/setup-repo.sh` from a clone
with gh signed in, which a cloud session cannot do (no gh, no admin rights).
The token comes only from the owner's own `claude setup-token`, pasted at
gh's hidden prompt, or from `/install-github-app`. An organization can set
some of it once for every repository it makes: organization rulesets (GitHub
Team or Enterprise; import docs/setup/ruleset-org.json) and organization
Actions secrets and variables (any plan, but a Free organization's private
repositories cannot read them; gh needs `--visibility all`). Settings as code
needs an app, a new dependency, so it is an issue first. The steps and the
plan each needs: docs/setup/owner-checklist.md.
