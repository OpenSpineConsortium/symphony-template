# Automatic handoff at the weekly limit, and swapping whole accounts

Source: the thread "Automatic checkpoint and account handoff", 2026-10-23, from the owner's ask at 02:17 UTC: build automatic checkpointing and handoff in one step, in the style of handoff-2026-10-23.md, fired at 90 percent of the weekly limit, so that swapping whole accounts is trivial; and his question whether, with several grid runners each running Claude Code signed in to a different account and each serving a project in the cloud, swapping which account a project attaches to is nearly instant. Read on the day: Claude Code 2.1.309's binary (strings), hpcworker at d31482d (framework/lib/accounts.sh, framework/lib/accounts_read.py, framework/jobs/worker.sbatch.tpl), and this repository's tools/pool.py, docs/research/claude-token-pool.md and docs/research/grid-claude-accounts.md. No Claude Doc, artifact or upload lies behind it.

## The answer to the grid question, in short

Mechanically yes, for the account; no, for the conversation. On the grid the swap is a symbolic link moved in one rename (hpcworker's `accounts use N`, or auto mode at 90 percent of any window), and the worker's loop sees it on its next turn, stops Remote Control on the old account and starts it on the new one inside the same Slurm job, so no queue wait: seconds plus Remote Control's start, not yet timed on the grid. What does not move with it:

- The conversation. A Remote Control session belongs to the account that started it; the worker's own comment says the old session is not continued, since it belongs to the other account. The new account starts a new session with a new link.
- The prompt cache. It is kept per account, so a session that resumed the old transcript on the new account would pay its whole context again as cache writes, out of the new account's window. Resuming the transcript is not what saves the work.
- The person's side (inferred from Remote Control's sign-in, not tested with two accounts). claude.ai and the app show a Remote Control session only to the account that owns it, so the browser or app must be signed in to the new account; a browser profile per account, as the token wizard already keeps (docs/research/token-wizard.md), makes that one click. A claude.ai Project belongs to one account and cannot be moved or shared, so each account has its own Project on the same repository, as decided before.

So the speed of a swap is limited by what the next session must read to carry on, and that is what the handoff fixes: a committed page of a few thousand tokens, named by the session-start hook, in place of a conversation that cannot cross accounts. The other limits are each account's own windows (all sessions of one account share them), each worker's Slurm allocation, Remote Control being on the plan, the one sign-in sitting per account with a browser, the probe's word that auto mode spends every half hour, and the terms-of-service question about rotating accounts, which the owner decided on 2026-10-13 knowing it (docs/research/grid-claude-accounts.md).

## Switching which worker a claude.ai tab shows

The owner's follow-up at 02:32 UTC: he meant Beethoven on his own side switching which worker the claude.ai tab shows. Between workers on one account that is a change of link, instant. Between accounts it is not: claude.ai's sign-in lives in the browser profile, so one tab shows one account's sessions, and a Chrome extension has no call that opens a tab in another profile. The way that works is Beethoven in one Chrome profile per account, each opening its own account's workers and pointing to the right profile for the rest; asked of the coordinator as a thread of its own on beethoven-extension. The owner wants both: that switch of view, and the same worker moving itself to another account at the limit, which hpcworker's auto mode does and which now waits for the handoff.

## What can see the weekly window, measured in the binary

- The status line's input carries `rate_limits.five_hour` and `rate_limits.seven_day`, each with `used_percentage` (0 to 100) and `resets_at` (unix seconds), for subscribers after the first response. This is the only place an interactive session's own usage reaches a command the repository can name.
- A headless run's stream-json carries `rate_limit_event` with the same two windows as fractions; tools/pool.py reads it in Actions and hpcworker's auto mode keeps it on the grid as `accounts/<N>.use.json`.
- No hook's input carries either, as far as the binary shows: the input each hook event is built with names no rate-limit field, and this session's own transcript holds none. So a hook can only read what the status line or the grid wrote.
- A cloud session on claude.ai renders no status line that this session could see run, and its window is shown to the person in the web page alone. Whether Claude Code runs the status line command in a cloud session is not measured; until it is, the trigger there is the person's word ("hand off"), and the skill does the rest.

## What was built

- tools/handoff.py, with tests/test_handoff.py. `statusline` keeps the status line's reading in the git directory and prints `model | 5h N% | 7d N%`, with "handoff due" past the threshold. `hook`, on Stop, UserPromptSubmit and PostToolUse of Bash, tells the session once per window and session: as context while it works, or by holding the stop once at the end of a turn. `new` writes the skeleton under docs/checkpoints/<date>/ with git's facts filled in and each part to fill marked; `done PATH` refuses a page with a mark left, quiets the window and on the grid writes `accounts/<N>.handoff.json`; `latest` names the newest handoff committed in the last 72 hours, which the session-start hook prints.
- .claude/skills/handoff: the eight steps, from parking the work and landing research first to telling the person the next account may start.
- The switches: SYMPHONY_HANDOFF=off, SYMPHONY_HANDOFF_AT (percent, 90), SYMPHONY_HANDOFF_WINDOW (seven_day, five_hour or any). Nothing is said in GitHub Actions, where pool.py's pick already passes over a slot at 90 percent and a run ends by itself.
- The grid's contract: hpcworker writes `accounts/<N>.handoff-due` when auto mode is about to move a worker, the hook treats it as due whatever the window, and hpcworker waits for `accounts/<N>.handoff.json` newer than it, or a grace, before moving (the hpcworker pull request of the same thread).

The project's status line replaces a person's own while they work in this repository; one who prefers theirs sets `statusLine` in .claude/settings.local.json and loses only the local sensor.

## Not yet measured

- Whether the status line runs in a claude.ai cloud session or under `claude remote-control` on the grid. Under Remote Control the grid's own reading covers it.
- A real crossing of 90 percent end to end, and how long a grid swap takes from the link's move to the new link online.
