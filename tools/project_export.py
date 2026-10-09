"""Write export.json: the repository described as a cswap project export.

cswap (claude-swap-cloud on PyPI) imports a claude.ai Code project from a
folder that holds an export.json manifest, and the person runs that import
in their own browser with one click: the Import button of cswap's Chrome
extension, which opens the computer's own Open window for the folder; the
import script that `cswap project-move import` copies to the clipboard for
the browser's console; or `cswap project-move auto --export <folder>`. This
script writes that manifest at the repository root from the repository's
own files, so the repository is such an export, and a Project is set up
from it with no Claude prompt and no Claude session: the Goal paragraph of
docs/project.md becomes the Project's description, the pointer text of
docs/setup/claude-project.md its instructions, each file under docs/memory/
one entry of the Project's memory under the same name, and the repository
itself the Project's linked repository. Given an existing Project's address
as the name, the same import places them into that Project instead.
Nothing here runs against claude.ai: the manifest is data the person's own
import reads.

The manifest is version 1 of cswap's format, "claude-project-export", as
its project-import.js reads it and its project_move.py checks it: the
listed files are paths inside this folder, each with its size, and the
memory rows carry the path the memory gets. Nothing in it comes from a
clock, so the same files give the same bytes, and `--check` compares the
committed export.json with what would be written and fails when they
differ; scripts/check.sh runs that, and tools/template_init.py writes the
file after filling the placeholders, since the names and sizes change
then. Run it again whenever a file under docs/memory/, the Goal or the
pointer text changes.
"""

import argparse
import json
import re
import sys
from pathlib import Path

MANIFEST = "export.json"
FORMAT = "claude-project-export"
VERSION = 1
CLAUDE_MD = "CLAUDE.md"
README = "README.md"
PROJECT_PAGE = Path("docs") / "project.md"
SETUP_PAGE = Path("docs") / "setup" / "claude-project.md"
MEMORY_DIR = Path("docs") / "memory"
GOAL_HEADING = "## Goal"
POINTER_HEADING = "## The pointer text"
REPOSITORIES_HEADING = "## Repositories"
GOAL_UNWRITTEN = "Not yet written"
# Where the import puts a memory entry the Project's memory does not take
# (memory off in the account's settings): among the Project's files, in
# this folder, as cswap's own exports do.
CARRIED_MEMORY = "carried-memory"
GITHUB = "https://github.com/"
HEADING = re.compile(r"^#{1,6} ")
THIS_REPOSITORY = re.compile(r"^- (\S+), this one\b")


def read(root, rel):
    """The file as text with LF endings, or '' when it is not there."""
    path = root / rel
    if not path.is_file():
        return ""
    return path.read_bytes().decode("utf-8").replace("\r\n", "\n")


def section(text, heading):
    """The lines under one heading, up to the next heading of any level."""
    lines = text.split("\n")
    try:
        start = lines.index(heading) + 1
    except ValueError:
        return []
    body = []
    for line in lines[start:]:
        if HEADING.match(line):
            break
        body.append(line)
    return body


def first_paragraph(lines):
    """The first run of non-blank lines, joined with its line breaks."""
    paragraph = []
    for line in lines:
        if line.strip():
            paragraph.append(line.rstrip())
        elif paragraph:
            break
    return "\n".join(paragraph)


def fenced_block(lines):
    """The text inside the first fenced code block among the lines."""
    inside = False
    block = []
    for line in lines:
        if line.startswith("```"):
            if inside:
                break
            inside = True
            continue
        if inside:
            block.append(line)
    return "\n".join(block).strip("\n")


def project_name(root):
    """The title of CLAUDE.md, which the init tool fills with the project's name."""
    first = read(root, CLAUDE_MD).split("\n", 1)[0]
    return first[2:].strip() if first.startswith("# ") else root.name


