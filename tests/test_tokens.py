"""scripts/tokens.py stores a Claude account's subscription token as an
Actions secret without the token reaching the screen, a command line, a
file or a log: claude setup-token runs behind a pseudo-terminal whose
output is masked, the token goes to gh on a pipe, and GitHub's own listing
is read back by name. No test has a signed-in gh, a browser or claude: a
fake gh on PATH, or in the process (tests/fake_gh.py), answers the calls
and records them, and a fake claude prints the sign-in's screens with a
token built here from pieces, so this file never holds one."""

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
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import check_docs  # noqa: E402
import fake_gh  # noqa: E402
import tokens  # noqa: E402
from fake_gh import answer  # noqa: E402

SCRIPT = ROOT / "scripts" / "tokens.py"
ORG = "octo"
REPO = "widgets"
# A stand-in token in the shape claude setup-token prints, built from pieces
# as tools/check_docs.py builds its own shapes, so no line here is one.
TOKEN = "sk-" + "ant-" + "oat01-" + "A" * 40 + "_" + "b" * 39 + "-Zz"
OTHER = "sk-" + "ant-" + "oat01-" + "C" * 60 + "-Qq"
API_KEY = "sk-" + "ant-" + "api03-" + "k" * 60 + "AA"
SCOPES_LINE = "  Token scopes: 'admin:org', 'gist', 'read:org', 'repo', 'workflow'\n"
SIGNED_IN = "github.com\n  Logged in to github.com account greg (keyring)\n  Active account: true\n" + SCOPES_LINE
CROWD_OFF = "# Project\n\n## Crowd mode\n\n- Crowd mode: off. Nobody has run setup.\n"
OLD = "2026-01-10T10:00:00Z"
NEW = "2026-10-16T01:00:00Z"
# What the fake claude prints: the screens of a real sign-in as the binary's
# strings give them, with an escape code around the token and a redraw, as
# Ink does, and the token twice, once on its own line and once in the
# export line.
FAKE_CLAUDE = '''
import json, os, sys
token = {token!r}
w = sys.stdout.write
w("\\x1b[?25lThis will guide you through long-lived (1-year) auth token setup for your Claude account.\\n")
w("Claude subscription required.\\n\\nBrowser didn't open? Use the url below to sign in (ctrl/cmd + click):\\n\\n")
w("https://claude.ai/oauth/authorize?code=true&client_id=abc\\n\\nPaste code here if prompted > ")
sys.stdout.flush()
code = sys.stdin.readline().strip()
for _ in range(2):
    w("\\n\\x1b[2K\\x1b[1A\\x1b[2K\\r\\x1b[32mLong-lived authentication token created successfully!\\x1b[39m\\n\\n")
    w("Your OAuth token (valid for 1 year):\\n\\n\\x1b[1m" + token + "\\x1b[22m\\n\\n")
    w("Store this token securely. You won't be able to see it again.\\n\\n")
    w("Use this token by setting: export CLAUDE_CODE_OAUTH_TOKEN=" + token + "\\n")
    sys.stdout.flush()
w("\\x1b[?25h")
sys.stdout.flush()
columns = os.get_terminal_size(1).columns if sys.stdout.isatty() else None
with open(os.environ["FAKE_CLAUDE_REPORT"], "w") as handle:
    json.dump({{"code": code, "columns": columns, "tty": sys.stdout.isatty()}}, handle)
'''


def read_json(path):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def secret(name, updated=OLD, visibility="selected", selected=1):
    return {"name": name, "updatedAt": updated, "visibility": visibility, "numSelectedRepos": selected}


def variable(name, value, updated=OLD, visibility="selected", selected=1):
    found = secret(name, updated, visibility, selected)
    found["value"] = value
    return found


def install_claude(folder, token=TOKEN):
    """The fake claude, first on PATH, that prints a sign-in's screens."""
    bin_dir = Path(folder) / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    claude = bin_dir / "claude"
    claude.write_text(f"#!{sys.executable} -IS\n" + FAKE_CLAUDE.format(token=token), encoding="utf-8")
    claude.chmod(0o755)
    return bin_dir


def code_pipe(text="thecode\n"):
    """A pipe standing for the keyboard, with the code already typed."""
    reader, writer = os.pipe()
    os.write(writer, text.encode())
    os.close(writer)
    return reader


class Collector:
    def __init__(self):
        self.text = ""

    def __call__(self, text):
        self.text += text


