"""The vendored claim protocol, and the three tools that now hand off to it.

The board, the protocol check and team mode's clerk moved to the library
OpenSpineConsortium/sdlc-protocol, whose own tests cover the rules and hold
them to this repository's old tools byte for byte. What is left to test
here is the copy and the wiring: that tools/sdlc_protocol is the release
tools/VENDORED names, unchanged, with the sha256 of each of its files on
the record's lines after the first; that scripts/check.sh holds the copy
to that record, so a hand edit fails the required check; that template-init
leaves the copy and the record as they are in a repository made from the
template; and that tools/board.py, check_protocol.py and team.py still
answer as the workflows that call them expect.

The comparison with the library reads a clone of it beside this
repository, as /home/user/sdlc-protocol is beside /home/user/sdlc-template,
or the one SDLC_PROTOCOL names, and skips when there is none, as on CI."""

import hashlib
import importlib.util
import io
import json
import os
import re
import shutil
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
import template_init  # noqa: E402
from sdlc_protocol.adapters import github  # noqa: E402

VENDORED = TOOLS / "VENDORED"
PACKAGE = TOOLS / "sdlc_protocol"
FIXTURES = ROOT / "tests" / "fixtures"
LIBRARY = Path(os.environ.get("SDLC_PROTOCOL") or ROOT.parent / "sdlc-protocol")
FIRST_LINE = re.compile(r"sdlc-protocol (\S+) (\S+)")
DIGEST_LINE = re.compile(r"([0-9a-f]{64})  (\S+)")
VERIFY = "python3 tools/sdlc_protocol/vendoring.py verify tools"
SHIMS = ("board", "check_protocol", "team")
REPO = "octo/widgets"


def read_record():
    """The version, the commit and the digests tools/VENDORED records: a
    first line "sdlc-protocol <version> <commit>", then one line per copied
    file, "<sha256>  <path inside the copy>", in path order, the layout
    sha256sum writes. Read here on its own terms rather than by the copy's
    vendoring.py, so the copy is not the only judge of itself."""
    text = VENDORED.read_text(encoding="ascii")
    if not text.endswith("\n"):
        raise AssertionError(f"{VENDORED} does not end with a newline")
    first, *rest = text[:-1].split("\n")
    head = FIRST_LINE.fullmatch(first)
    if not head:
        raise AssertionError(f"{VENDORED} does not start with 'sdlc-protocol <version> <commit>'")
    lines = [DIGEST_LINE.fullmatch(line) for line in rest]
    if not lines or not all(lines):
        raise AssertionError(f"{VENDORED} does not list '<sha256>  <path>' for each copied file")
    paths = [line.group(2) for line in lines]
    if paths != sorted(set(paths)):
        raise AssertionError(f"{VENDORED} does not list each file once, in path order")
    return head.group(1), head.group(2), {line.group(2): line.group(1) for line in lines}


def vendored():
    """The version and the commit tools/VENDORED names."""
    version, commit, _ = read_record()
    return version, commit


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


def copy_of_the_vendor_dir(folder):
    """tools/VENDORED and tools/sdlc_protocol copied into folder/tools,
    without Python's caches, as a checkout would have them."""
    vendor_dir = Path(folder) / "tools"
    vendor_dir.mkdir()
    shutil.copyfile(VENDORED, vendor_dir / "VENDORED")
    shutil.copytree(PACKAGE, vendor_dir / "sdlc_protocol", ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    return vendor_dir


def verify(vendor_dir, cwd=ROOT):
    """The copy's own check, run as a script by its path, as scripts/check.sh
    runs it."""
    script = Path(vendor_dir) / "sdlc_protocol" / "vendoring.py"
    return subprocess.run([sys.executable, "-B", str(script), "verify", str(vendor_dir)],
                          cwd=cwd, capture_output=True, text=True)


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

    def test_the_record_lists_every_file_of_the_copy_with_its_sha256(self):
        _, _, digests = read_record()
        self.assertEqual(sorted(digests), package_files())
        for name in package_files():
            with self.subTest(name=name):
                self.assertEqual(digests[name], hashlib.sha256((PACKAGE / name).read_bytes()).hexdigest())

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


class TheVerification(unittest.TestCase):
    """scripts/check.sh holds the copy to its record before the tests run,
    so a pull request that edits tools/sdlc_protocol by hand fails the
    required check, offline; the library's own tests cover each problem
    the check can name."""

    def test_check_sh_verifies_the_copy_before_the_tests(self):
        lines = [line.strip() for line in (ROOT / "scripts" / "check.sh").read_text(encoding="utf-8").splitlines()]
        self.assertIn(VERIFY, lines)
        tests = next(number for number, line in enumerate(lines) if line.startswith("python3 -m unittest"))
        self.assertLess(lines.index(VERIFY), tests)

    def test_the_copy_matches_its_record(self):
        version, commit = vendored()
        done = verify(TOOLS)
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        self.assertTrue(done.stdout.startswith(f"vendored sdlc-protocol {version} at {commit[:7]}: "), done.stdout)

    def test_a_hand_edit_of_the_copy_fails(self):
        with tempfile.TemporaryDirectory() as folder:
            vendor_dir = copy_of_the_vendor_dir(folder)
            with open(vendor_dir / "sdlc_protocol" / "board.py", "a", encoding="ascii", newline="\n") as board:
                board.write("# a local fix\n")
            done = verify(vendor_dir, cwd=folder)
        self.assertEqual(done.returncode, 1, done.stdout + done.stderr)
        self.assertIn("board.py was edited by hand", done.stdout)


class TheTemplateInit(unittest.TestCase):
    """template-init fills the placeholders in every file of a new copy but
    its workflows; were one in tools/sdlc_protocol or tools/VENDORED, the new
    copy's first check would fail on its own unedited copy."""

    def test_it_leaves_the_copy_and_its_record_as_they_are(self):
        with tempfile.TemporaryDirectory() as folder:
            copy_of_the_vendor_dir(folder)
            changed = template_init.fill_tree(Path(folder), template_init.values(REPO, "main", 2026))
        self.assertEqual(changed, [])


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
