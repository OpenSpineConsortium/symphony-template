"""The protocol check holds a claude/N pull request to its claim file,
its Closes line and its home repository, and touches nothing else."""

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import check_protocol  # noqa: E402


def event(branch="claude/7", body="Closes #7", draft=True,
          head_repo="octo/widgets", base_repo="octo/widgets"):
    return {"pull_request": {
        "head": {"ref": branch, "repo": {"full_name": head_repo}},
        "base": {"repo": {"full_name": base_repo}},
        "body": body,
        "draft": draft,
    }}


class CheckProtocolTest(unittest.TestCase):
    def with_claim(self, present, the_event):
        with tempfile.TemporaryDirectory() as folder:
            if present:
                claim = check_protocol.claim_path(folder, 7)
                claim.parent.mkdir(parents=True)
                claim.write_text("# Claim: #7\n", encoding="utf-8")
            return check_protocol.problems_for(the_event, folder)

    def test_another_branch_is_no_claim(self):
        problems = self.with_claim(False, event(branch="dependabot/actions/checkout-8"))
        self.assertEqual(problems, [])

    def test_draft_with_claim_file_and_closes_line_is_clean(self):
        self.assertEqual(self.with_claim(True, event()), [])

    def test_draft_without_claim_file_is_named(self):
        problems = self.with_claim(False, event())
        self.assertTrue(any("claims/7.md is missing" in p for p in problems))

    def test_ready_with_claim_file_is_named(self):
        problems = self.with_claim(True, event(draft=False))
        self.assertTrue(any("still here" in p for p in problems))

    def test_ready_without_claim_file_is_clean(self):
        self.assertEqual(self.with_claim(False, event(draft=False)), [])

    def test_missing_closes_line_is_named(self):
        problems = self.with_claim(True, event(body="A fine change."))
        self.assertTrue(any("does not close #7" in p for p in problems))

    def test_closing_the_wrong_issue_is_named(self):
        problems = self.with_claim(True, event(body="Closes #8"))
        self.assertTrue(any("does not close #7" in p for p in problems))

    def test_the_other_closing_forms_count(self):
        for body in ("fixes #7", "Fixed #7 at last", "resolves #7", "close #7"):
            self.assertEqual(self.with_claim(True, event(body=body)), [], body)

    def test_a_fork_head_is_named(self):
        problems = self.with_claim(True, event(head_repo="someone/widgets"))
        self.assertTrue(any("not in a fork" in p for p in problems))

    def test_an_event_without_a_pull_request_passes(self):
        self.assertEqual(check_protocol.problems_for({}, "."), [])


if __name__ == "__main__":
    unittest.main()