def has_token(text):
    return tokens.TOKEN_SHAPE.search(text) is not None


class World:
    """A fake gh for one organization with one repository, with the secrets
    and variables given, where every write is answered and a store shows in
    the next listing with a later date."""

    def __init__(self, test, secrets=(), variables=(), stored=NEW, scopes=SCOPES_LINE, crowd=None):
        self.folder = tempfile.mkdtemp(prefix="tokens-")
        test.addCleanup(shutil.rmtree, self.folder, ignore_errors=True)
        self.secrets, self.variables = list(secrets), list(variables)
        self.stored = stored
        self.report = None
        # A copy of the template runs these tests too (tests/test_filled_copy.py),
        # a crowd copy among them, where the clone's own docs/project.md says
        # crowd mode is on and the wizard refuses; the tests read a project
        # file of their own that says off.
        self.project = Path(self.folder) / "docs" / "project.md"
        self.project.parent.mkdir(parents=True, exist_ok=True)
        self.project.write_text(CROWD_OFF, encoding="utf-8")
        self.log = str(Path(self.folder) / "gh-log.jsonl")
        self.routes_file = str(Path(self.folder) / "routes.json")
        status = SIGNED_IN.replace(SCOPES_LINE, scopes)
        routes = {
            "auth status": [answer(200, status)],
            f"GET users/{ORG}": [answer(200, "Organization\n")],
            f"GET repos/{ORG}/{REPO}/actions/variables/{tokens.CROWD_VARIABLE}": [
                answer(404, {"message": "Not Found"}) if crowd is None else answer(200, crowd + "\n")],
            f"GET repos/{ORG}/other/actions/variables/{tokens.CROWD_VARIABLE}": [answer(404, {"message": "Not Found"})],
            "secret list": [answer(200, self.secrets)],
            "variable list": [answer(200, self.variables)],
            "secret set": [answer(200, "", after=self.after_store())],
            "variable set": [answer(200, "")],
            "secret delete": [answer(200, "")],
            "variable delete": [answer(200, "")],
        }
        # Every selected secret or variable reaches the one repository.
        names = [tokens.slot_secret(slot) for slot in tokens.SLOTS] + [tokens.MAIN_SECRET]
        names += [tokens.slot_label(slot) for slot in tokens.SLOTS] + [tokens.ACCOUNTS_VARIABLE]
        for kind in ("secrets", "variables"):
            for name in names:
                routes[f"GET orgs/{ORG}/actions/{kind}/{name}/repositories"] = [answer(200, REPO + "\n")]
        fake_gh.write_routes(self.routes_file, routes)
        self.environment = fake_gh.environment(self.folder, routes)

    def after_store(self):
        """The listing once a store happened: every slot and the main secret
        listed, with the store's date on the ones the test stores."""
        listed = {item["name"]: dict(item) for item in self.secrets}
        for slot in tokens.SLOTS:
            listed.setdefault(tokens.slot_secret(slot), None)
        listed.setdefault(tokens.MAIN_SECRET, None)
        names = [name for name, item in listed.items() if item is not None or name in self.will_store()]
        found = [listed[name] if listed[name] is not None and name not in self.will_store() else secret(name, self.stored)
                 for name in names]
        return {"secret list": [answer(200, found)]}

    def will_store(self):
        return getattr(self, "storing", ())

    def expect_store(self, *names):
        """The names a store will add to the listing; set before the run."""
        self.storing = names
        routes = read_json(self.routes_file)
        routes["secret set"] = [answer(200, "", after=self.after_store())]
        fake_gh.write_routes(self.routes_file, routes)

    def run_in_process(self, test, function, *args, **options):
        """A command in this process against the fake, with the fake claude
        on PATH and a pipe for the keyboard: (printed text, the calls)."""
        bin_dir = install_claude(self.folder)
        report = str(Path(self.folder) / "claude-report.json")
        collector = Collector()
        printed = io.StringIO()
        environ = {"PATH": str(bin_dir) + os.pathsep + os.environ.get("PATH", ""), "FAKE_CLAUDE_REPORT": report}
        run = fake_gh.routed_run(subprocess.run, self.log, self.routes_file)
        with patch.dict(os.environ, environ), patch.object(tokens.subprocess, "run", run), \
                patch.object(tokens, "PROJECT", self.project), redirect_stdout(printed):
            reader = code_pipe()
            try:
                result = function(*args, write=collector, stdin_fd=reader, **options)
            finally:
                os.close(reader)
        self.report = read_json(report) if os.path.exists(report) else None
        return result, printed.getvalue() + collector.text, fake_gh.calls(self.log)

    def calls(self):
        return fake_gh.calls(self.log)


