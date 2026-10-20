---
name: grid-ashley-deletion-2026-09-28
description: On 2026-09-28 22:34 local the whole ~/.ashley folder on the grid (Claude login, config, license, tokens) was deleted while a phone Remote Control session was open; cause unproven; destructive commands now refuse under CLAUDECODE; never let an agent context delete outside its own run dirs
metadata:
  type: feedback
---

At 22:34 local on 2026-09-28, `~/.ashley` on the WSU grid vanished entirely (the daemon inside the
still-running worker job recreated empty `bin/`, `claude/`, `workers/default/rc`). The `.bashrc`
block and the worker job survived, so it was not `ashley uninstall`; the build agents' transcripts
contain no deleting command touching it; the new framework has no such path. The only activity in
that minute was a new Remote Control session spawned from Greg's phone (`~/.claude/bridge-spawn`
created 22:34); its transcript lived inside the deleted folder. Greg had to sign in a fourth time.

**Why it matters:** a Claude Code session on the cluster can run anything the student can, and a
"clean up"/"reinstall" prompt can wipe the installation and the login.

**How to apply:** every destructive subcommand in Ashley (`uninstall`, `claude forget`) and in
hpcworker refuses when `CLAUDECODE`, `ASHLEY_REQUEST_ID`, `ASHLEY_WORKER` or a similar agent marker
is set or stdin is not a terminal (grid scripts v6). The framework's removers accept only its own
per-job directories (`hpcworker_<id>`, `hpcw_<id>`). Keep worker permission mode supervised by
default. When something disappears on the grid, check the `.bashrc` block, the worker job and the
agent transcripts before blaming a tool. Related: [[ashley-extension-project]], [[ashley-bridge-project]].
