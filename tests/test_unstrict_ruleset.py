"""tools/unstrict_ruleset.py turns the strict policy off in a ruleset that
has it on, keeping every other rule, and writes nothing for one that has it
off, so the Settings workflow sends no PUT that changes nothing."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import unstrict_ruleset  # noqa: E402

MAIN = ROOT / "docs" / "setup" / "ruleset-main.json"


def live(strict):
    """The shipped ruleset as GitHub would give it back, strict or not."""
    ruleset = json.loads(MAIN.read_text())
    for rule in ruleset["rules"]:
        if rule["type"] == "required_status_checks":
            rule["parameters"]["strict_required_status_checks_policy"] = strict
    return dict(ruleset, id=1, source_type="Repository", _links={})


class Unstrict(unittest.TestCase):
    def test_turns_it_off_keeping_every_other_rule(self):
        self.assertEqual(unstrict_ruleset.unstrict(live(True)), json.loads(MAIN.read_text()))

    def test_leaves_a_ruleset_with_it_off_alone(self):
        self.assertIsNone(unstrict_ruleset.unstrict(live(False)))

    def test_a_ruleset_with_no_required_checks_is_left_alone(self):
        self.assertIsNone(unstrict_ruleset.unstrict({"name": "x", "rules": [{"type": "deletion"}]}))

    def test_main_writes_the_body_or_exits_one(self):
        with tempfile.TemporaryDirectory() as scratch:
            source, target = Path(scratch, "in.json"), Path(scratch, "out.json")
            source.write_text(json.dumps(live(True)))
            self.assertEqual(unstrict_ruleset.main(["x", str(source), str(target)]), 0)
            self.assertEqual(json.loads(target.read_text()), json.loads(MAIN.read_text()))
            target.unlink()
            source.write_text(json.dumps(live(False)))
            self.assertEqual(unstrict_ruleset.main(["x", str(source), str(target)]), 1)
            self.assertFalse(target.exists())


if __name__ == "__main__":
    unittest.main()