def repository(root, override=None):
    """OWNER/NAME as docs/project.md names this repository, or the override."""
    if override:
        return override
    for line in section(read(root, PROJECT_PAGE), REPOSITORIES_HEADING):
        match = THIS_REPOSITORY.match(line)
        if match:
            return match.group(1)
    return ""


def description(root):
    """The Goal paragraph, or the README's opening while the goal is unwritten."""
    goal = first_paragraph(section(read(root, PROJECT_PAGE), GOAL_HEADING))
    if goal and not goal.startswith(GOAL_UNWRITTEN):
        return goal
    lines = read(root, README).split("\n")
    body = lines[1:] if lines and lines[0].startswith("# ") else lines
    return first_paragraph(body)


def instructions(root):
    """The pointer text, the few lines every account's Project carries."""
    return fenced_block(section(read(root, SETUP_PAGE), POINTER_HEADING))


def memory_rows(root):
    """One row per file under docs/memory/, in name order.

    `path` is the file here; `memory_path` is where the entry goes in the
    Project's memory, the same name at its root, which is how a Project
    keeps MEMORY.md and one file per fact, so the index's relative links
    hold; `name` is where the import puts it among the Project's files
    when the memory does not take it.
    """
    folder = root / MEMORY_DIR
    if not folder.is_dir():
        return []
    rows = []
    for path in sorted(folder.iterdir()):
        if not path.is_file() or path.suffix != ".md":
            continue
        rows.append({
            "path": (MEMORY_DIR / path.name).as_posix(),
            "name": f"{CARRIED_MEMORY}/{path.name}",
            "type": "project_memory",
            "bytes": path.stat().st_size,
            "memory_path": f"/{path.name}",
        })
    return rows


def manifest(root, repo=None):
    """The export.json the import reads, as a dict in a fixed order."""
    repo = repository(root, repo)
    url = GITHUB + repo if repo else ""
    rows = memory_rows(root)
    sources = [{"kind": "github_repository", "name": repo, "path": "", "url": url}] if repo else []
    return {
        "format": FORMAT,
        "version": VERSION,
        "kind": "code",
        "source": {"repository": url},
        "name": project_name(root),
        "description": description(root),
        "instructions": instructions(root),
        "settings": {
            "visibility": "private",
            "context_sources": sources,
            "config": {"default_source_urls": [url] if url else []},
        },
        "files": rows,
        "history": [],
        "memory": {"source": MEMORY_DIR.as_posix(), "files": len(rows), "beta": False},
        "problems": [],
    }


def render(root, repo=None):
    """The bytes of export.json: ASCII, two-space indents, LF, one trailing newline."""
    return (json.dumps(manifest(root, repo), indent=2, ensure_ascii=True) + "\n").encode("ascii")


def write(root, repo=None):
    """Write export.json; True when the file changed."""
    path = root / MANIFEST
    rendered = render(root, repo)
    if path.is_file() and path.read_bytes() == rendered:
        return False
    path.write_bytes(rendered)
    return True


def check(root, repo=None):
    """Problems with the committed export.json, one line each; none when it is current."""
    path = root / MANIFEST
    if not path.is_file():
        return [f"{MANIFEST}: missing; run python3 tools/project_export.py"]
    if path.read_bytes() != render(root, repo):
        return [f"{MANIFEST}: out of date with the files it lists; run python3 tools/project_export.py"]
    return []


def parse_args(argv):
    parser = argparse.ArgumentParser(description="Write export.json, the repository as a cswap project export.")
    parser.add_argument("--root", default=".", help="the repository root (default: the current directory)")
    parser.add_argument("--repo", default=None, help="OWNER/NAME, when docs/project.md does not name this repository")
    parser.add_argument("--check", action="store_true", help="compare the committed file with what would be written; exit 1 when they differ")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    root = Path(args.root).resolve()
    if args.check:
        problems = check(root, args.repo)
        for line in problems:
            print(line)
        return 1 if problems else 0
    changed = write(root, args.repo)
    print(f"{MANIFEST}: {'written' if changed else 'unchanged'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
