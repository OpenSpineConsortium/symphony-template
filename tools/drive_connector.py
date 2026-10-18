"""Organize a whole OneDrive from a Claude session, through the Microsoft 365
connector, with no app of our own between the session and the drive.

The drive organizer's workflow (tools/drive_organize.py, drive-organize.yml)
reads the drive with the token the control panel's Folders tab gets, which a
work or school account has only once its administrator consents to the app.
A Claude session that has the Microsoft 365 connector reads the same drive
under the consent the organization gave Claude. This is the session's side
of that: the session lists folders with the connector's read_resource and
hands each listing here, and this keeps the walk, writes the same catalog the
workflow writes, checks the session's projects against it, and turns them
into a plan of moves for the owner to read. Nothing in the drive changes
until the owner says go, and every move can be undone.

  python3 tools/drive_connector.py add --walk WALK.jsonl --item root --drive ID --raw LISTING.txt
  python3 tools/drive_connector.py unlisted --walk WALK.jsonl
  python3 tools/drive_connector.py found --walk WALK.jsonl --raw SEARCH.txt
  python3 tools/drive_connector.py catalog --walk WALK.jsonl --out DIR
  python3 tools/drive_connector.py check --plan PLAN.json --catalog DIR/catalog.json
  python3 tools/drive_connector.py moves --plan PLAN.json --catalog DIR/catalog.json --out DIR
  python3 tools/drive_connector.py approve --moves DIR/moves.json
  python3 tools/drive_connector.py next --moves DIR/moves.json
  python3 tools/drive_connector.py done --moves DIR/moves.json --op N [--id NEW_ID]
  python3 tools/drive_connector.py undo --moves DIR/moves.json

add keeps one folder's listing, as read_resource gave it for
file:///<drive id>/<item id> (the drive's top is the item root), and unlisted
names the folders still to read, so the walk is the session's loop of
read_resource, add, until unlisted names none. A listing gives no date and
no link, so found keeps what pages of the connector's sharepoint_search
give for the walk's items (each one's lastModifiedDateTime and webUrl); one
link is enough to learn the drive's web address, from which every other
item's link is made. The plan is the organizer's
own JSON (drive_organize.schema), so its projects open as proposed epics
through the workflow's step open, or stay in the session. moves writes
moves.json and MOVES.md: one folder "Symphony projects" at the drive's top,
one folder per project inside it, and each of a project's folders and files
moved into its project's folder. next prints the one connector call to make,
with every id filled in, and refuses until approve has been run, which the
session runs only on the owner's own word; done records what the call gave.
undo turns the moves that were made into a plan that moves each item back to
the folder it came from, under its own name, and deletes nothing: an empty
project folder is the owner's to delete.

A walk and a catalog name a person's files: keep them in the session's
scratchpad, never in a commit, and push a catalog only to a private
repository's branch drive-catalog. Standard library only.
"""

import argparse
import json
import re
import sys
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import drive_organize  # noqa: E402
import drive_sync  # noqa: E402

TOP_NAME = "OneDrive"
HOME = "Symphony projects"
# The folders Microsoft 365 keeps for its own apps: moving one breaks the
# app that writes there, so they are listed but never read into or moved.
MANAGED = {"apps", "attachments", "meetings", "microsoft copilot chat files", "microsoft teams chat files",
           "microsoft teams data", "recordings", "notebooks", "desktop", "documents", "pictures"}
MAX_OPS = 600
BUSINESS_ID = re.compile(r"01[0-9A-Z]{32}")


class ConnectorError(Exception):
    """A step that cannot go on, said in one line."""


# The walk

