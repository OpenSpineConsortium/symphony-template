Crowd mode: scripts/crowd.py sets a repository up for volunteers on their own Claude accounts, and GitHub then holds it to the rules through the variable CLAUDE_CROWD, the required check and queue.yml.

A crowd repository (docs/setup/crowdsourcing.md) holds no Claude credential
of anyone's. It has two switches: the repository variable CLAUDE_CROWD,
which the workflows can read at job level, and the line "- Crowd mode: on."
in docs/project.md, which every session loads and only the owner's review
changes. The template ships the line off and no variable, so nothing below
does anything in an ordinary copy.

`python3 scripts/crowd.py setup` does what GitHub lets a script do (the
organization's defaults, the repository and Actions settings, labels, teams,
the ruleset docs/setup/ruleset-crowd.json, the variable) and opens one pull
request from crowd/setup with the files under docs/setup/crowd/ and the edits
crowd.py holds as data. `finish` merges it once "check" passed on GitHub
Actions and pins that check to app 15368; `invite` refuses until then;
`audit` checks everything weekly; `doctor` walks a contributor to ready.

What GitHub then enforces:

- claude.yml, claude-lead.yml and claude-worker.yml never start: each job's
  `if` puts `vars.CLAUDE_CROWD != 'true' &&` first. An unset variable reads
  as empty, so elsewhere each condition is exactly the old one.
- The required check runs `tools/crowd_check.py guard`, which fails while a
  Claude secret or CLAUDE_WORKER or CLAUDE_TEAM reaches the repository and
  crowd mode shows anywhere; while the default branch says on and
  CLAUDE_CROWD is not true; and when a pull request changes
  .claude/session.md or CLAUDE.md's checkpoint block while the default
  branch says on. A checkpoint is a pull request comment there.
- .github/workflows/queue.yml takes todo or blocker off again when someone
  without Maintain or Admin adds one, opens an issue with one, or edits a
  queued issue's title or body.
- scripts/setup-repo.sh stops before any write while CLAUDE_CROWD is true,
  since it turns auto-merge on and can store a token.

What stays a convention, made loud but not prevented: any writer can delete
the variable, add a secret, disable a workflow, or push to another's claim
branch or to board. The check, queue.yml and the audit report each; the
protection against a writer's own workflow reading secrets is that none
exists.

Source: scripts/crowd.py, tools/crowd_check.py and the workflows, built
2026-10-10; never run against a live organization.
