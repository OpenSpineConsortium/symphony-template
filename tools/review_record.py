"""Hold a pull request to its review record, in CI.

The owner's rule for the owner's own sessions is an adversarial review before each
substantive pull request. Written only in the owner's Claude instructions it binds
nobody else, so this check makes it part of the required check "check" for
every contributor, a person or a session alike: a pull request marked ready
for review carries a section headed "## Adversarial review" whose text says
what was checked against the change and what came of it.

What passes without one, and why:
- a draft, since a claim opens its draft before any work is done
  (docs/agents/PROTOCOL.md, Work in the open), and the review comes before
  the pull request is marked ready;
- a pull request opened by a bot account (Dependabot, a GitHub App, a
  workflow's GITHUB_TOKEN), whose change is generated and whose own check
  is the review;
- a pull request opened before the rule began (STARTED), so work already in
  review is not stopped half way;
- a run outside a pull request event, such as bash scripts/check.sh on a
  laptop or a push to the default branch.

It reads the event from GITHUB_EVENT_PATH, prints one line on what it found
and exits 1 when the record is missing or still the template's placeholder.
ci.yml runs it on the edited event too, so writing the section into the
body is enough to turn the check green.
"""

import json
import os
import re
import sys
from datetime import datetime

STARTED = "2026-10-22T05:00:00Z"
HEADING = re.compile(r"^#{2,3}\s+adversarial review\s*$", re.IGNORECASE)
NEXT_HEADING = re.compile(r"^#{1,3}\s")
PLACEHOLDER = "What a reviewer who wanted the change to fail checked"
MINIMUM_LETTERS = 40


def review_text(body):
    """The text under the review heading, up to the next heading, or None."""
    lines = (body or "").replace("\r\n", "\n").split("\n")
    for at, line in enumerate(lines):
        if HEADING.match(line.strip()):
            section = []
            for following in lines[at + 1:]:
                if NEXT_HEADING.match(following):
                    break
                section.append(following)
            return "\n".join(section).strip()
    return None


def letters_in(text):
    return sum(1 for character in text if character.isalnum())


def opened_before_rule(created_at):
    if not created_at:
        return False
    parsed = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
    return parsed < datetime.fromisoformat(STARTED.replace("Z", "+00:00"))


def verdict(pull):
    """(passes, message) for one pull request as the event gives it."""
    if pull.get("draft"):
        return True, "review record: a draft, so not yet asked for"
    if (pull.get("user") or {}).get("type") == "Bot":
        return True, "review record: opened by a bot, so not asked for"
    if opened_before_rule(pull.get("created_at")):
        return True, f"review record: opened before {STARTED}, so not asked for"
    text = review_text(pull.get("body"))
    if text is None:
        return False, ("review record: missing; add a section headed '## Adversarial review' to the "
                       "pull request's body saying what was checked against the change and what came of it "
                       "(CONTRIBUTING.md)")
    if PLACEHOLDER in text:
        return False, "review record: still the template's placeholder; replace it with what was checked"
    if letters_in(text) < MINIMUM_LETTERS:
        return False, (f"review record: too short ({letters_in(text)} letters, at least {MINIMUM_LETTERS}); "
                       "say what was checked and what came of it")
    return True, "review record: present"


def main(environ=None):
    environ = os.environ if environ is None else environ
    path = environ.get("GITHUB_EVENT_PATH")
    if environ.get("GITHUB_EVENT_NAME") != "pull_request" or not path:
        print("review record: not a pull request event, nothing to check")
        return 0
    with open(path, encoding="utf-8") as handle:
        pull = json.load(handle).get("pull_request") or {}
    passes, message = verdict(pull)
    print(message)
    return 0 if passes else 1


if __name__ == "__main__":
    sys.exit(main())
