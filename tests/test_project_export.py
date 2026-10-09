"""project_export writes export.json, the repository as a cswap project
export, from the repository's own files: deterministic bytes, every memory
file listed with its size and the path it gets, and --check that fails when
the committed file no longer matches."""

import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import project_export  # noqa: E402

CLAUDE_MD = "# widgets\n\nThe project kept as files.\n"
PROJECT = (
    "# widgets: goal and settings\n\n## Goal\n\nA widget for every desk.\nDone is a widget on each.\n\n"
    "## Repositories\n\n- octo/widgets, this one: the shared plane.\n- octo/other: read only.\n"
)
PROJECT_UNWRITTEN = PROJECT.replace("A widget for every desk.\nDone is a widget on each.", "Not yet written. One paragraph.")
SETUP = (
    "# Making the Project\n\n## The pointer text\n\n```\nThis Project works on octo/widgets. Read CLAUDE.md first.\n```\n\n"
    "## The main account\n\nText.\n"
)
README = "# widgets\n\nWidgets for desks, kept as files.\n\nSecond paragraph.\n"
INDEX = "# Memory index\n\n- [A fact](a-fact.md): one line.\n"
FACT = "One line about the fact.\n\nThe fact itself.\n"


def write(root, rel, text):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode("utf-8"))


def project_tree(root):
    write(root, "CLAUDE.md", CLAUDE_MD)
    write(root, "README.md", README)
    write(root, "docs/project.md", PROJECT)
    write(root, "docs/setup/claude-project.md", SETUP)
    write(root, "docs/memory/MEMORY.md", INDEX)
    write(root, "docs/memory/a-fact.md", FACT)
    write(root, "docs/memory/notes.txt", "not a memory file\n")


