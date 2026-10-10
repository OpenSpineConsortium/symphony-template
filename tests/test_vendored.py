"""The vendored claim protocol, and the three tools that now hand off to it.

The board, the protocol check and team mode's clerk moved to the library
OpenSpineConsortium/sdlc-protocol, whose own tests cover the rules and hold
them to this repository's old tools byte for byte. What is left to test
here is the copy and the wiring: that tools/sdlc_protocol is the release
tools/VENDORED names, unchanged, and that tools/board.py, check_protocol.py
and team.py still answer as the workflows that call them expect.

The comparison with the library reads a clone of it beside this
repository, as /home/user/sdlc-protocol is beside /home/user/sdlc-template,
or the one SDLC_PROTOCOL names, and skips when there is none, as on CI."""

import importlib.util
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
TOOLS = ROOT / "tools"
sys.path.insert(0, str(TOOLS))

import sdlc_protocol  # noqa: E402
from sdlc_protocol.adapters import github  # noqa: E402

VENDORED = TOOLS / "VENDORED"
PACKAGE = TOOLS / "sdlc_protocol"
FIXTURES = ROOT / "tests" / "fixtures"
LIBRARY = Path(os.environ.get("SDLC_PROTOCOL") or ROOT.parent / "sdlc-protocol")
VENDORED_LINE = re.compile(r"^sdlc-protocol (\S+) (\S+)\n$")
SHIMS = ("board", "check_protocol", "team")
REPO = "octo/widgets"


def vendored():
    """The version and the commit tools/VENDORED names."""
    match = VENDORED_LINE.match(VENDORED.read_text(encoding="utf-8"))
    if not match:
        raise AssertionError(f"{VENDORED} is not one line 'sdlc-protocol <version> <commit>'")
    return match.group(1), match.group(2)