def target(repos=(REPO,), visibility="selected"):
    return tokens.Target("org", ORG, repos, visibility)


def call_keys(calls):
    return [call["key"] for call in calls]


def find(calls, key, name=None):
    return [call for call in calls if call["key"] == key and (name is None or name in call["args"])]


class TheMask(unittest.TestCase):
    """What claude prints reaches the screen with the token taken out,
    however the output is cut into pieces."""

    FRAME = ("\x1b[?25lYour OAuth token (valid for 1 year):\n\n\x1b[1m" + TOKEN + "\x1b[22m\n\n"
             "Store this token securely.\n\nUse this token by setting: export CLAUDE_CODE_OAUTH_TOKEN=" + TOKEN + "\n\x1b[?25h")

    def masked(self, text, size):
        masker = tokens.Masker()
        out = "".join(masker.feed(text[i:i + size]) for i in range(0, len(text), size))
        out += masker.feed("", final=True)
        return out, masker.tokens

    def test_the_token_never_reaches_the_screen_at_any_chunk_size(self):
        for size in list(range(1, 48)) + [64, 100, 1000]:
            out, found = self.masked(self.FRAME, size)
            self.assertEqual(found, [TOKEN], size)
            self.assertNotIn(TOKEN, out, size)
            self.assertFalse(has_token(out), size)
            self.assertEqual(out.count(tokens.MASK), 2, size)
            # Everything else is on the screen as claude printed it; where
            # the token came one character at a time, its first "s" was
            # on the screen before the mask took the rest.
            self.assertEqual(re.sub("s?" + re.escape(tokens.MASK), TOKEN, out), self.FRAME, size)

    def test_two_different_tokens_are_both_kept(self):
        out, found = self.masked("a " + TOKEN + " b " + OTHER + " c", 7)
        self.assertEqual(found, [TOKEN, OTHER])
        self.assertFalse(has_token(out))

    def test_text_that_only_looks_like_a_start_comes_through_whole(self):
        text = "task desk sk- sk-ant sk-ant-oat sk-ant-oatmeal and more\n"
        for size in (1, 3, 5, 100):
            out, found = self.masked(text, size)
            self.assertEqual(out, text, size)
            self.assertEqual(found, [], size)

    def test_a_tail_held_back_is_printed_at_the_end(self):
        masker = tokens.Masker()
        first = masker.feed("ready sk-")
        self.assertEqual(first, "ready ")
        self.assertEqual(masker.feed("", final=True), "sk-")

    def test_the_mask_is_no_secret_shape(self):
        for name, pattern in check_docs.SECRET_PATTERNS:
            self.assertIsNone(pattern.search(tokens.MASK), name)
        self.assertIsNone(tokens.TOKEN_SHAPE.search(tokens.MASK))


