# Handoff: grid connection and one Slurm protocol (2026-10-22 00:02 UTC)

Done and live:
- hpcworker framework 27 on the grid (installed 2026-10-21 23:49 UTC, hpcworker 682ca31): `hpcworker job submit|status|log|cancel|version`, job interface 2. Every thread queues Slurm jobs through it; placement comes from the site profile.
- beethoven-sites #5: Wayne site module carries partitions_gpu gmsap,gvohp,galhp, qos_gpu gpu, node_domain nas.grid.wayne.edu.
- hpcworker #29 (framework 26) composes it; #30 (framework 27) has the SchwingNet thread's review fixes.
- beethoven-base #5 and #6: profile.ts gains jobClassOf, sbatchOptionsOf and nodeHostOf; the vscode export now carries profile.ts.

Open:
- beethoven-vscode #20 (draft, branch claude/project-thread-h72c2u, 15c0764) reads job placement and the node domain from base and the profile. Typecheck, 128 unit tests and the build pass. `npm run test:vscode` still has to run on a machine with VS Code (the cloud container cannot download it); the Remote Control run was stopped at greg's word before it reported.
- Next: move the promoter and CT priors jobs onto `hpcworker job` (the coordinator has been asked to pass this on). Multi-project grid workers plan https://claude.ai/artifact/UjuFBMxLEL8CnifRofU3Vv awaits greg's go. Grid tab account 2 needs one more Sign in press.

Pending request (00:02 UTC, from "Automated dataset PR review"; greg chose it on that thread's card): add a fixed gate word `promoter-restart` with no argument, in hpcworker's grid gate.
- It reads main's sha with gh, as promoter-start does.
- It fetches tools/promote.py and grid/promote.sh at that sha into $PROMOTER_DIR/code, each through a .tmp file and then mv, keeping the held() checks.
- It runs `promote.sh stop` and then `promote.sh start <sha>`.
- It passes HPCWORKER="$CLONE/framework/bin/hpcworker" to the promoter, as the schwingnet words do.
spine-datasets #121 is merged and waits on this word. Nothing has been started on it: greg ordered every thread to stop.
