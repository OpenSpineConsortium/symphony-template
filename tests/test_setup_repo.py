"""scripts/setup-repo.sh parses, documents every option, reads the labels
from tools/template_init.py so the list lives in one place, and carries
every gh call the owner's checklist relies on; docs/setup/ruleset-org.json
holds the same rules as ruleset-main.json, so the two cannot drift apart;
and every ruleset the template ships targets the default branch alone, so
none can stand in the way of a branch the workflows rewrite. gh itself is
not run here: the script needs a signed-in CLI with admin rights, which no
test has."""

import json
import re
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "setup-repo.sh"
MAIN = ROOT / "docs" / "setup" / "ruleset-main.json"
ORG = ROOT / "docs" / "setup" / "ruleset-org.json"
# The gh calls the research notes verified against gh 2.89.0 and the REST
# description, one piece each.
GH_CALLS = (
    "rulesets", "--input", "repo edit", "--delete-branch-on-merge", "--enable-auto-merge", "--add-topic symphony",
    "--enable-secret-scanning", "--enable-secret-scanning-push-protection",
    "label create", "variable set", "secret set", "codeowners/errors",
)


def run(*args):
    return subprocess.run(["bash", str(SCRIPT), *args], capture_output=True, text=True, cwd=ROOT)


class Script(unittest.TestCase):
    def test_bash_parses_it(self):
        subprocess.run(["bash", "-n", str(SCRIPT)], check=True, cwd=ROOT)

    def test_help_exits_0_and_names_every_option(self):
        done = run("--help")
        self.assertEqual(done.returncode, 0, done.stderr)
        for option in ("OWNER/NAME", "--var NAME=VALUE", "--token", "--help"):
            self.assertIn(option, done.stdout)

    def test_an_unknown_option_exits_2_before_any_gh_call(self):
        self.assertEqual(run("--nope").returncode, 2)
        self.assertEqual(run("--var", "not a pair").returncode, 2)

    def test_the_labels_come_from_template_init_and_nowhere_else(self):
        text = SCRIPT.read_text()
        self.assertIn("template_init", text)
        self.assertIn("LABELS", text)
        self.assertNotIn("account:main", text)

    def test_every_verified_gh_call_is_there(self):
        text = SCRIPT.read_text()
        for piece in GH_CALLS:
            self.assertIn(piece, text)

    def test_the_token_never_goes_on_a_command_line(self):
        # gh secret set without --body prompts without echo, or reads stdin.
        calls = [line for line in SCRIPT.read_text().splitlines() if re.search(r"gh secret set", line)]
        self.assertTrue(calls)
        for line in calls:
            self.assertNotIn("--body", line)
            self.assertNotIn(" -b ", line)


class EveryShippedRuleset(unittest.TestCase):
    """The workflows rewrite branches of their own with GitHub's token: the
    board force-pushes board, the metrics workflow metrics and the protocol
    workflow symphony-protocol/sync, and the board renames a released
    claim's branch out of claude/ into released/. GitHub lets only an
    administrator do that to a branch a ruleset covers, so a ruleset over
    any of them strands a claim or leaves a branch stale. Every ruleset the
    template ships, which setup-repo.sh, crowd.py and an organization's
    owner apply, therefore targets the default branch and nothing else, and
    a change that widens one fails here before any repository takes it."""

    def test_each_targets_the_default_branch_and_nothing_else(self):
        files = sorted((ROOT / "docs" / "setup").glob("ruleset-*.json"))
        self.assertEqual([path.name for path in files],
                         ["ruleset-crowd.json", "ruleset-main.json", "ruleset-org.json"])
        for path in files:
            with self.subTest(ruleset=path.name):
                ruleset = json.loads(path.read_text())
                self.assertEqual(ruleset["target"], "branch")
                self.assertEqual(ruleset["conditions"]["ref_name"], {"include": ["~DEFAULT_BRANCH"], "exclude": []})


class OrganizationRuleset(unittest.TestCase):
    def test_holds_the_same_rules_and_ref_condition_as_the_repository_one(self):
        main = json.loads(MAIN.read_text())
        org = json.loads(ORG.read_text())
        self.assertEqual(org["rules"], main["rules"])
        self.assertEqual(org["conditions"]["ref_name"], main["conditions"]["ref_name"])
        for key in ("target", "enforcement", "bypass_actors"):
            self.assertEqual(org[key], main[key])

    def test_targets_every_repository_of_the_organization(self):
        # The organization endpoint wants repository_name beside ref_name.
        org = json.loads(ORG.read_text())
        self.assertEqual(org["conditions"]["repository_name"], {"include": ["~ALL"], "exclude": [], "protected": False})
        self.assertNotIn("repository_name", json.loads(MAIN.read_text())["conditions"])


if __name__ == "__main__":
    unittest.main()
