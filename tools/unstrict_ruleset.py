"""Turn "Require branches to be up to date" off in one ruleset.

The Settings workflow reads a ruleset from GitHub into a file and calls
this with that file and the path of the body to write back. The body keeps
every rule as it was and sets the required checks' strict policy to false,
since with it on every merge sent each other ready pull request back to CI
(the owner's word of 2026-10-20). It exits 1, writing nothing, where the
policy is off already, so the workflow sends no PUT that changes nothing.
"""

import json
import sys

# The fields of GitHub's answer that a ruleset's PUT takes back.
KEYS = ("name", "target", "enforcement", "conditions", "rules", "bypass_actors")


def unstrict(ruleset):
    """The ruleset's PUT body with the strict policy off, or None where it is off already."""
    rules = [rule for rule in ruleset.get("rules") or [] if rule.get("type") == "required_status_checks"]
    if not any((rule.get("parameters") or {}).get("strict_required_status_checks_policy") for rule in rules):
        return None
    for rule in rules:
        rule["parameters"]["strict_required_status_checks_policy"] = False
    return {key: ruleset[key] for key in KEYS if key in ruleset}


def main(argv):
    with open(argv[1], encoding="utf-8") as source:
        body = unstrict(json.load(source))
    if body is None:
        return 1
    with open(argv[2], "w", encoding="utf-8") as target:
        json.dump(body, target)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