def parse_listing(text):
    """The entries of one read_resource folder listing, in its order. The
    connector writes them one after another with no separator, so an entry's
    id is read by its own shape, a business id first, and the next entry's
    name begins where the id ends."""
    entries, at = [], 0
    pattern = re.compile(r" \((folder|file), (\d+) bytes\) file:///([^/\s]+)/")
    while True:
        mark = pattern.search(text, at)
        if not mark:
            break
        rest = text[mark.end():]
        shaped = BUSINESS_ID.match(rest)
        if not shaped:
            # An id of any other shape, a personal drive's among them, has
            # no length to end it, and a name may hold spaces, so only a
            # line's end or the listing's may.
            shaped = re.match(r"[^\s]+", rest)
            if not shaped or (shaped.end() < len(rest) and rest[shaped.end()] not in "\r\n"):
                raise ConnectorError("an entry's id runs into the next entry's name: list this folder "
                                     "with each entry on its own line")
        name = text[at:mark.start()].strip()
        if not name:
            raise ConnectorError("an entry of the listing has no name")
        entries.append({"name": name, "folder": mark.group(1) == "folder", "size": int(mark.group(2)),
                        "drive": mark.group(3), "id": shaped.group(0)})
        at = mark.end() + shaped.end()
    return entries


def read_walk(path):
    records = []
    if Path(path).exists():
        for line in Path(path).read_text(encoding="utf-8").splitlines():
            if line.strip():
                records.append(json.loads(line))
    return records


def nodes_of(records):
    """Every folder and file the walk has seen, by id, with its path and
    parent, the drive's top first."""
    nodes = {"root": {"id": "root", "path": TOP_NAME, "parent": "", "folder": True, "name": TOP_NAME,
                      "size": 0, "drive": next((r["drive"] for r in records), "")}}
    for record in records:
        parent = nodes.get(record.get("item"))
        if parent is None:
            continue
        for entry in record["entries"]:
            if entry["id"] in nodes:
                continue
            nodes[entry["id"]] = {**entry, "parent": parent["id"],
                                  "path": f"{parent['path']}/{drive_sync.segment(entry['name'])}"}
    return nodes


def add(walk_path, item, drive, text):
    """Keep one folder's listing; a folder read twice keeps its first."""
    records = read_walk(walk_path)
    if any(r.get("item") == item for r in records):
        return 0
    if item != "root" and item not in nodes_of(records):
        raise ConnectorError("that folder is not in the walk yet: read the drive's top first, then the "
                             "folders unlisted names")
    entries = parse_listing(text)
    if text.strip() and not entries:
        raise ConnectorError("the listing holds no entry this can read")
    with open(walk_path, "a", encoding="utf-8") as stream:
        stream.write(json.dumps({"item": item, "drive": drive, "entries": entries}) + "\n")
    return len(entries)


def search_hits(text):
    """The documents of sharepoint_search's answer, which writes them as
    JSON objects one after another, with its paging note among them."""
    decoder, at, hits = json.JSONDecoder(), 0, []
    while True:
        while at < len(text) and text[at].isspace():
            at += 1
        if at >= len(text):
            break
        try:
            value, at = decoder.raw_decode(text, at)
        except ValueError as problem:
            raise ConnectorError("the search answer is not the connector's JSON") from problem
        if isinstance(value, dict) and isinstance(value.get("id"), str):
            hits.append({"id": value["id"], "drive": str(value.get("driveId", "")),
                         "modified": str(value.get("lastModifiedDateTime") or ""),
                         "web": str(value.get("webUrl") or "")})
    return hits


def found(walk_path, text):
    """Keep the dates and links a search gave for items the walk has, and
    say how many it had."""
    records = read_walk(walk_path)
    nodes = nodes_of(records)
    hits = [h for h in search_hits(text) if h["id"] in nodes]
    if hits:
        with open(walk_path, "a", encoding="utf-8") as stream:
            stream.write(json.dumps({"search": hits}) + "\n")
    return len(hits)


def raw_path(nodes, node_id):
    """An item's path under the drive's top in the drive's own names."""
    names = []
    while node_id and node_id != "root":
        node = nodes[node_id]
        names.append(node["name"])
        node_id = node["parent"]
    return "/".join(reversed(names))


