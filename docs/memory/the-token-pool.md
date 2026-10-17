The branch pool holds each Claude slot's latest usage readings (five-hour, seven-day, per-model limits such as Fable), written by tools/pool.py from runs, from pool.yml's one-word probes and from cswap through tokens.py usage; pool.py pick is the auto mode.

A runner cannot read a token's usage page, since a token from claude
setup-token is inference-only, so the five-hour and seven-day windows
come from Claude's own rate_limit_event (every run and pool.yml's probe)
and the Fable weekly limit only from cswap on the owner's machine
(`python3 scripts/tokens.py usage`). One file per slot and kind
(slot-N.run|probe|cswap.json) on the branch pool, one commit with no
history, no token, e-mail or text. A probe spends one word of the
window it reads, so pool.yml probes only on Run workflow or the panel's
Refresh, never on a schedule (the owner's choice, 2026-10-17). pick takes the least used five-hour, then
seven-day window, passing over a slot held at 90 percent until its
reset. .github/symphony/accounts.json gives each worker in Actions
main, a slot or auto (no file: main), and workers.yml records each run's
reading. The picker moves to the protocol library after 0.5.1 is cut.
docs/research/claude-token-pool.md has the sources and the four steps;
from the token wizard's thread, 2026-10-17.
