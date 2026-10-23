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
import time
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


class Answers(unittest.TestCase):
    def test_the_newest_answers_of_the_day_are_kept(self):
        now = 1_800_000_000
        with tempfile.TemporaryDirectory() as td:
            def answer(name, age):
                at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now - age))
                Path(td, name + ".json").write_text(json.dumps({"at": at}))
            answer("old", 25 * 3600)
            answer("broken", 0)
            Path(td, "broken.json").write_text("not json")
            for i in range(3):
                answer(f"r{i}", 60 * i)
            gone = G.prune_answers(td, keep=2, now=now)
            self.assertEqual(sorted(os.listdir(td)), ["r0.json", "r1.json"])
            self.assertEqual(len(gone), 3)


class Link(unittest.TestCase):
    def test_a_jobs_output_is_kept_cleaned_again(self):
        token = "sk-ant-oat01-" + "B" * 40
        lines = ["HPCW-GRID-GATE accounts ok", "HPCW-ACCOUNTS-LOG-BEGIN login 2", "--- the job's output (last 120 lines)",
                 "signed in as someone@example.org", "leaked " + token, "AUTH-URL: https://claude.ai/x", "bell\x07here",
                 "HPCW-ACCOUNTS-LOG-END", "HPCW-ACCOUNTS-JSON {}"]
        rec = G.log_record(lines, "login 2", "r1", 0)
        self.assertEqual(rec["lines"][0], "--- the job's output (last 120 lines)")
        self.assertNotIn("someone@", json.dumps(rec))
        self.assertNotIn("B" * 32, json.dumps(rec))
        self.assertNotIn("claude.ai/x", json.dumps(rec))
        self.assertIn("bellhere", rec["lines"])
        self.assertEqual(len(rec["lines"]), 4)

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

    def run_script(self, action, slot="", name="", busy=0, count="", job=""):
        with tempfile.TemporaryDirectory() as td:
            bin_dir = Path(td) / "bin"
            bin_dir.mkdir()
            said = Path(td) / "said"
            fake = bin_dir / "ssh"
            # the first `busy` calls find the gate busy, as an overlapping run leaves it
            fake.write_text('#!/bin/bash\necho "${@: -1}" >> "%s"\n'
                            'n=$(wc -l < "%s"); if [ "$n" -le %d ]; then echo "HPCW-GRID-GATE limit: one call a minute;'
                            ' try again in 0 seconds"; exit 123; fi\necho "HPCW-GRID-GATE accounts ok"\n' % (said, said, busy))
            fake.chmod(0o755)
            git = bin_dir / "git"
            git.write_text("#!/bin/bash\nexit 1\n")
            git.chmod(0o755)
            env = dict(os.environ, PATH=f"{bin_dir}:{os.environ['PATH']}", ACTION=action, SLOT=slot, NAME=name, COUNT=count, JOB=job,
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

    def test_several_workers_in_one_press(self):
        self.assertEqual(self.run_script("worker-start", "2", "team", count="3")[1],
                         ["accounts start 2 team-1", "accounts start 2 team-2", "accounts start 2 team-3", "accounts"])
        self.assertEqual(self.run_script("worker-start", "4", count="2")[1],
                         ["accounts start 4 account4-1", "accounts start 4 account4-2", "accounts"])
        self.assertEqual(self.run_script("worker-start", "2", "team", count="1")[1], ["accounts start 2 team", "accounts"])
        for count, name in (("9", "team"), ("0", "team"), ("2;x", "team"), ("2", "a" * 22)):
            rc, words, _ = self.run_script("worker-start", "2", name, count=count)
            self.assertNotEqual(rc, 0, (count, name))
            self.assertEqual(words, [], (count, name))

    def test_log_names_the_job_whose_output_it_reads(self):
        self.assertEqual(self.run_script("log", "2")[1], ["accounts log login 2"])
        self.assertEqual(self.run_script("log", name="teamb")[1], ["accounts log worker teamb"])
        self.assertEqual(self.run_script("log")[1], ["accounts log usage"])
        for slot, name in (("33", ""), ("", "a b"), ("", "../x")):
            rc, words, _ = self.run_script("log", slot, name)
            self.assertNotEqual(rc, 0, (slot, name))
            self.assertEqual(words, [], (slot, name))

    def test_a_job_says_its_one_word_and_nothing_else(self):
        for job, word in (("update", "update"), ("artifacts", "artifacts"), ("promoter-status", "promoter status"), ("promoter-start", "promoter start"),
                          ("promoter-stop", "promoter stop"), ("promoter-restart", "promoter restart"),
                          ("freeze-status", "freeze status"), ("freeze-pilot", "freeze pilot"), ("freeze-start", "freeze start"),
                          ("schwingnet-status", "schwingnet status"),
                          ("schwingnet-start", "schwingnet start"), ("schwingnet-v1", "schwingnet v1"),
                          ("schwingnet-fetch-vindr_pcxr", "schwingnet fetch vindr_pcxr"),
                          ("schwingnet-prior", "schwingnet prior"), ("schwingnet-chain_eval", "schwingnet chain_eval"),
                          ("schwingnet-census-all", "schwingnet census all"), ("schwingnet-samples", "schwingnet samples"),
                          ("schwingnet-explore-kaggle_scoliosis_yolov5", "schwingnet explore kaggle_scoliosis_yolov5"),
                          ("schwingnet-cancel-40704982", "schwingnet cancel 40704982")):
            self.assertEqual(self.run_script("job", job=job)[1], [word, "accounts"], job)
        for job in ("", "update now", "artifacts-now", "artifacts now", "promoter start abc", "promoter-restart-now", "promoter restart", "freeze-stop", "freeze-start-4", "freeze-pilot-amos22", "schwingnet-xray-chain", "schwingnet-pull", "schwingnet-fetch-",
                    "schwingnet-fetch-VinDr", "schwingnet-census-", "schwingnet-explore-", "schwingnet-explore-Bad", "schwingnet-chain-eval", "schwingnet-prior-x", "schwingnet-samples-x", "schwingnet-fetch-a b", "schwingnet-fetch-a;id", "accounts", "id;x"):
            rc, words, _ = self.run_script("job", job=job)
            self.assertNotEqual(rc, 0, job)
            self.assertEqual(words, [], job)

    def run_key(self, name, value):
        with tempfile.TemporaryDirectory() as td:
            bin_dir = Path(td) / "bin"
            bin_dir.mkdir()
            said, given = Path(td) / "said", Path(td) / "stdin"
            fake = bin_dir / "ssh"
            fake.write_text('#!/bin/bash\necho "${@: -1}" >> "%s"\ncat >> "%s"\necho "HPCW-GRID-GATE key ok"\n' % (said, given))
            fake.chmod(0o755)
            git = bin_dir / "git"
            git.write_text("#!/bin/bash\nexit 1\n")
            git.chmod(0o755)
            env = dict(os.environ, PATH=f"{bin_dir}:{os.environ['PATH']}", ACTION="key", SLOT="", NAME=name, COUNT="", JOB="",
                       CODE="", KEY_VALUE=value, PANEL_KEY="", REQUEST="r1", KEY="k", ACCESS_ID="go2432", HOST_KEY="h",
                       HOST="grid", GH_TOKEN="", REPO="o/r", RUNNER_TEMP=td)
            env.pop("GITHUB_STEP_SUMMARY", None)
            proc = subprocess.run(["bash", "scripts/grid-accounts.sh"], cwd=ROOT, env=env, capture_output=True, text=True)
            words = said.read_text().splitlines() if said.exists() else []
            sent = given.read_text() if given.exists() else ""
            return proc.returncode, words, sent, proc.stdout + proc.stderr

    def test_a_key_goes_on_stdin_and_is_masked(self):
        # the stand-in git fails the branch's publish, so the run's own exit is not read here
        _, words, sent, out = self.run_key("kaggle", "KGAT_testonly0123")
        self.assertEqual(words[0], "key kaggle")
        self.assertTrue(sent.startswith("KGAT_testonly0123\n"))
        self.assertIn("::add-mask::KGAT_testonly0123", out)
        self.assertNotIn("KGAT_testonly0123", out.replace("::add-mask::KGAT_testonly0123", ""))
        _, words, sent, out = self.run_key("physionet", "greg pass1234")
        self.assertEqual(words[0], "key physionet")
        self.assertIn("::add-mask::pass1234", out)
        self.assertTrue(sent.startswith("greg pass1234\n"))

    def test_a_bad_name_or_a_missing_secret_reaches_no_gate(self):
        for name, value in (("foo", "tok_0123456789"), ("hf;id", "tok_0123456789"), ("", "tok_0123456789"),
                            ("hf", ""), ("physionet", " "), ("physionet", "greg "), ("physionet", " pass")):
            rc, words, _, _ = self.run_key(name, value)
            self.assertNotEqual(rc, 0, (name, value))
            self.assertEqual(words, [], (name, value))

    def test_the_workflow_hands_the_step_only_the_named_secret(self):
        flow = (ROOT / ".github/workflows/grid-accounts.yml").read_text()
        for name, secret in (("kaggle", "KAGGLE_API_TOKEN"), ("hf", "HF_TOKEN"), ("zenodo", "ZENODO_TOKEN"),
                             ("redivis", "REDIVIS_API_TOKEN"), ("wandb", "WANDB_API_KEY"), ("ratic", "RATIC_LINK")):
            self.assertIn(f"inputs.name == '{name}' && secrets.{secret}", flow)
        self.assertIn("${{ inputs.action == 'key' && (", flow)

    def test_a_busy_gate_is_asked_again(self):
        words = self.run_script("worker-start", "2", "teamb", busy=2)[1]
        self.assertEqual(words, ["accounts start 2 teamb"] * 3 + ["accounts"])

    def test_a_gate_busy_for_good_fails_in_the_end(self):
        rc, words, _ = self.run_script("use", "2", busy=99)
        self.assertNotEqual(rc, 0)
        self.assertEqual(words, ["accounts use 2"] * 8)

    def test_only_lists_share_a_concurrency_group(self):
        flow = (ROOT / ".github/workflows/grid-accounts.yml").read_text()
        self.assertIn("group: grid-accounts-${{ inputs.action == 'list' && 'list' || github.run_id }}", flow)

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
        self.assertIn("JOB: ${{ inputs.job }}", flow)