class TheMint(unittest.TestCase):
    """claude setup-token behind the pseudo-terminal: the keyboard goes
    through, the terminal is wide, and the token comes back unseen."""

    def test_the_sign_in_runs_on_a_wide_terminal_and_the_token_comes_back_masked(self):
        folder = tempfile.mkdtemp(prefix="tokens-mint-")
        self.addCleanup(shutil.rmtree, folder, ignore_errors=True)
        bin_dir = install_claude(folder)
        report = str(Path(folder) / "report.json")
        collector = Collector()
        reader = code_pipe()
        with patch.dict(os.environ, {"FAKE_CLAUDE_REPORT": report}):
            try:
                found, status = tokens.mint(stdin_fd=reader, write=collector, command=(str(bin_dir / "claude"), "setup-token"))
            finally:
                os.close(reader)
        self.assertEqual(found, [TOKEN])
        self.assertEqual(status, 0)
        seen = read_json(report)
        self.assertEqual(seen["code"], "thecode")
        self.assertTrue(seen["tty"])
        self.assertEqual(seen["columns"], tokens.TERMINAL_SIZE[1])
        self.assertNotIn(TOKEN, collector.text)
        self.assertFalse(has_token(collector.text))
        self.assertIn("Paste code here if prompted", collector.text)
        self.assertIn(tokens.MASK, collector.text)

    def test_a_claude_that_prints_no_token_is_reported_not_stored(self):
        folder = tempfile.mkdtemp(prefix="tokens-mint-")
        self.addCleanup(shutil.rmtree, folder, ignore_errors=True)
        bin_dir = Path(folder) / "bin"
        bin_dir.mkdir()
        claude = bin_dir / "claude"
        claude.write_text(f"#!{sys.executable} -IS\nimport sys\nsys.stdout.write('nothing today\\n')\nsys.exit(3)\n")
        claude.chmod(0o755)
        collector = Collector()
        reader = code_pipe("")
        try:
            with self.assertRaises(tokens.TokensError) as caught:
                tokens.minted_token(stdin_fd=reader, write=collector, command=(str(claude), "setup-token"))
        finally:
            os.close(reader)
        self.assertIn("exit 3", str(caught.exception))
        self.assertIn("--paste", str(caught.exception))

    def test_a_claude_that_is_not_there_is_named(self):
        collector = Collector()
        reader = code_pipe("")
        try:
            with self.assertRaises(tokens.TokensError) as caught:
                tokens.minted_token(stdin_fd=reader, write=collector, command=("/nonexistent/claude", "setup-token"))
        finally:
            os.close(reader)
        self.assertIn("could not be started", str(caught.exception))


class ThePaste(unittest.TestCase):
    def test_the_token_is_taken_out_of_what_was_pasted(self):
        self.assertEqual(tokens.check_token(TOKEN), TOKEN)
        self.assertEqual(tokens.check_token("export CLAUDE_CODE_OAUTH_TOKEN=" + TOKEN), TOKEN)
        self.assertEqual(tokens.pasted_token(ask=lambda prompt: "  " + TOKEN + "\n"), TOKEN)

    def test_an_api_key_is_refused(self):
        with self.assertRaises(tokens.TokensError) as caught:
            tokens.check_token(API_KEY)
        self.assertIn("API key", str(caught.exception))

    def test_anything_else_is_refused(self):
        for text in ("", "hello", "ghp_" + "x" * 40, TOKEN + " " + OTHER):
            with self.assertRaises(tokens.TokensError):
                tokens.check_token(text)


