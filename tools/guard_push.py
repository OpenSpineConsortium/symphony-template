"""Refuse a git push the board rules forbid, before it runs: a shim.

Claude Code runs this as a PreToolUse hook on the Bash tool
(.claude/settings.json): the tool call arrives as JSON on stdin, exit
code 2 stops it, and stderr goes back into the session as the reason.
The rules are .claude/rules/board.md's, and their code now lives in the
claim protocol's library, OpenSpineConsortium/symphony-protocol, vendored
here as tools/sdlc_protocol (tools/VENDORED names the version and the
commit). This file stays because the hook and every copy of the template
already made run "python3 tools/guard_push.py".

The rule functions are the library's, re-exported under their old names,
so tests/test_guard_push.py exercises the library's code unchanged. main()
is the library's guard.run written out here, because the tests and any
caller patch this module's branches(), which the library's run() would
not see. Anything the guard cannot read it lets through rather than
wedging the session; branch protection on GitHub refuses what matters.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from sdlc_protocol import guard  # noqa: E402
from sdlc_protocol.guard import branches, plain_shell, push_arguments, refusal, simple_commands  # noqa: E402,F401


def main():
    try:
        payload = json.load(sys.stdin)
    except ValueError:
        return guard.PASS
    command = guard.command_of(payload)
    if "push" not in command:
        return guard.PASS
    pushes = [args for argv in simple_commands(command)
              if (args := push_arguments(argv)) is not None]
    if not pushes:
        return guard.PASS
    current, default = branches(guard.where_to_ask(payload, None))
    for args in pushes:
        reason = refusal(args, current, default)
        if reason:
            print(reason, file=sys.stderr)
            return guard.REFUSE
    return guard.PASS


if __name__ == "__main__":
    sys.exit(main())
