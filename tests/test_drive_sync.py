"""tools/drive_sync.py: what each file of a connected drive does in a run,
pulled, pushed, put beside or left waiting, decided from the drive, the
default branch and the last run; a run end to end against a drive kept in
memory, nothing either side wrote lost; and the two providers' calls, a
redirect followed without the token and a drive's name kept to one path
segment."""

import io
import json
import shutil
import sys
import tempfile
import unittest
import urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import drive_sync  # noqa: E402


def entry(version, native=False, rel="a.docx"):
    return {"id": "f1", "rel": rel, "version": version, "native": native}


def record(version, blob, pending=False, base=None, staged=(), rel="a.docx"):
    return {"rel": rel, "version": version, "blob": blob, "pending": pending, "base": base,
            "staged": list(staged)}


class DecideTest(unittest.TestCase):
    def test_each_side_alone(self):
        self.assertEqual(drive_sync.decide(entry("2"), "a", record("1", "a")), "pull")
        self.assertEqual(drive_sync.decide(entry("1"), "b", record("1", "a")), "push")
        self.assertEqual(drive_sync.decide(entry("1"), "a", record("1", "a")), "nothing")
        self.assertEqual(drive_sync.decide(entry("2"), "b", record("1", "a")), "conflict")

    def test_first_sight_and_a_file_the_drive_dropped(self):
        self.assertEqual(drive_sync.decide(entry("1"), None, None), "first")
        self.assertEqual(drive_sync.decide(None, "a", record("1", "a")), "forget")
        self.assertEqual(drive_sync.decide(None, "a", None), "nothing")

    def test_a_pulled_file_waits_for_its_merge_and_is_never_pushed_back(self):
        waiting = record("2", "new", pending=True, base="old")
        self.assertEqual(drive_sync.decide(entry("2"), "old", waiting), "wait")
        self.assertEqual(drive_sync.decide(entry("3"), "old", waiting), "pull")
        self.assertEqual(drive_sync.decide(entry("2"), "other", waiting), "conflict")

    def test_a_copy_staged_once_that_merged_late_is_pulled_over_not_pushed(self):
        self.assertEqual(drive_sync.decide(entry("3"), "b1", record("3", "m0", staged=["b1", "m0"])), "pull")

    def test_a_rename_in_the_drive_moves_the_file_and_keeps_our_revision(self):
        self.assertEqual(drive_sync.decide(entry("1", rel="b.docx"), "a", record("1", "a")), "pull")
        self.assertEqual(drive_sync.decide(entry("1", rel="b.docx"), "ours", record("1", "a")), "conflict")

    def test_a_file_removed_here_is_not_pushed(self):
        self.assertEqual(drive_sync.decide(entry("1"), None, record("1", "a")), "nothing")


class MemoryDrive:
    """A drive kept in memory, with the provider's four calls."""

    def __init__(self, files):
        self.files = dict(files)  # id -> (version, bytes, native), or (version, bytes, native, rel)
        self.beside = {}
        self.reverse = False

    def rel(self, file_id):
        found = self.files[file_id]
        return found[3] if len(found) > 3 else file_id

    def listing(self, items):
        for file_id in sorted(self.files, reverse=self.reverse):
            version, _, native = self.files[file_id][:3]
            yield {"id": file_id, "rel": self.rel(file_id), "version": version, "native": native,
                   "parent": "p", "mime": "m"}

    def download(self, found):
        return self.files[found["id"]][1]

    def upload(self, found, data):
        old = self.files[found["id"]]
        version = str(int(old[0]) + 1)
        self.files[found["id"]] = (version, data, False, *old[3:])
        return version

    def upload_beside(self, found, name, data):
        self.beside[name] = data