class Manifest(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.root = Path(self.folder.name)
        project_tree(self.root)
        self.manifest = project_export.manifest(self.root)

    def tearDown(self):
        self.folder.cleanup()

    def test_is_version_1_of_cswap_s_code_project_export(self):
        self.assertEqual(self.manifest["format"], "claude-project-export")
        self.assertEqual(self.manifest["version"], 1)
        self.assertEqual(self.manifest["kind"], "code")
        self.assertEqual(self.manifest["history"], [])
        self.assertEqual(self.manifest["problems"], [])
        self.assertNotIn("exported_at", self.manifest, "a clock would change the bytes")

    def test_names_the_project_after_claude_md(self):
        self.assertEqual(self.manifest["name"], "widgets")

    def test_takes_the_goal_as_the_description(self):
        self.assertEqual(self.manifest["description"], "A widget for every desk.\nDone is a widget on each.")

    def test_takes_the_readme_s_opening_while_the_goal_is_unwritten(self):
        write(self.root, "docs/project.md", PROJECT_UNWRITTEN)
        self.assertEqual(project_export.description(self.root), "Widgets for desks, kept as files.")

    def test_takes_the_pointer_text_as_the_instructions(self):
        self.assertEqual(self.manifest["instructions"], "This Project works on octo/widgets. Read CLAUDE.md first.")

    def test_links_the_repository_docs_project_md_names(self):
        url = "https://github.com/octo/widgets"
        self.assertEqual(self.manifest["source"], {"repository": url})
        self.assertEqual(self.manifest["settings"]["context_sources"], [
            {"kind": "github_repository", "name": "octo/widgets", "path": "", "url": url},
        ])
        self.assertEqual(self.manifest["settings"]["config"], {"default_source_urls": [url]})
        self.assertEqual(self.manifest["settings"]["visibility"], "private")

    def test_an_override_names_the_repository_instead(self):
        manifest = project_export.manifest(self.root, "acme/gadgets")
        self.assertEqual(manifest["settings"]["config"]["default_source_urls"], ["https://github.com/acme/gadgets"])

    def test_no_repository_links_nothing(self):
        write(self.root, "docs/project.md", "# x\n\n## Repositories\n\n- none yet\n")
        manifest = project_export.manifest(self.root)
        self.assertEqual(manifest["source"], {"repository": ""})
        self.assertEqual(manifest["settings"]["context_sources"], [])
        self.assertEqual(manifest["settings"]["config"], {"default_source_urls": []})

    def test_lists_each_memory_file_with_its_size_and_the_path_it_gets(self):
        self.assertEqual(self.manifest["files"], [
            {"path": "docs/memory/MEMORY.md", "name": "carried-memory/MEMORY.md", "type": "project_memory",
             "bytes": len(INDEX.encode()), "memory_path": "/MEMORY.md"},
            {"path": "docs/memory/a-fact.md", "name": "carried-memory/a-fact.md", "type": "project_memory",
             "bytes": len(FACT.encode()), "memory_path": "/a-fact.md"},
        ])
        self.assertEqual(self.manifest["memory"], {"source": "docs/memory", "files": 2, "beta": False})

    def test_copes_with_a_tree_that_has_none_of_the_files(self):
        with tempfile.TemporaryDirectory() as empty:
            manifest = project_export.manifest(Path(empty))
        self.assertEqual(manifest["name"], Path(empty).name)
        self.assertEqual(manifest["description"], "")
        self.assertEqual(manifest["instructions"], "")
        self.assertEqual(manifest["files"], [])


class Rendering(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.root = Path(self.folder.name)
        project_tree(self.root)

    def tearDown(self):
        self.folder.cleanup()

    def test_the_bytes_are_ascii_lf_and_the_same_twice(self):
        first = project_export.render(self.root)
        self.assertEqual(first, project_export.render(self.root))
        first.decode("ascii")
        self.assertNotIn(b"\r", first)
        self.assertTrue(first.endswith(b"}\n"))
        self.assertEqual(json.loads(first), project_export.manifest(self.root))

    def test_a_non_ascii_memory_file_is_still_rendered_as_ascii(self):
        write(self.root, "docs/project.md", PROJECT.replace("every desk", "every café"))
        rendered = project_export.render(self.root)
        rendered.decode("ascii")
        self.assertEqual(json.loads(rendered)["description"], "A widget for every café.\nDone is a widget on each.")


class WriteAndCheck(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.root = Path(self.folder.name)
        project_tree(self.root)

    def tearDown(self):
        self.folder.cleanup()

    def test_write_then_check_is_quiet_and_a_second_write_changes_nothing(self):
        self.assertTrue(project_export.write(self.root))
        self.assertEqual(project_export.check(self.root), [])
        self.assertFalse(project_export.write(self.root))

    def test_check_names_a_missing_file(self):
        self.assertEqual(project_export.check(self.root), ["export.json: missing; run python3 tools/project_export.py"])

    def test_check_fails_once_a_memory_file_changed(self):
        project_export.write(self.root)
        write(self.root, "docs/memory/a-fact.md", FACT + "A line more.\n")
        self.assertEqual(project_export.check(self.root), [
            "export.json: out of date with the files it lists; run python3 tools/project_export.py",
        ])
        project_export.write(self.root)
        self.assertEqual(project_export.check(self.root), [])

    def test_check_fails_once_a_memory_file_was_added(self):
        project_export.write(self.root)
        write(self.root, "docs/memory/b-fact.md", "Another.\n")
        self.assertEqual(len(project_export.check(self.root)), 1)

    def test_main_writes_and_main_check_exits_1_when_stale(self):
        held = io.StringIO()
        with redirect_stdout(held):
            self.assertEqual(project_export.main(["--root", str(self.root)]), 0)
            self.assertEqual(project_export.main(["--root", str(self.root), "--check"]), 0)
            write(self.root, "docs/memory/a-fact.md", "Changed.\n")
            self.assertEqual(project_export.main(["--root", str(self.root), "--check"]), 1)
            self.assertEqual(project_export.main(["--root", str(self.root)]), 0)
            self.assertEqual(project_export.main(["--root", str(self.root), "--check"]), 0)
        self.assertEqual(held.getvalue().splitlines(), [
            "export.json: written",
            "export.json: out of date with the files it lists; run python3 tools/project_export.py",
            "export.json: written",
        ])


class ThisRepository(unittest.TestCase):
    def test_the_committed_export_json_is_current(self):
        self.assertEqual(project_export.check(ROOT), [])

    def test_every_listed_file_exists_with_the_listed_size(self):
        manifest = json.loads((ROOT / "export.json").read_text(encoding="utf-8"))
        for row in manifest["files"]:
            path = ROOT / row["path"]
            self.assertTrue(path.is_file(), row["path"])
            self.assertEqual(path.stat().st_size, row["bytes"], row["path"])
            self.assertNotIn("..", row["path"])
            self.assertFalse(row["path"].startswith("/"))

    def test_the_memory_index_is_among_the_listed_files(self):
        manifest = json.loads((ROOT / "export.json").read_text(encoding="utf-8"))
        self.assertIn("/MEMORY.md", [row["memory_path"] for row in manifest["files"]])


if __name__ == "__main__":
    unittest.main()
