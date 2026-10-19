"""Keep the files the control panel needs up to date in every adopted repository.

An adoption copies the template's files once, and nothing of the template
reached a repository after that: one adopted for the protocol alone had no
workflow Token and kept the board, the metrics and the library it was
adopted with (the owner, 2026-10-19: "existing repos which dont get the full
template files should at least get the files needed to function on the
symphony board"). .github/workflows/sync.yml runs this script in the
template whenever those files change on the default branch, weekly and by
hand. With the SymphonyBoard App's own key it walks every installation, and
in each adopted repository the installation reaches, one whose default
branch holds docs/agents/PROTOCOL.md, it offers the template's current
files as one pull request from the branch symphony/sync, which belongs to
this run alone. Nobody's default branch changes until they merge it.

The files come in units, as an adoption brings them (symphony-start's
scripts/adopt.py): a workflow with its script and every module of the
template that script imports, and the vendored library with its record. A
file is replaced only where the repository holds a version the template
itself once held at that path, so a file of their own is never overwritten:
such a file holds its unit back whole, and the pull request says which file
and why. A unit is added where it is missing only when ADDED names it, the
Token workflow alone, since a repository without the board or the metrics
removed them or never took them: the metrics workflow shares aggregates,
and only an adoption's switch says whether it may. A pull request closed
without its merge is not opened again for the same files, so a no stays a
no until the template changes them; `off` in .github/symphony-sync stops
the offers for good.

The log names no repository: an installation's repositories may be private
and belong to anyone, so the run prints counts alone.

  run     walk every installation (APP_ID, APP_PRIVATE_KEY, and ONLY_OWNER
          to keep to one account)
"""

import ast
import base64
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
API = "https://api.github.com"
BRANCH = "symphony/sync"
MARK = "<!-- symphony-sync: tree "
PROTOCOL_TEXT = "docs/agents/PROTOCOL.md"
OPT_OUTS = (".github/symphony-sync", ".github/symphony-adopt", ".github/sdlc-adopt")
LIBRARY = "tools/sdlc_protocol"
LIBRARY_PACKAGE = "sdlc_protocol"
VENDORED = "tools/VENDORED"
# The front door and the template take no offer of themselves.
OWN = {"openspineconsortium/symphony-template", "openspineconsortium/symphony-start",
       "openspineconsortium/sdlc-template", "openspineconsortium/sdlc-start"}
# Each workflow and the script it runs, with the folders Python finds the
# template's modules in for that script, in its order: tools/token_run.py
# puts scripts/ on its path after its own folder.
WORKFLOWS = (
    ("the board's workflow and its script", ".github/workflows/board.yml", "tools/board.py", ("tools",)),
    ("the workflow that tidies closed claims", ".github/workflows/tidy.yml", None, ()),
    ("the metrics workflow and the scripts it runs", ".github/workflows/metrics.yml", "tools/metrics.py", ("tools",)),
    ("the Token workflow and the scripts it runs", ".github/workflows/token.yml", "tools/token_run.py",
     ("tools", "scripts")),
)
LIBRARY_UNIT = "the vendored library and its record"
ADDED = {".github/workflows/token.yml"}
# GitHub's modes for a file that is no link and no submodule.
FILE_MODES = {"100644", "100755"}


class SyncError(Exception):
    pass


# ---------- the template's side ----------

def git(*args):
    return subprocess.run(["git", "-C", str(ROOT), *args], check=True, capture_output=True).stdout


def template_tree():
    """path -> (mode, blob sha) of the template's head."""
    out = {}
    for line in git("ls-tree", "-r", "-z", "HEAD").split(b"\0"):
        if not line:
            continue
        meta, path = line.split(b"\t", 1)
        mode, kind, sha = meta.decode().split()
        if kind == "blob":
            out[path.decode()] = (mode, sha)
    return out


def history(paths):
    """path -> every blob sha the default branch's history held at it."""
    held = {path: set() for path in paths}
    raw = git("log", "--raw", "--no-abbrev", "--no-renames", "--format=", "-z", "HEAD", "--", *sorted(paths))
    fields = raw.split(b"\0")
    i = 0
    while i < len(fields) - 1:
        meta = fields[i].decode().strip()
        if not meta.startswith(":"):
            i += 1
            continue
        parts = meta.split()
        path = fields[i + 1].decode()
        if path in held and set(parts[3]) != {"0"}:
            held[path].add(parts[3])
        i += 2
    return held


