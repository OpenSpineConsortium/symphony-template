"""The names crowd mode holds a repository to, in one place.

A crowdsourced repository (docs/setup/crowdsourcing.md) is worked by
volunteers on their own Claude accounts. It holds no Claude credential,
token or routine trigger token of anyone's, runs none of the workflows that
spend a subscription, and takes work into the queue only from someone with
the Maintain or Admin role. scripts/crowd.py sets a repository up that way,
audits it and checks a contributor's machine, and it reads every name it
holds the repository to from here, so the setup, the audit and any check
that enforces the same rules cannot drift apart.

Standard library only, like the other tools: the module is imported by a
script that may run on an older Python to say what is wrong with it.
"""

import re

# The secrets that would let a workflow run on someone's Claude
# subscription, or start a routine, or act as the template's GitHub App.
# None of them has a place in a crowd repository, from the repository or
# from the organization.
SECRET_NAMES = (
    "CLAUDE_CODE_OAUTH_TOKEN",
    "ANTHROPIC_API_KEY",
    "COORDINATOR_TRIGGER_URL",
    "COORDINATOR_TRIGGER_TOKEN",
    "SDLC_APP_PRIVATE_KEY",
)
# The variables that switch on the Actions worker and team mode, which run
# on the owner's subscription and land by auto-merge.
VARIABLE_NAMES = ("CLAUDE_WORKER", "CLAUDE_TEAM")
# The variable the workflows read at job level: while it is true, the
# Claude workflows never start.
CROWD_VARIABLE = "CLAUDE_CROWD"
# The roles GitHub reports for someone who may queue work.
MAINTAINER_ROLES = ("admin", "maintain")
# The labels that put an issue in front of the workers.
QUEUE_LABELS = ("todo", "blocker")
# The line in docs/project.md that says which mode the repository is in;
# docs/project.md is imported into every session, so every session knows.
MODE_LINE = re.compile(r"^- Crowd mode: (on|off)\.", re.MULTILINE)


def mode_of(text):
    """'on' or 'off' as docs/project.md's mode line says, or None when the
    text has no such line (a copy older than crowd mode)."""
    match = MODE_LINE.search(text or "")
    return match.group(1) if match else None
