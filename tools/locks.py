"""The locks of the claim protocol, in a clone: a shim.

The code lives in the claim protocol's library,
OpenSpineConsortium/symphony-protocol, vendored here as tools/sdlc_protocol
(tools/VENDORED names the version and the commit). This file hands its
arguments to "python3 -m sdlc_protocol locks", as tools/board.py and
tools/check_protocol.py hand theirs to board and check, so a workflow and a
person run the same thing: "python3 tools/locks.py overlap --base
origin/main" says whether a change must bring the default branch in, and
status, plan, acquire, release, sweep and verify keep the lock table on the
branch locks (docs/agents/PROTOCOL.md, Locks). verify and overlap obey the
switch .github/symphony-locks, or SYMPHONY_LOCKS in the environment: off,
advise or enforce.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from sdlc_protocol.cli import main as protocol_main  # noqa: E402


def main(argv=None):
    return protocol_main(["locks", *(sys.argv[1:] if argv is None else argv)])


if __name__ == "__main__":
    sys.exit(main())