class Adding(unittest.TestCase):
    """add: the token minted behind the terminal goes to gh on its standard
    input, under the slot's name, with the place's visibility; the label and
    the list of slots follow; GitHub's listing is read back."""

    def test_a_new_slot_at_the_organization(self):
        world = World(self, secrets=[secret(tokens.slot_secret(1))])
        world.expect_store(tokens.slot_secret(2))
        state, printed, calls = world.run_in_process(self, tokens.add, tokens.Gh(), target(), None, "work", False, False)
        stores = find(calls, "secret set")
        self.assertEqual(len(stores), 1)
        self.assertEqual(stores[0]["stdin"], TOKEN)
        self.assertEqual(stores[0]["args"], ["secret", "set", tokens.slot_secret(2), "--org", ORG, "--visibility", "selected", "--repos", REPO])
        labels = find(calls, "variable set", tokens.slot_label(2))
        self.assertEqual(labels[0]["args"][-2:], ["--body", "work"])
        accounts = find(calls, "variable set", tokens.ACCOUNTS_VARIABLE)
        self.assertEqual(accounts[0]["args"][-2:], ["--body", "1,2"])
        self.assertEqual(world.report["code"], "thecode")
        self.assertNotIn(TOKEN, printed)
        self.assertFalse(has_token(printed))
        for call in calls:
            self.assertFalse(any(TOKEN in arg for arg in call["args"]), call["args"])
        self.assertIn("GitHub lists it", printed)
        self.assertIn(tokens.slot_secret(2), state.secrets)

    def test_a_slot_that_exists_keeps_its_list_and_grows_it(self):
        world = World(self, secrets=[secret(tokens.slot_secret(1))], variables=[variable(tokens.ACCOUNTS_VARIABLE, "1")])
        world.expect_store(tokens.slot_secret(1))
        _, printed, calls = world.run_in_process(self, tokens.add, tokens.Gh(), target(repos=("other",)), 1, "", False, False)
        store = find(calls, "secret set")[0]
        self.assertEqual(store["args"][-2:], ["--repos", "other,widgets"])
        self.assertIn("replaces it", printed)
        # The list of slots did not change, so it was not written.
        self.assertEqual(find(calls, "variable set", tokens.ACCOUNTS_VARIABLE), [])
        self.assertIn("unchanged", printed)

    def test_also_main_stores_the_same_token_under_the_workflows_name(self):
        world = World(self)
        world.expect_store(tokens.slot_secret(1), tokens.MAIN_SECRET)
        _, printed, calls = world.run_in_process(self, tokens.add, tokens.Gh(), target(), None, "", True, False)
        stores = find(calls, "secret set")
        self.assertEqual([call["args"][2] for call in stores], [tokens.slot_secret(1), tokens.MAIN_SECRET])
        self.assertEqual({call["stdin"] for call in stores}, {TOKEN})
        self.assertEqual(find(calls, "variable set", tokens.ACCOUNTS_VARIABLE)[0]["args"][-2:], ["--body", "1"])

    def test_a_pasted_token_goes_the_same_way(self):
        world = World(self)
        world.expect_store(tokens.slot_secret(1))
        _, printed, calls = world.run_in_process(self, tokens.add, tokens.Gh(), target(), None, "", False, True,
                                                 ask=lambda prompt: TOKEN)
        self.assertEqual(find(calls, "secret set")[0]["stdin"], TOKEN)
        self.assertIsNone(world.report, "claude did not run")

    def test_a_pasted_api_key_stores_nothing(self):
        world = World(self)
        with self.assertRaises(tokens.TokensError):
            world.run_in_process(self, tokens.add, tokens.Gh(), target(), None, "", False, True, ask=lambda prompt: API_KEY)
        self.assertEqual(find(world.calls(), "secret set"), [])

    def test_a_store_github_does_not_list_is_an_error(self):
        world = World(self)
        _, printed, calls = (None, "", [])
        with self.assertRaises(tokens.TokensError) as caught:
            world.run_in_process(self, tokens.add, tokens.Gh(), target(), None, "", False, False)
        self.assertIn("does not list", str(caught.exception))

    def test_a_label_is_a_word_not_an_address(self):
        world = World(self)
        for label in ("me@example.org", "x" * 41, "-dash", "a\tb"):
            with self.assertRaises(tokens.TokensError):
                world.run_in_process(self, tokens.add, tokens.Gh(), target(), None, label, False, False)
        self.assertEqual(find(world.calls(), "secret set"), [])

    def test_the_repository_level_names_no_visibility(self):
        world = World(self)
        world.expect_store(tokens.slot_secret(1))
        place = tokens.Target("repo", ORG, name=REPO)
        _, printed, calls = world.run_in_process(self, tokens.add, tokens.Gh(), place, None, "", False, False)
        self.assertEqual(find(calls, "secret set")[0]["args"], ["secret", "set", tokens.slot_secret(1), "--repo", f"{ORG}/{REPO}"])
        self.assertEqual(find(calls, "variable set", tokens.ACCOUNTS_VARIABLE)[0]["args"][:5],
                         ["variable", "set", tokens.ACCOUNTS_VARIABLE, "--repo", f"{ORG}/{REPO}"])


class CrowdMode(unittest.TestCase):
    """A crowd repository holds no Claude token: the clone's mode line and
    the repository's variable each stop the wizard before any write."""

    def test_the_clone_s_mode_line_refuses(self):
        folder = tempfile.mkdtemp(prefix="tokens-crowd-")
        self.addCleanup(shutil.rmtree, folder, ignore_errors=True)
        project = Path(folder) / "project.md"
        project.write_text("# P\n\n## Crowd mode\n\n- Crowd mode: on. Set up 2026-10-01.\n")
        with self.assertRaises(tokens.TokensError) as caught:
            tokens.refuse_crowd(tokens.Gh(), target(), project=project)
        self.assertIn("crowd mode is on", str(caught.exception))

    def test_the_repository_s_variable_refuses_before_any_store(self):
        world = World(self, crowd="TRUE")
        with self.assertRaises(tokens.TokensError) as caught:
            world.run_in_process(self, tokens.add, tokens.Gh(), target(), None, "", False, False)
        self.assertIn("crowd mode", str(caught.exception))
        self.assertEqual(find(world.calls(), "secret set"), [])
        self.assertIsNone(world.report, "claude did not run")


