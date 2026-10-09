"""The push guard refuses exactly what the board rules forbid and lets
everything else through, including what it cannot parse: the hook is the
first fence, branch protection the second, so it fails open. Each case
below that names a shell shape pins a way a real session writes commands."""

import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import guard_push  # noqa: E402


def refusal(args, current="claude/7", default="main"):
    return guard_push.refusal(args, current, default)


def commands(command):
    return guard_push.simple_commands(command)


def pushes(command):
    return [p for argv in commands(command) if (p := guard_push.push_invocation(argv))]


class RefusalTest(unittest.TestCase):
    def test_push_to_default_branch(self):
        self.assertIsNotNone(refusal(["origin", "main"]))
        self.assertIsNotNone(refusal(["origin", "HEAD:main"]))
        self.assertIsNotNone(refusal(["origin", "refs/heads/main"]))

    def test_delete_board_branch(self):
        self.assertIsNotNone(refusal(["origin", ":board"]))
        self.assertIsNotNone(refusal(["--delete", "origin", "board"]))

    def test_plain_push_on_default_branch(self):
        self.assertIsNotNone(refusal([], current="main"))

    def test_force_refused_even_on_own_claim(self):
        self.assertIsNotNone(refusal(["--force", "origin", "claude/7"]))
        self.assertIsNotNone(refusal(["-f", "origin", "claude/7"]))

    def test_plus_refspec_is_a_forced_push(self):
        self.assertIsNotNone(refusal(["origin", "+claude/7"]))
        self.assertIsNotNone(refusal(["origin", "+HEAD:claude/8"]))

    def test_short_cluster_with_f_is_a_forced_push(self):
        self.assertIsNotNone(refusal(["-uf", "origin", "claude/7"]))
        self.assertIsNone(refusal(["-uq", "origin", "claude/7"]))

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
        self.assertIsNone(refusal(["-u", "origin", "HEAD"]))
        self.assertIsNone(refusal([]))

    def test_detached_head_plain_push_passes(self):
        self.assertIsNone(refusal([], current=None))

    def test_a_dry_run_writes_nothing(self):
        self.assertIsNone(refusal(["--dry-run", "origin", "main"]))
        self.assertIsNone(refusal(["-n", "origin", "main"]))

    def test_tags_alone_write_no_branch(self):
        self.assertIsNone(refusal(["--tags"], current="main"))
        self.assertIsNone(refusal(["origin", "--tags"], current="main"))
        self.assertIsNotNone(refusal(["--tags", "origin", "main"], current="main"))

    def test_exec_takes_its_value(self):
        self.assertIsNone(refusal(["--force-with-lease", "--exec", "/usr/bin/git-receive-pack",
                                   "origin", "claude/7"]))