def web_base(nodes, hits):
    """The drive's web address, learnt from one link a search gave: the
    link less the item's path. OneDrive for work or school writes it as
    https://<tenant>-my.sharepoint.com/personal/<user>/Documents."""
    for hit in hits:
        relative = raw_path(nodes, hit["id"])
        for form in (relative, urllib.parse.quote(relative)):
            if hit["web"].startswith("https://") and relative and hit["web"].endswith("/" + form):
                return hit["web"][:-len(form) - 1]
    return ""


def dated(records, nodes):
    """Each item's date and link: a search's where it gave them, else a
    link made from the drive's web address, else nothing."""
    hits = {}
    for record in records:
        for hit in record.get("search", []):
            hits.setdefault(hit["id"], hit)
    base = web_base(nodes, list(hits.values()))
    for node_id, node in nodes.items():
        hit = hits.get(node_id, {})
        web = hit.get("web", "")
        if not web.startswith("https://"):
            web = f"{base}/{urllib.parse.quote(raw_path(nodes, node_id))}" if base and node_id != "root" else ""
        node["web"] = web
        node["modified"] = hit.get("modified", "")
    return nodes


def managed(entry):
    return entry["parent"] == "root" and entry["name"].strip().lower() in MANAGED


def unlisted(records):
    """The folders still to read, shallowest first, with what keeps any
    from being read: a folder of the apps' own, the depth or the size."""
    nodes, listed = nodes_of(records), {r["item"] for r in records if "item" in r}
    if "root" not in listed:
        return {"next": [{"item": "root", "path": TOP_NAME}], "left": []}, False
    todo, left = [], []
    stopped = len(nodes) >= drive_organize.MAX_NODES
    for entry in nodes.values():
        if not entry["folder"] or entry["id"] in listed:
            continue
        depth = entry["path"].count("/")
        if managed(entry):
            left.append(f"{entry['path']}: kept by Microsoft 365's apps, not read")
        elif depth > drive_organize.MAX_DEPTH:
            left.append(f"{entry['path']}: deeper than {drive_organize.MAX_DEPTH} levels, not listed")
        elif not stopped:
            todo.append({"item": entry["id"], "path": entry["path"],
                         "uri": f"file:///{entry['drive']}/{entry['id']}"})
    todo.sort(key=lambda e: (e["path"].count("/"), e["path"]))
    return {"next": todo, "left": left}, stopped


def catalog(records):
    """The workflow's catalog (drive_organize.catalog_of) from the walk, with
    each entry's parent, which the moves need."""
    nodes = dated(records, nodes_of(records))
    status, stopped = unlisted(records)
    problems = status["left"] + [f"{e['path']}: not read yet" for e in status["next"]]
    entries = [{"id": n["id"], "path": n["path"], "drive": n["drive"], "folder": n["folder"], "name": n["name"],
                "mime": "", "size": n["size"], "modified": n["modified"], "web": n["web"]} for n in nodes.values()]
    made = drive_organize.catalog_of("microsoft", entries, problems, stopped)
    made["source"] = "connector"
    made["parents"] = {n["id"]: n["parent"] for n in nodes.values() if n["parent"]}
    made["managed"] = sorted(n["path"] for n in nodes.values() if n["id"] != "root" and managed(n))
    return made


