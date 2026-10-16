"""tools/usage.py: a session's usage read from its transcript and its
helpers', written on each commit as one trailer line by way of a real git
repository's commit-msg hook, with the session's profile on a second line
where tools/profile.py is beside it, and a run in Actions read from the
action's execution file; the switch turns both off, and inside Actions a
session records nothing, so no run counts twice."""

import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import usage  # noqa: E402

profile = usage.profiler()

# The environment the commit tests run in: without git's own variables, which
# would point the hooks' git at another repository, and without the two the
# tool reads to decide whether to record at all, GitHub Actions and the
# metrics switch, which a person may have turned off in their own shell, as
# usage.py's docstring tells them to; a test that wants either sets it itself.
QUIET = {key: value for key, value in os.environ.items()
         if not key.startswith("GIT_") and key not in ("GITHUB_ACTIONS", usage.SWITCH_VARIABLE)}
# No git of the commit tests runs gc or maintenance on its own: git 2.55
# starts it detached after a commit, and it raced the removal of a scratch
# folder; set in the environment and in each repository's config, as
# tests/test_claim_skill.py sets them.
NO_MAINTENANCE = {"gc.auto": "0", "gc.autoDetach": "false", "maintenance.auto": "false",
                  "maintenance.autoDetach": "false", "receive.autogc": "false"}
GIT_QUIET = {"GIT_CONFIG_COUNT": str(len(NO_MAINTENANCE)),
             **{f"GIT_CONFIG_KEY_{i}": key for i, key in enumerate(NO_MAINTENANCE)},
             **{f"GIT_CONFIG_VALUE_{i}": value for i, value in enumerate(NO_MAINTENANCE.values())}}


def assistant(message_id, model, usage_fields, at="2026-10-12T10:00:00Z"):
    return {"type": "assistant", "timestamp": at, "requestId": "r-" + message_id,
            "message": {"id": message_id, "model": model, "usage": usage_fields}}


def used(inp=0, write=0, read=0, out=0, hour=None):
    fields = {"input_tokens": inp, "cache_creation_input_tokens": write, "cache_read_input_tokens": read,
              "output_tokens": out}
    if hour is not None:
        fields["cache_creation"] = {"ephemeral_5m_input_tokens": write - hour, "ephemeral_1h_input_tokens": hour}
    return fields


def write_lines(path, entries):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(e) + "\n" for e in entries) + "not json\n", encoding="utf-8")


def asking(message_id, usage_fields, at, *tools):
    """An assistant line that asks for tools, each a (name, input) pair whose
    call's id is the message's and its place."""
    entry = assistant(message_id, "claude-opus-5-5", usage_fields, at)
    entry["message"]["content"] = [{"type": "tool_use", "id": f"{message_id}-{index}", "name": name, "input": given}
                                   for index, (name, given) in enumerate(tools)]
    return entry


def answer(tool_id, text, at, error=False):
    block = {"type": "tool_result", "tool_use_id": tool_id, "content": text, "is_error": error}
    return {"type": "user", "timestamp": at, "message": {"role": "user", "content": [block]}}