class Status(unittest.TestCase):
    def test_the_state_is_names_dates_and_counts(self):
        world = World(self, secrets=[secret(tokens.slot_secret(1)), secret(tokens.slot_secret(3), NEW), secret(tokens.MAIN_SECRET, OLD, "all", 0)],
                      variables=[variable(tokens.slot_label(1), "greg"), variable(tokens.ACCOUNTS_VARIABLE, "1, 3")])
        run = fake_gh.routed_run(subprocess.run, world.log, world.routes_file)
        printed = io.StringIO()
        with patch.object(tokens.subprocess, "run", run), redirect_stdout(printed):
            tokens.print_status(tokens.State(tokens.Gh(), target()), now=datetime(2026, 10, 16, tzinfo=timezone.utc))
        text = printed.getvalue()
        self.assertIn(f"slot 1 (greg): {tokens.slot_secret(1)} set 2026-01-10, renew by 2027-01-10, seen by {REPO}", text)
        self.assertIn(f"slot 3: {tokens.slot_secret(3)} set 2026-10-16, renew by 2027-10-16", text)
        self.assertIn("free slots: 2, 4, 5, 6, 7, 8", text)
        self.assertIn(f"{tokens.ACCOUNTS_VARIABLE}: 1,3", text)
        self.assertIn(f"{tokens.MAIN_SECRET}: set 2026-01-10, renew by 2027-01-10 (the workflows' token)", text)

    def test_an_old_token_is_told_to_renew(self):
        now = datetime(2027, 2, 1, tzinfo=timezone.utc)
        self.assertIn("renew now", tokens.age_line(secret("x", OLD), now))
        self.assertIn("renew soon", tokens.age_line(secret("x", OLD), datetime(2026, 12, 20, tzinfo=timezone.utc)))
        self.assertNotIn("renew now", tokens.age_line(secret("x", NEW), now))

    def test_a_repository_s_own_secret_is_shown_as_outranking(self):
        world = World(self, secrets=[secret(tokens.MAIN_SECRET, OLD, "all", 0)])
        routes = read_json(world.routes_file)
        routes["secret list"] = [answer(200, world.secrets), answer(200, [{"name": tokens.MAIN_SECRET, "updatedAt": NEW}])]
        fake_gh.write_routes(world.routes_file, routes)
        run = fake_gh.routed_run(subprocess.run, world.log, world.routes_file)
        printed = io.StringIO()
        with patch.object(tokens.subprocess, "run", run), redirect_stdout(printed):
            tokens.print_status(tokens.State(tokens.Gh(), target()))
        self.assertIn(f"{ORG}/{REPO} holds its own {tokens.MAIN_SECRET}", printed.getvalue())


class Removing(unittest.TestCase):
    def test_the_secret_and_the_label_go_and_the_list_follows(self):
        world = World(self, secrets=[secret(tokens.slot_secret(1)), secret(tokens.slot_secret(2))],
                      variables=[variable(tokens.slot_label(2), "work"), variable(tokens.ACCOUNTS_VARIABLE, "1,2")])
        routes = read_json(world.routes_file)
        routes["secret delete"] = [answer(200, "", after={"secret list": [answer(200, [secret(tokens.slot_secret(1))])]})]
        fake_gh.write_routes(world.routes_file, routes)
        run = fake_gh.routed_run(subprocess.run, world.log, world.routes_file)
        with patch.object(tokens.subprocess, "run", run), redirect_stdout(io.StringIO()):
            tokens.remove(tokens.Gh(), target(), 2)
        calls = world.calls()
        self.assertEqual(find(calls, "secret delete")[0]["args"], ["secret", "delete", tokens.slot_secret(2), "--org", ORG])
        self.assertEqual(find(calls, "variable delete")[0]["args"][2], tokens.slot_label(2))
        self.assertEqual(find(calls, "variable set", tokens.ACCOUNTS_VARIABLE)[0]["args"][-2:], ["--body", "1"])


