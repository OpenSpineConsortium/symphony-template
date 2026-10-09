"""The push guard refuses exactly what the board rules forbid and lets
everything else through, including what it cannot parse: the hook is the
first fence, branch protection the second, so it fails open."""

import io
import json
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import guard_push  # noqa: E402


def refusal(args, current="claude/7", default="main"):
    return guard_push.refusal(args, current, default)


class RefusalTest(unittest.TestCase):
    def test_push_to_default_branch(self):
        self.assertIsNotNone(refusal(["origin", "main"]))

    def test_push_head_to_default_branch(self):
        self.assertIsNotNone(refusal(["origin", "HEAD:main"]))

    def test_delete_board_branch(self):
        self.assertIsNotNone(refusal(["origin", ":board"]))
        self.assertIsNotNone(refusal(["--delete", "origin", "board"]))

    def test_plain_push_on_default_branch(self):
        self.assertIsNotNone(refusal([], current="main"))

    def test_force_refused_even_on_own_claim(self):
        self.assertIsNotNone(refusal(["--force", "origin", "claude/7"]))
        self.assertIsNotNone(refusal(["-f", "origin", "claude/7"]))

    def test_lease_allowed_on_claim_branch(self):
        self.assertIsNone(refusal(["--force-with-lease", "origin", "claude/7"]))
        self.assertIsNone(refusal(["-u", "--force-with-lease=claude/7", "origin", "claude/7"]))

    def test_lease_refused_elsewhere(self):
        self.assertIsNotNone(refusal(["--force-with-lease", "origin", "feature"], current="feature"))

    def test_wholesale_pushes_refused(self):
        self.assertIsNotNone(refusal(["--mirror", "origin"]))
        self.assertIsNotNone(refusal(["--all", "origin"]))

    def test_ordinary_claim_pushes_allowed(self):
        self.assertIsNone(refusal(["origin", "claude/7"]))
        self.assertIsNone(refusal(["-u", "origin", "HEAD"], current="claude/7"))
        self.assertIsNone(refusal([], current="claude/7"))

    def test_full_ref_to_default_refused(self):
        self.assertIsNotNone(refusal(["origin", "refs/heads/main"]))

    def test_detached_head_plain_push_passes(self):
        self.assertIsNone(refusal([], current=None))


class ParsingTest(unittest.TestCase):
    def test_compound_command_finds_the_push(self):
        commands = guard_push.simple_commands("git fetch origin && git push origin main")
        pushes = [guard_push.push_arguments(argv) for argv in commands]
        self.assertIn(["origin", "main"], pushes)

    def test_quoted_text_is_not_a_push(self):
        commands = guard_push.simple_commands("echo 'git push origin main'")
        self.assertTrue(all(guard_push.push_arguments(argv) is None for argv in commands))

    def test_redirection_target_is_not_a_refspec(self):
        commands = guard_push.simple_commands("git push origin claude/7 2>&1")
        self.assertEqual(guard_push.push_arguments(commands[0]), ["origin", "claude/7"])

    def test_git_global_options_are_stepped_over(self):
        self.assertEqual(guard_push.push_arguments(["git", "-C", "clone", "push", "origin", "x"]),
                         ["origin", "x"])

    def test_other_git_verbs_are_not_pushes(self):
        self.assertIsNone(guard_push.push_arguments(["git", "pull", "origin", "main"]))

    def test_unparseable_command_yields_nothing(self):
        self.assertEqual(guard_push.simple_commands("git push 'unclosed"), [])


class MainTest(unittest.TestCase):
    def run_main(self, command):
        payload = json.dumps({"tool_input": {"command": command}, "cwd": str(ROOT)})
        err = io.StringIO()
        with mock.patch.object(sys, "stdin", io.StringIO(payload)), \
             mock.patch.object(sys, "stderr", err), \
             mock.patch.object(guard_push, "branches", return_value=("claude/7", "main")):
            code = guard_push.main()
        return code, err.getvalue()

    def test_forbidden_push_is_refused_with_a_reason(self):
        code, message = self.run_main("git push origin main")
        self.assertEqual(code, 2)
        self.assertIn("pull requests", message)

    def test_allowed_push_passes(self):
        code, message = self.run_main("git push -u origin claude/7")
        self.assertEqual(code, 0)
        self.assertEqual(message, "")

    def test_command_without_push_passes_without_git(self):
        payload = json.dumps({"tool_input": {"command": "git status"}})
        with mock.patch.object(sys, "stdin", io.StringIO(payload)):
            self.assertEqual(guard_push.main(), 0)

    def test_broken_payload_passes(self):
        with mock.patch.object(sys, "stdin", io.StringIO("not json")):
            self.assertEqual(guard_push.main(), 0)


if __name__ == "__main__":
    unittest.main()
