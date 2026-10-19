"""tools/sync_adopted.py: what each adopted repository is offered, and how."""

import base64
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

import sync_adopted as sync  # noqa: E402

LIB = "the vendored library and its record"
BOARD = "the board's workflow and its script"
TOKEN = "the Token workflow and the scripts it runs"
METRICS = "the metrics workflow and the scripts it runs"
TREE = {
    "tools/VENDORED": ("100644", "v2"), "tools/sdlc_protocol/a.py": ("100644", "l2"),
    ".github/workflows/board.yml": ("100644", "b2"), "tools/board.py": ("100644", "p2"),
    ".github/workflows/metrics.yml": ("100644", "m2"), "tools/metrics.py": ("100644", "n2"),
    ".github/workflows/token.yml": ("100644", "t2"), "tools/token_run.py": ("100755", "r2"),
}
UNITS = [
    (LIB, ["tools/VENDORED", "tools/sdlc_protocol/a.py"], False, False),
    (BOARD, [".github/workflows/board.yml", "tools/board.py"], True, False),
    (METRICS, [".github/workflows/metrics.yml", "tools/metrics.py"], True, False),
    (TOKEN, [".github/workflows/token.yml", "tools/token_run.py"], False, True),
]
HELD = {"tools/VENDORED": {"v1"}, "tools/sdlc_protocol/a.py": {"l1"}, ".github/workflows/board.yml": {"b1"},
        "tools/board.py": {"p1"}, ".github/workflows/metrics.yml": {"m1"}, "tools/metrics.py": {"n1"},
        ".github/workflows/token.yml": {"t1"}, "tools/token_run.py": {"r1"}}


def theirs(**shas):
    """A default branch holding, for each path of TREE, the sha given by the
    path's file name without its extension (board names both of its unit's
    files), None for no file, or the template's own."""
    out = {}
    for rel, (mode, sha) in TREE.items():
        key = Path(rel).stem
        if shas.get(key, "") is None:
            continue
        out[rel] = (mode, shas.get(key, sha), "blob")
    out[sync.PROTOCOL_TEXT] = ("100644", "x", "blob")
    return out


class ThePlan(unittest.TestCase):
    def test_a_current_repository_is_offered_nothing(self):
        self.assertEqual(sync.plan(theirs(), TREE, HELD, UNITS), ({}, []))

    def test_the_token_unit_is_added_where_it_is_missing(self):
        changes, kept = sync.plan(theirs(token=None, token_run=None), TREE, HELD, UNITS)
        self.assertEqual(set(changes), {".github/workflows/token.yml", "tools/token_run.py"})
        self.assertEqual(changes["tools/token_run.py"], ("100755", "r2"))
        self.assertEqual(kept, [])

    def test_a_missing_metrics_workflow_is_never_added(self):
        # the metrics workflow shares aggregates, which only an adoption's switch allows
        changes, _ = sync.plan(theirs(metrics=None), TREE, HELD, UNITS)
        self.assertEqual(changes, {})

    def test_an_old_version_is_replaced(self):
        mine = theirs(VENDORED="v1", a="l1")
        mine[".github/workflows/board.yml"] = ("100644", "b1", "blob")
        changes, _ = sync.plan(mine, TREE, HELD, UNITS)
        self.assertEqual(set(changes), {".github/workflows/board.yml", "tools/VENDORED", "tools/sdlc_protocol/a.py"})

    def test_a_file_of_their_own_holds_its_unit_back_whole(self):
        changes, kept = sync.plan(theirs(token="mine", token_run="r1"), TREE, HELD, UNITS)
        self.assertEqual(changes, {})
        self.assertEqual(kept[0][0], TOKEN)
        self.assertIn(".github/workflows/token.yml", kept[0][1])

    def test_a_module_python_would_find_first_holds_the_unit_back(self):
        units = UNITS[:3] + [(TOKEN, [".github/workflows/token.yml", "tools/token_run.py", "scripts/tokens.py"], False, True)]
        tree = {**TREE, "scripts/tokens.py": ("100644", "k2")}
        mine = theirs(token=None, token_run=None)
        mine["tools/tokens.py"] = ("100644", "mine", "blob")
        changes, kept = sync.plan(mine, tree, HELD, units)
        self.assertEqual(changes, {})
        self.assertIn("tools/tokens.py", kept[0][1])

    def test_a_link_is_theirs(self):
        mine = theirs(token_run="r1")
        mine["tools/token_run.py"] = ("120000", "r1", "blob")
        self.assertEqual(sync.plan(mine, TREE, HELD, UNITS)[0], {})

    def test_the_library_stays_while_a_script_that_imports_it_is_theirs(self):
        changes, kept = sync.plan(theirs(VENDORED="v1", a="l1", board="mine"), TREE, HELD, UNITS)
        self.assertEqual(changes, {})
        self.assertEqual({name for name, _ in kept}, {LIB, BOARD})

    def test_a_script_needing_the_library_waits_for_a_library_that_cannot_come(self):
        mine = theirs(VENDORED="mine")
        mine[".github/workflows/board.yml"] = ("100644", "b1", "blob")
        changes, kept = sync.plan(mine, TREE, HELD, UNITS)
        self.assertNotIn(".github/workflows/board.yml", changes)
        self.assertEqual({name for name, _ in kept}, {LIB, BOARD})

    def test_a_copy_with_its_own_protocol_workflow_keeps_its_library(self):
        mine = theirs(VENDORED="v1", a="l1", token=None, token_run=None)
        mine[".github/workflows/protocol.yml"] = ("100644", "q", "blob")
        changes, kept = sync.plan(mine, TREE, HELD, UNITS)
        self.assertEqual(set(changes), {".github/workflows/token.yml", "tools/token_run.py"})
        self.assertEqual(kept, [])


