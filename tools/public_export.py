"""Publish chosen parts of this repository to public ones, and take back
what contributors change there, with one manifest as the record of what
leaves.

GitHub sets visibility per repository, never per file, so a project that is
part open and part proprietary keeps everything here and lists what goes
public in .github/symphony/public.json; .github/workflows/export.yml copies
exactly that, as a pull request in the public repository, on every push to
the default branch, and .github/workflows/import.yml brings changes made
there to the files an export marks as importable back as a pull request
here. Nothing outside the manifest is ever copied, a path under one of its
"private" globs is refused, and the check fails while the manifest does not
hold together, so the manifest is always what really happens.

The manifest:

    {
      "private": ["globs in this repository that never leave it"],
      "exports": [
        {
          "name": "a word, the branch symphony/export/<name> in the target",
          "source": "OWNER/NAME of this repository, so a copy of it exports nothing",
          "repository": "OWNER/NAME of the public repository",
          "files": [{"from": "path here", "to": "path there"}],
          "build": "a command writing generated files into $EXPORT_DIR",
          "owns": ["globs there the build's output replaces wholesale"],
          "import": false
        }
      ]
    }

A "from" or "to" ending in / is a folder, copied with what it holds. "build"
is optional, and needs "owns", so files the build stopped writing are taken
out there. "import" true brings the target's changes to the "files" back
here; a build's output is generated, so it is never imported.

    python3 tools/public_export.py check
    python3 tools/public_export.py plan                 # JSON for a matrix
    python3 tools/public_export.py stage NAME OUT       # what NAME publishes
    python3 tools/public_export.py apply NAME OUT TARGET
    python3 tools/public_export.py import NAME TARGET
"""

import argparse
import fnmatch
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / ".github" / "symphony" / "public.json"
NAME = re.compile(r"^[a-z0-9][a-z0-9-]{0,39}$")
REPOSITORY = re.compile(r"^[A-Za-z0-9-]+/[A-Za-z0-9._-]+$")
KEYS = {"name", "source", "repository", "files", "build", "owns", "import"}


def load(path=None):
    path = path or MANIFEST
    if not path.exists():
        return {"private": [], "exports": []}
    return json.loads(path.read_text(encoding="utf-8"))


def relative(text):
    """A path that stays inside the repository it names."""
    parts = Path(text).parts
    return bool(text) and not Path(text).is_absolute() and ".." not in parts and ".git" not in parts


def tracked(root):
    listed = subprocess.run(["git", "-C", str(root), "ls-files", "-z"], capture_output=True, check=True).stdout
    return sorted(name for name in listed.decode().split("\0") if name)


def sources(entry, files):
    """The files here one "from" names."""
    origin = entry["from"]
    if origin.endswith("/"):
        return [name for name in files if name.startswith(origin)]
    return [name for name in files if name == origin]


def regular(path, inside):
    """A plain file that is where its name says: no symlink anywhere on the
    way, so copying it can neither read nor write outside the tree."""
    path, inside = Path(path), Path(inside).resolve()
    if path.is_symlink() or not path.resolve().is_relative_to(inside):
        raise SystemExit(f"{path}: a symlink, or reached through one; refused")
    return path


def destination(entry, name):
    if entry["from"].endswith("/"):
        return entry["to"] + name[len(entry["from"]):]
    return entry["to"]


def matches(name, globs):
    return any(fnmatch.fnmatchcase(name, glob) for glob in globs)


def problems(manifest, files):
    found = []
    private = manifest.get("private", [])
    if not isinstance(private, list) or not all(isinstance(g, str) and relative(g) for g in private):
        found.append("private: a list of globs inside the repository")
        private = []
    names = set()
    for number, export in enumerate(manifest.get("exports", []), 1):
        label = f"export {export.get('name') or number}"
        for key in sorted(set(export) - KEYS):
            found.append(f"{label}: unknown key {key}")
        if not NAME.match(str(export.get("name", ""))):
            found.append(f"{label}: name must be lower case letters, digits and dashes")
        elif export["name"] in names:
            found.append(f"{label}: a second export of that name")
        names.add(export.get("name"))
        for key in ("source", "repository"):
            if not REPOSITORY.match(str(export.get(key, ""))):
                found.append(f"{label}: {key} must be OWNER/NAME")
        entries = export.get("files", [])
        if not entries and not export.get("build"):
            found.append(f"{label}: neither files nor a build, so it publishes nothing")
        if export.get("build") and not export.get("owns"):
            found.append(f"{label}: a build needs owns, the globs its output replaces there")
        for glob in export.get("owns", []):
            if not relative(glob):
                found.append(f"{label}: owns {glob!r} leaves the target repository")
        for entry in entries:
            origin, target = entry.get("from", ""), entry.get("to", "")
            if not (relative(origin) and relative(target)) or origin.endswith("/") != target.endswith("/"):
                found.append(f"{label}: {origin!r} to {target!r} must both stay inside, and both be folders or files")
                continue
            named = sources(entry, files)
            if not named:
                found.append(f"{label}: {origin} names no tracked file")
            for name in named:
                if matches(name, private):
                    found.append(f"{label}: {name} is private and may not be published")
    return found