class ReadingATranscript(unittest.TestCase):
    def setUp(self):
        self.folder = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.folder, True)
        self.transcript = self.folder / "abcdef12-3456.jsonl"

    def test_each_message_counts_once_and_helpers_count_too(self):
        write_lines(self.transcript, [
            {"type": "user", "timestamp": "2026-10-12T10:00:00Z"},
            assistant("m1", "claude-opus-5-5", used(10, 100, 1000, 5), "2026-10-12T10:00:10Z"),
            assistant("m1", "claude-opus-5-5", used(10, 100, 1000, 5), "2026-10-12T10:00:11Z"),
            assistant("m2", "claude-opus-5-5", used(1, 0, 2000, 7, hour=0), "2026-10-12T10:01:00Z"),
            assistant("s", usage.SYNTHETIC, used(99, 99, 99, 99), "2026-10-12T10:01:01Z"),
            {"type": "user", "timestamp": "2026-10-12T11:00:00Z"},
        ])
        write_lines(self.folder / "abcdef12-3456" / "subagents" / "agent-1.jsonl",
                    [assistant("h1", "claude-haiku-5-5", used(3, 30, 300, 4, hour=10))])
        found = usage.session_usage(self.transcript)
        self.assertEqual(found["models"], {"claude-opus-5-5": [11, 100, 0, 3000, 12],
                                           "claude-haiku-5-5": [3, 20, 10, 300, 4]})
        self.assertEqual(found["seconds"], 61, "the hour's pause is left out")

    def test_what_was_spent_since_the_last_commit(self):
        before = {"models": {"m": [1, 2, 3, 4, 5]}, "seconds": 10}
        now = {"models": {"m": [2, 2, 3, 6, 9], "n": [0, 0, 0, 0, 0], "o": [1, 0, 0, 0, 0]}, "seconds": 25}
        self.assertEqual(usage.since(now, before), {"models": {"m": [1, 0, 0, 2, 4], "o": [1, 0, 0, 0, 0]}, "seconds": 15})

    def test_the_trailer_round_trips(self):
        value = usage.trailer("6e4cb20b-affa", {"models": {"b": [1, 2, 3, 4, 5], "a": [0, 0, 0, 1, 0]}, "seconds": 9})
        self.assertEqual(value, "v1 session=6e4cb20b seconds=9 a=0,0,0,1,0 b=1,2,3,4,5")
        message = f"Do it\n\nWhy.\n\nCo-Authored-By: x\nSymphony-Usage: {value}\n"
        self.assertEqual(usage.parse_trailer(message), [("6e4cb20b", 9, {"a": [0, 0, 0, 1, 0], "b": [1, 2, 3, 4, 5]})])
        self.assertEqual(usage.parse_trailer("symphony-usage: v1 session=x seconds=no m=1,2\n"), [("x", 0, {})])
        self.assertEqual(usage.parse_trailer("Symphony-Usage: v2 later\n"), [])

    def test_a_count_too_long_or_in_other_digits_is_passed_over_as_unreadable(self):
        # Anyone who can push a commit writes its message, and int() refuses
        # a string of more than 4,300 digits with ValueError, which stopped
        # the metrics run; a count is read as the Actions records' are, a
        # whole number below 2 ** 53 in ASCII digits.
        huge = "1" * 4301
        self.assertEqual(usage.parse_trailer(f"Symphony-Usage: v1 session=x seconds={huge} m={huge},0,0,0,0\n"),
                         [("x", 0, {})])
        self.assertEqual(usage.parse_trailer(f"Symphony-Usage: v1 session=x seconds={2 ** 53} m=0,0,0,0,{2 ** 53}\n"),
                         [("x", 0, {})])
        self.assertEqual(usage.parse_trailer("Symphony-Usage: v1 session=x seconds=\u0663 m=\u0663,0,0,0,0\n"),
                         [("x", 0, {})])
        self.assertEqual(usage.parse_trailer(f"Symphony-Usage: v1 session=x seconds={2 ** 53 - 1} m=0,0,0,0,7\n"),
                         [("x", 2 ** 53 - 1, {"m": [0, 0, 0, 0, 7]})])

    def test_a_line_with_a_long_run_of_blanks_is_read_in_one_pass(self):
        # A value read lazily up to optional blanks before the line's end took
        # time that grew with the square of a run of blanks inside the line:
        # a second for 16,000 of them, and the metrics run reads each message
        # more than once, under a 20-minute limit.
        message = "Symphony-Usage: v1 session=x" + " " * 100_000 + "m=1,2,3,4,5" + " " * 100_000 + "\n"
        started = time.monotonic()
        self.assertEqual(usage.parse_trailer(message), [("x", 0, {"m": [1, 2, 3, 4, 5]})])
        self.assertLess(time.monotonic() - started, 1.0)
        self.assertEqual(usage.parse_trailer("Symphony-Usage: v1 \t session=y\t \r\n"), [("y", 0, {})])

    def test_the_trailer_carries_eight_characters_of_the_session_and_nothing_more(self):
        spent = {"models": {"m": [1, 0, 0, 0, 1]}, "seconds": 1}
        self.assertTrue(usage.trailer("session_01AMrLKnvPcvNBSchUXZbDDX", spent).startswith("v1 session=01AMrLKn "))
        self.assertTrue(usage.trailer("6e4cb20b-affa-5339", spent).startswith("v1 session=6e4cb20b "))
        self.assertTrue(usage.trailer("a b;c$d", spent).startswith("v1 session=abcd "))


class ARepository(unittest.TestCase):
    """A real repository whose commit-msg hook runs the tools copied into it."""

    COPIED = ("usage.py",)

    def setUp(self):
        environment = mock.patch.dict(os.environ, {**QUIET, **GIT_QUIET}, clear=True)
        environment.start()
        self.addCleanup(environment.stop)
        self.folder = Path(tempfile.mkdtemp()).resolve()
        self.addCleanup(shutil.rmtree, self.folder, True)
        self.repo = self.folder / "repo"
        (self.repo / "tools").mkdir(parents=True)
        for name in self.COPIED:
            shutil.copy(ROOT / "tools" / name, self.repo / "tools" / name)
        shutil.copytree(ROOT / "tools" / "sdlc_protocol", self.repo / "tools" / "sdlc_protocol")
        self.git("init", "-q")
        for key, value in NO_MAINTENANCE.items():
            self.git("config", key, value)
        self.transcript = self.folder / "s1.jsonl"

    def git(self, *args):
        done = subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@example.invalid", "-c",
                               "commit.gpgsign=false", *args], cwd=self.repo, capture_output=True, text=True, timeout=60)
        self.assertEqual(done.returncode, 0, done.stderr)
        return done.stdout.strip()

    def hook(self, command="git commit -m x", session="6e4cb20b-affa-5339", where=None):
        payload = {"session_id": session, "transcript_path": str(self.transcript), "cwd": str(where or self.repo),
                   "tool_input": {"command": command}}
        self.assertEqual(usage.main(["hook"], stdin=io.StringIO(json.dumps(payload))), 0)

    def commit(self, name, where=None):
        where = where or self.repo
        (where / name).write_text(name, encoding="ascii")
        self.git("-C", str(where), "add", name)
        self.git("-C", str(where), "commit", "-q", "-m", f"Add {name}\n\nCo-Authored-By: someone")
        return self.git("-C", str(where), "log", "-1", "--format=%B")