class ThePlace(unittest.TestCase):
    def parse(self, *argv):
        return tokens.build_parser().parse_args(list(argv))

    def test_the_place_options_go_before_or_after_the_command(self):
        self.assertEqual(self.parse("--org", ORG, "add").org, ORG)
        self.assertEqual(self.parse("add", "--org", ORG).org, ORG)
        self.assertIsNone(self.parse("add").org)
        self.assertEqual(self.parse("status", "--repos", "a,b").repos, "a,b")
        self.assertEqual(self.parse("--repo", "o/n", "remove", "2").slot, 2)

    def test_the_origin_decides_when_nothing_is_said(self):
        folder = tempfile.mkdtemp(prefix="tokens-origin-")
        self.addCleanup(shutil.rmtree, folder, ignore_errors=True)
        subprocess.run(["git", "init", "-q", folder], check=True)
        subprocess.run(["git", "-C", folder, "remote", "add", "origin", f"git@github.com:{ORG}/{REPO}.git"], check=True)
        self.assertEqual(tokens.origin_repository(Path(folder)), (ORG, REPO))
        world = World(self)
        run = fake_gh.routed_run(subprocess.run, world.log, world.routes_file)
        with patch.object(tokens.subprocess, "run", run):
            place = tokens.target_from(self.parse(), tokens.Gh(), root=Path(folder))
        self.assertEqual((place.level, place.owner, place.repos), ("org", ORG, [REPO]))
        self.assertEqual(place.describe(), f"the organization {ORG}, seen by {REPO}")

    def test_a_personal_account_takes_the_repository_level(self):
        folder = tempfile.mkdtemp(prefix="tokens-origin-")
        self.addCleanup(shutil.rmtree, folder, ignore_errors=True)
        subprocess.run(["git", "init", "-q", folder], check=True)
        subprocess.run(["git", "-C", folder, "remote", "add", "origin", "https://github.com/ada/engine.git"], check=True)
        world = World(self)
        routes = read_json(world.routes_file)
        routes["GET users/ada"] = [answer(200, "User\n")]
        fake_gh.write_routes(world.routes_file, routes)
        run = fake_gh.routed_run(subprocess.run, world.log, world.routes_file)
        with patch.object(tokens.subprocess, "run", run):
            place = tokens.target_from(self.parse(), tokens.Gh(), root=Path(folder))
            with self.assertRaises(tokens.TokensError):
                tokens.target_from(self.parse("--repos", "x"), tokens.Gh(), root=Path(folder))
        self.assertEqual((place.level, place.full_name), ("repo", "ada/engine"))

    def test_an_organization_named_alone_takes_the_origin_s_repository(self):
        world = World(self)
        run = fake_gh.routed_run(subprocess.run, world.log, world.routes_file)
        with patch.object(tokens.subprocess, "run", run):
            with self.assertRaises(tokens.TokensError) as caught:
                tokens.target_from(self.parse("--org", "elsewhere"), tokens.Gh(), root=Path(tempfile.gettempdir()))
        self.assertIn("--repos", str(caught.exception))
        place = tokens.target_from(self.parse("--org", "elsewhere", "--visibility", "all"), tokens.Gh(), root=Path(tempfile.gettempdir()))
        self.assertEqual(place.describe(), "the organization elsewhere, seen by every repository")

    def test_the_organization_needs_the_scope_before_any_sign_in(self):
        world = World(self, scopes="  Token scopes: 'gist', 'read:org', 'repo', 'workflow'\n")
        run = fake_gh.routed_run(subprocess.run, world.log, world.routes_file)
        with patch.object(tokens.subprocess, "run", run):
            with self.assertRaises(tokens.TokensError) as caught:
                tokens.check_scopes(tokens.Gh(), target())
            tokens.check_scopes(tokens.Gh(), tokens.Target("repo", ORG, name=REPO))
        self.assertIn("admin:org", str(caught.exception))

    def test_not_signed_in_is_said_first(self):
        world = World(self)
        routes = read_json(world.routes_file)
        routes["auth status"] = [answer(1, "", stderr="You are not logged into any GitHub hosts. To log in, run: gh auth login\n")]
        routes["auth status"][0]["status"] = 401
        fake_gh.write_routes(world.routes_file, routes)
        run = fake_gh.routed_run(subprocess.run, world.log, world.routes_file)
        with patch.object(tokens.subprocess, "run", run):
            with self.assertRaises(tokens.TokensError) as caught:
                tokens.check_signed_in(tokens.Gh())
        self.assertIn("gh auth login", str(caught.exception))


