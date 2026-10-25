"""tools/handoff.py tells a session once, when its account nears the weekly
limit, to write the handoff a fresh account resumes from, and keeps that
handoff findable. No test has a Claude account: the status line's input
and the grid's reading are written here in the shapes Claude Code and
hpcworker give them, in a scratch repository."""

import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import handoff  # noqa: E402

NOW = datetime.now(timezone.utc).replace(microsecond=0)
LATER = int((NOW + timedelta(days=3)).timestamp())
SOON = int((NOW + timedelta(hours=2)).timestamp())
QUIET = {"gc.auto": "0", "gc.autoDetach": "false", "maintenance.auto": "false",
         "maintenance.autoDetach": "false", "receive.autogc": "false"}
CLEAN = {key: "" for key in ("SYMPHONY_HANDOFF", "SYMPHONY_HANDOFF_AT", "SYMPHONY_HANDOFF_WINDOW",
                             "CLAUDE_CONFIG_DIR", "GITHUB_ACTIONS", "SYMPHONY_WORKER")}


def status_input(five, seven, seven_resets=LATER):
    return {"model": {"display_name": "Opus"}, "workspace": {"project_dir": ""},
            "rate_limits": {"five_hour": {"used_percentage": five, "resets_at": SOON},
                            "seven_day": {"used_percentage": seven, "resets_at": seven_resets}}}


def git(root, *args):
    subprocess.run(["git", *args], cwd=root, check=True, capture_output=True)