def write_catalog(records, out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    made = catalog(records)
    (out / "catalog.json").write_text(json.dumps(made, indent=1) + "\n", encoding="utf-8")
    (out / "TREE.md").write_text(drive_organize.tree(made), encoding="utf-8")
    return {"folders": len(made["folders"]), "files": len(made["files"]), "unlisted": len(made["problems"])}


# The plan

def lookup_of(made):
    return {entry["path"]: entry for entry in made["folders"] + made["files"]}


def check(plan, made):
    """What of the session's plan the catalog does not hold, project by
    project, so the session corrects its paths before anything opens."""
    lookup, report = lookup_of(made), []
    for project in plan.get("projects", []):
        slug = str(project.get("slug", ""))
        paths = list(project.get("folders", [])) + list(project.get("files", []))
        unknown = [p for p in paths if str(p).strip().strip("/") not in lookup]
        problems = []
        if not drive_organize.SLUG.fullmatch(slug):
            problems.append("the slug is not lowercase letters, digits and dashes")
        if not project.get("tasks"):
            problems.append("no tasks")
        if project.get("domain") not in drive_organize.DOMAINS:
            problems.append("a domain outside the list")
        repo = project.get("repository")
        if repo and not isinstance(repo, dict):
            problems.append("repository is not an object")
        elif repo and not drive_organize.REPO_NAME.fullmatch(str(repo.get("name", ""))):
            problems.append("a repository name GitHub would refuse")
        report.append({"slug": slug, "paths": len(paths), "unknown": unknown, "problems": problems})
    return report


# The moves

def folder_name(text):
    """A project's title as a OneDrive folder name."""
    cleaned = re.sub(r'[\x00-\x1f<>:"/\\|?*#%]', " ", str(text))
    cleaned = re.sub(r"\s+", " ", cleaned).strip().strip(".")
    return cleaned[:80] or "Project"


def free_name(name, taken):
    if name.lower() not in taken:
        taken.add(name.lower())
        return name
    stem, dot, ext = name.rpartition(".") if "." in name[1:] else (name, "", "")
    number = 2
    while f"{stem} ({number}){dot}{ext}".lower() in taken:
        number += 1
    taken.add(f"{stem} ({number}){dot}{ext}".lower())
    return f"{stem} ({number}){dot}{ext}"


def kept_by_apps(made):
    """The paths of the folders Microsoft 365's apps keep, read from each
    folder's name and parent, not from any list the catalog carries."""
    parents = made["parents"]
    return [f["path"] for f in made["folders"]
            if parents.get(f["id"]) == "root" and f["path"].rpartition("/")[2].strip().lower() in MANAGED]


def movable(entry, managed_paths):
    """Whether an entry may move: never the drive's top, a folder of the
    apps' own or what is inside one, nor what is in Symphony projects already."""
    path = entry["path"]
    if "/" not in path:
        return False
    first = path.split("/")[1]
    if first == HOME or any(path == m or path.startswith(m + "/") for m in managed_paths):
        return False
    return True


def plan_moves(plan, made):
    """The moves a plan asks for, in the order to make them: the home
    folder, each project's folder, then its items. An item inside another
    that moves goes with it, and an item two projects name goes to the first."""
    if made.get("source") != "connector" or not isinstance(made.get("parents"), dict):
        raise ConnectorError("moves takes a catalog this tool wrote from a walk, which names each item's parent")
    lookup, parents, managed_paths = lookup_of(made), made["parents"], kept_by_apps(made)
    drive = next((e["drive"] for e in made["files"] + made["folders"] if e["drive"]), "")
    ops = [{"op": "create", "key": "home", "name": HOME, "parent": "root", "state": "todo"}]
    chosen, skipped, homes, slugs = [], [], set(), set()
    for project in plan.get("projects", [])[:drive_organize.MAX_PROJECTS]:
        slug = str(project.get("slug", ""))
        if not drive_organize.SLUG.fullmatch(slug) or slug in slugs:
            continue
        slugs.add(slug)
        for path in list(project.get("folders", [])) + list(project.get("files", [])):
            entry = lookup.get(str(path).strip().strip("/"))
            if entry is None:
                skipped.append(f"{path}: not in the catalog")
            elif not movable(entry, managed_paths):
                skipped.append(f"{entry['path']}: the drive's top, a folder of Microsoft 365's apps, or moved before")
            else:
                chosen.append((slug, project, entry))
    paths = sorted({c[2]["path"] for c in chosen})
    covered = {p for p in paths if any(p.startswith(q + "/") for q in paths if q != p)}
    taken, seen, made_for = {}, set(), set()
    for slug, project, entry in chosen:
        if entry["path"] in covered:
            skipped.append(f"{entry['path']}: moves with the folder that holds it")
            continue
        if entry["id"] in seen:
            skipped.append(f"{entry['path']}: named by two projects, goes to the first")
            continue
        seen.add(entry["id"])
        if slug not in made_for:
            made_for.add(slug)
            ops.append({"op": "create", "key": slug, "name": free_name(folder_name(project.get("title", slug)), homes),
                        "parent": "@home", "state": "todo"})
        name = entry["path"].rpartition("/")[2]
        actual = entry.get("name") or name
        new = free_name(actual, taken.setdefault(slug, set()))
        if not parents.get(entry["id"]):
            raise ConnectorError(f"the catalog names no parent for step {len(ops)}, so it could not be undone")
        ops.append({"op": "move", "item": entry["id"], "path": entry["path"], "to": f"@{slug}",
                    "name": actual, "new_name": new if new != actual else "",
                    "back": parents.get(entry["id"], ""), "state": "todo"})
    if len(ops) > MAX_OPS:
        raise ConnectorError(f"the plan asks for {len(ops)} steps, more than {MAX_OPS}: fewer, larger folders")
    return {"drive": drive, "approved": False, "ops": ops, "skipped": skipped, "ids": {}}


def moves_markdown(moves):
    lines = ["# What would move", "",
             f"{sum(op['op'] == 'move' for op in moves['ops'])} items into {HOME}/, "
             f"{sum(op['op'] == 'create' for op in moves['ops'])} new folders. Nothing has moved; "
             "the owner reads this and says go. Every move can be undone.", ""]
    names = {op["key"]: op["name"] for op in moves["ops"] if op["op"] == "create"}
    for number, op in enumerate(moves["ops"]):
        if op["op"] == "create":
            where = f"{HOME}/" if op["key"] == "home" else f"{HOME}/{op['name']}/"
            lines.append(f"{number}. new folder `{where}`")
            continue
        target = f"`{HOME}/{names[op['to'][1:]]}/`" if op["to"].startswith("@") else "the folder it came from"
        rename = f", renamed `{op['new_name']}`" if op["new_name"] else ""
        lines.append(f"{number}. move `{op['path']}` to {target}{rename}")
    if moves["skipped"]:
        lines += ["", "## Left where they are", ""] + [f"- {line}" for line in moves["skipped"]]
    return "\n".join(lines) + "\n"


def resolve(ref, ids):
    if ref == "root":
        return "root"
    if ref.startswith("@"):
        if ref[1:] not in ids:
            raise ConnectorError(f"step for {ref[1:]} has not been made yet")
        return ids[ref[1:]]
    return ref


def next_call(moves):
    """The one connector call to make next, or None when every step is done."""
    if not moves["approved"]:
        raise ConnectorError("the moves are not approved: show the owner MOVES.md and run approve only on their word")
    for number, op in enumerate(moves["ops"]):
        if op["state"] == "done":
            continue
        if op["op"] == "create":
            args = {"driveId": moves["drive"], "name": op["name"], "conflictBehavior": "fail"}
            parent = resolve(op["parent"], moves["ids"])
            if parent != "root":
                args["parentItemId"] = parent
            return {"op": number, "tool": "sharepoint_create_folder", "arguments": args,
                    "then": f"done --op {number} --id <the new folder's id>"}
        args = {"driveId": moves["drive"], "itemId": op["item"],
                "destinationParentItemId": resolve(op["to"], moves["ids"])}
        if op["new_name"]:
            args["newName"] = op["new_name"]
        return {"op": number, "tool": "sharepoint_move_item", "arguments": args, "then": f"done --op {number}"}
    return None


def done(moves, number, new_id=None):
    if not moves["approved"]:
        raise ConnectorError("the moves are not approved, so no step has been made")
    if not 0 <= number < len(moves["ops"]):
        raise ConnectorError(f"there is no step {number}")
    op = moves["ops"][number]
    if op["op"] == "create":
        if not new_id or not re.fullmatch(r"[A-Za-z0-9!_.-]{1,200}", new_id):
            raise ConnectorError("a new folder's step needs --id, the id the connector gave it")
        moves["ids"][op["key"]] = new_id
    op["state"] = "done"
    return moves


def undo(moves):
    """A plan that moves back each item that moved, last first, to the
    folder it came from under its own name. It creates and deletes nothing;
    the empty folders are listed for the owner."""
    ops = []
    for op in reversed(moves["ops"]):
        if op["op"] == "move" and op["state"] == "done" and op["back"]:
            ops.append({"op": "move", "item": op["item"], "path": f"{HOME}/.../{op['new_name'] or op['name']}",
                        "to": op["back"], "name": op["new_name"] or op["name"],
                        "new_name": op["name"] if op["new_name"] else "", "back": "", "state": "todo"})
    empty = [op["name"] for op in moves["ops"] if op["op"] == "create" and op["state"] == "done"]
    return {"drive": moves["drive"], "approved": False, "ops": ops, "ids": {},
            "skipped": [f"{name}: a folder this made, left for the owner to delete if it is empty" for name in empty]}


# The command line

def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def save(path, value):
    Path(path).write_text(json.dumps(value, indent=1) + "\n", encoding="utf-8")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    adding = sub.add_parser("add")
    adding.add_argument("--walk", required=True)
    adding.add_argument("--item", required=True)
    adding.add_argument("--drive", required=True)
    adding.add_argument("--raw", required=True)
    sub.add_parser("unlisted").add_argument("--walk", required=True)
    finding = sub.add_parser("found")
    finding.add_argument("--walk", required=True)
    finding.add_argument("--raw", required=True)
    cataloging = sub.add_parser("catalog")
    cataloging.add_argument("--walk", required=True)
    cataloging.add_argument("--out", required=True)
    for name in ("check", "moves"):
        command = sub.add_parser(name)
        command.add_argument("--plan", required=True)
        command.add_argument("--catalog", required=True)
        command.add_argument("--out", required=name == "moves")
    for name in ("approve", "next", "undo"):
        sub.add_parser(name).add_argument("--moves", required=True)
    recording = sub.add_parser("done")
    recording.add_argument("--moves", required=True)
    recording.add_argument("--op", required=True, type=int)
    recording.add_argument("--id")
    args = parser.parse_args(argv)
    try:
        print(json.dumps(run(args), indent=1))
    except (ConnectorError, KeyError, ValueError, OSError) as problem:
        print(f"drive_connector: {problem}", file=sys.stderr)
        return 1
    return 0


def run(args):
    if args.command == "add":
        text = Path(args.raw).read_text(encoding="utf-8")
        return {"added": add(args.walk, args.item, args.drive, text)}
    if args.command == "found":
        return {"kept": found(args.walk, Path(args.raw).read_text(encoding="utf-8"))}
    if args.command == "unlisted":
        status, stopped = unlisted(read_walk(args.walk))
        return {"next": status["next"][:20], "waiting": len(status["next"]), "left": status["left"], "stopped": stopped}
    if args.command == "catalog":
        return write_catalog(read_walk(args.walk), args.out)
    if args.command == "check":
        return check(load(args.plan), load(args.catalog))
    if args.command == "moves":
        moves = plan_moves(load(args.plan), load(args.catalog))
        out = Path(args.out)
        out.mkdir(parents=True, exist_ok=True)
        save(out / "moves.json", moves)
        (out / "MOVES.md").write_text(moves_markdown(moves), encoding="utf-8")
        return {"steps": len(moves["ops"]), "skipped": len(moves["skipped"]), "review": str(out / "MOVES.md")}
    moves = load(args.moves)
    if args.command == "approve":
        moves["approved"] = True
        save(args.moves, moves)
        return {"approved": True, "steps": len(moves["ops"])}
    if args.command == "next":
        return next_call(moves) or {"done": True}
    if args.command == "done":
        save(args.moves, done(moves, args.op, args.id))
        return next_call(moves) or {"done": True}
    back = undo(moves)
    target = Path(args.moves).with_name("undo.json")
    if target.exists():
        raise ConnectorError(f"{target} is there already, with its own progress: run it, or move it away first")
    save(target, back)
    (target.with_name("UNDO.md")).write_text(moves_markdown(back).replace("What would move", "What would move back"),
                                             encoding="utf-8")
    return {"steps": len(back["ops"]), "plan": str(target)}


if __name__ == "__main__":
    sys.exit(main())
