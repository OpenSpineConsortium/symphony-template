"""tools/drive_connector.py: a OneDrive walked from a Claude session's
connector listings into the organizer's catalog, a plan checked against it,
and the plan's moves written for the owner to read, made one connector call
at a time only once approved, and undone back to where each item came from.
Every name here is made up."""

import contextlib
import io
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import drive_connector  # noqa: E402

DRIVE = "b!fakeDriveId-0123456789"


def item(number):
    """A business OneDrive item id: 01 and 32 capitals or digits."""
    return "01" + f"{number:032d}".replace("0", "A")


def listing(*entries):
    """Entries as the connector writes them, one after another with no separator."""
    return "".join(f"{name} ({kind}, {size} bytes) file:///{DRIVE}/{item(n)}" for name, kind, size, n in entries)


TOP = listing(("Budget 2026", "folder", 0, 1), ("Novel", "folder", 0, 2), ("Recordings", "folder", 0, 3),
              ("loose.txt", "file", 12, 4))
BUDGET = listing(("ledger.xlsx", "file", 2048, 11), ("Receipts", "folder", 0, 12))
NOVEL = listing(("chapter 1.docx", "file", 900, 21), ("cover.psd", "file", 5000, 22))
RECEIPTS = listing(("r1.pdf", "file", 300, 31))


def plan(*projects):
    return {"summary": "s", "unsorted": [], "directions": [], "projects": list(projects)}


def project(slug, title, *paths, repository=None):
    found = {"slug": slug, "title": title, "domain": "accounting", "summary": "s", "folders": list(paths),
             "files": [], "directions": ["d"], "plan": "p",
             "tasks": [{"title": "t", "owner": "", "files": [], "body": "b"}]}
    if repository:
        found["repository"] = repository
    return found


class Drive(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.dir)
        self.walk = self.dir / "walk.jsonl"

    def add(self, item_id, text):
        return drive_connector.add(self.walk, item_id, DRIVE, text)

    def walked(self):
        self.add("root", TOP)
        self.add(item(1), BUDGET)
        self.add(item(2), NOVEL)
        self.add(item(12), RECEIPTS)
        return drive_connector.read_walk(self.walk)