class Scratch(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / "repo"
        self.root.mkdir()
        git(self.root, "init", "-q", "-b", "main")
        for key, value in QUIET.items():
            git(self.root, "config", key, value)
        git(self.root, "config", "user.email", "t@example.invalid")
        git(self.root, "config", "user.name", "t")
        (self.root / "README.md").write_text("x\n")
        git(self.root, "add", "README.md")
        git(self.root, "commit", "-q", "-m", "first")
        env = {key: value for key, value in os.environ.items() if key not in CLEAN}
        self.env = mock.patch.dict(os.environ, env, clear=True)
        self.env.start()

    def tearDown(self):
        self.env.stop()
        self.temp.cleanup()

    def see(self, five, seven, seven_resets=LATER):
        return handoff.statusline(status_input(five, seven, seven_resets), self.root, NOW)

    def ask(self, event="PostToolUse", session="s1", **more):
        return handoff.hook(dict({"hook_event_name": event, "session_id": session}, **more), self.root, NOW)

    def grid_folder(self):
        folder = Path(self.temp.name) / "accounts" / "3"
        folder.mkdir(parents=True)
        os.environ["CLAUDE_CONFIG_DIR"] = str(folder)
        return folder


class TheStatusLine(Scratch):
    def test_it_prints_both_windows_and_keeps_the_reading(self):
        self.assertEqual(self.see(13, 42), "Opus | 5h 13% | 7d 42%")
        kept = json.loads((self.root / ".git" / handoff.READING_FILE).read_text())
        self.assertEqual(kept["windows"]["seven_day"]["utilization"], 0.42)
        self.assertEqual(kept["source"], "statusline")

    def test_it_says_when_the_handoff_is_due(self):
        self.assertTrue(self.see(13, 91).endswith("| handoff due"))

    def test_input_with_no_limits_prints_the_model_alone(self):
        self.assertEqual(handoff.statusline({"model": {"display_name": "Opus"}}, self.root, NOW), "Opus")

    def test_bad_input_never_stops_the_status_line(self):
        with mock.patch("sys.stdin", io.StringIO("not json")), redirect_stdout(io.StringIO()):
            self.assertEqual(handoff.main(["statusline"]), 0)


class TheNudge(Scratch):
    def test_below_the_threshold_nothing_is_said(self):
        self.see(99, 89)
        self.assertIsNone(self.ask())

    def test_at_the_threshold_the_session_is_told_once(self):
        self.see(10, 90)
        first = self.ask()
        self.assertIn("weekly limit is at 90%", first["hookSpecificOutput"]["additionalContext"])
        self.assertIn(".claude/skills/handoff", first["hookSpecificOutput"]["additionalContext"])
        self.assertIsNone(self.ask())
        self.assertIsNone(self.ask("Stop"))

    def test_another_session_on_the_clone_is_told_too(self):
        self.see(10, 95)
        self.assertIsNotNone(self.ask(session="s1"))
        self.assertIsNotNone(self.ask(session="s2"))

    def test_at_the_end_of_a_turn_the_stop_is_held_once(self):
        self.see(10, 95)
        answer = self.ask("Stop")
        self.assertEqual(answer["decision"], "block")
        self.assertIsNone(self.ask("Stop", session="s3", stop_hook_active=True))

    def test_a_window_past_its_reset_is_empty(self):
        self.see(10, 95, seven_resets=int((NOW - timedelta(minutes=1)).timestamp()))
        self.assertIsNone(self.ask())

    def test_the_five_hour_window_alone_says_nothing_unless_asked(self):
        self.see(97, 20)
        self.assertIsNone(self.ask())
        os.environ["SYMPHONY_HANDOFF_WINDOW"] = "any"
        self.assertIn("five-hour", self.ask(session="s2")["hookSpecificOutput"]["additionalContext"])

    def test_the_threshold_is_a_switch(self):
        os.environ["SYMPHONY_HANDOFF_AT"] = "80"
        self.see(10, 85)
        self.assertIsNotNone(self.ask())

    def test_off_and_actions_say_nothing(self):
        self.see(10, 99)
        os.environ["SYMPHONY_HANDOFF"] = "off"
        self.assertIsNone(self.ask())
        del os.environ["SYMPHONY_HANDOFF"]
        os.environ["GITHUB_ACTIONS"] = "true"
        self.assertIsNone(self.ask())

    def test_a_recorded_handoff_quiets_the_window(self):
        self.see(10, 95)
        path = self.root / "h.md"
        path.write_text("# filled\n")
        handoff.done(str(path), self.root, NOW)
        self.assertIsNone(self.ask())

    def test_the_hook_never_fails(self):
        with mock.patch("sys.stdin", io.StringIO("[1, 2")), redirect_stdout(io.StringIO()) as out:
            self.assertEqual(handoff.main(["hook"]), 0)
        self.assertEqual(out.getvalue(), "")


class TheGrid(Scratch):
    def test_the_grids_reading_beside_the_account_folder_counts(self):
        folder = self.grid_folder()
        Path(str(folder) + ".use.json").write_text(json.dumps({
            "v": 1, "slot": "3", "read_at": handoff.iso(NOW),
            "windows": {"seven_day": {"utilization": 0.93, "resetsAt": handoff.iso(NOW + timedelta(days=2))}}}))
        self.assertIn("grid reading", self.ask()["hookSpecificOutput"]["additionalContext"])

    def test_the_grids_word_makes_it_due_until_the_handoff_is_recorded(self):
        folder = self.grid_folder()
        Path(str(folder) + ".handoff-due").write_text(json.dumps({"at": handoff.iso(NOW - timedelta(minutes=1))}))
        self.assertIn("about to move", self.ask()["hookSpecificOutput"]["additionalContext"])
        page = self.root / "h.md"
        page.write_text("# filled\n")
        handoff.done(str(page), self.root, NOW)
        recorded = json.loads(Path(str(folder) + ".handoff.json").read_text())
        self.assertEqual(recorded["path"], "h.md")
        self.assertIsNone(handoff.grid_due(NOW))

    def test_a_config_folder_outside_the_grids_layout_is_left_alone(self):
        os.environ["CLAUDE_CONFIG_DIR"] = str(Path(self.temp.name) / ".claude")
        self.assertIsNone(handoff.account_folder())


class TheHandoffPage(Scratch):
    def test_new_writes_a_skeleton_that_done_refuses_until_filled(self):
        self.see(10, 92)
        path = handoff.new(self.root, NOW)
        self.assertEqual(path.parent.name, NOW.strftime("%Y-%m-%d"))
        text = path.read_text()
        self.assertIn("weekly limit is at 92%", text)
        self.assertIn("Branch main at", text)
        with self.assertRaises(ValueError):
            handoff.done(str(path), self.root, NOW)
        path.write_text(text.replace(handoff.FILL, "Filled."))
        self.assertIn("handoff recorded", handoff.done(str(path), self.root, NOW))

    def test_a_second_handoff_of_the_day_gets_its_own_name(self):
        first = handoff.new(self.root, NOW)
        second = handoff.new(self.root, NOW)
        self.assertNotEqual(first, second)
        self.assertTrue(second.name.startswith("handoff-"))

    def test_the_skeleton_is_ascii(self):
        handoff.new(self.root, NOW).read_text(encoding="ascii")

    def test_latest_names_a_recent_committed_handoff_only(self):
        self.assertIsNone(handoff.latest(self.root, NOW))
        path = handoff.new(self.root, NOW)
        self.assertIsNone(handoff.latest(self.root, NOW), "not committed yet")
        git(self.root, "add", ".")
        git(self.root, "commit", "-q", "-m", "handoff")
        self.assertEqual(handoff.latest(self.root, NOW), str(path.relative_to(self.root)))
        self.assertIsNone(handoff.latest(self.root, NOW + timedelta(days=4)))


class TheSettings(unittest.TestCase):
    def test_the_hooks_and_the_status_line_are_wired(self):
        settings = json.loads((ROOT / ".claude" / "settings.json").read_text())
        command = 'python3 "$CLAUDE_PROJECT_DIR"/tools/handoff.py'
        self.assertEqual(settings["statusLine"]["command"], command + " statusline")
        for event in ("Stop", "UserPromptSubmit", "PostToolUse"):
            hooks = [hook["command"] for group in settings["hooks"][event] for hook in group["hooks"]]
            self.assertIn(command + " hook", hooks, event)


if __name__ == "__main__":
    unittest.main()
