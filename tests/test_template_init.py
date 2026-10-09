"""template_init fills every placeholder outside the workflows, removes the
marker folder, leaves the workflows alone, and does nothing the second time.
The placeholders are assembled at run time so this file survives an init of
the repository it lives in."""

import io
import re
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import template_init  # noqa: E402
from template_init import placeholder  # noqa: E402

P = {name: placeholder(name) for name in template_init.PLACEHOLDER_NAMES}
README = f"# {P['PROJECT_NAME']}\n\nClone {P['REPO']}; the default branch is {P['DEFAULT_BRANCH']}.\n"
LICENSE = f"MIT License\n\nCopyright (c) {P['YEAR']} {P['OWNER']}\n"
CODEOWNERS = f"* @{P['OWNER']}\n"
HOOK = f"#!/usr/bin/env bash\nprintf '%s\\n' \"{P['DEFAULT_BRANCH']}\"\n"
# A workflow that carries a placeholder anyway: the run must leave it as it
# is, since GITHUB_TOKEN could not push the change.
WORKFLOW = f"on:\n  push:\n    branches: [\"{P['DEFAULT_BRANCH']}\"]\n"
INIT_WORKFLOW = "on:\n  push:\n"
PLAIN = "nothing to fill here\r\nwith CRLF kept\r\n"
BINARY = bytes(range(256))


def write(root, rel, data):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data if isinstance(data, bytes) else data.encode("utf-8"))


def tree_bytes(root):
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in sorted(root.rglob("*")) if p.is_file()}


def tiny_tree(root):
    write(root, "README.md", README)
    write(root, "LICENSE", LICENSE)
    write(root, ".github/CODEOWNERS", CODEOWNERS)
    write(root, ".github/workflows/ci.yml", WORKFLOW)
    write(root, ".github/workflows/template-init.yml", INIT_WORKFLOW)
    write(root, ".claude/hooks/session-start.sh", HOOK)
    write(root, ".template/PENDING", "not initialised\n")
    write(root, "docs/plain.md", PLAIN)
    write(root, "data/blob.bin", BINARY)
    write(root, ".git/config", f"[remote]\n\turl = {P['REPO']}\n")


def run_init(root, extra=()):
    held = io.StringIO()
    with redirect_stdout(held):
        code = template_init.main(["--repo", "octo/widgets", "--default-branch", "main", "--year", "2026", "--root", str(root), *extra])
    return code, held.getvalue().splitlines()


class Values(unittest.TestCase):
    def test_mapping(self):
        mapping = template_init.values("octo/widgets", "main", 2026)
        self.assertEqual(mapping[P["PROJECT_NAME"]], "widgets")
        self.assertEqual(mapping[P["REPO"]], "octo/widgets")
        self.assertEqual(mapping[P["OWNER"]], "octo")
        self.assertEqual(mapping[P["DEFAULT_BRANCH"]], "main")
        self.assertEqual(mapping[P["YEAR"]], "2026")

    def test_a_bad_repo_is_refused(self):
        for bad in ("widgets", "octo/", "/widgets", "a/b/c"):
            with self.assertRaises(template_init.InitError):
                template_init.values(bad, "main", 2026)

    def test_this_file_and_the_tool_carry_no_placeholder(self):
        for path in (ROOT / "tools" / "template_init.py", Path(__file__)):
            text = path.read_text(encoding="utf-8")
            for marker in P.values():
                self.assertNotIn(marker, text, path.name)

    def test_the_workflows_carry_no_placeholder(self):
        # The run never writes them, so a placeholder there would stay forever.
        folder = ROOT / ".github" / "workflows"
        files = sorted(folder.glob("*.yml"))
        self.assertTrue(files)
        for path in files:
            text = path.read_text(encoding="utf-8")
            for marker in P.values():
                self.assertNotIn(marker, text, path.name)


