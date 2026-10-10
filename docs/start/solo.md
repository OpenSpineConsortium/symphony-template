# One person, one account, a new project

You make a repository from the template, set its GitHub side in one command, claim the first issue and turn on @claude, all on your own Claude account. About fifteen minutes. ORG/NAME is your new repository; [README.md](README.md) says how to read the blocks.

## Once per machine

Claude Code, signed in to your own claude.ai account, and the GitHub CLI, signed in to your own GitHub login. Bash (macOS, Linux, WSL):

```bash
curl -fsSL https://claude.ai/install.sh | bash
claude
gh auth login
```

PowerShell (Windows):

```powershell
irm https://claude.ai/install.ps1 | iex
winget install --id GitHub.cli
claude
gh auth login
```

After the installs, open a new terminal so they are on its path; `claude` then opens a browser to sign in. You should see your account under "Login method" when you type `/status` in Claude Code, and "Logged in to github.com" from `gh auth status`.

## Steps

1. **Make the repository.** Open the link, name the repository and create it. Public, because on GitHub Free only a public repository gets enforced branch rules and unlimited Actions minutes ([tiers.md](../setup/tiers.md)); put an organization's name in place of `@me` to make it there.

   - A member of the template's enterprise: https://github.com/new?template_owner=OpenSpineConsortium&template_name=sdlc-template&owner=@me&visibility=public
   - Anyone else, from the public copy: https://github.com/new?template_owner=TEMPLATE_OWNER&template_name=TEMPLATE_NAME&owner=@me&visibility=public

   You should see the new repository with the template's files.

2. **Wait for "Set up this project".** The first push runs the workflow "Template init", which fills your names into the files, makes the seven labels and opens that issue; its checklist is the rest of this page. Open https://github.com/ORG/NAME/issues: you should see it within a few minutes, and a green "Template init" run at https://github.com/ORG/NAME/actions. If it never comes, do it by hand:

   ```bash
   gh repo clone ORG/NAME
   cd NAME
   GITHUB_TOKEN=$(gh auth token) python3 tools/template_init.py --repo ORG/NAME --default-branch main --create-labels --open-issue
   git add -A
   git commit -m "Initialise from the template"
   git push origin main
   ```

3. **The GitHub side, in one command, on your own computer.** A cloud session cannot run it: its GitHub proxy refuses gh's GraphQL commands, and the session has no admin rights. Leave out the first two lines if step 2 already made the clone. In a second terminal run `claude setup-token`, approve it in the browser, and paste the token it prints at the hidden prompt of the first; nothing you paste is shown or saved.

   ```bash
   gh repo clone ORG/NAME
   cd NAME
   bash scripts/setup-repo.sh --token
   ```

   It touches [Rules](https://github.com/ORG/NAME/settings/rules), [General](https://github.com/ORG/NAME/settings), [Advanced Security](https://github.com/ORG/NAME/settings/security_analysis), [Labels](https://github.com/ORG/NAME/labels) and [Actions secrets](https://github.com/ORG/NAME/settings/secrets/actions). You should see one line per step, among them `ruleset "Protect the default branch": created from docs/setup/ruleset-main.json`, `general: delete head branches on merge, allow auto-merge: on`, `secret CLAUDE_CODE_OAUTH_TOKEN: set` and `code owners: GitHub resolves every owner in .github/CODEOWNERS`. Run it again at any time; nothing is done twice.

   On Windows without WSL, store the token from PowerShell and do the rest by hand from the first box of "Set up this project"; gh asks for the value at a hidden prompt:

   ```powershell
   claude setup-token
   gh secret set CLAUDE_CODE_OAUTH_TOKEN --repo ORG/NAME
   ```

4. **Install the Claude GitHub App.** Cloud sessions push through it, and Projects and routines need it. Follow "install the app" in the second box of "Set up this project", which has your repository already chosen; or run `/install-github-app` in Claude Code in your clone, pick the repository, and choose "Skip for now" when it offers the GitHub Actions setup, since step 3 stored the token and .github/workflows/claude.yml is already here. You should see Claude at https://github.com/ORG/NAME/settings/installations. On an organization, an organization owner may need to approve the installation.

5. **Open the first task and claim it.** Open https://github.com/ORG/NAME/issues/new?template=task.yml with the title "Task: write the goal", the goal "docs/project.md's Goal, Scope and Model and effort are written" and the acceptance "bash scripts/check.sh passes and the owner agrees". You should see it labelled todo, and a minute later in the Queue of the board at https://github.com/ORG/NAME/blob/board/STATE.md. Then, in your clone:

   ```bash
   git pull
   claude
   ```

   and paste, with the issue's number for N:

   ```
   Claim issue N with the claim skill and carry it to a ready pull request, as docs/agents/PROTOCOL.md says; ask me for the goal, the scope and the model and effort, and write them into docs/project.md. Do not merge.
   ```

   You should see the branch `claude/N` on GitHub, the issue labelled claimed and account:main with the plan as a comment, a draft pull request saying "Closes #N", and at the end the pull request ready with the label in-review. Merge it yourself at https://github.com/ORG/NAME/pulls; the merge closes the issue. To do the same from a cloud session instead, use the prompt in [README.md](README.md), step 5.

6. **@claude in Actions, on your own token.** Write on any issue:

   ```
   @claude summarise what this repository is for, in three sentences.
   ```

   You should see a run of "Claude" at https://github.com/ORG/NAME/actions/workflows/claude.yml and its answer on the issue. Each run spends your own plan's usage (the five-hour window and the weekly limit), which is why the workflow caps its turns; only someone with write access starts it. Keep usage credits off unless you want overage billed at API rates.

7. **Keep it going, optional: one worker, not two.** Either the Actions worker, which every six hours starts Claude only when the queue has work:

   ```bash
   bash scripts/setup-repo.sh --var CLAUDE_WORKER=true
   gh workflow run claude-worker.yml --repo ORG/NAME
   ```

   (you should see a "Worker" run at https://github.com/ORG/NAME/actions/workflows/claude-worker.yml), or the worker routine on claude.ai, made as [docs/agents/routines/worker.md](../agents/routines/worker.md) says. Both on one account would race for the same queue under the same label.

8. **A thin Project, optional (Pro and Max).** At https://claude.ai/code/projects/browse make a Project that links ORG/NAME and nothing else, with its instructions, description and memory left blank, since every thread reads them from the repository ([claude-project.md](../setup/claude-project.md)). Then close "Set up this project" when every box is ticked.

Next: [parallel.md](parallel.md) runs several sessions at once on this repository; [prompts.md](prompts.md) has the everyday sentences.
