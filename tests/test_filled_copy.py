"""A copy made from the template passes its own check on its first day.

"Use this template" copies the template's files, and the copy's first push
runs .github/workflows/template-init.yml, which fills the placeholders
(tools/template_init.py) and commits the result; the front door's whole
template does the same in the adopter's own repository. From then on the
copy's required check is its own `bash scripts/check.sh`, over the filled
files. A test that holds only for the template's own files, one that
expects a placeholder the fill has replaced, reads the template's switch as
on, or lets a variable of the caller's reach the code it tests, turns every
new copy red while the template stays green. So the template's check makes
such a copy of the template as it stands, a change not yet committed
included, in a temporary folder, and runs the copy's own check there, twice
and side by side: an organization's copy on main with sharing on, as "Use
this template" leaves it, and a person's copy on master as the front door's
whole template makes it with sharing off, with no LICENSE, which the front
door never copies, and the word off alone in the switch file, as its
opt-out writes it, and with SDLC_METRICS=off in the environment besides, as
a person may set it in their shell. Side by side, the two add about the
time of one copy's check to the template's.

Only the template makes a copy: a copy has no .template/ folder, so its own
check skips this, which also keeps it from making a copy of itself.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import check_docs  # noqa: E402
import usage  # noqa: E402

IN_TEMPLATE = (ROOT / ".template" / "PENDING").is_file()
PERSON = "example-person"
# A check that hangs fails here instead of holding the template's check.
CHECK_TIMEOUT = 900
STEP_TIMEOUT = 120
# How many of a failed check's last lines the failure shows.
TAIL = 40
COPIES = {
    "on": {"repo": "example-org/example", "branch": "main", "owner_type": "Organization", "sharing": "on"},
    "off": {"repo": PERSON + "/example", "branch": "master", "owner_type": "User", "sharing": "off"},
}


def without_git_variables(environ):
    """The environment without git's own variables, which would point a git
    started in the copy at the template's repository, as they do when the
    template's check runs from a git hook."""
    return {name: value for name, value in environ.items() if not name.startswith("GIT_")}


def run(argv, folder, environ):
    """One step of making the copy; a failure says what the step printed."""
    done = subprocess.run(argv, cwd=folder, env=environ, stdin=subprocess.DEVNULL, capture_output=True,
                          text=True, timeout=STEP_TIMEOUT)
    if done.returncode != 0:
        raise AssertionError(f"{' '.join(argv)}: exit {done.returncode}\n{done.stdout}{done.stderr}")


def git(folder, *args):
    """git in the copy, as the person who made it, with nobody's own
    configuration, so no signing setting or hook of theirs takes part."""
    environ = without_git_variables(os.environ) | {"GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull}
    run(["git", "-c", f"user.name={PERSON}", "-c", f"user.email={PERSON}@example.invalid",
         "-c", "commit.gpgsign=false", *args], folder, environ)


def copy_template(target):
    """The template's files as a commit of its working tree would hold them:
    what git tracks and what it would add, as they stand now, the list
    tools/check_docs.py checks."""
    for rel in check_docs.tracked_files(ROOT):
        (target / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / rel, target / rel, follow_symlinks=False)


def push_event(repo, branch, owner_type):
    """What template_init reads of the first push's event: whose repository
    it is, and who pushed, the person who made the copy."""
    owner = repo.partition("/")[0]
    return {"ref": f"refs/heads/{branch}", "sender": {"login": PERSON, "type": "User"},
            "repository": {"full_name": repo, "default_branch": branch, "owner": {"login": owner, "type": owner_type}}}


def make_copy(folder, repo, branch, owner_type, sharing):
    """A copy as "Use this template" and its first push's run make it: the
    template's files in one commit on the default branch, then the commit of
    tools/template_init.py's fill; and for sharing off, the commit that
    makes it what the front door's whole template makes with sharing off,
    which has no LICENSE and says off in the switch file."""
    copy = folder / repo.partition("/")[2]
    copy_template(copy)
    git(copy, "init", "-q")
    git(copy, "symbolic-ref", "HEAD", f"refs/heads/{branch}")
    git(copy, "add", "-A")
    git(copy, "commit", "-q", "-m", "Initial commit")
    event = folder / "event.json"
    event.write_text(json.dumps(push_event(repo, branch, owner_type)), encoding="utf-8")
    run([sys.executable, "tools/template_init.py", "--repo", repo, "--default-branch", branch, "--event", str(event)],
        copy, without_git_variables(os.environ))
    git(copy, "add", "-A")
    git(copy, "commit", "-q", "-m", "Initialise from the template")
    if sharing == "off":
        (copy / "LICENSE").unlink()
        (copy / usage.SWITCH_FILE).write_text("off\n", encoding="ascii")
        git(copy, "commit", "-q", "-am", "Leave out LICENSE and turn sharing off, as the front door does")
    return copy


def start_check(copy, sharing, log):
    """The copy's own check, started in the environment the template's check
    runs in, with the metrics switch variable unset for sharing on and off
    for sharing off; its output goes to log."""
    environ = without_git_variables(os.environ)
    environ.pop(usage.SWITCH_VARIABLE, None)
    if sharing == "off":
        environ[usage.SWITCH_VARIABLE] = "off"
    with open(log, "w", encoding="utf-8") as stream:
        return subprocess.Popen(["bash", "scripts/check.sh"], cwd=copy, env=environ, stdin=subprocess.DEVNULL,
                                stdout=stream, stderr=subprocess.STDOUT)


def stop(process):
    if process.poll() is None:
        process.kill()
        process.wait()


def summary(output):
    """What a failed check said: each test that failed, then its last lines."""
    lines = output.splitlines()
    failed = [line for line in lines if line.startswith(("FAIL:", "ERROR:"))]
    return "\n".join(["the copy's check failed", *failed, "...", *lines[-TAIL:]])


@unittest.skipUnless(IN_TEMPLATE, "only the template makes a filled copy of itself, and this is a copy")
class AFilledCopy(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        folder = Path(tempfile.mkdtemp())
        cls.addClassCleanup(shutil.rmtree, folder, True)
        cls.checks = {}
        for name, made in COPIES.items():
            copy = make_copy(folder / name, **made)
            log = folder / f"{name}.log"
            process = start_check(copy, made["sharing"], log)
            cls.addClassCleanup(stop, process)
            cls.checks[name] = (process, log)

    def assert_passes(self, name):
        process, log = self.checks[name]
        try:
            code = process.wait(timeout=CHECK_TIMEOUT)
        except subprocess.TimeoutExpired:
            stop(process)
            self.fail(f"the copy's check ran past {CHECK_TIMEOUT} s")
        self.assertEqual(code, 0, summary(log.read_text(encoding="utf-8", errors="replace")))

    def test_an_organizations_copy_on_main_with_sharing_on_passes_its_own_check(self):
        self.assert_passes("on")

    def test_a_persons_copy_on_master_with_sharing_off_passes_its_own_check(self):
        self.assert_passes("off")


if __name__ == "__main__":
    unittest.main()
