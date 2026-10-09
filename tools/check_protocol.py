"""Hold a claude/<issue> pull request to the claim protocol, in CI.

docs/agents/PROTOCOL.md says what a claim looks like; this check makes
the checkable parts of it part of the required check named "check"
(.github/workflows/ci.yml), so a pull request that forgot them cannot
merge however the session that made it was feeling:

- A claim branch belongs to this repository, never a fork.
- The body closes its own issue, so the merge closes it.
- A draft still carries docs/agents/claims/<issue>.md: the claim stays
  visible exactly as long as it holds.
- A pull request marked ready has deleted it: finishing lets go.

Any other head branch, dependabot's or a person's, is not a claim and
passes untouched. The pull request arrives as the event GitHub hands the
run (GITHUB_EVENT_PATH); the claim file is read from the checkout. One
problem per line, exit 1 on any; a run outside a pull request event
passes, so the script never breaks a push build.
"""

import json
import os
import re
import sys
from pathlib import Path

CLAIM_BRANCH = re.compile(r"^claude/(\d+)$")
# The forms GitHub links a pull request to an issue with; the protocol
# writes "Closes #N" and the rest are the same promise.
CLOSES = r"(?i)\b(?:close[sd]?|fix(?:e[sd])?|resolve[sd]?)\s+#%d\b"


def claim_path(root, number):
    return Path(root) / "docs" / "agents" / "claims" / f"{number}.md"


def problems_for(event, root):
    """Every way this pull request breaks the protocol; [] when it is no
    claim at all or keeps the rules."""
    pull = event.get("pull_request") or {}
    branch = ((pull.get("head") or {}).get("ref")) or ""
    match = CLAIM_BRANCH.match(branch)
    if not match:
        return []
    number = int(match.group(1))
    problems = []
    head_repo = (((pull.get("head") or {}).get("repo")) or {}).get("full_name")
    base_repo = (((pull.get("base") or {}).get("repo")) or {}).get("full_name")
    if head_repo != base_repo:
        problems.append(f"{branch}: a claim branch lives in this repository, not in a fork "
                        "(docs/agents/PROTOCOL.md, Claim)")
    if not re.search(CLOSES % number, pull.get("body") or ""):
        problems.append(f"the body does not close #{number}, so the merge would leave the issue open; "
                        f'write "Closes #{number}" (docs/agents/PROTOCOL.md, Finish)')
    claim = claim_path(root, number)
    if pull.get("draft"):
        if not claim.is_file():
            problems.append(f"docs/agents/claims/{number}.md is missing: a draft carries its claim file "
                            "(docs/agents/PROTOCOL.md, Claim)")
    elif claim.is_file():
        problems.append(f"docs/agents/claims/{number}.md is still here: a pull request marked ready "
                        "has deleted its claim file (docs/agents/PROTOCOL.md, Finish)")
    return problems


def main():
    where = os.environ.get("GITHUB_EVENT_PATH")
    if not where or not Path(where).is_file():
        print("no pull request event to check")
        return 0
    try:
        event = json.loads(Path(where).read_text(encoding="utf-8"))
    except ValueError:
        print("the event is not readable; nothing checked")
        return 0
    problems = problems_for(event, ".")
    for problem in problems:
        print(problem)
    if problems:
        return 1
    print("protocol ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