def package_files():
    """The vendored package's files, relative to it, without Python's caches,
    which running the tests writes there and git ignores."""
    return sorted(path.relative_to(PACKAGE).as_posix() for path in PACKAGE.rglob("*")
                  if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc")


def git(*args):
    return subprocess.run(["git", "-C", str(LIBRARY), *args], capture_output=True, check=True).stdout


def library_has(commit):
    return subprocess.run(["git", "-C", str(LIBRARY), "cat-file", "-e", f"{commit}^{{commit}}"],
                          capture_output=True).returncode == 0


def run_tool(name, *args, cwd=ROOT, env=None):
    """A shim run the way a workflow runs it, by its path; -B keeps Python's
    caches out of the tree."""
    return subprocess.run([sys.executable, "-B", str(TOOLS / f"{name}.py"), *args],
                          cwd=cwd, env=env, capture_output=True, text=True)


def load_shim(name):
    """A shim as a module of its own name, so its main can run in this
    process where the GitHub adapter can be replaced."""
    spec = importlib.util.spec_from_file_location(f"{name}_shim", TOOLS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TheCopy(unittest.TestCase):
    def test_the_package_states_the_version_vendored_names(self):
        version, _ = vendored()
        self.assertEqual(sdlc_protocol.__version__, version)

    def test_vendored_names_a_whole_commit_with_no_changes_on_top(self):
        _, commit = vendored()
        self.assertRegex(commit, r"^[0-9a-f]{40}$")

    def test_every_file_is_the_librarys_at_that_commit(self):
        _, commit = vendored()
        if not (LIBRARY / ".git").exists():
            self.skipTest(f"no clone of sdlc-protocol at {LIBRARY}")
        if not library_has(commit):
            self.skipTest(f"the clone at {LIBRARY} does not have {commit}")
        listed = git("ls-tree", "-r", "--name-only", commit, "--", "sdlc_protocol").decode("utf-8").split()
        theirs = sorted(name.removeprefix("sdlc_protocol/") for name in listed)
        self.assertEqual(package_files(), theirs)
        for name in theirs:
            with self.subTest(name=name):
                self.assertEqual((PACKAGE / name).read_bytes(), git("show", f"{commit}:sdlc_protocol/{name}"))


class TheShims(unittest.TestCase):
    def test_each_shim_answers_help(self):
        for name in SHIMS:
            with self.subTest(name=name):
                done = run_tool(name, "--help")
                self.assertEqual(done.returncode, 0, done.stderr)
                self.assertIn("usage:", done.stdout)

    def test_the_board_renders_the_librarys_state_for_its_fixture(self):
        with tempfile.TemporaryDirectory() as folder:
            out = Path(folder) / "STATE.md"
            done = run_tool("board", "--dry-run", str(FIXTURES / "board.json"), "--out", str(out))
            self.assertEqual(done.returncode, 0, done.stderr)
            self.assertEqual(out.read_bytes(), (FIXTURES / "board-STATE.md").read_bytes())


def pull_request_event(draft):
    return {"pull_request": {
        "head": {"ref": "claude/7", "repo": {"full_name": REPO}},
        "base": {"repo": {"full_name": REPO}},
        "body": "Closes #7",
        "draft": draft,
    }}


class TheProtocolCheck(unittest.TestCase):
    """ci.yml runs the check in the checkout with the event GitHub wrote;
    a draft keeps its claim file and a ready pull request has deleted it."""

    def check(self, event, claim_file):
        with tempfile.TemporaryDirectory() as folder:
            where = Path(folder)
            (where / "event.json").write_text(json.dumps(event), encoding="utf-8")
            if claim_file:
                claim = where / "docs" / "agents" / "claims" / "7.md"
                claim.parent.mkdir(parents=True)
                claim.write_text("# Claim: #7\n", encoding="utf-8")
            env = dict(os.environ, GITHUB_EVENT_PATH=str(where / "event.json"))
            return run_tool("check_protocol", cwd=where, env=env)

    def test_a_draft_with_its_claim_file_passes(self):
        done = self.check(pull_request_event(draft=True), claim_file=True)
        self.assertEqual((done.returncode, done.stdout), (0, "protocol ok\n"))

    def test_a_draft_without_its_claim_file_fails(self):
        done = self.check(pull_request_event(draft=True), claim_file=False)
        self.assertEqual(done.returncode, 1)
        self.assertIn("docs/agents/claims/7.md is missing", done.stdout)

    def test_a_ready_pull_request_without_the_claim_file_passes(self):
        done = self.check(pull_request_event(draft=False), claim_file=False)
        self.assertEqual((done.returncode, done.stdout), (0, "protocol ok\n"))

    def test_a_ready_pull_request_that_kept_the_claim_file_fails(self):
        done = self.check(pull_request_event(draft=False), claim_file=True)
        self.assertEqual(done.returncode, 1)
        self.assertIn("docs/agents/claims/7.md is still here", done.stdout)


class OneIssue:
    """The one call team route makes to plan an epic: read the issue."""

    def __init__(self, issue):
        self.issues = {issue["number"]: issue}

    def issue(self, number):
        return self.issues[number]


class TheTeamClerk(unittest.TestCase):
    """claude-lead.yml reads one line from route; the clerk's other answers
    are the library's to test."""

    def route(self, issue):
        team = load_shim("team")
        environ = {"GITHUB_TOKEN": "t", "GITHUB_REPOSITORY": REPO}
        out = io.StringIO()
        with mock.patch.object(github, "GitHub", lambda token, repo: OneIssue(issue)), \
                mock.patch.dict(os.environ, environ), redirect_stdout(out):
            code = team.main(["route", "--event", "labeled", "--issue", str(issue["number"]), "--label", "epic"])
        return code, out.getvalue()

    def test_a_newly_labelled_epic_is_planned(self):
        epic = {"number": 3, "state": "open", "body": "Build the widget.", "labels": [{"name": "epic"}]}
        self.assertEqual(self.route(epic), (0, "plan 3\n"))

    def test_an_epic_already_planned_is_left_alone(self):
        epic = {"number": 3, "state": "open", "body": "<!-- team:plan -->", "labels": [{"name": "epic"}]}
        self.assertEqual(self.route(epic), (0, "none\n"))


if __name__ == "__main__":
    unittest.main()
