"""tools/grid_accounts.py keeps what the control panel's Grid tab shows of
the grid's Claude accounts: the gate's list with every e-mail masked, its
plain lines with no link among them, and Anthropic's link only from
Anthropic's own hosts."""

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

import grid_accounts as G  # noqa: E402

LISTING = {
    "v": 1, "current": "1", "auto": False, "usage_job": "running",
    "accounts": [
        {"slot": "1", "current": True, "who": {"signed_in": True, "email": "gregory@example.edu", "plan": "max"},
         "use": {"windows": {"five_hour": {"utilization": 0.4}}}, "login": {"state": "none", "line": ""}},
        {"slot": "2", "current": False, "who": None, "use": None, "login": {"state": "link", "line": "Open the link"}},
    ],
}
LINK = "https://claude.ai/oauth/authorize?code=true&client_id=x&state=abc"
OUTPUT = [
    "HPCW-ACCOUNTS login 2 signed-in: Signed in as other@example.org pro",
    "AUTH-URL: " + LINK,
    "noise from somewhere",
    "HPCW-ACCOUNTS-JSON " + json.dumps(LISTING),
    "HPCW-GRID-GATE accounts ok",
]


class Record(unittest.TestCase):
    def test_emails_are_masked_everywhere(self):
        r = G.record(OUTPUT, "list", "", "req1", 0)
        text = json.dumps(r)
        self.assertNotIn("gregory@", text)
        self.assertNotIn("other@", text)
        self.assertEqual(r["list"]["accounts"][0]["who"]["email"], "gr***@example.edu")
        self.assertIn("Signed in as ot***@example.org pro", r["said"][0])

    def test_no_link_and_no_stray_line_is_kept(self):
        r = G.record(OUTPUT, "login", "2", "req1", 0)
        self.assertNotIn(LINK, json.dumps(r))
        self.assertEqual(r["said"], ["HPCW-ACCOUNTS login 2 signed-in: Signed in as ot***@example.org pro", "HPCW-GRID-GATE accounts ok"])

    def test_states(self):
        self.assertEqual(G.login_state(LISTING, "2"), "link")
        self.assertEqual(G.login_state(LISTING, "1"), "none")
        self.assertEqual(G.login_state(None, "3"), "none")

    def test_a_gate_refusal_has_no_list(self):
        r = G.record(["HPCW-GRID-GATE limit: one call every 3 seconds; try again in 2 seconds"], "use", "2", "r", 123)
        self.assertIsNone(r["list"])
        self.assertEqual(r["rc"], 123)


class Link(unittest.TestCase):
    def test_only_anthropics_hosts(self):
        self.assertEqual(G.link_in(OUTPUT), LINK)
        self.assertEqual(G.link_in(["AUTH-URL: https://claude.ai.evil.example/x"]), "")
        self.assertEqual(G.link_in(["AUTH-URL: https://evil.example/claude.ai"]), "")
        self.assertEqual(G.link_in(["AUTH-URL: https://claude.ai/x y"]), "")


if __name__ == "__main__":
    unittest.main()