class Commits(ARepository):
    """The hook and the commit-msg hook in a real repository, here one whose
    tools hold usage.py alone, as a copy may that has no profile.py, so the
    usage line stands by itself."""

    def test_each_commit_carries_what_the_session_spent_since_the_last(self):
        self.assertIn("commit-msg hook in place", usage.install(cwd=self.repo))
        write_lines(self.transcript, [assistant("m1", "claude-opus-5-5", used(10, 0, 100, 5))])
        self.hook()
        first = self.commit("a.txt")
        self.assertEqual(usage.parse_trailer(first), [("6e4cb20b", 0, {"claude-opus-5-5": [10, 0, 0, 100, 5]})])
        self.assertTrue(first.rstrip().endswith("Symphony-Usage: v1 session=6e4cb20b seconds=0 claude-opus-5-5=10,0,0,100,5"))
        self.assertIn("Co-Authored-By: someone", first)
        write_lines(self.transcript, [assistant("m1", "claude-opus-5-5", used(10, 0, 100, 5)),
                                      assistant("m2", "claude-opus-5-5", used(1, 0, 50, 2))])
        self.hook()
        second = self.commit("b.txt")
        self.assertEqual(usage.parse_trailer(second)[0][2], {"claude-opus-5-5": [1, 0, 0, 50, 2]})

    def test_a_commit_no_session_asked_for_carries_nothing(self):
        usage.install(cwd=self.repo)
        self.assertEqual(usage.parse_trailer(self.commit("a.txt")), [])
        write_lines(self.transcript, [assistant("m1", "m", used(1, 0, 0, 1))])
        self.hook(command="git status")
        self.assertEqual(usage.parse_trailer(self.commit("b.txt")), [])

    def test_a_usage_left_too_long_ago_belongs_to_no_commit(self):
        usage.install(cwd=self.repo)
        write_lines(self.transcript, [assistant("m1", "m", used(1, 0, 0, 1))])
        self.hook()
        pending = usage.state_dir(self.repo) / "pending.json"
        data = json.loads(pending.read_text())
        data["at"] = time.time() - usage.PENDING_FRESH - 5
        pending.write_text(json.dumps(data))
        self.assertEqual(usage.parse_trailer(self.commit("a.txt")), [])

    def test_inside_actions_or_with_the_switch_off_nothing_is_recorded(self):
        usage.install(cwd=self.repo)
        write_lines(self.transcript, [assistant("m1", "m", used(1, 0, 0, 1))])
        with mock.patch.dict(os.environ, {"GITHUB_ACTIONS": "true"}):
            self.hook()
        self.assertFalse((usage.state_dir(self.repo) / "pending.json").exists())
        (self.repo / ".github").mkdir()
        (self.repo / usage.SWITCH_FILE).write_text("off\n", encoding="ascii")
        self.hook()
        self.assertFalse((usage.state_dir(self.repo) / "pending.json").exists())
        self.assertIn("switch is off", usage.install(cwd=self.repo))
        self.assertIn("GitHub Actions", usage.install(cwd=self.repo, environ={"GITHUB_ACTIONS": "true"}))

    def test_a_clones_own_commit_msg_hook_is_left_alone(self):
        hooks = Path(self.git("rev-parse", "--absolute-git-dir")) / "hooks"
        hooks.mkdir(exist_ok=True)
        (hooks / "commit-msg").write_text("#!/bin/sh\nexit 0\n", encoding="ascii")
        self.assertIn("left as it is", usage.install(cwd=self.repo))
        self.assertEqual((hooks / "commit-msg").read_text(), "#!/bin/sh\nexit 0\n")

    def test_the_profiler_is_loaded_once(self):
        self.assertIs(usage.profiler(), usage.profiler())
        self.assertIs(usage.profiler(), profile)

    def test_the_hook_reads_only_a_git_commit(self):
        for command, commits in (("git commit -m x", True), ("git -C . commit -qm x", True),
                                 ("cd x && git commit --amend --no-edit", True), ("echo git commit", False),
                                 ("git log --grep commit", False), ("GIT_EDITOR=true git commit", True),
                                 ("gh pr create", False), ("", False)):
            self.assertEqual(usage.is_commit(command), commits, command)

    def test_a_payload_the_hook_cannot_read_passes(self):
        for text in ("not json", "[]", json.dumps({"tool_input": "git commit"})):
            self.assertEqual(usage.main(["hook"], stdin=io.StringIO(text)), 0)


