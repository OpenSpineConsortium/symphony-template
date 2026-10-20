"""tools/living_docs.py builds the documentation site: a link cannot inject
script, a table's cells split only on real pipes, and the site builds every
page with its links, its test results and its reference. The lessons, which
the check once ran here, live in symphony-protocol and are tested there."""

import json
import sys
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import living_docs  # noqa: E402


class Html(unittest.TestCase):
    def test_alt_text_and_script_links_cannot_inject(self):
        made = living_docs.inline('![q" onerror="x](y.png) [a](javascript:alert(1))', lambda t: t)
        self.assertNotIn('" onerror', made)
        self.assertIn('href="#"', made)

    def test_an_escaped_pipe_and_a_pipe_in_code_stay_in_their_cell(self):
        self.assertEqual(living_docs.cells_of("| a \\| b | `x|y` | c |"), ["a | b", "`x|y`", "c"])


class TheSite(unittest.TestCase):
    def test_every_page_is_built_with_its_links(self):
        out = Path(tempfile.mkdtemp()) / "site"
        results = out.parent / "tests.json"
        results.write_text(json.dumps({"tests": [{"id": "test_x.A.test_b", "outcome": "passed", "seconds": 0.1}]}))
        self.assertEqual(living_docs.site(Namespace(out=str(out.parent), tests=None, repo="", sha="")), 1)
        living_docs.site(Namespace(out=str(out), tests=str(results), repo="o/n", sha="abc1234def"))
        index = (out / "index.html").read_text(encoding="utf-8")
        self.assertIn("github.com/OpenSpineConsortium/symphony-protocol/blob/main/lessons/01-first-claim.md", index)
        self.assertIn('href="capabilities.html"', index)
        self.assertFalse((out / "01-first-claim.html").exists())
        self.assertIn("1 of 1 tests passed", (out / "tests.html").read_text(encoding="utf-8"))
        self.assertIn("tools/living_docs.py", (out / "reference.html").read_text(encoding="utf-8"))
        self.assertTrue((out / "capabilities-claim.svg").exists())


if __name__ == "__main__":
    unittest.main()
