"""tools/public_export.py publishes exactly what .github/symphony/public.json
lists: the check refuses a manifest that names no file, leaves a repository
or publishes a private path; apply makes the target's owned paths hold the
stage and leaves everything else there alone; a copy of the repository
plans no export; and only the listed files of an importable export come
back. The committed manifest holds together."""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import public_export  # noqa: E402

GIT = dict(os.environ, GIT_CONFIG_GLOBAL="/dev/null", GIT_CONFIG_NOSYSTEM="1")


def repository(files):
    root = Path(tempfile.mkdtemp())
    for name, text in files.items():
        (root / name).parent.mkdir(parents=True, exist_ok=True)
        (root / name).write_text(text)
    subprocess.run(["git", "init", "--quiet", str(root)], check=True, env=GIT)
    subprocess.run(["git", "-C", str(root), "add", "-A"], check=True, env=GIT)
    return root


def export(**fields):
    made = {"name": "docs", "source": "o/private", "repository": "o/public",
            "files": [{"from": "guide/", "to": "docs/"}]}
    made.update(fields)
    return made


class Check(unittest.TestCase):
    files = ["guide/a.md", "secret/key.md", "README.md"]

    def test_a_sound_manifest_has_no_problems(self):
        self.assertEqual(public_export.problems({"private": ["secret/*"], "exports": [export()]}, self.files), [])

    def test_a_private_path_is_refused(self):
        bad = export(files=[{"from": "secret/", "to": "x/"}])
        self.assertIn("secret/key.md is private", "\n".join(public_export.problems({"private": ["secret/*"], "exports": [bad]}, self.files)))

    def test_paths_that_leave_or_name_nothing_are_refused(self):
        found = "\n".join(public_export.problems({"exports": [
            export(files=[{"from": "../up/", "to": "docs/"}]),
            export(name="other", files=[{"from": "gone.md", "to": "gone.md"}])]}, self.files))
        self.assertIn("must both stay inside", found)
        self.assertIn("gone.md names no tracked file", found)

    def test_a_build_needs_owns_and_names_are_unique(self):
        found = "\n".join(public_export.problems({"exports": [export(build="true"), export()]}, self.files))
        self.assertIn("a build needs owns", found)
        self.assertIn("a second export of that name", found)

    def test_the_committed_manifest_holds_together(self):
        self.assertEqual(public_export.problems(public_export.load(), public_export.tracked(ROOT)), [])


class Publishing(unittest.TestCase):
    def test_apply_replaces_owned_paths_and_leaves_the_rest(self):
        here = repository({"guide/a.md": "new a\n", "secret/key.md": "k\n"})
        there = repository({"docs/a.md": "old a\n", "docs/stale.md": "s\n", "README.md": "theirs\n"})
        out = Path(tempfile.mkdtemp())
        chosen = export()
        self.assertEqual(public_export.stage(chosen, out, root=here), ["docs/a.md"])
        public_export.apply(chosen, out, there)
        self.assertEqual((there / "docs/a.md").read_text(), "new a\n")
        self.assertFalse((there / "docs/stale.md").exists())
        self.assertEqual((there / "README.md").read_text(), "theirs\n")
        self.assertFalse((there / "secret").exists())

    def test_a_build_writes_into_the_stage(self):
        here = repository({"x.txt": "x\n"})
        out = Path(tempfile.mkdtemp())
        made = export(files=[], build='mkdir -p "$EXPORT_DIR/gen" && echo hi > "$EXPORT_DIR/gen/n.txt"', owns=["gen/*"])
        self.assertEqual(public_export.stage(made, out, root=here), ["gen/n.txt"])

    def test_a_copy_plans_nothing(self):
        manifest = Path(tempfile.mkdtemp()) / "public.json"
        manifest.write_text(json.dumps({"exports": [export()]}))
        for repo, count in (("o/private", 1), ("someone/copy", 0)):
            done = subprocess.run([sys.executable, "-c",
                                   f"import sys; sys.path.insert(0, {str(ROOT / 'tools')!r}); import public_export as p; "
                                   f"from pathlib import Path; p.MANIFEST = Path({str(manifest)!r}); p.main(['plan'])"],
                                  capture_output=True, text=True, env=dict(os.environ, GITHUB_REPOSITORY=repo))
            self.assertEqual(len(json.loads(done.stdout)), count, done.stderr)


class Symlinks(unittest.TestCase):
    def test_a_tracked_symlink_is_never_published(self):
        here = repository({"guide/a.md": "a\n", "secret.md": "private\n"})
        (here / "guide/link.md").symlink_to(here / "secret.md")
        subprocess.run(["git", "-C", str(here), "add", "-A"], check=True, env=GIT)
        with self.assertRaises(SystemExit):
            public_export.stage(export(), Path(tempfile.mkdtemp()), root=here)

    def test_a_symlink_in_the_target_is_never_written_through_or_read(self):
        outside = Path(tempfile.mkdtemp()) / "runner-file"
        outside.write_text("secret\n")
        there = repository({"docs/a.md": "x\n"})
        (there / "docs/a.md").unlink()
        (there / "docs/a.md").symlink_to(outside)
        subprocess.run(["git", "-C", str(there), "add", "-A"], check=True, env=GIT)
        here = repository({"guide/a.md": "mine\n"})
        out = Path(tempfile.mkdtemp())
        public_export.stage(export(), out, root=here)
        with self.assertRaises(SystemExit):
            public_export.apply(export(), out, there)
        self.assertEqual(outside.read_text(), "secret\n")
        with self.assertRaises(SystemExit):
            public_export.take_back(export(**{"import": True}), there, root=here)
        self.assertEqual((here / "guide/a.md").read_text(), "mine\n")


class Importing(unittest.TestCase):
    def test_only_listed_files_of_an_importable_export_come_back(self):
        here = repository({"guide/a.md": "mine\n", "README.md": "private readme\n"})
        there = repository({"docs/a.md": "improved\n", "README.md": "public readme\n"})
        self.assertEqual(public_export.take_back(export(), there, root=here), [])
        self.assertEqual(public_export.take_back(export(**{"import": True}), there, root=here), ["guide/a.md"])
        self.assertEqual((here / "guide/a.md").read_text(), "improved\n")
        self.assertEqual((here / "README.md").read_text(), "private readme\n")


if __name__ == "__main__":
    unittest.main()