class ProfiledCommits(ARepository):
    """With tools/profile.py beside usage.py, as in every copy of the
    template, each commit carries the session's profile since its last
    commit too, on a line of its own after the usage line."""

    COPIED = ("usage.py", "profile.py", "economics.py")
    SESSION = "6e4cb20b-affa-5339"
    # A call that reads a file and runs a failing command, its context 4,010
    # tokens; then a compaction, and a call of 1,200 that reads the file again.
    FIRST = [asking("m1", used(10, 4000, 0, 5), "2026-10-12T10:00:00Z",
                    ("Read", {"file_path": "/r/a.py"}), ("Bash", {"command": "ls"})),
             answer("m1-0", "x" * 300, "2026-10-12T10:00:02Z"),
             answer("m1-1", "boom", "2026-10-12T10:00:03Z", error=True)]
    SECOND = [{"type": "system", "subtype": "compact_boundary", "timestamp": "2026-10-12T10:00:04Z"},
              asking("m2", used(1200, 0, 0, 7), "2026-10-12T10:00:05Z", ("Read", {"file_path": "/r/a.py"})),
              answer("m2-0", "y" * 50, "2026-10-12T10:00:06Z")]
    # A call of 1,301 tokens that runs the first call's command again.
    THIRD = [asking("m3", used(1, 0, 1300, 3), "2026-10-12T10:00:08Z", ("Bash", {"command": "ls"})),
             answer("m3-0", "z", "2026-10-12T10:00:09Z")]

    def setUp(self):
        super().setUp()
        usage.install(cwd=self.repo)

    def test_each_commit_carries_the_profile_since_the_last(self):
        write_lines(self.transcript, self.FIRST)
        self.hook(session=self.SESSION)
        first = self.commit("a.txt")
        usage_line, profile_line = first.rstrip().split("\n")[-2:]
        self.assertTrue(usage_line.startswith("Symphony-Usage: v1 session=6e4cb20b "), first)
        self.assertTrue(profile_line.startswith("Symphony-Profile: v1 session=6e4cb20b "), first)
        self.assertEqual(profile.parse_trailer(first), [("6e4cb20b", {
            "calls": 2, "failed": 1, "repeated": 0, "reads": 1, "rereads": 0, "read_bytes": 300, "reread_bytes": 0,
            "peak": 4010, "compactions": 0, "drops": 0, "tool_seconds": 3})])
        write_lines(self.transcript, self.FIRST + self.SECOND)
        self.hook(session=self.SESSION)
        second = self.commit("b.txt")
        self.assertEqual(usage.parse_trailer(second)[0][2], {"claude-opus-5-5": [1200, 0, 0, 0, 7]})
        # The peak is the second call's, not the session's; the Read repeats
        # the first one's and reads a.py again.
        self.assertEqual(profile.parse_trailer(second), [("6e4cb20b", {
            "calls": 1, "failed": 0, "repeated": 1, "reads": 1, "rereads": 1, "read_bytes": 50, "reread_bytes": 50,
            "peak": 1200, "compactions": 1, "drops": 1, "tool_seconds": 1})])

    def test_a_last_commit_recorded_without_a_profile_leaves_one_commit_without_it(self):
        """A hook older than the profile line kept the usage of the session's
        last commit and no profile: the counts since that commit cannot be
        told, so the next commit carries the usage line alone, and the one
        after it the profile since."""
        state = usage.kept_dir(self.repo) / f"{self.SESSION}.json"
        state.write_text(json.dumps({"models": {"claude-opus-5-5": [1, 0, 0, 0, 1]}, "seconds": 0}))
        write_lines(self.transcript, self.FIRST)
        self.hook(session=self.SESSION)
        first = self.commit("a.txt")
        self.assertEqual(usage.parse_trailer(first)[0][2], {"claude-opus-5-5": [9, 4000, 0, 0, 4]})
        self.assertEqual(profile.parse_trailer(first), [])
        write_lines(self.transcript, self.FIRST + self.SECOND)
        self.hook(session=self.SESSION)
        self.assertEqual(profile.parse_trailer(self.commit("b.txt"))[0][1]["calls"], 1)

    def test_a_profile_the_hook_cannot_read_leaves_that_commit_without_the_line_and_the_next_counts_it(self):
        write_lines(self.transcript, self.FIRST)
        self.hook(session=self.SESSION)
        self.commit("a.txt")
        write_lines(self.transcript, self.FIRST + self.SECOND)
        with mock.patch.object(usage, "profiler", side_effect=OSError("no profile.py")):
            self.hook(session=self.SESSION)
        second = self.commit("b.txt")
        self.assertEqual(usage.parse_trailer(second)[0][2], {"claude-opus-5-5": [1200, 0, 0, 0, 7]})
        self.assertEqual(profile.parse_trailer(second), [])
        write_lines(self.transcript, self.FIRST + self.SECOND + self.THIRD)
        self.hook(session=self.SESSION)
        third = self.commit("c.txt")
        self.assertEqual(usage.parse_trailer(third)[0][2], {"claude-opus-5-5": [1, 0, 0, 1300, 3]})
        # Counted from the first commit, the last whose profile is known: the
        # second's Read and the third's ls, both repeats of the first's.
        self.assertEqual(profile.parse_trailer(third), [("6e4cb20b", {
            "calls": 2, "failed": 0, "repeated": 2, "reads": 1, "rereads": 1, "read_bytes": 50, "reread_bytes": 50,
            "peak": 1301, "compactions": 1, "drops": 1, "tool_seconds": 2})])

    def test_kept_counts_that_cannot_be_read_start_the_count_from_now(self):
        """Counts kept at the last commit as kept() keeps them, or empty,
        are counted from; any other shape, a damaged file or another
        version's, gives no line, so no line claims what one carried."""
        write_lines(self.transcript, self.FIRST)
        now = usage.profile_so_far(self.transcript)
        kept = profile.kept(now)
        self.assertIn("calls=2 ", usage.profile_line(self.SESSION, now, {"models": {}, "profile": {}})[0])
        line, keep = usage.profile_line(self.SESSION, now, {"models": {}, "profile": kept})
        self.assertIn("calls=0 ", line)
        self.assertEqual(keep, kept)
        broken = [{"api_calls": 0}, {"sums": None, "api_calls": 0}, {"sums": [], "api_calls": 0},
                  {"sums": {**kept["sums"], "calls": -1000}, "api_calls": 0}, {"sums": kept["sums"]},
                  {"sums": {**kept["sums"], "calls": "40"}, "api_calls": 0},
                  {"sums": kept["sums"], "api_calls": -1}, {"sums": {"calls": 1}, "api_calls": 0}]
        for earlier in broken:
            self.assertEqual(usage.profile_line(self.SESSION, now, {"models": {}, "profile": earlier}), (None, kept),
                             earlier)

    def test_the_usage_is_left_before_the_profile_is_read(self):
        """Reading the profile takes longer than reading the usage: a hook
        stopped while it reads the profile, at Claude Code's timeout for a
        hook, has left the usage for the commit already."""
        write_lines(self.transcript, self.FIRST)
        with mock.patch.object(usage, "profile_so_far", side_effect=SystemExit("stopped")), \
                self.assertRaises(SystemExit):
            self.hook(session=self.SESSION)
        first = self.commit("a.txt")
        self.assertEqual(usage.parse_trailer(first)[0][2], {"claude-opus-5-5": [10, 4000, 0, 0, 5]})
        self.assertEqual(profile.parse_trailer(first), [])
        write_lines(self.transcript, self.FIRST + self.SECOND)
        self.hook(session=self.SESSION)
        self.assertEqual(profile.parse_trailer(self.commit("b.txt"))[0][1]["calls"], 3,
                         "the first commit carried no line, so the second counts from the start")

    def test_a_commit_whose_hook_read_nothing_keeps_nothing(self):
        """A commit whose hook read nothing at all, a transcript not there
        for that one hook, carries no line and keeps nothing, so the next
        line counts from the last line and claims nothing it carried."""
        write_lines(self.transcript, self.FIRST)
        self.hook(session=self.SESSION)
        self.commit("a.txt")
        kept = usage.kept_dir(self.repo) / f"{self.SESSION}.json"
        before = kept.read_text()
        write_lines(self.transcript, [])
        self.hook(session=self.SESSION)
        self.assertEqual(usage.parse_trailer(self.commit("b.txt")), [])
        self.assertEqual(kept.read_text(), before)
        write_lines(self.transcript, self.FIRST + self.SECOND)
        self.hook(session=self.SESSION)
        third = self.commit("c.txt")
        self.assertEqual(usage.parse_trailer(third)[0][2], {"claude-opus-5-5": [1200, 0, 0, 0, 7]})
        self.assertEqual(profile.parse_trailer(third)[0][1]["calls"], 1)

    def test_counts_that_fall_for_good_are_counted_on_from(self):
        """A transcript replaced under the session reads below the counts
        kept: that commit carries no line and keeps the lower counts, so
        the commits after it carry lines again; keeping the old counts left
        every later commit without one until the session spent past them."""
        write_lines(self.transcript, self.FIRST + self.SECOND)
        self.hook(session=self.SESSION)
        self.commit("a.txt")
        replaced = [asking("m4", used(5, 0, 0, 2), "2026-10-12T11:00:00Z", ("Bash", {"command": "pwd"})),
                    answer("m4-0", "/r", "2026-10-12T11:00:01Z")]
        write_lines(self.transcript, replaced)
        self.hook(session=self.SESSION)
        self.assertEqual(usage.parse_trailer(self.commit("b.txt")), [])
        more = [asking("m5", used(5, 0, 0, 2), "2026-10-12T11:00:02Z", ("Bash", {"command": "date"})),
                answer("m5-0", "now", "2026-10-12T11:00:03Z")]
        write_lines(self.transcript, replaced + more)
        self.hook(session=self.SESSION)
        third = self.commit("c.txt")
        self.assertEqual(usage.parse_trailer(third)[0][2], {"claude-opus-5-5": [5, 0, 0, 0, 2]})
        self.assertEqual(profile.parse_trailer(third)[0][1]["calls"], 1)
        self.assertEqual(profile.parse_trailer(third)[0][1]["peak"], 5)

    def test_another_sessions_usage_left_while_the_profile_is_read_stays(self):
        """Two sessions in one clone: when the second one's hook leaves its
        usage while the first one's reads the profile, the first one's
        second write would put its own usage back on the second one's
        commit, so it writes nothing."""
        write_lines(self.transcript, self.FIRST)
        pending = usage.state_dir(self.repo) / "pending.json"
        other = {"session": "bbbbbbbb-other", "at": time.time(), "models": {"claude-opus-5-5": [1, 0, 0, 0, 1]},
                 "seconds": 0}

        def read_while_another_hook_runs(transcript):
            usage.write_json(pending, other)
            return {"sums": dict.fromkeys(profile.SUMS, 0), "sizes": []}

        with mock.patch.object(usage, "profile_so_far", side_effect=read_while_another_hook_runs):
            self.hook(session=self.SESSION)
        self.assertEqual(json.loads(pending.read_text()), other)

    def test_a_session_committing_from_two_worktrees_counts_nothing_twice(self):
        """A linked worktree has a git directory of its own, where the hook
        leaves what it read; the counts already written are kept in the
        common one, so the second worktree's commit counts from the first's."""
        self.git("add", "tools")
        self.git("commit", "-q", "-m", "Add the tools")
        side = self.folder / "side"
        self.git("worktree", "add", "-q", "-b", "side", str(side))
        write_lines(self.transcript, self.FIRST)
        self.hook(session=self.SESSION)
        self.commit("a.txt")
        write_lines(self.transcript, self.FIRST + self.SECOND)
        self.hook(session=self.SESSION, where=side)
        second = self.commit("b.txt", where=side)
        self.assertEqual(usage.parse_trailer(second)[0][2], {"claude-opus-5-5": [1200, 0, 0, 0, 7]})
        self.assertEqual(profile.parse_trailer(second)[0][1]["calls"], 1)
        self.assertEqual(usage.kept_dir(side), usage.kept_dir(self.repo))
        self.assertNotEqual(usage.state_dir(side), usage.state_dir(self.repo))


