# Volunteers on their own accounts

Crowd mode opens a project to volunteers who each work under their own Claude Pro or Max account, on their own machine or in their own cloud sessions, while the repository holds no Claude credential of anyone's and GitHub holds it to the rules. [docs/setup/crowdsourcing.md](../setup/crowdsourcing.md) is the whole procedure, with every reason and the safety checklist; this page is its commands in order, to copy. Every crowd.py command runs on your own computer, never in a cloud session: a cloud session's proxy refuses gh's GraphQL commands, and setup needs the organization scope on your own login. On Windows, run them in WSL. ORG/NAME is the crowd repository, AREA a slice of it such as `parser`, LOGIN a GitHub login.

## The commands

| Command | What it does |
| --- | --- |
| `crowd.py setup [--dry-run] [--area AREA] [--owner LOGIN] [--template OWNER/NAME] [--members-only] [--open-pull-requests] [--wait SECONDS] ORG/NAME` | Turn a public copy of the template into a crowd repository. |
| `crowd.py finish [--dry-run] [--owner LOGIN] ORG/NAME` | Check, pin and merge the crowd/setup pull request, then audit. |
| `crowd.py invite [--dry-run] [--area AREA] [--maintainer] [--owner LOGIN] ORG/NAME LOGIN [LOGIN ...]` | Invite people into the teams, with their labels. |
| `crowd.py remove [--dry-run] ORG/NAME LOGIN` | Remove someone from the organization and the repository. |
| `crowd.py audit [--owner LOGIN] ORG/NAME` | Check the repository against crowd mode; exit 1 on any failure. |
| `crowd.py publish-template [--dry-run] [--yes] SRC DEST` | Publish a public copy of a template (route A). |
| `crowd.py doctor [--repo ORG/NAME] [--area AREA] [--worker]` | Check a contributor's machine and clone. |

`--dry-run` makes the reads, prints the writes and makes none; every command can be run again, and writes only what differs.

## The owner

1. **Sign gh in with the organization scope,** after turning on two-factor authentication for your own login at https://github.com/settings/security, since GitHub asks that before you can require it of others:

   ```bash
   gh auth login
   gh auth refresh -h github.com -s admin:org
   ```

2. **Make the organization** on the Free plan at https://github.com/account/organizations/new?plan=free; no API makes one, and a public repository there has every feature crowd mode uses.

3. **A public copy of the template.** sdlc-template is internal to its enterprise, so the template's owner publishes one from their own clone of it, once they agree, since its history goes public too. The first line only prints what would be published; `--yes` publishes; then you clone the copy, which gives you scripts/crowd.py:

   ```bash
   python3 scripts/crowd.py publish-template OpenSpineConsortium/sdlc-template TEMPLATE_OWNER/TEMPLATE_NAME
   python3 scripts/crowd.py publish-template OpenSpineConsortium/sdlc-template TEMPLATE_OWNER/TEMPLATE_NAME --yes
   gh repo clone TEMPLATE_OWNER/TEMPLATE_NAME
   cd TEMPLATE_NAME
   ```

   Route B (a member of the enterprise pushes it for you) and the bundle route for managed users are in [crowdsourcing.md](../setup/crowdsourcing.md#part-1-the-owner), step 2.

4. **Setup,** first as a dry run:

   ```bash
   python3 scripts/crowd.py setup ORG/NAME --template TEMPLATE_OWNER/TEMPLATE_NAME --area AREA --dry-run
   python3 scripts/crowd.py setup ORG/NAME --template TEMPLATE_OWNER/TEMPLATE_NAME --area AREA
   ```

   You should see one line per step, ending with what is left to you and the crowd/setup pull request. Do not run scripts/setup-repo.sh here: it would turn auto-merge on and can store a token, and it refuses to.

5. **What setup leaves to you:** require two-factor authentication at https://github.com/organizations/ORG/settings/security; install the Claude GitHub App on this repository only, from the link setup prints; and take this repository off any Claude secret or variable of the organization at https://github.com/organizations/ORG/settings/secrets/actions and https://github.com/organizations/ORG/settings/variables/actions.

6. **Read every file of the crowd/setup pull request, then finish:**

   ```bash
   python3 scripts/crowd.py finish ORG/NAME
   ```

   You should see the pull request merged and the audit's lines after it. While the check still runs, it says to wait and run it again.

7. **Write the goal and seed the queue:** claim the Task issue setup opened with the claim skill, as crowdsourcing.md's step 6 says, then one epic per area with its tasks as sub-issues (step 7). Only Maintain or Admin queues work.

8. **The coordinator, on your own account, outside any Project:** at https://claude.ai/code/routines, New routine, the prompt from docs/agents/routines/coordinator.md as setup wrote it, the Default environment, an hourly Schedule trigger, no other trigger and no connector; then Run now once and read the transcript.

9. **Invite, and remove:**

   ```bash
   python3 scripts/crowd.py invite ORG/NAME LOGIN [LOGIN ...]
   python3 scripts/crowd.py invite ORG/NAME LOGIN --area AREA --maintainer
   python3 scripts/crowd.py remove ORG/NAME LOGIN
   ```

   It prints the message to send each person. An invitation expires after 7 days, and a new organization can send 50 a day.

10. **Every week, the audit;** it reads only, and exits 1 on any failure, so your own cron can mail it:

    ```bash
    python3 scripts/crowd.py audit ORG/NAME
    ```

## A contributor

1. **Your own plan, your own sign-in.** Claude Pro or Max of your own; never give anyone your login, a token from `claude setup-token` or a routine's trigger token. The first line prints the names, never the values, of any other Claude credential set in this shell; unset each it prints before the first `claude`, since it would outrank your own sign-in:

   ```bash
   env | cut -d= -f1 | grep -E '^(ANTHROPIC_(API_KEY|AUTH_TOKEN|PROFILE|FEDERATION_RULE_ID|ORGANIZATION_ID)|CLAUDE_CODE_(OAUTH_TOKEN|USE_BEDROCK|USE_VERTEX|USE_FOUNDRY))$'
   curl -fsSL https://claude.ai/install.sh | bash
   claude
   gh auth login
   ```

2. **Accept the invitation,** after turning on two-factor authentication at https://github.com/settings/security, at https://github.com/orgs/ORG/invitation within 7 days.

3. **Clone, read what doctor runs, and run doctor until it says ready;** its last line, "Next:", names the step still open:

   ```bash
   gh repo clone ORG/NAME && cd NAME
   less scripts/crowd.py tools/crowd_check.py tools/marked_section.py tools/template_init.py
   python3 scripts/crowd.py doctor --area AREA
   ```

4. **Claim one issue:** run `claude` in the clone and say the sentence doctor printed; hold one open claim at a time. In a cloud session, connect GitHub at https://claude.ai/code first; there `gh issue` and `gh pr` are refused, and the worker prompt says what to use instead.

5. **A worker on your own account, optional:** this prints the crowd worker prompt with your login and area filled in, for a routine at https://claude.ai/code/routines, a Desktop task or `/loop` ([crowdsourcing.md](../setup/crowdsourcing.md#part-2-a-contributor), step 9):

   ```bash
   python3 scripts/crowd.py doctor --worker --area AREA
   ```