class ShellTest(unittest.TestCase):
    def test_compound_command(self):
        self.assertIn((["origin", "main"], None), pushes("git fetch origin && git push origin main"))

    def test_quoted_text_is_not_a_push(self):
        self.assertEqual(pushes("echo 'git push origin main'"), [])

    def test_redirection_target_is_not_a_refspec(self):
        self.assertEqual(pushes("git push origin claude/7 2>&1"), [(["origin", "claude/7"], None)])

    def test_a_newline_ends_a_command(self):
        found = commands("git add -A\ngit commit -m x\ngit push origin main")
        self.assertEqual(found, [["git", "add", "-A"], ["git", "commit", "-m", "x"],
                                 ["git", "push", "origin", "main"]])

    def test_a_newline_beside_other_operators_still_ends_a_command(self):
        self.assertEqual(commands("true;\n</dev/null git push origin main")[-1],
                         ["git", "push", "origin", "main"])
        self.assertEqual(commands("true;</dev/null git push origin main")[-1],
                         ["git", "push", "origin", "main"])

    def test_a_comment_does_not_join_the_lines_around_it(self):
        self.assertEqual(commands("git status # look first\ngit push origin main"),
                         [["git", "status"], ["git", "push", "origin", "main"]])

    def test_a_comment_ending_in_a_backslash_does_not_join_lines(self):
        self.assertEqual(commands("true; # note \\\ngit push origin main")[-1],
                         ["git", "push", "origin", "main"])

    def test_a_hash_inside_a_word_or_quotes_is_not_a_comment(self):
        self.assertEqual(commands("git commit -m 'Claim #7' && git push origin main")[-1],
                         ["git", "push", "origin", "main"])
        self.assertEqual(commands("echo a#b; git push origin main")[-1],
                         ["git", "push", "origin", "main"])

    def test_a_backslash_newline_joins_two_lines(self):
        self.assertEqual(commands("git push \\\n  origin main"), [["git", "push", "origin", "main"]])

    def test_heredoc_bodies_are_not_commands_whatever_the_opener(self):
        for opener, closer in (("'EOF'", "EOF"), ('"EOF"', "EOF"), ("\\EOF", "EOF"),
                               ("EOF", "EOF"), ("'END-MSG'", "END-MSG"), ("'MSG.txt'", "MSG.txt"),
                               ("-EOF", "\tEOF")):
            command = (f"git commit -F - <<{opener}\nRefuse pushes\n\ngit push origin main\n"
                       f"{closer}\ngit push -u origin claude/7")
            self.assertEqual(pushes(command), [(["-u", "origin", "claude/7"], None)], opener)

    def test_a_crlf_heredoc_closes(self):
        command = "git commit -F - <<'EOF'\r\ngit push origin main\r\nEOF\r\ngit push -u origin claude/7"
        self.assertEqual(pushes(command), [(["-u", "origin", "claude/7"], None)])

    def test_two_heredocs_on_one_line_close_in_turn(self):
        command = ("cat <<A >a.txt; cat <<B >b.txt\nalpha\nA\ngit push origin main\nB\n"
                   "git push -u origin claude/7")
        self.assertEqual(pushes(command), [(["-u", "origin", "claude/7"], None)])

    def test_a_quoted_or_commented_heredoc_marker_cuts_nothing(self):
        for command in ("git commit --allow-empty -m 'Skip <<EOF bodies' &&\ngit push origin main\nEOF",
                        "true; # see <<EOF\ngit push origin main\nEOF",
                        'echo "a <<EOF" ; git push origin main ; echo "\nEOF\n"'):
            self.assertIn((["origin", "main"], None), pushes(command), command)

    def test_a_continued_opener_line_keeps_its_commands(self):
        command = "cat > /dev/null <<'EOF' && \\\ngit push origin main\nMessage\nEOF"
        self.assertIn((["origin", "main"], None), pushes(command))

    def test_a_quoted_heredoc_message_then_a_push(self):
        command = "git commit -m \"$(cat <<'EOF'\nClaim #7\n\nEOF\n)\" && git push -u origin claude/7"
        self.assertIn((["-u", "origin", "claude/7"], None), pushes(command))

    def test_a_here_string_and_a_shift_are_not_heredocs(self):
        self.assertIn((["origin", "main"], None), pushes("cat <<<word\ngit push origin main"))
        self.assertIn((["origin", "main"], None), pushes("echo $((1<<2))\ngit push origin main"))

    def test_an_unclosed_quote_yields_nothing(self):
        self.assertEqual(commands("git push 'unclosed"), [])


class InvocationTest(unittest.TestCase):
    def test_git_global_options_are_stepped_over(self):
        self.assertEqual(guard_push.push_invocation(["git", "-C", "clone", "push", "origin", "x"]),
                         (["origin", "x"], "clone"))

    def test_dash_c_options_stack(self):
        self.assertEqual(guard_push.push_invocation(["git", "-C", "a", "-C", "b", "push"]), ([], "a/b"))

    def test_other_git_verbs_are_not_pushes(self):
        self.assertIsNone(guard_push.push_invocation(["git", "pull", "origin", "main"]))

    def test_switched_branch(self):
        cases = ((["git", "switch", "-c", "claude/9", "origin/main"], "claude/9"),
                 (["git", "switch", "claude/7"], "claude/7"),
                 (["git", "checkout", "-b", "claude/9"], "claude/9"),
                 (["git", "checkout", "claude/7"], None),
                 (["git", "switch", "-"], None),
                 (["git", "switch", "--detach", "origin/main"], None),
                 (["git", "status"], None))
        for argv, expected in cases:
            self.assertEqual(guard_push.switched_branch(argv), expected, argv)