def imported(source):
    """The top-level names of every module the Python source imports."""
    names = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            names.update(alias.name.partition(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            names.add(node.module.partition(".")[0])
    return names


def closure(tree, script, folders, read):
    """The script and every module of the template it imports, in turn, as
    Python finds them in folders; and whether any of them imports the
    vendored library, which is a unit of its own."""
    files, waiting, needs = [], [script], False
    while waiting:
        rel = waiting.pop(0)
        if rel in files:
            continue
        files.append(rel)
        names = imported(read(rel))
        needs = needs or LIBRARY_PACKAGE in names
        for name in sorted(names - {LIBRARY_PACKAGE}):
            for folder in folders:
                found = sorted(p for p in tree if p == f"{folder}/{name}.py" or p.startswith(f"{folder}/{name}/"))
                if found:
                    waiting += found
                    break
    return files, needs


def units(tree, read):
    """(name, files, needs the library, may be added) for each unit the
    template holds, the library first."""
    library = sorted(p for p in tree if p.startswith(LIBRARY + "/") or p == VENDORED)
    out = [(LIBRARY_UNIT, library, False, False)]
    for name, workflow, script, folders in WORKFLOWS:
        if workflow not in tree or (script and script not in tree):
            continue
        files, needs = closure(tree, script, folders, read) if script else ([], False)
        out.append((name, [workflow] + files, needs, workflow in ADDED))
    return out


# ---------- the plan for one repository ----------

def plan(theirs, tree, held, unit_list):
    """What the pull request changes and what it holds back.

    theirs maps a path of the repository's default branch to (mode, sha,
    kind). Returns (changes, kept): changes maps a path to the template's
    (mode, sha), kept lists (unit name, why) for each unit held back. A
    unit lands whole or not at all; the library lands only where every unit
    of theirs that imports it lands too or is current, and a unit that
    imports it lands only beside a library that will be current."""
    decided = []
    for name, files, needs, may_add in unit_list:
        key = VENDORED if name == LIBRARY_UNIT else files[0]
        states = {rel: state(theirs.get(rel), tree[rel], held.get(rel, set())) for rel in files}
        if all(s == "same" for s in states.values()):
            verdict = "same"
        elif states.get(key) == "absent" and not may_add:
            # a unit the repository never took, or removed: not ours to add
            verdict = "missing"
        elif name == LIBRARY_UNIT and ".github/workflows/protocol.yml" in theirs:
            # a whole template's copy takes each release by its own workflow
            verdict = "theirs to update"
        else:
            foreign = next((rel for rel, s in states.items() if s == "theirs"), None)
            shadow = first_shadow(theirs, files)
            verdict = (f"`{foreign}` is this repository's own, and {name} come together or not at all" if foreign
                       else f"`{shadow}` is this repository's own, and Python would import it in place of the"
                            f" template's module" if shadow else "land")
        decided.append([name, files, needs, states, verdict])
    library = decided[0]
    users_held = [d for d in decided[1:] if d[2] and d[4] not in ("same", "land", "missing")]
    if library[4] == "land" and users_held:
        library[4] = f"{users_held[0][0]} stay as they are and need the library they have"
    if library[4] != "land" and library[4] != "same":
        for d in decided[1:]:
            if d[2] and d[4] == "land":
                d[4] = f"{d[0]} need the template's vendored library, which this pull request cannot bring"
    changes, kept = {}, []
    for name, files, needs, states, verdict in decided:
        if verdict == "land":
            changes.update({rel: tree[rel] for rel, s in states.items() if s != "same"})
        elif verdict not in ("same", "missing", "theirs to update"):
            kept.append((name, verdict))
    return changes, kept


def first_shadow(theirs, files):
    """A file of theirs that Python would import in place of one of the
    unit's modules, since it lies in a folder the script searches earlier
    (WORKFLOWS), or None."""
    folders = next((f for _, workflow, _, f in WORKFLOWS if workflow == files[0]), ())
    for rel in files[1:]:
        parts = rel.split("/")
        if parts[0] not in folders or len(parts) < 2:
            continue
        name = parts[1].removesuffix(".py")
        for earlier in folders[:folders.index(parts[0])]:
            for shadow in (f"{earlier}/{name}.py", f"{earlier}/{name}/__init__.py"):
                if shadow in theirs:
                    return shadow
    return None


def state(entry, current, known):
    if entry is None:
        return "absent"
    mode, sha, kind = entry
    if kind != "blob" or mode not in FILE_MODES:
        return "theirs"
    if sha == current[1] and mode == current[0]:
        return "same"
    if sha == current[1] or sha in known:
        return "old"
    return "theirs"


# ---------- GitHub ----------

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


OPENER = urllib.request.build_opener(NoRedirect)


class GitHub:
    def __init__(self, token, transport=None):
        self.token = token
        self.transport = transport or self.urllib

    def urllib(self, method, url, headers, body):
        request = urllib.request.Request(url, data=body, method=method, headers=headers)
        try:
            with OPENER.open(request, timeout=30) as reply:
                return reply.status, dict(reply.headers), reply.read()
        except urllib.error.HTTPError as error:
            return error.code, dict(error.headers or {}), error.read()

    def call(self, method, path, body=None, ok=()):
        headers = {"Authorization": f"Bearer {self.token}", "Accept": "application/vnd.github+json",
                   "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "symphony-sync"}
        data = None
        if body is not None:
            data = json.dumps(body).encode()
            headers["Content-Type"] = "application/json"
        status, reply_headers, raw = self.transport(method, API + path, headers, data)
        if status in ok:
            return None
        if status >= 300:
            raise SyncError(f"{method} answered {status}")
        return json.loads(raw) if raw else None

    def pages(self, path, key=None, limit=50):
        out = []
        for page in range(1, limit + 1):
            sep = "&" if "?" in path else "?"
            got = self.call("GET", f"{path}{sep}per_page=100&page={page}")
            items = got.get(key, []) if key else got
            out += items
            if len(items) < 100:
                return out
        return out


def app_jwt(app_id, key):
    """The App's JWT, signed RS256 by openssl, which Python's standard
    library cannot do; the key reaches openssl through a pipe, never a file."""
    def b64(raw):
        return base64.urlsafe_b64encode(raw).rstrip(b"=")
    now = int(time.time())
    head = b64(b'{"alg":"RS256","typ":"JWT"}')
    body = b64(json.dumps({"iat": now - 60, "exp": now + 540, "iss": str(app_id)}).encode())
    read, write = os.pipe()
    os.write(write, key.encode() + b"\n")
    os.close(write)
    try:
        signed = subprocess.run(["openssl", "dgst", "-sha256", "-binary", "-sign", f"/dev/fd/{read}"],
                                input=head + b"." + body, capture_output=True, check=True, pass_fds=(read,))
    finally:
        os.close(read)
    return (head + b"." + body + b"." + b64(signed.stdout)).decode()


# ---------- one repository ----------

def their_tree(gh, repo):
    """(head sha, path -> (mode, sha, kind)) of the default branch, or None
    for an empty repository or a tree GitHub cuts short."""
    name = repo["full_name"]
    ref = gh.call("GET", f"/repos/{name}/git/ref/heads/{quote(repo['default_branch'])}", ok=(404, 409))
    if not ref:
        return None
    head = ref["object"]["sha"]
    commit = gh.call("GET", f"/repos/{name}/git/commits/{head}")
    got = gh.call("GET", f"/repos/{name}/git/trees/{commit['tree']['sha']}?recursive=1")
    if got.get("truncated"):
        return None
    return head, commit["tree"]["sha"], {e["path"]: (e["mode"], e["sha"], e["type"]) for e in got["tree"]}


def opted_out(gh, repo, theirs):
    for rel in OPT_OUTS:
        entry = theirs.get(rel)
        if entry and entry[2] == "blob":
            blob = gh.call("GET", f"/repos/{repo['full_name']}/git/blobs/{entry[1]}")
            if base64.b64decode(blob.get("content", "")).decode("utf-8", "replace").strip().lower() == "off":
                return True
    return False


def quote(text):
    return urllib.parse.quote(text, safe="/")


def body_of(changes, kept, tree_sha):
    lines = [MARK + tree_sha + " -->",
             "This pull request brings the files Symphony's board and control panel run on up to date with the"
             " Symphony template, as the template's own sync offers them to every adopted repository. Each file"
             " it replaces holds a version the template itself once held; none of this repository's own files"
             " is touched, and nothing changes until it is merged.", "", "Files:"]
    lines += [f"- `{rel}`" for rel in sorted(changes)]
    if kept:
        lines += ["", "Held back:"] + [f"- {name}: {why}." for name, why in kept]
    lines += ["", "Closing this pull request without merging it stops this offer until the template changes these"
              " files again; `off` in `.github/symphony-sync` stops the offers for good."]
    return "\n".join(lines) + "\n"


def offer(gh, repo, bot, read_blob, tree, held, unit_list):
    """Offer one repository its pull request; the outcome as one word."""
    name = repo["full_name"]
    if name.lower() in OWN or repo.get("archived") or repo.get("disabled"):
        return "skipped"
    got = their_tree(gh, repo)
    if not got:
        return "skipped"
    head, base_tree, theirs = got
    if PROTOCOL_TEXT not in theirs:
        return "not adopted"
    if opted_out(gh, repo, theirs):
        return "opted out"
    changes, kept = plan(theirs, tree, held, unit_list)
    if not changes:
        return "up to date"
    branch = gh.call("GET", f"/repos/{name}/git/ref/heads/{quote(BRANCH)}", ok=(404,))
    tip = None
    if branch:
        tip = gh.call("GET", f"/repos/{name}/commits/{branch['object']['sha']}")
        if bot not in (((tip.get("author") or {}).get("login") or ""), ((tip.get("committer") or {}).get("login") or "")):
            return "branch theirs"
    entries = []
    for rel, (mode, sha) in sorted(changes.items()):
        blob = gh.call("POST", f"/repos/{name}/git/blobs",
                       {"content": base64.b64encode(read_blob(sha)).decode(), "encoding": "base64"})
        entries.append({"path": rel, "mode": mode, "type": "blob", "sha": blob["sha"]})
    new_tree = gh.call("POST", f"/repos/{name}/git/trees", {"base_tree": base_tree, "tree": entries})["sha"]
    pulls = gh.call("GET", f"/repos/{name}/pulls?state=all&head={quote(name.split('/')[0] + ':' + BRANCH)}"
                    "&sort=created&direction=desc&per_page=10")
    open_pull = next((p for p in pulls if p["state"] == "open"), None)
    if not open_pull and pulls and not pulls[0].get("merged_at") and MARK + new_tree + " -->" in (pulls[0].get("body") or ""):
        return "declined"
    if open_pull and tip and tip["commit"]["tree"]["sha"] == new_tree:
        return "offered already"
    commit = gh.call("POST", f"/repos/{name}/git/commits",
                     {"message": "Bring Symphony's board files up to date\n\nOffered by the Symphony template's sync.",
                      "tree": new_tree, "parents": [head]})
    if branch:
        gh.call("PATCH", f"/repos/{name}/git/refs/heads/{quote(BRANCH)}", {"sha": commit["sha"], "force": True})
    else:
        gh.call("POST", f"/repos/{name}/git/refs", {"ref": "refs/heads/" + BRANCH, "sha": commit["sha"]})
    body = body_of(changes, kept, new_tree)
    if open_pull:
        gh.call("PATCH", f"/repos/{name}/pulls/{open_pull['number']}", {"body": body})
        return "updated"
    gh.call("POST", f"/repos/{name}/pulls", {"title": "Bring Symphony's board files up to date", "head": BRANCH,
                                             "base": repo["default_branch"], "body": body})
    return "offered"


# ---------- every installation ----------

def run(environ, transport=None):
    app_id, key = environ.get("APP_ID", ""), environ.get("APP_PRIVATE_KEY", "")
    if not app_id or not key:
        raise SyncError("APP_ID and APP_PRIVATE_KEY must both be set")
    only = (environ.get("ONLY_OWNER") or "").lower()
    tree = template_tree()
    unit_list = units(tree, lambda rel: git("show", f"HEAD:{rel}"))
    held = history({rel for _, files, _, _ in unit_list for rel in files})
    blobs = {}

    def read_blob(sha):
        if sha not in blobs:
            blobs[sha] = git("cat-file", "blob", sha)
        return blobs[sha]

    def as_app():
        return GitHub(app_jwt(app_id, key), transport)

    bot = as_app().call("GET", "/app")["slug"] + "[bot]"
    tally = {}
    for installation in as_app().pages("/app/installations"):
        owner = ((installation.get("account") or {}).get("login") or "").lower()
        if only and owner != only:
            continue
        token = as_app().call("POST", f"/app/installations/{installation['id']}/access_tokens",
                              {"permissions": {"contents": "write", "pull_requests": "write", "metadata": "read"}},
                              ok=(403, 404, 422))
        if not token:
            tally["installation refused"] = tally.get("installation refused", 0) + 1
            continue
        gh = GitHub(token["token"], transport)
        try:
            for repo in gh.pages("/installation/repositories", "repositories"):
                try:
                    word = offer(gh, repo, bot, read_blob, tree, held, unit_list)
                except SyncError:
                    word = "failed"
                tally[word] = tally.get(word, 0) + 1
        finally:
            gh.call("DELETE", "/installation/token", ok=(401, 404))
    for word in sorted(tally):
        print(f"{word}: {tally[word]}")
    return 1 if tally.get("failed") else 0


def main(argv):
    if argv[1:] != ["run"]:
        print(__doc__, file=sys.stderr)
        return 2
    try:
        return run(os.environ)
    except SyncError as error:
        print(f"sync: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