class AnActionsRun(unittest.TestCase):
    MESSAGES = [
        {"type": "system", "subtype": "init", "model": "claude-sonnet-5-5"},
        assistant("a1", "claude-sonnet-5-5", used(5, 10, 20, 30)),
        {"type": "result", "subtype": "success", "is_error": False, "duration_ms": 61234, "duration_api_ms": 50000,
         "num_turns": 7, "total_cost_usd": 0.42,
         "modelUsage": {"claude-sonnet-5-5": {"inputTokens": 5, "outputTokens": 30, "cacheReadInputTokens": 20,
                                              "cacheCreationInputTokens": 10, "costUSD": 0.4},
                        "claude-haiku-5-5": {"inputTokens": 1, "outputTokens": 2}}},
    ]

    def test_the_record_holds_counts_times_and_where_it_ran(self):
        record = usage.actions_record(self.MESSAGES, "worker", "workers", "nightly", 12, 40, at="2026-10-12T10:00:00Z")
        self.assertEqual(record, {
            "v": 1, "source": "actions", "workflow": "workers", "job": "worker", "worker": "nightly", "issue": 12,
            "pull": 40, "at": "2026-10-12T10:00:00Z", "seconds": 61.2, "api_seconds": 50.0, "turns": 7,
            "reported_usd": 0.42, "error": False,
            "models": {"claude-sonnet-5-5": [5, 10, 0, 20, 30], "claude-haiku-5-5": [1, 0, 0, 0, 2]}})

    # A run that read a file: an execution file has no clock, so its seconds
    # in tools are nothing; its larger context is the second call's, 36.
    READING = [
        {"type": "system", "subtype": "init", "model": "claude-sonnet-5-5"},
        {"type": "assistant", "message": {"id": "a1", "model": "claude-sonnet-5-5", "usage": used(5, 10, 20, 30),
                                          "content": [{"type": "tool_use", "id": "t1", "name": "Read",
                                                       "input": {"file_path": "/w/a.py"}}]}},
        {"type": "user", "message": {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "t1",
                                                                  "content": "abc"}]}},
        {"type": "assistant", "message": {"id": "a2", "model": "claude-sonnet-5-5", "usage": used(1, 0, 35, 4),
                                          "content": [{"type": "text", "text": "Done."}]}},
        {"type": "result", "subtype": "success", "is_error": False, "duration_ms": 1000, "num_turns": 2},
    ]
    READ = {"calls": 1, "failed": 0, "repeated": 0, "reads": 1, "rereads": 0, "read_bytes": 3, "reread_bytes": 0,
            "peak": 36, "compactions": 0, "drops": 0, "tool_seconds": 0}

    def recorded_by_a_copy(self, names, messages=None, indent=None):
        """The record a copy of the named tools writes, as each workflow runs
        one, made in the runner's temporary folder before Claude starts."""
        with tempfile.TemporaryDirectory() as folder:
            for name in names:
                source = ROOT / "tools" / name
                (shutil.copytree if source.is_dir() else shutil.copy)(source, Path(folder) / name)
            execution = Path(folder) / "execution.json"
            execution.write_text(json.dumps(messages or self.READING, indent=indent), encoding="utf-8")
            out = Path(folder) / "record.json"
            done = subprocess.run([sys.executable, str(Path(folder) / "usage.py"), "actions", "--execution-file",
                                   str(execution), "--out", str(out), "--workflow", "workers", "--job", "worker",
                                   "--root", folder], capture_output=True, text=True, timeout=60, env=QUIET)
            self.assertEqual(done.returncode, 0, done.stderr)
            return json.loads(out.read_text())

    def test_a_copy_with_the_profiler_records_the_runs_profile_and_one_without_it_the_rest(self):
        record = self.recorded_by_a_copy(("usage.py", "profile.py", "economics.py", "sdlc_protocol"))
        self.assertEqual(record["profile"], self.READ)
        alone = self.recorded_by_a_copy(("usage.py",))
        self.assertNotIn("profile", alone)
        self.assertEqual(alone["models"], record["models"])
        self.assertEqual(record["models"], {"claude-sonnet-5-5": [6, 10, 0, 55, 34]})

    def test_a_helpers_calls_in_the_runs_file_count_and_its_context_does_not(self):
        """claude-code-action writes the execution file indented, and the
        Agent SDK puts a helper's messages in it, each naming the call that
        started the helper: its call and its read count, and its 5,000
        tokens of context are its own, no peak of the run's."""
        helper = [
            {"type": "assistant", "parent_tool_use_id": "t0", "message": {
                "id": "h1", "model": "claude-haiku-5-5", "usage": used(5000, 0, 0, 2),
                "content": [{"type": "tool_use", "id": "h-t1", "name": "Read", "input": {"file_path": "/w/b.py"}}]}},
            {"type": "user", "parent_tool_use_id": "t0", "message": {"role": "user", "content": [
                {"type": "tool_result", "tool_use_id": "h-t1", "content": "abcdef"}]}},
        ]
        record = self.recorded_by_a_copy(("usage.py", "profile.py", "economics.py", "sdlc_protocol"),
                                         self.READING[:3] + helper + self.READING[3:], indent=2)
        self.assertEqual(record["profile"], {**self.READ, "calls": 2, "reads": 2, "read_bytes": 9})
        self.assertEqual(record["models"]["claude-haiku-5-5"], [5000, 0, 0, 0, 2])

    def test_without_a_result_the_messages_are_summed_and_the_run_marked(self):
        record = usage.actions_record(self.MESSAGES[:2], "plan", "coordinator")
        self.assertTrue(record["error"])
        self.assertEqual(record["models"], {"claude-sonnet-5-5": [5, 10, 0, 20, 30]})

    def test_the_command_writes_the_record_or_says_why_not(self):
        with tempfile.TemporaryDirectory() as folder:
            execution = Path(folder) / "claude-execution-output.json"
            execution.write_text(json.dumps(self.MESSAGES), encoding="utf-8")
            out = Path(folder) / "usage" / "record.json"
            # The switch that counts is the one in the checkout --root names,
            # here a folder with no switch file, which is on, whatever the
            # repository running this test has turned its own to.
            argv = ["actions", "--execution-file", str(execution), "--out", str(out), "--workflow", "workers",
                    "--job", "worker", "--worker", "nightly", "--issue", "12", "--pull", "", "--root", folder]
            with mock.patch("sys.stdout", io.StringIO()) as printed:
                self.assertEqual(usage.main(argv, environ={}), 0)
            self.assertIn("68 tokens", printed.getvalue())
            record = json.loads(out.read_text())
            self.assertEqual((record["issue"], record["pull"]), (12, None))
            out.unlink()
            with mock.patch("sys.stdout", io.StringIO()) as printed:
                usage.main(argv, environ={"SDLC_METRICS": "off"})
            self.assertFalse(out.exists())
            self.assertIn("switch is off", printed.getvalue())
            missing = list(argv)
            missing[2] = str(Path(folder) / "none.json")
            with mock.patch("sys.stdout", io.StringIO()) as printed:
                self.assertEqual(usage.main(missing, environ={}), 0)
            self.assertIn("no execution file", printed.getvalue())
            (Path(folder) / ".github").mkdir()
            (Path(folder) / usage.SWITCH_FILE).write_text("off\n", encoding="ascii")
            with mock.patch("sys.stdout", io.StringIO()) as printed:
                self.assertEqual(usage.main(argv, environ={}), 0)
            self.assertFalse(out.exists(), "the switch of the checkout --root names says off")
            self.assertIn("switch is off", printed.getvalue())