def export_named(manifest, name):
    for export in manifest.get("exports", []):
        if export.get("name") == name:
            return export
    raise SystemExit(f"no export named {name} in {MANIFEST.relative_to(ROOT)}")


def stage(export, out, root=ROOT):
    """Write what the export publishes into out, at the target's paths."""
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    files = tracked(root)
    for entry in export.get("files", []):
        for name in sources(entry, files):
            target = out / destination(entry, name)
            target.parent.mkdir(parents=True, exist_ok=True)
            # a tracked symlink could point at a private file the names pass
            shutil.copyfile(regular(root / name, root), target)
    if export.get("build"):
        subprocess.run(["bash", "-c", export["build"]], cwd=root, check=True,
                       env=dict(os.environ, EXPORT_DIR=str(out.resolve())))
    return written(out)


def written(out):
    """The staged files, refusing a symlink a build may have left."""
    out = Path(out)
    return sorted(str(regular(p, out).relative_to(out)) for p in out.rglob("*") if p.is_file() or p.is_symlink())


def owned(export, name):
    """Whether the export answers for this path in the target."""
    if matches(name, export.get("owns", [])):
        return True
    for entry in export.get("files", []):
        target = entry["to"]
        if name == target or (target.endswith("/") and name.startswith(target)):
            return True
    return False


def apply(export, out, target):
    """Make the target's owned paths what out holds: copy each staged file
    in and take out each owned file the stage no longer has."""
    out, target = Path(out), Path(target)
    staged = set(written(out))
    for name in tracked(target):
        if owned(export, name) and name not in staged:
            regular(target / name, target).unlink()
    for name in sorted(staged):
        if not owned(export, name):
            raise SystemExit(f"{name}: written by the export but outside what it owns there")
        (target / name).parent.mkdir(parents=True, exist_ok=True)
        if (target / name).exists() or (target / name).is_symlink():
            regular(target / name, target)
        elif not (target / name).parent.resolve().is_relative_to(target.resolve()):
            raise SystemExit(f"{name}: its folder there is reached through a symlink; refused")
        shutil.copyfile(out / name, target / name)
    return sorted(staged)


def take_back(export, target, root=ROOT):
    """Copy the target's versions of the export's files back here, for an
    export marked importable; return the paths here that changed."""
    if not export.get("import"):
        return []
    target, changed = Path(target), []
    there = set(tracked(target))
    for entry in export.get("files", []):
        for name in sources(entry, tracked(root)):
            theirs = destination(entry, name)
            if theirs not in there:
                continue
            # a contributor's symlink could point at the runner's secrets
            if regular(target / theirs, target).read_bytes() != regular(root / name, root).read_bytes():
                shutil.copyfile(target / theirs, root / name)
                changed.append(name)
    return changed


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("check", help="fail while the manifest does not hold together")
    sub.add_parser("plan", help="the exports as JSON, for a workflow's matrix")
    staged = sub.add_parser("stage", help="write what one export publishes into a folder")
    staged.add_argument("name")
    staged.add_argument("out")
    applied = sub.add_parser("apply", help="make a clone of the target hold a staged export")
    applied.add_argument("name")
    applied.add_argument("out")
    applied.add_argument("target")
    taken = sub.add_parser("import", help="bring the target's changes to importable files back here")
    taken.add_argument("name")
    taken.add_argument("target")
    args = parser.parse_args(argv)
    manifest = load()
    if args.command == "check":
        found = problems(manifest, tracked(ROOT))
        for line in found:
            print(f"{MANIFEST.relative_to(ROOT)}: {line}")
        return 1 if found else 0
    if args.command == "plan":
        # a copy made from this repository carries the manifest too, and
        # must never publish into the original's public repositories
        here = os.environ.get("GITHUB_REPOSITORY", "").lower()
        rows = [{"name": e["name"], "owner": e["repository"].split("/")[0], "repo": e["repository"].split("/")[1],
                 "import": bool(e.get("import"))}
                for e in manifest.get("exports", []) if e.get("source", "").lower() == here]
        print(json.dumps(rows))
        return 0
    export = export_named(manifest, args.name)
    if args.command == "stage":
        print("\n".join(stage(export, args.out)))
    elif args.command == "apply":
        print(f"{len(apply(export, args.out, args.target))} files published by {args.name}")
    else:
        print("\n".join(take_back(export, args.target)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