class FakeGitHub:
    """Answers the calls offer() makes from a small model of one repository."""

    def __init__(self, files, branch=None, pulls=()):
        self.files, self.branch, self.pulls, self.calls = files, branch, list(pulls), []

    def __call__(self, method, url, headers, body):
        path = url[len(sync.API):]
        data = json.loads(body) if body else None
        self.calls.append((method, path, data))
        repo = "/repos/o/r"
        routes = {
            ("GET", f"{repo}/git/ref/heads/main"): (200, {"object": {"sha": "head"}}),
            ("GET", f"{repo}/git/commits/head"): (200, {"tree": {"sha": "base"}}),
            ("GET", f"{repo}/git/trees/base?recursive=1"):
                (200, {"tree": [{"path": p, "mode": m, "sha": s, "type": k} for p, (m, s, k) in self.files.items()]}),
            ("GET", f"{repo}/git/ref/heads/symphony/sync"):
                (200, {"object": {"sha": "tip"}}) if self.branch else (404, {}),
            ("GET", f"{repo}/commits/tip"): (200, self.branch or {}),
            ("POST", f"{repo}/git/blobs"): (201, {"sha": "blob-" + str(len(self.calls))}),
            ("POST", f"{repo}/git/trees"): (201, {"sha": "newtree"}),
            ("POST", f"{repo}/git/commits"): (201, {"sha": "newcommit"}),
            ("POST", f"{repo}/git/refs"): (201, {}),
            ("PATCH", f"{repo}/git/refs/heads/symphony/sync"): (200, {}),
            ("POST", f"{repo}/pulls"): (201, {"number": 9}),
            ("PATCH", f"{repo}/pulls/3"): (200, {}),
        }
        if method == "GET" and path.startswith(f"{repo}/pulls?"):
            return 200, {}, json.dumps(self.pulls).encode()
        status, reply = routes.get((method, path), (599, {"message": "no route"}))
        return status, {}, json.dumps(reply).encode()

    def made(self, method, suffix):
        return [data for m, p, data in self.calls if m == method and p.endswith(suffix)]


REPO = {"full_name": "o/r", "default_branch": "main"}
BOT = "symphonyboard[bot]"