class NeverInTheWay(unittest.TestCase):
    def test_whatever_goes_wrong_the_hook_and_the_trailer_exit_0(self):
        with mock.patch.object(usage, "run_hook", side_effect=KeyError("surprise")):
            self.assertEqual(usage.main(["hook"], stdin=io.StringIO("{}")), 0)
        with mock.patch.object(usage, "run_trailer", side_effect=TypeError("surprise")):
            self.assertEqual(usage.main(["trailer", "MSG"]), 0)


class Switch(unittest.TestCase):
    def test_the_switch_reads_as_the_metrics_tool_reads_it(self):
        import metrics
        cases = [({}, None), ({"SDLC_METRICS": "off"}, None), ({"SDLC_METRICS": "no"}, None),
                 ({"SDLC_METRICS": "on"}, "off\n"), ({}, "on\n"), ({}, "off\n"), ({}, "maybe\n"), ({}, ""),
                 ({"SDLC_METRICS": ""}, "on please\n")]
        for environ, file_text in cases:
            with tempfile.TemporaryDirectory() as folder:
                if file_text is not None:
                    (Path(folder) / ".github").mkdir()
                    (Path(folder) / usage.SWITCH_FILE).write_text(file_text, encoding="ascii")
                self.assertEqual(usage.sharing_off(folder, environ), metrics.sharing(folder, environ) == metrics.OFF,
                                 (environ, file_text))
        with tempfile.TemporaryDirectory() as folder:
            (Path(folder) / ".github").mkdir()
            (Path(folder) / ".github" / "sdlc-metrics").write_text("off\n", encoding="ascii")
            self.assertTrue(usage.sharing_off(folder, {}))
        # Both names at once, as in a repository adopted again since the
        # rename: an off in either wins, as tools/metrics.py reads them.
        for new, old in (("on\n", "off\n"), ("off\n", "on\n"), ("on\n", "on\n")):
            with self.subTest(new=new, old=old), tempfile.TemporaryDirectory() as folder:
                (Path(folder) / ".github").mkdir()
                (Path(folder) / usage.SWITCH_FILE).write_text(new, encoding="ascii")
                (Path(folder) / ".github" / "sdlc-metrics").write_text(old, encoding="ascii")
                self.assertEqual(usage.sharing_off(folder, {}), "off" in (new.strip(), old.strip()))
                self.assertEqual(usage.sharing_off(folder, {}), metrics.sharing(folder, {}) == metrics.OFF)


