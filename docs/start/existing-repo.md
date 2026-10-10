# The protocol in a repository you already have

A repository not made from the template takes the protocol in two halves. The sdlc plugin from [OpenSpineConsortium/sdlc-marketplace](https://github.com/OpenSpineConsortium/sdlc-marketplace) brings the Claude Code side to every local session: the skills `/sdlc:claim`, `/sdlc:remember` and `/sdlc:checkpoint`, the command `/sdlc:board`, a push guard before every Bash call, a document check after every edit, and the board at session start. The repository brings the files the plugin acts on, which a plugin cannot ship: the board's workflow, the protocol's text, the claim folder and the labels. ORG/NAME is your repository and NAME its clone; bash, on Windows in WSL.

## Steps

1. **Clone the two sources beside your repository, and branch.** sdlc-protocol is public; TEMPLATE_OWNER/TEMPLATE_NAME is the template for a member of its enterprise and the public copy for anyone else ([README.md](README.md)):

   ```bash
   cd ..
   git clone --branch v0.2.0 https://github.com/OpenSpineConsortium/sdlc-protocol.git
   gh repo clone TEMPLATE_OWNER/TEMPLATE_NAME sdlc-template
   cd NAME
   git switch -c sdlc-setup
   ```

2. **The library and the board's workflow.** vendor.py copies the protocol's package where the template keeps it, tools/sdlc_protocol, with its record tools/VENDORED; board.yml renders the board with GitHub's own token on every issue and pull request event, and tidy.yml deletes a closed issue's claim branch:

   ```bash
   python3 ../sdlc-protocol/scripts/vendor.py . --consumer OpenSpineConsortium/sdlc-template
   mkdir -p .github/workflows
   cp ../sdlc-template/.github/workflows/board.yml ../sdlc-template/.github/workflows/tidy.yml .github/workflows/
   cp ../sdlc-template/tools/board.py tools/
   python3 tools/sdlc_protocol/vendoring.py verify tools
   ```

   You should see `vendor: wrote tools/VENDORED: sdlc-protocol 0.2.0 f530a6694477466c5826a6626681c8c84c8f1aa9, 15 file hashes` and then `vendored sdlc-protocol 0.2.0 at f530a66: 15 files match VENDORED`. Later releases come the same way ([protocol.md](protocol.md), step 7); nothing reaches this repository by itself.

3. **The protocol's text and the claim folder.** spec/PROTOCOL.md is the protocol in prose with no placeholders, the claim file's shape included, and the skills read it at docs/agents/PROTOCOL.md:

   ```bash
   mkdir -p docs/agents/claims
   cp ../sdlc-protocol/spec/PROTOCOL.md docs/agents/PROTOCOL.md
   printf '%s\n' '# Claim files' '' 'One file per claimed issue, docs/agents/claims/N.md, in the shape docs/agents/PROTOCOL.md gives under Claim; the pull request that finishes the issue deletes it.' > docs/agents/claims/README.md
   ```

4. **Tell every session,** in CLAUDE.md, which Claude Code loads at the start of each one; the `@` line imports the protocol whole:

   ```bash
   cat >> CLAUDE.md <<'EOF'

   ## How work is claimed

   @docs/agents/PROTOCOL.md

   Before any work: fetch, read the board with `git fetch origin board && git show origin/board:STATE.md`, and check the claim on the issue you mean to take. One issue, one branch `claude/<issue>`, one pull request. Never push to the default branch or to another account's claim branch.
   EOF
   ```

5. **The plugin, for everyone who works here.** These write the marketplace and the plugin into the committed .claude/settings.json, beside whatever it holds; each collaborator runs the second line once after trusting the folder, since a project's setting names the plugin but does not download it:

   ```bash
   claude plugin marketplace add OpenSpineConsortium/sdlc-marketplace --scope project
   claude plugin install sdlc@sdlc-marketplace --scope project
   ```

   You should see sdlc in `claude plugin list`, and `/sdlc:board` in a new session. Auto-update is off for a marketplace that is not Anthropic's: turn it on under `/plugin`, Marketplaces, sdlc-marketplace, Enable auto-update, or take the project preset with `"autoUpdate": true` from the marketplace's README. Just for yourself instead, in a session: `/plugin marketplace add OpenSpineConsortium/sdlc-marketplace`, then `/plugin install sdlc@sdlc-marketplace`, which turns the push guard on in every repository you open.

6. **The labels the board reads:**

   ```bash
   gh label create todo --repo ORG/NAME --color 0e8a16 --description "In the queue, open for a claim"
   gh label create claimed --repo ORG/NAME --color fbca04 --description "A claude/<issue> branch holds it"
   gh label create in-review --repo ORG/NAME --color 1d76db --description "A pull request is open and waiting"
   gh label create blocker --repo ORG/NAME --color b60205 --description "Stops everyone until it is settled"
   gh label create account:main --repo ORG/NAME --color 5319e7 --description "Work for the main Claude account"
   ```

   You should see them at https://github.com/ORG/NAME/labels. epic and blocked belong to team mode, which needs the template's other workflows.

7. **Land it by pull request.** A push of files under .github/workflows/ needs gh's workflow scope; `gh auth refresh -s workflow` adds it if the push is refused:

   ```bash
   git add .claude/settings.json .github/workflows/board.yml .github/workflows/tidy.yml tools docs/agents CLAUDE.md
   git commit -m "Take up the claim protocol"
   git push -u origin sdlc-setup
   gh pr create --fill
   ```

   Once it is merged, the next issue event runs "Board" (https://github.com/ORG/NAME/actions/workflows/board.yml; `gh workflow run board.yml --repo ORG/NAME` starts one now), and you should see the board at https://github.com/ORG/NAME/blob/board/STATE.md.

8. **Protect the default branch, and only it,** at https://github.com/ORG/NAME/settings/rules: require a pull request and your own checks, and block force pushes and deletions. Never target the branch `board`, which board.yml force-pushes on every change. The template's docs/setup/ruleset-main.json requires a check named "check", which this repository has only if its CI has a job of that name.

9. **Claim the first issue.** Open one labelled todo, run `claude` in the clone and paste:

   ```
   Claim issue N with /sdlc:claim and carry it to a ready pull request, as docs/agents/PROTOCOL.md says. Where the skill names bash scripts/check.sh, run this repository's own checks instead. Do not merge.
   ```

## What stays different from a copy of the template

- Cloud sessions do not install the plugins a repository declares, so there the push guard and the board at session start are missing, and the ruleset of step 8 is the fence; a Project can add the plugin under Project settings, Plugins. A copy of the template wires the same hooks in its own .claude/settings.json, which cloud sessions do load.
- `/sdlc:remember` and `/sdlc:checkpoint` act on docs/memory/, tools/marked_section.py and the checkpoint markers in CLAUDE.md, which only the template carries; copy them from it if you want those two. Copy tools/check_docs.py too and the plugin runs it after every edit, holding CLAUDE.md, README.md, .claude/, docs/, tools/ and .github/ to ASCII with LF endings and CLAUDE.md to one pair of checkpoint markers.
- No @claude, Actions worker, team mode, coordinator trigger or protocol check in CI: those are the template's workflows and docs ([solo.md](solo.md), [team.md](team.md)). Keep one wiring of the hooks: a repository that has the template's hooks and enables the plugin runs each twice.