class Walk(Drive):
    def test_a_listing_is_read_by_the_shape_of_its_ids(self):
        entries = drive_connector.parse_listing(TOP)
        self.assertEqual([e["name"] for e in entries], ["Budget 2026", "Novel", "Recordings", "loose.txt"])
        self.assertEqual(entries[0]["id"], item(1))
        self.assertEqual((entries[3]["folder"], entries[3]["size"]), (False, 12))

    def test_a_personal_drives_ids_and_a_listing_one_a_line(self):
        text = f"a.docx (file, 5 bytes) file:///{DRIVE}/ABCDEF0123456789!101\nb (folder, 0 bytes) file:///{DRIVE}/ABCDEF0123456789!102"
        self.assertEqual([e["id"] for e in drive_connector.parse_listing(text)],
                         ["ABCDEF0123456789!101", "ABCDEF0123456789!102"])

    def test_an_id_that_runs_into_the_next_name_is_refused(self):
        text = f"a.docx (file, 5 bytes) file:///{DRIVE}/ABCDEF0123456789!1012025 plan.docx (file, 5 bytes) file:///{DRIVE}/ABCDEF0123456789!102"
        with self.assertRaises(drive_connector.ConnectorError):
            drive_connector.parse_listing(text)
        with self.assertRaises(drive_connector.ConnectorError):
            drive_connector.parse_listing(f" (file, 5 bytes) file:///{DRIVE}/{item(1)}")

    def test_unlisted_names_the_next_folders_and_never_the_apps_own(self):
        self.assertEqual(drive_connector.unlisted([])[0]["next"], [{"item": "root", "path": "OneDrive"}])
        self.add("root", TOP)
        status, _ = drive_connector.unlisted(drive_connector.read_walk(self.walk))
        self.assertEqual([e["path"] for e in status["next"]], ["OneDrive/Budget 2026", "OneDrive/Novel"])
        self.assertEqual(status["next"][0]["uri"], f"file:///{DRIVE}/{item(1)}")
        self.assertIn("OneDrive/Recordings: kept by Microsoft 365's apps, not read", status["left"])

    def test_a_folder_is_read_once_and_only_from_the_walk(self):
        self.add("root", TOP)
        self.assertEqual(self.add("root", TOP), 0)
        with self.assertRaises(drive_connector.ConnectorError):
            self.add(item(99), BUDGET)
        with self.assertRaises(drive_connector.ConnectorError):
            self.add(item(1), "not a listing")

    def test_the_catalog_is_the_workflows_with_parents(self):
        made = drive_connector.catalog(self.walked())
        paths = {f["path"] for f in made["files"]}
        self.assertIn("OneDrive/Budget 2026/Receipts/r1.pdf", paths)
        budget = next(f for f in made["folders"] if f["path"] == "OneDrive/Budget 2026")
        self.assertEqual((budget["files"], budget["bytes"]), (2, 2348))
        self.assertEqual(made["parents"][item(12)], item(1))
        self.assertEqual(made["managed"], ["OneDrive/Recordings"])
        self.assertFalse(made["complete"])

    def test_a_search_gives_dates_and_one_link_gives_every_link(self):
        self.walked()
        base = "https://example-my.sharepoint.com/personal/someone_example_edu/Documents"
        search = (json.dumps({"uri": "x", "driveId": DRIVE, "id": item(11), "name": "ledger.xlsx",
                              "webUrl": f"{base}/Budget 2026/ledger.xlsx", "lastModifiedDateTime": "2026-09-01T00:00:00Z"})
                  + json.dumps({"id": "01" + "Z" * 32, "webUrl": "https://elsewhere.example/x"})
                  + json.dumps({"moreResults": True, "nextOffset": 2}))
        self.assertEqual(drive_connector.found(self.walk, search), 1)
        made = drive_connector.catalog(drive_connector.read_walk(self.walk))
        files = {f["path"]: f for f in made["files"]}
        self.assertEqual(files["OneDrive/Budget 2026/ledger.xlsx"]["modified"], "2026-09-01T00:00:00Z")
        self.assertEqual(files["OneDrive/Novel/chapter 1.docx"]["web"], f"{base}/Novel/chapter%201.docx")
        self.assertEqual(files["OneDrive/Novel/chapter 1.docx"]["modified"], "")
        budget = next(f for f in made["folders"] if f["path"] == "OneDrive/Budget 2026")
        self.assertEqual((budget["latest"], budget["web"]), ("2026-09-01T00:00:00Z", f"{base}/Budget%202026"))
        with self.assertRaises(drive_connector.ConnectorError):
            drive_connector.found(self.walk, "not json")

    def test_without_a_search_the_links_are_unknown(self):
        made = drive_connector.catalog(self.walked())
        self.assertEqual({f["web"] for f in made["files"]}, {""})

    def test_check_names_the_paths_the_catalog_lacks(self):
        made = drive_connector.catalog(self.walked())
        self.assertIn("repository is not an object",
                      drive_connector.check(plan(project("b", "B", repository="x")), made)[0]["problems"])
        report = drive_connector.check(plan(project("books", "Books", "OneDrive/Novel", "OneDrive/Nowhere",
                                                    repository={"name": "bad name", "team": True, "why": "w"})),
                                       made)
        self.assertEqual(report[0]["unknown"], ["OneDrive/Nowhere"])
        self.assertIn("a repository name GitHub would refuse", report[0]["problems"])