class Wiring(unittest.TestCase):
    """Every Claude session the repository runs leaves what it spent where
    the metrics workflow reads it, and every session of a person's records
    its own on its commits."""

    WORKFLOWS = sorted((ROOT / ".github" / "workflows").glob("*.yml"))

    def test_every_claude_step_in_actions_is_recorded_and_kept(self):
        found = 0
        for path in self.WORKFLOWS:
            steps = path.read_text(encoding="utf-8").split("\n      - ")
            for index, step in enumerate(steps):
                if not step.startswith("uses: anthropics/claude-code-action@"):
                    continue
                found += 1
                step_id = re.search(r"\n        id: (\S+)", step)
                self.assertIsNotNone(step_id, f"{path.name}: a Claude step with no id")
                self.assertIn('cp tools/usage.py "$RUNNER_TEMP/usage.py"', steps[index - 1], path.name)
                self.assertIn('cp -r tools/profile.py tools/economics.py tools/sdlc_protocol "$RUNNER_TEMP/" || true',
                              steps[index - 1], path.name)
                record, kept = steps[index + 1], steps[index + 2]
                self.assertIn(f"steps.{step_id.group(1)}.outputs.execution_file", record, path.name)
                self.assertIn('python3 "$RUNNER_TEMP/usage.py" actions --root "$GITHUB_WORKSPACE"', record, path.name)
                self.assertIn("continue-on-error: true", record, path.name)
                self.assertIn("uses: actions/upload-artifact@v7", kept, path.name)
                self.assertIn("name: symphony-usage-${{ github.run_id }}-${{ github.run_attempt }}-", kept, path.name)
                self.assertIn("if-no-files-found: ignore", kept, path.name)
        self.assertEqual(found, 6, "workers.yml's one, coordinator.yml's four and claude.yml's one")

    def test_the_metrics_workflow_reads_the_records_and_keeps_what_it_read(self):
        text = (ROOT / ".github" / "workflows" / "metrics.yml").read_text(encoding="utf-8")
        for needed in ("  actions: read\n", "uses: actions/cache/restore@v6", "uses: actions/cache/save@v6",
                       '--usage-cache "$RUNNER_TEMP/usage-records.json"'):
            self.assertIn(needed, text)

    def test_every_session_runs_the_hook_and_installs_the_commit_msg_hook(self):
        settings = json.loads((ROOT / ".claude" / "settings.json").read_text(encoding="utf-8"))
        commands = [hook["command"] for entry in settings["hooks"]["PreToolUse"] if entry["matcher"] == "Bash"
                    for hook in entry["hooks"]]
        self.assertIn('python3 "$CLAUDE_PROJECT_DIR"/tools/usage.py hook', commands)
        start = (ROOT / ".claude" / "hooks" / "session-start.sh").read_text(encoding="utf-8")
        self.assertIn("python3 tools/usage.py install >/dev/null 2>&1 || true", start)


if __name__ == "__main__":
    unittest.main()