class Checkpoint(unittest.TestCase):
    """The template's own repository keeps a real checkpoint for whoever
    continues its work; a new copy starts blank instead of inheriting it."""

    def test_a_new_copy_starts_with_the_blank_checkpoint(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            tiny_tree(root)
            (root / ".claude" / "session.md").write_text("# Session checkpoint\n\nWork on claude/10.\n")
            code, lines = run_init(root)
            self.assertEqual(code, 0)
            self.assertEqual((root / ".claude" / "session.md").read_text(), template_init.BLANK_CHECKPOINT)
            self.assertIn(".claude/session.md: reset to a blank checkpoint", lines)

    def test_a_blank_checkpoint_is_left_alone(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            tiny_tree(root)
            (root / ".claude" / "session.md").write_text(template_init.BLANK_CHECKPOINT)
            code, lines = run_init(root)
            self.assertNotIn(".claude/session.md: reset to a blank checkpoint", lines)


class Init(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.root = Path(self.folder.name)
        tiny_tree(self.root)
        self.code, self.lines = run_init(self.root)

    def tearDown(self):
        self.folder.cleanup()

    def test_exits_0_and_fills_every_placeholder_outside_the_workflows(self):
        self.assertEqual(self.code, 0)
        self.assertEqual((self.root / "README.md").read_text(), "# widgets\n\nClone octo/widgets; the default branch is main.\n")
        self.assertEqual((self.root / "LICENSE").read_text(), "MIT License\n\nCopyright (c) 2026 octo\n")
        self.assertEqual((self.root / ".github" / "CODEOWNERS").read_text(), "* @octo\n")
        self.assertEqual((self.root / ".claude" / "hooks" / "session-start.sh").read_text(), "#!/usr/bin/env bash\nprintf '%s\\n' \"main\"\n")
        for path, data in tree_bytes(self.root).items():
            if path.startswith(".git/") or path.startswith(".github/workflows/"):
                continue
            for marker in P.values():
                self.assertNotIn(marker.encode(), data, path)

    def test_leaves_the_workflows_as_they_are(self):
        self.assertEqual((self.root / ".github" / "workflows" / "ci.yml").read_text(), WORKFLOW)
        self.assertEqual((self.root / ".github" / "workflows" / "template-init.yml").read_text(), INIT_WORKFLOW)

    def test_removes_the_marker_folder_only(self):
        self.assertFalse((self.root / ".template").exists())
        self.assertEqual(template_init.REMOVED, (".template",))

    def test_leaves_everything_else_alone(self):
        self.assertEqual((self.root / "docs" / "plain.md").read_bytes(), PLAIN.encode())
        self.assertEqual((self.root / "data" / "blob.bin").read_bytes(), BINARY)
        self.assertEqual((self.root / ".git" / "config").read_text(), f"[remote]\n\turl = {P['REPO']}\n")

    def test_prints_each_changed_or_deleted_path_and_the_note_once(self):
        self.assertEqual(self.lines, [
            ".claude/hooks/session-start.sh: filled",
            ".github/CODEOWNERS: filled",
            "LICENSE: filled",
            "README.md: filled",
            "(workflows are left as they are: GITHUB_TOKEN may not write them)",
            ".template/: deleted",
        ])

    def test_a_second_run_changes_nothing(self):
        before = tree_bytes(self.root)
        code, lines = run_init(self.root)
        self.assertEqual(code, 0)
        self.assertEqual(lines, [])
        self.assertEqual(tree_bytes(self.root), before)

    def test_api_flags_without_a_token_exit_1(self):
        import os
        from contextlib import redirect_stderr
        saved = os.environ.pop("GITHUB_TOKEN", None)
        held = io.StringIO()
        try:
            with redirect_stderr(held):
                code, _ = run_init(self.root, ["--create-labels"])
        finally:
            if saved is not None:
                os.environ["GITHUB_TOKEN"] = saved
        self.assertEqual(code, 1)
        self.assertIn("GITHUB_TOKEN", held.getvalue())


class Labels(unittest.TestCase):
    def test_the_seven_labels_and_their_colours(self):
        self.assertEqual(
            [(name, color) for name, color, _ in template_init.LABELS],
            [("todo", "0e8a16"), ("claimed", "fbca04"), ("in-review", "1d76db"), ("blocker", "b60205"),
             ("account:main", "5319e7"), ("epic", "8b5cf6"), ("blocked", "e99695")],
        )

    def test_already_exists_reads_the_422(self):
        self.assertTrue(template_init.already_exists({"errors": [{"resource": "Label", "code": "already_exists"}]}))
        self.assertFalse(template_init.already_exists({"errors": [{"code": "invalid"}]}))
        self.assertFalse(template_init.already_exists(None))

    def test_the_setup_issue_links_the_nine_pages(self):
        body = template_init.setup_issue_body("octo/widgets", "main")
        for page in ("docs/setup/github.md", "docs/setup/claude-action.md", "docs/setup/claude-project.md", "docs/agents/routines/worker.md", "docs/agents/TEAM.md", "docs/agents/routines/coordinator.md", "docs/project.md", "docs/agents/OWNERSHIP.md", "docs/setup/tiers.md"):
            self.assertIn(f"https://github.com/octo/widgets/blob/main/{page}", body)
        self.assertIn("bash scripts/check.sh", body)
        self.assertIn("ruleset-main.json", body)
        self.assertIn("/install-github-app", body)
        self.assertEqual(body.count("- [ ]"), 6)

    def test_the_setup_issue_opens_with_the_one_command_and_links_every_settings_page(self):
        body = template_init.setup_issue_body("octo/widgets", "main")
        self.assertTrue(body.splitlines()[2].startswith("- [ ] Run `bash scripts/setup-repo.sh` once from your clone, with gh signed in; or by hand:"))
        settings = "https://github.com/octo/widgets/settings"
        for page in (f"{settings}/rules", f"{settings})", f"{settings}/security_analysis", "https://github.com/octo/widgets/labels",
                     f"{settings}/secrets/actions/new", f"{settings}/variables/actions/new", template_init.APP_INSTALL):
            self.assertIn(page, body)
        for target in re.findall(r"\]\(([^)]+)\)", body):
            self.assertTrue(target.startswith("https://"), target)

    def test_the_app_link_preselects_the_owner_and_the_repository(self):
        link = template_init.app_install_link(285817514, 1411163972)
        self.assertEqual(link, "https://github.com/apps/claude/installations/new/permissions?suggested_target_id=285817514&repository_ids[]=1411163972")
        self.assertIn(f"[install the app]({link})", template_init.setup_issue_body("octo/widgets", "main", link))


class FakeRequest:
    """Stands in for template_init.request: answers by method and path, and
    remembers every call; a path it has no answer for is a 404."""

    def __init__(self, answers):
        self.answers = answers
        self.calls = []

    def __call__(self, token, method, path, body=None, params=None):
        self.calls.append((method, path, body))
        return self.answers.get((method, path), (404, None))


class SetupIssue(unittest.TestCase):
    OPENED = (201, {"number": 1})
    REPO = (200, {"id": 1411163972, "owner": {"id": 285817514}})

    def open_with(self, answers):
        fake = FakeRequest({("GET", "/repos/octo/widgets/issues"): (200, []), ("POST", "/repos/octo/widgets/issues"): self.OPENED, **answers})
        with patch.object(template_init, "request", fake):
            line = template_init.open_setup_issue("t", "octo/widgets", "main")
        posted = [body for method, path, body in fake.calls if method == "POST"]
        return line, fake.calls, posted[0]["body"] if posted else None

    def test_one_get_of_the_repository_gives_the_preselected_install_link(self):
        line, calls, body = self.open_with({("GET", "/repos/octo/widgets"): self.REPO})
        self.assertEqual(line, "issue #1: opened")
        self.assertEqual([(m, p) for m, p, _ in calls], [("GET", "/repos/octo/widgets/issues"), ("GET", "/repos/octo/widgets"), ("POST", "/repos/octo/widgets/issues")])
        self.assertIn(template_init.app_install_link(285817514, 1411163972), body)

    def test_a_failed_get_falls_back_to_the_plain_install_link(self):
        for answer in ((404, None), (200, {"id": 1}), (200, "not json we expect")):
            line, _, body = self.open_with({("GET", "/repos/octo/widgets"): answer})
            self.assertEqual(line, "issue #1: opened")
            self.assertIn(f"[install the app]({template_init.APP_INSTALL})", body)
            self.assertNotIn("suggested_target_id", body)

    def test_an_open_setup_issue_is_not_opened_again(self):
        fake = FakeRequest({("GET", "/repos/octo/widgets/issues"): (200, [{"number": 4, "title": template_init.SETUP_ISSUE_TITLE}])})
        with patch.object(template_init, "request", fake):
            self.assertEqual(template_init.open_setup_issue("t", "octo/widgets", "main"), "issue #4: exists")
        self.assertEqual(len(fake.calls), 1)


if __name__ == "__main__":
    unittest.main()
