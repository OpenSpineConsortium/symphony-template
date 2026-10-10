# Several people, each on their own account

Each person brings their own Claude plan and their own GitHub login, and the repository coordinates them: a label per account on the board, a row per account in docs/agents/OWNERSHIP.md, one worker routine per account, and the main account's coordinator to release idle claims and flag collisions. Nobody's credential reaches anyone else. The last section is a different thing with a similar name: team mode, several agents in Actions on the main account. ORG/NAME is the repository; [README.md](README.md) says how to read the blocks.

## Steps

1. **Give each person Write.** A claim is a branch pushed to this repository, not to a fork, and a fork's pull request gets no secrets. At https://github.com/ORG/NAME/settings/access (Collaborators & teams), or:

   ```bash
   gh api --method PUT repos/ORG/NAME/collaborators/LOGIN -f permission=push
   ```

   You should see LOGIN listed with Write once they accept the invitation.

2. **A label per account,** so the board and the issues say whose claim is whose; the name after `account:` is the claim file's Account line.

   ```bash
   gh label create account:alice --repo ORG/NAME --color 5319e7 --description "Work for alice's Claude account"
   ```

   You should see it at https://github.com/ORG/NAME/labels beside account:main.

3. **A row in OWNERSHIP.md, by pull request.** Open a Task issue at https://github.com/ORG/NAME/issues/new?template=task.yml asking for it, and in a session paste:

   ```
   Claim issue N with the claim skill: add a row to docs/agents/OWNERSHIP.md for the account alice, label account:alice, owning the paths I name next, and say so in docs/project.md under Owners. Do not merge.
   ```

   You should see the row on main once you merge it; a pull request touching another account's area then asks that account for a look.

4. **Each person, once, on their own account.** Claude Pro or Max, or a Team or Enterprise seat with Claude Code; `claude` signed in as themselves; Sign in with GitHub at https://claude.ai/code; a cloud environment of their own ([parallel.md](parallel.md), step 1); a thin Project of their own on ORG/NAME, Pro and Max only ([claude-project.md](../setup/claude-project.md)); and, if they want work taken without starting sessions by hand, a worker routine made from [docs/agents/routines/worker.md](../agents/routines/worker.md) with `account:main` changed to their own label. In any session they start by hand, one sentence tells it whose claim it makes:

   ```
   My account label is account:alice and the claim file's Account line is alice.
   ```

5. **The coordinator, on the main account, once a second account joins.** It splits requests into issues, releases a claim idle for 24 hours, flags two pull requests that touch the same files and tidies the memory; it comments and opens pull requests, and never merges. In the main account's Project, paste the prompt from [docs/agents/routines/coordinator.md](../agents/routines/coordinator.md) and add "run this every hour". On the Project's Routines tab, open it and add the pull request events for ORG/NAME and the API trigger, press Generate token (it is shown once), and store the trigger's address and token, each at gh's hidden prompt:

   ```bash
   gh secret set COORDINATOR_TRIGGER_URL --repo ORG/NAME
   gh secret set COORDINATOR_TRIGGER_TOKEN --repo ORG/NAME
   ```

   The same two lines run in PowerShell. You should see both names at https://github.com/ORG/NAME/settings/secrets/actions, and, after the next change to the board, a run on the routine's page started by its API trigger: .github/workflows/board.yml fires it only when the board changed, so its own labels and comments never call it back in a chain. Without Projects (Team and Enterprise plans do not have them yet), make it at https://claude.ai/code/routines with New routine, the same prompt, the repository and an hourly Schedule trigger.

## Team mode: several agents in Actions on the main account

A lead plans an issue labelled epic into tasks pre-assigned to members, the members work them in parallel and land by auto-merge, and the lead integrates the whole ([docs/agents/TEAM.md](../agents/TEAM.md)). The members are names, not people: every one of them runs on the main account's CLAUDE_CODE_OAUTH_TOKEN, so three members spend that account's usage window about three times as fast as one session, and Max suits it better than Pro. The board leaves an epic and its tasks out of the Queue, so no person's session takes them.

1. **Switch it on.** It needs the token from [solo.md](solo.md), step 3, both variables and "Allow auto-merge", which setup-repo.sh turns on:

   ```bash
   bash scripts/setup-repo.sh --var 'CLAUDE_TEAM=["w1","w2","w3"]' --var CLAUDE_WORKER=true
   ```

   On Windows, set the two at https://github.com/ORG/NAME/settings/variables/actions/new instead (CLAUDE_TEAM with the value `["w1","w2","w3"]`, CLAUDE_WORKER with `true`), since Windows PowerShell can strip the inner quotes of a JSON value on its way to gh. Turn the main account's worker routine off: it and the members would race for the same queue. You should see both at https://github.com/ORG/NAME/settings/variables/actions.

2. **Label an issue epic.** Write what the work is and what done looks like into epic.md, then:

   ```bash
   gh issue create --repo ORG/NAME --title "Epic: what it delivers" --label epic --body-file epic.md
   ```

   You should see a "Lead" run at https://github.com/ORG/NAME/actions/workflows/claude-lead.yml, the plan written into the epic, its tasks opened as sub-issues, at most one per member, each labelled todo and `agent:w1` and so on, then a "Worker" leg per member at https://github.com/ORG/NAME/actions/workflows/claude-worker.yml and their pull requests landing on a green check. A member that is stuck labels its task `blocked`, which calls the lead. When the last task closes, the lead checks the integrated default branch and closes the epic.

3. **Tune it, optional.** `CLAUDE_MAX_ROUNDS` (6 if unset) bounds how many rounds a member runs in a row; `CLAUDE_ALLOWED_TOOLS` replaces the tools the sessions may use when your checks need more than git, gh, python3 and scripts/check.sh ([claude-action.md](../setup/claude-action.md)). Delete CLAUDE_WORKER to stop it all.