class RunTest(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.root)
        (self.root / "papers").mkdir()
        self.config = {"provider": "google", "folder": "papers", "items": [{"id": "x"}]}

    def sync(self, drive, state):
        out = self.root / "staging"
        shutil.rmtree(out, ignore_errors=True)
        summary = drive_sync.run(self.config, state, self.root, out, drive)
        return summary, out / "papers"

    def merge(self, staged):
        for path in staged.rglob("*"):
            if path.is_file():
                target = self.root / "papers" / path.relative_to(staged)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(path.read_bytes())

    def test_the_round_trip_loses_nothing(self):
        drive = MemoryDrive({"a.docx": ("1", b"draft", False)})
        state = {}
        summary, staged = self.sync(drive, state)
        self.assertEqual(summary["pulled"], ["a.docx"])
        summary, staged_again = self.sync(drive, state)
        self.assertEqual(summary["waiting"], ["a.docx"])
        self.merge(staged_again)
        summary, _ = self.sync(drive, state)
        self.assertEqual(sum(map(len, summary.values())), 0)
        (self.root / "papers" / "a.docx").write_bytes(b"revised")
        summary, _ = self.sync(drive, state)
        self.assertEqual(summary["pushed"], ["a.docx"])
        self.assertEqual(drive.files["a.docx"][1], b"revised")
        summary, _ = self.sync(drive, state)
        self.assertEqual(sum(map(len, summary.values())), 0)

    def test_both_sides_changed_puts_ours_beside_theirs(self):
        drive = MemoryDrive({"a.docx": ("1", b"draft", False)})
        state = {}
        _, staged = self.sync(drive, state)
        self.merge(staged)
        self.sync(drive, state)
        (self.root / "papers" / "a.docx").write_bytes(b"ours")
        drive.files["a.docx"] = ("5", b"theirs", False)
        summary, staged = self.sync(drive, state)
        self.assertEqual(drive.beside, {"a (Symphony revisions).docx": b"ours"})
        self.assertEqual((staged / "a.docx").read_bytes(), b"theirs")
        self.assertEqual(summary["beside"], ["a.docx"])

    def test_a_native_google_file_takes_its_revision_beside_it(self):
        drive = MemoryDrive({"g.docx": ("1", b"export", True)})
        state = {}
        _, staged = self.sync(drive, state)
        self.merge(staged)
        self.sync(drive, state)
        (self.root / "papers" / "g.docx").write_bytes(b"revised")
        summary, _ = self.sync(drive, state)
        self.assertEqual(summary["beside"], ["g.docx"])
        self.assertEqual(drive.files["g.docx"][1], b"export")
        self.assertEqual(sum(map(len, self.sync(drive, state)[0].values())), 0)

    def test_a_late_merge_of_an_old_pull_never_overwrites_the_drive(self):
        drive = MemoryDrive({"a.docx": ("1", b"m0", False)})
        state = {}
        _, staged = self.sync(drive, state)
        self.merge(staged)
        self.sync(drive, state)
        drive.files["a.docx"] = ("2", b"b1", False)
        _, old_pull = self.sync(drive, state)
        late = (old_pull / "a.docx").read_bytes()
        drive.files["a.docx"] = ("3", b"m0", False)
        summary, staged = self.sync(drive, state)
        self.assertFalse(staged.exists())
        (self.root / "papers" / "a.docx").write_bytes(late)
        summary, staged = self.sync(drive, state)
        self.assertEqual(summary["pushed"], [])
        self.assertEqual(drive.files["a.docx"][1], b"m0")
        self.assertEqual((staged / "a.docx").read_bytes(), b"m0")

    def test_two_files_of_one_name_keep_their_own_paths_whatever_the_order(self):
        drive = MemoryDrive({"id-a": ("1", b"A", False, "x.docx"), "id-b": ("1", b"B", False, "x.docx")})
        state = {}
        _, first = self.sync(drive, state)
        drive.reverse = True
        self.merge(first)
        summary, _ = self.sync(drive, state)
        self.assertEqual(sum(map(len, summary.values())), 0)
        self.assertEqual((self.root / "papers" / "x.docx").read_bytes(), b"A")

    def test_a_file_seen_first_with_another_copy_here_keeps_ours_beside(self):
        (self.root / "papers" / "a.docx").write_bytes(b"ours")
        drive = MemoryDrive({"a.docx": ("1", b"theirs", False)})
        summary, staged = self.sync(drive, {})
        self.assertEqual(drive.beside, {"a (Symphony revisions).docx": b"ours"})
        self.assertEqual((staged / "a.docx").read_bytes(), b"theirs")

    def test_a_copy_that_cannot_go_beside_still_lets_theirs_come_down(self):
        drive = MemoryDrive({"a.docx": ("1", b"draft", False)})
        state = {}
        _, staged = self.sync(drive, state)
        self.merge(staged)
        self.sync(drive, state)

        def refuse(*args):
            raise drive_sync.DriveError("too big")
        drive.upload_beside = refuse
        (self.root / "papers" / "a.docx").write_bytes(b"ours")
        drive.files["a.docx"] = ("5", b"theirs", False)
        summary, staged = self.sync(drive, state)
        self.assertEqual((staged / "a.docx").read_bytes(), b"theirs")
        self.assertEqual(len(summary["problems"]), 1)

    def test_a_file_already_equal_is_recorded_not_staged(self):
        (self.root / "papers" / "a.docx").write_bytes(b"same")
        summary, staged = self.sync(MemoryDrive({"a.docx": ("1", b"same", False)}), {})
        self.assertEqual(summary["pulled"], [])
        self.assertFalse(staged.exists())