class TheWizard(unittest.TestCase):
    def test_one_account_then_stop(self):
        world = World(self)
        world.expect_store(tokens.slot_secret(1), tokens.MAIN_SECRET)
        answers = iter(["", "greg", "", "y", "n"])
        _, printed, calls = world.run_in_process(self, tokens.wizard, tokens.Gh(), target(), ask=lambda prompt: next(answers))
        stores = find(calls, "secret set")
        self.assertEqual([call["args"][2] for call in stores], [tokens.slot_secret(1), tokens.MAIN_SECRET])
        self.assertEqual(find(calls, "variable set", tokens.slot_label(1))[0]["args"][-2:], ["--body", "greg"])
        self.assertIn("sign in to claude.ai as the account this slot is for", printed)
        self.assertFalse(has_token(printed))

    def test_the_slot_question(self):
        world = World(self, secrets=[secret(tokens.slot_secret(1))])
        run = fake_gh.routed_run(subprocess.run, world.log, world.routes_file)
        with patch.object(tokens.subprocess, "run", run):
            state = tokens.State(tokens.Gh(), target())
        self.assertEqual(tokens.chosen_slot(state, lambda prompt: ""), 2)
        self.assertEqual(tokens.chosen_slot(state, lambda prompt: "1"), 1)
        self.assertIsNone(tokens.chosen_slot(state, lambda prompt: "n"))
        with self.assertRaises(tokens.TokensError):
            tokens.chosen_slot(state, lambda prompt: "9")


class TheScript(unittest.TestCase):
    """The whole command as a process, against the fake gh on PATH."""

    def test_add_from_the_command_line(self):
        world = World(self, secrets=[secret(tokens.slot_secret(1))])
        world.expect_store(tokens.slot_secret(2))
        bin_dir = install_claude(world.folder)
        report = str(Path(world.folder) / "claude-report.json")
        environ = dict(os.environ)
        environ.update(world.environment)
        environ["PATH"] = str(bin_dir) + os.pathsep + environ["PATH"]
        environ["FAKE_CLAUDE_REPORT"] = report
        # The script as a process reads the project file beside it, so it
        # runs from a tree of the test's own, whose mode line says off.
        script = Path(world.folder) / "scripts" / "tokens.py"
        script.parent.mkdir(exist_ok=True)
        shutil.copy(SCRIPT, script)
        done = subprocess.run([sys.executable, str(script), "add", "--org", ORG, "--repos", REPO, "--label", "dev"],
                              input="thecode\n", capture_output=True, text=True, env=environ, cwd=world.folder)
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertNotIn(TOKEN, done.stdout + done.stderr)
        self.assertFalse(has_token(done.stdout + done.stderr))
        self.assertIn(tokens.MASK, done.stdout)
        calls = world.calls()
        store = find(calls, "secret set")[0]
        self.assertEqual(store["stdin"], TOKEN)
        self.assertEqual(store["args"][2], tokens.slot_secret(2))
        self.assertEqual(find(calls, "variable set", tokens.ACCOUNTS_VARIABLE)[0]["args"][-2:], ["--body", "1,2"])
        self.assertEqual(read_json(report)["code"], "thecode")

    def test_help_and_usage_errors(self):
        done = subprocess.run([sys.executable, str(SCRIPT), "--help"], capture_output=True, text=True, cwd=ROOT)
        self.assertEqual(done.returncode, 0)
        for word in ("status", "add", "main", "remove", "--org", "--repos", "--visibility", "--repo"):
            self.assertIn(word, done.stdout)
        self.assertEqual(subprocess.run([sys.executable, str(SCRIPT), "--nope"], capture_output=True, cwd=ROOT).returncode, 2)
        self.assertEqual(subprocess.run([sys.executable, str(SCRIPT), "--repo", "bad", "status"], capture_output=True, cwd=ROOT).returncode, 2)
        self.assertEqual(subprocess.run([sys.executable, str(SCRIPT), "remove", "9"], capture_output=True, cwd=ROOT).returncode, 2)

    def test_the_token_never_goes_on_a_command_line(self):
        text = SCRIPT.read_text()
        lines = [line for line in text.splitlines() if "secret" in line and "set" in line and "args" in line]
        self.assertTrue(lines)
        for line in lines:
            self.assertNotIn("--body", line)
        self.assertNotIn("print(token", text)
        self.assertNotIn("{token}", text)

    def test_the_source_holds_no_secret_shape(self):
        for path in (SCRIPT, Path(__file__)):
            for name, pattern in check_docs.SECRET_PATTERNS:
                self.assertIsNone(pattern.search(path.read_text()), f"{path.name}: {name}")


if __name__ == "__main__":
    unittest.main()
