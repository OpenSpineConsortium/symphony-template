"""Ask every open pull request, once the default branch has moved, whether
it must bring the default branch in, and write the answer on its head as
the check run named overlap.

GitHub's rule that a branch be up to date before it merges sent every open
pull request back through a catch-up merge and a check run after each
merge, whatever it changed, and the rule is off (docs/setup/github.md).
What stood behind it is the one case where a branch that still merges
cleanly has changed its meaning: the default branch edited a function the
branch calls, or built on one the branch edits. tools/locks.py overlap
reads that case from what each side changed (docs/agents/PROTOCOL.md,
Locks), and .github/workflows/ci.yml runs it in the pull request's own run,
as the job named overlap. The default branch moves after that run too, so
.github/workflows/overlap.yml runs this tool on every push to the default
branch: it fetches each open pull request's head, judges it against the
default branch as it now stands, and writes a check run of the same name
on the head, where the newest word stands. The conclusion is success where
nothing the default branch changed meets the change, neutral where
something does and the switch says advise, failure where it says enforce,
and the same for a judgement that could not be made, so at enforce a
ruleset that requires the check named overlap holds exactly the pull
requests that must bring the default branch in. The switch is
.github/symphony-locks, or SYMPHONY_LOCKS in the environment (off, advise,
enforce); off, the tool writes nothing, as the check it fronts does nothing.

A head the pull request has moved past since the list was read is left
alone, since the pull request's own run judges the new one. The tool reads
the pull requests and writes the check runs through GitHub's REST API with
the workflow's own token (pull-requests: read, checks: write), and judges
in the clone it runs in.
"""

import io
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

NAME = "overlap"
API = "https://api.github.com"
PAGE = 100
SUMMARY_LIMIT = 60000  # GitHub takes 65535 characters of a check run's summary
SWITCH_FILE = ".github/symphony-locks"
MODES = ("off", "advise", "enforce")
NEED_NOTHING = "need not bring it in"


def switch_mode(environ, repo_dir):
    """The switch as sdlc_protocol.locks.mode_of reads it: SYMPHONY_LOCKS in
    the environment first, else the file, else off, and anything else off,
    so a typo never turns enforcement on."""
    try:
        text = (Path(repo_dir) / SWITCH_FILE).read_text(encoding="utf-8")
    except OSError:
        text = ""
    for value in (environ.get("SYMPHONY_LOCKS"), text):
        word = (value or "").strip().lower()
        if word in MODES:
            return word
    return "off"


def api(token, method, path, payload=None):
    """One call to GitHub's REST API; the parsed answer, or None for an
    empty one. A refusal is an HTTPError carrying GitHub's words."""
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(f"{API}/{path}", data=data, method=method, headers={
        "Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28", "Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=60) as answer:
        body = answer.read()
    return json.loads(body) if body.strip() else None


def open_pulls(call, repository):
    """Every open pull request, as (number, head sha), page by page."""
    pulls = []
    for page in range(1, 1000):
        listed = call("GET", f"repos/{repository}/pulls?state=open&per_page={PAGE}&page={page}") or []
        pulls += [(pull["number"], pull["head"]["sha"]) for pull in listed]
        if len(listed) < PAGE:
            break
    return pulls


def fetch_head(repo_dir, number, sha):
    """Bring the pull request's head into the clone, by the ref GitHub keeps
    for every pull request, a fork's too, and say whether it is still the
    head the list named."""
    done = subprocess.run(["git", "fetch", "--quiet", "--no-tags", "--depth=1", "origin",
                           f"+refs/pull/{number}/head:refs/remotes/pull/{number}/head"],
                          cwd=repo_dir, capture_output=True, text=True, timeout=300)
    if done.returncode != 0:
        return False
    found = subprocess.run(["git", "rev-parse", "--verify", "--quiet", f"refs/remotes/pull/{number}/head"],
                           cwd=repo_dir, capture_output=True, text=True, timeout=60)
    return found.stdout.strip() == sha


def judge(repo_dir, base, sha):
    """What tools/locks.py overlap says of the head: its exit code and its
    lines. Imported here, so the switch is read before the library is."""
    from sdlc_protocol.cli import run_locks
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = run_locks(["--repo", repo_dir, "overlap", "--base", base, "--head", sha])
    return code, out.getvalue() + err.getvalue()


def conclusion_of(code, text):
    """The check run's conclusion from the tool's answer: it exits 1 only
    where enforce fails the change, and at advise says what it found."""
    if code != 0:
        return "failure"
    if NEED_NOTHING in text:
        return "success"
    return "neutral"


def title_of(conclusion, text, base):
    meetings = sum(1 for line in text.splitlines() if line.startswith("locks: ") and line.endswith(f": bring {base} in"))
    if conclusion == "success":
        return f"Nothing {base} changed since this change's base meets it"
    if meetings:
        must = "must bring" if conclusion == "failure" else "should bring"
        return f"This change {must} {base} in: {meetings} meeting{'s' if meetings != 1 else ''}"
    return f"The change could not be judged against {base}"


def check_run(repository, sha, conclusion, title, summary, details_url):
    """The check run as GitHub's API takes it."""
    payload = {"name": NAME, "head_sha": sha, "status": "completed", "conclusion": conclusion,
               "output": {"title": title[:255], "summary": summary[:SUMMARY_LIMIT] or "(no lines)"}}
    if details_url:
        payload["details_url"] = details_url
    return f"repos/{repository}/check-runs", payload


def run(repository, base, repo_dir, details_url, call, mode, judge_head=judge, fetch=fetch_head, out=sys.stdout):
    """Judge every open pull request and write its check run; the
    conclusions by number, for the log."""
    if mode == "off":
        print("locks are off; nothing is asked or written", file=out)
        return {}
    written = {}
    for number, sha in open_pulls(call, repository):
        if not fetch(repo_dir, number, sha):
            print(f"#{number}: head {sha[:7]} is not the head any more, or could not be fetched; left to its own run",
                  file=out)
            continue
        code, text = judge_head(repo_dir, base, sha)
        conclusion = conclusion_of(code, text)
        title = title_of(conclusion, text, base)
        path, payload = check_run(repository, sha, conclusion, title, text, details_url)
        call("POST", path, payload)
        written[number] = conclusion
        print(f"#{number} at {sha[:7]}: {conclusion}: {title}", file=out)
    return written


def main(environ=None):
    environ = os.environ if environ is None else environ
    token = environ.get("GH_TOKEN") or environ.get("GITHUB_TOKEN") or ""
    repository = environ.get("GITHUB_REPOSITORY", "")
    default_branch = environ.get("DEFAULT_BRANCH") or "main"
    repo_dir = environ.get("REPO_DIR") or str(HERE.parent)
    mode = switch_mode(environ, repo_dir)
    if mode == "off":
        print("locks are off; nothing is asked or written")
        return 0
    if not token or not repository:
        print("overlap: GH_TOKEN and GITHUB_REPOSITORY are needed", file=sys.stderr)
        return 1

    def call(method, path, payload=None):
        return api(token, method, path, payload)

    try:
        run(repository, f"origin/{default_branch}", repo_dir, environ.get("RUN_URL", ""), call, mode)
    except urllib.error.HTTPError as refusal:
        print(f"overlap: GitHub refused {refusal.code}: {refusal.read().decode('utf-8', 'replace')[:500]}",
              file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