def offer(fake):
    return sync.offer(sync.GitHub("t", fake), REPO, BOT, lambda sha: b"bytes of " + sha.encode(), TREE, HELD, UNITS)


class TheOffer(unittest.TestCase):
    def test_a_repository_missing_the_token_unit_gets_a_pull_request(self):
        fake = FakeGitHub(theirs(token=None, token_run=None))
        self.assertEqual(offer(fake), "offered")
        blobs = fake.made("POST", "/git/blobs")
        self.assertEqual(sorted(base64.b64decode(b["content"]) for b in blobs), [b"bytes of r2", b"bytes of t2"])
        self.assertEqual(fake.made("POST", "/git/refs"), [{"ref": "refs/heads/symphony/sync", "sha": "newcommit"}])
        pull = fake.made("POST", "/pulls")[0]
        self.assertEqual((pull["head"], pull["base"]), ("symphony/sync", "main"))
        self.assertIn(sync.MARK + "newtree -->", pull["body"])

    def test_an_unadopted_repository_is_left_alone(self):
        files = theirs(token=None)
        del files[sync.PROTOCOL_TEXT]
        fake = FakeGitHub(files)
        self.assertEqual(offer(fake), "not adopted")
        self.assertEqual(fake.made("POST", ""), [])

    def test_a_branch_someone_else_pushed_is_not_taken(self):
        fake = FakeGitHub(theirs(token=None, token_run=None), branch={"author": {"login": "someone"}, "committer": {"login": "web-flow"}})
        self.assertEqual(offer(fake), "branch theirs")
        self.assertEqual(fake.made("POST", "/git/blobs"), [])

    def test_a_pull_request_closed_for_the_same_files_is_not_opened_again(self):
        closed = {"state": "closed", "merged_at": None, "number": 2, "body": sync.MARK + "newtree -->\n"}
        fake = FakeGitHub(theirs(token=None, token_run=None), pulls=[closed])
        self.assertEqual(offer(fake), "declined")
        self.assertEqual(fake.made("POST", "/git/commits"), [])

    def test_an_open_pull_request_is_updated_in_place(self):
        tip = {"author": {"login": BOT}, "commit": {"tree": {"sha": "older"}}}
        fake = FakeGitHub(theirs(token=None, token_run=None), branch=tip, pulls=[{"state": "open", "number": 3}])
        self.assertEqual(offer(fake), "updated")
        self.assertEqual(fake.made("PATCH", "/git/refs/heads/symphony/sync"), [{"sha": "newcommit", "force": True}])
        self.assertEqual(fake.made("POST", "/pulls"), [])

    def test_an_opt_out_stops_the_offer(self):
        files = theirs(token=None)
        files[".github/symphony-sync"] = ("100644", "off-blob", "blob")
        fake = FakeGitHub(files)
        original = fake.__call__

        def answer(method, url, headers, body):
            if url.endswith("/git/blobs/off-blob"):
                return 200, {}, json.dumps({"content": base64.b64encode(b"off\n").decode()}).encode()
            return original(method, url, headers, body)
        self.assertEqual(sync.offer(sync.GitHub("t", answer), REPO, BOT, lambda sha: b"", TREE, HELD, UNITS), "opted out")

    def test_the_template_itself_is_never_offered(self):
        own = {"full_name": "OpenSpineConsortium/symphony-template", "default_branch": "main"}
        self.assertEqual(sync.offer(sync.GitHub("t", FakeGitHub({})), own, BOT, None, TREE, HELD, UNITS), "skipped")


class TheTemplate(unittest.TestCase):
    def test_the_token_unit_carries_every_module_its_script_imports(self):
        tree = sync.template_tree()
        found = {name: files for name, files, _, _ in sync.units(tree, lambda rel: sync.git("show", f"HEAD:{rel}"))}
        self.assertEqual(set(found[TOKEN]), {".github/workflows/token.yml", "tools/token_run.py", "tools/sealbox.py",
                                             "scripts/tokens.py", "tools/pool.py"})
        self.assertIn("tools/VENDORED", found[LIB])


if __name__ == "__main__":
    unittest.main()