class DirectoryTest(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.work = os.path.join(folder.name, "work")
        self.other = os.path.join(folder.name, "other")
        os.mkdir(self.work)
        os.mkdir(self.other)

    def where(self, command):
        return [os.path.normpath(where) for _, where, _ in guard_push.judged_pushes(command, self.work)]

    def test_a_leading_literal_cd_is_followed(self):
        self.assertEqual(self.where("cd ../other && git push"), [self.other])
        self.assertEqual(self.where("cd ../other; git push"), [self.other])

    def test_a_cd_inside_a_subshell_or_substitution_is_not(self):
        for command in ("(cd ../other && git pull) && git push",
                        "root=$(cd ../other && pwd) && git push",
                        "top=$(cd ../other; pwd); git push",
                        "echo $(cd ../other); git push"):
            self.assertEqual(self.where(command), [self.work], command)

    def test_a_cd_the_guard_cannot_follow_leaves_the_session_directory(self):
        for command in ("cd ../other && cd - && git push",
                        "cd ../other | true; git push",
                        'cd "$PWD" && git push',
                        "cd -P ../other && git push",
                        "cd ./no-such-dir; git push"):
            self.assertEqual(self.where(command), [self.work], command)

    def test_git_dash_c_is_followed_only_to_a_literal_directory(self):
        self.assertEqual(self.where("git -C ../other push"), [self.other])
        self.assertEqual(self.where('git -C "$PWD" push'), [self.work])
        self.assertEqual(self.where("git -C ../no-such-dir push"), [self.work])

    def test_a_switch_names_the_branch_a_later_push_sends(self):
        found = guard_push.judged_pushes("git switch -c claude/9 && git push -u origin HEAD", self.work)
        self.assertEqual([switched for _, _, switched in found], ["claude/9"])


class MainTest(unittest.TestCase):
    def run_main(self, command, branch=("claude/7", "main"), cwd=str(ROOT)):
        payload = json.dumps({"tool_input": {"command": command}, "cwd": cwd})
        err = io.StringIO()
        by_place = branch if callable(branch) else (lambda where: branch)
        with mock.patch.object(sys, "stdin", io.StringIO(payload)), \
             mock.patch.object(sys, "stderr", err), \
             mock.patch.object(guard_push, "branches", side_effect=by_place):
            code = guard_push.main()
        return code, err.getvalue()

    def test_forbidden_push_is_refused_with_a_reason(self):
        code, message = self.run_main("git push origin main")
        self.assertEqual(code, 2)
        self.assertIn("pull requests", message)

    def test_allowed_push_passes(self):
        self.assertEqual(self.run_main("git push -u origin claude/7"), (0, ""))

    def test_push_to_main_on_a_later_line_is_refused(self):
        self.assertEqual(self.run_main("git add -A\ngit commit -m x\ngit push origin main")[0], 2)

    def test_claim_push_then_a_fetch_of_main_passes(self):
        self.assertEqual(self.run_main("git push -u origin claude/7\ngit fetch origin main")[0], 0)

    def test_switching_before_a_plain_push_names_its_branch(self):
        self.assertEqual(self.run_main("git switch -c claude/9 && git push -u origin HEAD",
                                       ("main", "main"))[0], 0)
        self.assertEqual(self.run_main("git switch main && git push", ("claude/7", "main"))[0], 2)

    def test_a_subshell_cd_does_not_move_the_judged_repository(self):
        with tempfile.TemporaryDirectory() as base:
            work, mainrepo = os.path.join(base, "work"), os.path.join(base, "mainrepo")
            os.mkdir(work)
            os.mkdir(mainrepo)

            def by_place(where):
                on_main = os.path.normpath(where) == mainrepo
                return ("main" if on_main else "claude/7", "main")
            for command in ("(cd ../mainrepo && git pull --ff-only) && git push",
                            "root=$(cd ../mainrepo && pwd) && git push --force-with-lease"):
                self.assertEqual(self.run_main(command, by_place, work)[0], 0, command)
            self.assertEqual(self.run_main("cd ../mainrepo && git push", by_place, work)[0], 2)

    def test_payloads_this_hook_does_not_read_pass(self):
        for text in ("not json", "[1, 2]", '{"tool_input": "git push origin main"}',
                     '{"tool_input": {"command": ["git", "push"]}}'):
            with mock.patch.object(sys, "stdin", io.StringIO(text)):
                self.assertEqual(guard_push.main(), 0, text)

    def test_command_without_push_passes_without_git(self):
        payload = json.dumps({"tool_input": {"command": "git status"}})
        with mock.patch.object(sys, "stdin", io.StringIO(payload)), \
             mock.patch.object(guard_push, "branches") as asked:
            self.assertEqual(guard_push.main(), 0)
        asked.assert_not_called()


if __name__ == "__main__":
    unittest.main()