class Answer:
    def __init__(self, body, status=200):
        self.status, self.headers, self.body = status, {}, body

    def read(self):
        return self.body

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class FakeOpener:
    """Answers by URL prefix, and keeps each request for the test to read."""

    def __init__(self, routes):
        self.routes, self.requests = routes, []

    def open(self, request, timeout=None):
        self.requests.append(request)
        for prefix, answer in self.routes:
            if request.full_url.startswith(prefix):
                if isinstance(answer, urllib.error.HTTPError):
                    raise answer
                return Answer(answer if isinstance(answer, bytes) else json.dumps(answer).encode())
        raise AssertionError(f"no route for {request.full_url}")


class ProviderTest(unittest.TestCase):
    def test_google_walks_a_folder_and_names_exports(self):
        opener = FakeOpener([
            ("https://www.googleapis.com/drive/v3/files/root?", {"id": "root", "name": "Paper ../x",
                                                                "mimeType": drive_sync.GOOGLE_FOLDER}),
            ("https://www.googleapis.com/drive/v3/files?q=", {"files": [
                {"id": "d1", "name": "Draft", "mimeType": "application/vnd.google-apps.document", "version": "4",
                 "parents": ["root"]},
                {"id": "f2", "name": "Draft (Symphony revisions).docx", "mimeType": drive_sync.DOCX},
                {"id": "s1", "name": "Shortcut", "mimeType": "application/vnd.google-apps.shortcut"}]}),
            ("https://www.googleapis.com/drive/v3/files/d1/comments", {"comments": []}),
        ])
        found = list(drive_sync.Google("t", opener).listing([{"id": "root"}]))
        self.assertEqual([f["rel"] for f in found], ["Paper .._x/Draft.docx"])
        self.assertTrue(found[0]["native"])
        self.assertTrue(all(r.get_header("Authorization") == "Bearer t" for r in opener.requests))

    def test_a_name_never_leaves_its_folder(self):
        for name in ("..", "../../etc", "a/b", "C:\\x", ".hidden.", ""):
            cleaned = drive_sync.segment(name)
            self.assertNotIn("/", cleaned)
            self.assertNotIn("\\", cleaned)
            self.assertNotIn(cleaned, ("", ".", ".."))

    def test_a_redirect_is_followed_without_the_token(self):
        moved = urllib.error.HTTPError("https://graph.microsoft.com/x", 302, "Found",
                                       {"Location": "https://storage.example/file"}, io.BytesIO(b""))
        opener = FakeOpener([("https://graph.microsoft.com/", moved), ("https://storage.example/", b"bytes")])
        data = drive_sync.Microsoft("t", opener).download({"drive": "d", "id": "i"})
        self.assertEqual(data, b"bytes")
        self.assertIsNone(opener.requests[-1].get_header("Authorization"))

    def test_the_access_token_comes_from_the_sign_in_service(self):
        opener = FakeOpener([("https://signin.example/", {"access_token": "a"})])
        self.assertEqual(drive_sync.access_token("https://signin.example/drive/token", "google", "r", opener), "a")
        self.assertEqual(json.loads(opener.requests[0].data), {"provider": "google", "refresh_token": "r"})


if __name__ == "__main__":
    unittest.main()