class Moves(Drive):
    def moves(self, *projects):
        return drive_connector.plan_moves(plan(*projects), drive_connector.catalog(self.walked()))

    def test_each_project_gets_a_folder_and_its_items_move_into_it(self):
        moves = self.moves(project("budget", "Budget: 2026/27", "OneDrive/Budget 2026"),
                           project("novel", "The novel", "OneDrive/Novel/chapter 1.docx"))
        kinds = [(op["op"], op.get("name")) for op in moves["ops"]]
        self.assertEqual(kinds, [("create", "Symphony projects"), ("create", "Budget 2026 27"),
                                 ("move", "Budget 2026"), ("create", "The novel"), ("move", "chapter 1.docx")])
        self.assertEqual(moves["ops"][2]["back"], "root")
        self.assertEqual(moves["ops"][4]["back"], item(2))
        self.assertFalse(moves["approved"])

    def test_what_may_not_move_stays_and_is_said(self):
        moves = self.moves(project("a", "A", "OneDrive", "OneDrive/Recordings", "OneDrive/Budget 2026",
                                   "OneDrive/Budget 2026/ledger.xlsx", "OneDrive/Gone"),
                           project("b", "B", "OneDrive/Budget 2026"))
        moved = [op["path"] for op in moves["ops"] if op["op"] == "move"]
        self.assertEqual(moved, ["OneDrive/Budget 2026"])
        said = " ".join(moves["skipped"])
        for words in ("OneDrive: the drive's top", "OneDrive/Recordings", "moves with the folder that holds it",
                      "OneDrive/Gone: not in the catalog", "named by two projects"):
            self.assertIn(words, said)

    def test_moves_take_only_a_catalog_that_names_parents(self):
        made = drive_connector.catalog(self.walked())
        for key in ("parents", "source"):
            broken = {k: v for k, v in made.items() if k != key}
            with self.assertRaises(drive_connector.ConnectorError):
                drive_connector.plan_moves(plan(project("a", "A", "OneDrive/Novel")), broken)
        made["managed"] = []
        moves = drive_connector.plan_moves(plan(project("a", "A", "OneDrive/Recordings")), made)
        self.assertEqual([op for op in moves["ops"] if op["op"] == "move"], [])

    def test_a_slug_twice_is_planned_once(self):
        moves = self.moves(project("a", "A", "OneDrive/Gone"), project("a", "A again", "OneDrive/Novel"))
        self.assertEqual([op for op in moves["ops"] if op["op"] == "move"], [])

    def test_nothing_is_recorded_done_before_approval_and_undo_keeps_its_progress(self):
        moves = self.moves(project("budget", "Budget", "OneDrive/Budget 2026"))
        with self.assertRaises(drive_connector.ConnectorError):
            drive_connector.done(moves, 0, "HOME1")
        path = self.dir / "moves.json"
        path.write_text(json.dumps(moves))
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(drive_connector.main(["undo", "--moves", str(path)]), 0)
            self.assertEqual(drive_connector.main(["undo", "--moves", str(path)]), 1)

    def test_a_name_twice_in_one_project_is_renamed(self):
        self.add("root", TOP)
        self.add(item(1), listing(("notes.txt", "file", 1, 41)))
        self.add(item(2), listing(("notes.txt", "file", 1, 42)))
        made = drive_connector.catalog(drive_connector.read_walk(self.walk))
        moves = drive_connector.plan_moves(plan(project("n", "Notes", "OneDrive/Budget 2026/notes.txt",
                                                        "OneDrive/Novel/notes.txt")), made)
        self.assertEqual([op["new_name"] for op in moves["ops"] if op["op"] == "move"], ["", "notes (2).txt"])

    def test_nothing_is_called_until_approved_then_one_step_at_a_time(self):
        moves = self.moves(project("budget", "Budget", "OneDrive/Budget 2026"))
        with self.assertRaises(drive_connector.ConnectorError):
            drive_connector.next_call(moves)
        moves["approved"] = True
        call = drive_connector.next_call(moves)
        self.assertEqual(call["tool"], "sharepoint_create_folder")
        self.assertNotIn("parentItemId", call["arguments"])
        with self.assertRaises(drive_connector.ConnectorError):
            drive_connector.done(moves, 0)
        drive_connector.done(moves, 0, "HOME1")
        self.assertEqual(drive_connector.next_call(moves)["arguments"]["parentItemId"], "HOME1")
        drive_connector.done(moves, 1, "PROJ1")
        call = drive_connector.next_call(moves)
        self.assertEqual(call["arguments"], {"driveId": DRIVE, "itemId": item(1), "destinationParentItemId": "PROJ1"})
        drive_connector.done(moves, 2)
        self.assertIsNone(drive_connector.next_call(moves))

    def test_undo_moves_back_what_moved_and_deletes_nothing(self):
        self.add("root", TOP)
        self.add(item(1), listing(("notes.txt", "file", 1, 41)))
        self.add(item(2), listing(("notes.txt", "file", 1, 42)))
        made = drive_connector.catalog(drive_connector.read_walk(self.walk))
        moves = drive_connector.plan_moves(plan(project("n", "Notes", "OneDrive/Budget 2026/notes.txt",
                                                        "OneDrive/Novel/notes.txt")), made)
        moves["approved"] = True
        drive_connector.done(moves, 0, "HOME1")
        drive_connector.done(moves, 1, "PROJ1")
        drive_connector.done(moves, 2)
        drive_connector.done(moves, 3)
        back = drive_connector.undo(moves)
        self.assertEqual([(op["item"], op["to"], op["new_name"]) for op in back["ops"]],
                         [(item(42), item(2), "notes.txt"), (item(41), item(1), "")])
        self.assertFalse(back["approved"])
        self.assertEqual(len(back["skipped"]), 2)
        self.assertNotIn("delete", json.dumps(back["ops"]))
        self.assertIn("the folder it came from", drive_connector.moves_markdown(back))

    def test_the_command_line_writes_the_review_and_refuses_unapproved(self):
        self.walked()
        out = self.dir / "out"
        plan_path = self.dir / "plan.json"
        plan_path.write_text(json.dumps(plan(project("budget", "Budget", "OneDrive/Budget 2026"))))
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()) as err:
            self.assertEqual(drive_connector.main(["catalog", "--walk", str(self.walk), "--out", str(out)]), 0)
            self.assertEqual(drive_connector.main(["moves", "--plan", str(plan_path), "--catalog",
                                                   str(out / "catalog.json"), "--out", str(out)]), 0)
            self.assertEqual(drive_connector.main(["next", "--moves", str(out / "moves.json")]), 1)
        self.assertIn("not approved", err.getvalue())
        self.assertIn("move `OneDrive/Budget 2026` to `Symphony projects/Budget/`", (out / "MOVES.md").read_text())
        self.assertTrue((out / "TREE.md").exists())


if __name__ == "__main__":
    unittest.main()
