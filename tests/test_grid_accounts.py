"""tools/grid_accounts.py keeps what the control panel's Grid tab shows of
the grid's Claude accounts: the gate's list with every e-mail masked, its
plain lines with no link among them, and Anthropic's link only from
Anthropic's own hosts."""

import json
import os
import re
import subprocess
import sys
import tempfile
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


ROOT = Path(__file__).resolve().parent.parent


class Words(unittest.TestCase):
    """scripts/grid-accounts.sh says to the gate only the words its action names, with a worker's
    name held to the gate's own shape, and the workflow offers every action the script takes."""

    def run_script(self, action, slot="", name=""):
        with tempfile.TemporaryDirectory() as td:
            bin_dir = Path(td) / "bin"
            bin_dir.mkdir()
            said = Path(td) / "said"
            fake = bin_dir / "ssh"
            fake.write_text('#!/bin/bash\necho "${@: -1}" >> "%s"\necho "HPCW-GRID-GATE accounts ok"\n' % said)
            fake.chmod(0o755)
            git = bin_dir / "git"
            git.write_text("#!/bin/bash\nexit 1\n")
            git.chmod(0o755)
            env = dict(os.environ, PATH=f"{bin_dir}:{os.environ['PATH']}", ACTION=action, SLOT=slot, NAME=name,
                       CODE="", PANEL_KEY="", REQUEST="r1", KEY="k", ACCESS_ID="go2432", HOST_KEY="h", HOST="grid",
                       GH_TOKEN="", REPO="o/r", RUNNER_TEMP=td)
            env.pop("GITHUB_STEP_SUMMARY", None)
            proc = subprocess.run(["bash", "scripts/grid-accounts.sh"], cwd=ROOT, env=env, capture_output=True, text=True)
            words = said.read_text().splitlines() if said.exists() else []
            return proc.returncode, words, proc.stdout + proc.stderr

    def test_start_and_stop_a_worker(self):
        self.assertEqual(self.run_script("worker-start", "2", "teamb")[1], ["accounts start 2 teamb", "accounts"])
        self.assertEqual(self.run_script("worker-start", "3")[1], ["accounts start 3", "accounts"])
        self.assertEqual(self.run_script("worker-stop", name="teamb")[1], ["accounts stop teamb", "accounts"])

    def test_a_bad_name_or_slot_reaches_no_gate(self):
        for action, slot, name in (("worker-start", "2", "a b"), ("worker-start", "2", "x;rm"), ("worker-start", "33", ""),
                                   ("worker-stop", "", ""), ("worker-stop", "", "../x")):
            rc, words, _ = self.run_script(action, slot, name)
            self.assertNotEqual(rc, 0, (action, slot, name))
            self.assertEqual(words, [], (action, slot, name))

    def test_the_workflow_offers_every_action(self):
        flow = (ROOT / ".github/workflows/grid-accounts.yml").read_text()
        script = (ROOT / "scripts/grid-accounts.sh").read_text()
        offered = re.search(r"options: \[([^\]]*)\]", flow).group(1).replace(" ", "").split(",")
        taken = re.search(r'case "\$ACTION" in ([a-z|-]+)\) ;;', script).group(1).split("|")
        self.assertEqual(sorted(offered), sorted(taken))
        self.assertIn("NAME: ${{ inputs.name }}", flow)
