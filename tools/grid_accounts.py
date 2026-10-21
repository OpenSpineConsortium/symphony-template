"""The grid's Claude accounts, as the control panel's Grid tab reads them.

.github/workflows/grid-accounts.yml says one word to the grid's ssh gate
(hpcworker's tools/grid_gate.sh, the accounts words of framework 21) and
hands its answer here. This module keeps what the panel shows and nothing
more: the list of accounts the gate printed as its HPCW-ACCOUNTS-JSON line,
each e-mail masked to its first two letters and its domain, since the
branch grid that holds it is read by everyone who may read the
repository; the gate's own plain lines, masked the same way; and how the
call ended. Anthropic's sign-in link never passes through here: the
workflow seals it for the browser that asked and writes only the sealed
form (docs/setup/grid.md, Several Claude accounts).

    python3 tools/grid_accounts.py record OUT --action A --slot N --request R --rc RC < gate-output
    python3 tools/grid_accounts.py state FILE SLOT     the login state of one account, or none
    python3 tools/grid_accounts.py usage-running FILE  exit 0 while the usage job runs
    python3 tools/grid_accounts.py link < gate-output  Anthropic's link, only from its own hosts
"""

import argparse
import json
import re
import sys
import time

EMAIL = re.compile(r"([A-Za-z0-9._%+-]{1,64})@([A-Za-z0-9.-]{1,253}\.[A-Za-z]{2,63})")
LINK = re.compile(r"^AUTH-URL: (https://(?:claude\.ai|claude\.com)/[A-Za-z0-9._~:/?#@!$&'()*+,;=%-]{1,2000})$")
SAID = re.compile(r"^(HPCW-ACCOUNTS|HPCW-GRID-GATE) ")
JSON_LINE = "HPCW-ACCOUNTS-JSON "


def mask_email(match):
    """a.person@example.edu as a.***@example.edu: enough to tell two accounts apart."""
    return match.group(1)[:2] + "***@" + match.group(2)


def masked(value):
    """Every string in a JSON value with its e-mails masked."""
    if isinstance(value, str):
        return EMAIL.sub(mask_email, value)
    if isinstance(value, list):
        return [masked(v) for v in value]
    if isinstance(value, dict):
        return {k: masked(v) for k, v in value.items()}
    return value


def listing_in(lines):
    """The last list the gate printed, as an object, or None."""
    for line in reversed(lines):
        if line.startswith(JSON_LINE):
            try:
                found = json.loads(line[len(JSON_LINE):])
            except ValueError:
                continue
            if isinstance(found, dict):
                return found
    return None


def said_in(lines):
    """The gate's and the tool's own plain lines, never a link and at most twenty."""
    kept = [EMAIL.sub(mask_email, l)[:300] for l in lines if SAID.match(l) and "AUTH-URL" not in l]
    return kept[-20:]


def record(lines, action, slot, request, rc):
    """What the branch grid keeps of one call."""
    listing = listing_in(lines)
    return {
        "v": 1,
        "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "action": action,
        "slot": slot,
        "request": request,
        "rc": rc,
        "said": said_in(lines),
        "list": masked(listing) if listing is not None else None,
    }


def login_state(listing, slot):
    """One account's sign-in state in a list, or none."""
    for account in (listing or {}).get("accounts") or []:
        if isinstance(account, dict) and account.get("slot") == slot:
            return ((account.get("login") or {}).get("state")) or "none"
    return "none"


def link_in(lines):
    """Anthropic's sign-in link the gate printed, only from Anthropic's own hosts."""
    for line in reversed(lines):
        found = LINK.match(line.strip())
        if found:
            return found.group(1)
    return ""


def read_record(path):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return {}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    rec = sub.add_parser("record")
    rec.add_argument("out")
    rec.add_argument("--action", required=True)
    rec.add_argument("--slot", default="")
    rec.add_argument("--request", default="")
    rec.add_argument("--rc", type=int, default=0)
    st = sub.add_parser("state")
    st.add_argument("file")
    st.add_argument("slot")
    us = sub.add_parser("usage-running")
    us.add_argument("file")
    sub.add_parser("link")
    args = parser.parse_args(argv)
    if args.command == "record":
        lines = sys.stdin.read().splitlines()
        with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(record(lines, args.action, args.slot, args.request, args.rc), fh, indent=1, sort_keys=True)
            fh.write("\n")
        return 0
    if args.command == "state":
        print(login_state(read_record(args.file).get("list"), args.slot))
        return 0
    if args.command == "usage-running":
        return 0 if (read_record(args.file).get("list") or {}).get("usage_job") == "running" else 1
    found = link_in(sys.stdin.read().splitlines())
    if found:
        print(found)
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
