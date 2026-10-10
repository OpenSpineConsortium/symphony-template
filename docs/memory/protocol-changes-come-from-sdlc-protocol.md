A change to the claim protocol is made in OpenSpineConsortium/sdlc-protocol and reaches this repository by that repository's sync pull request; tools/sdlc_protocol is never edited here.

tools/sdlc_protocol is a vendored copy of the package sdlc_protocol, and
tools/VENDORED records it: the release and the commit on the first line,
then the sha256 of every copied file. scripts/check.sh runs
`python3 tools/sdlc_protocol/vendoring.py verify tools` before the tests, so
a pull request that edits the copy by hand, adds a file to it or loses one
fails the required check, offline. A fix to the board, the protocol check,
team mode's clerk or the push guard is therefore a pull request to
sdlc-protocol. Its CI runs this repository's own check against the change
(the job `downstream (sdlc-template)`) before it merges, and the push to its
main starts its workflow Sync, which vendors the change here and opens, or
updates, the pull request from the branch `sdlc-protocol/sync`, made with
the App OpenSpine SDLC's token so this repository's CI runs on it, with
auto-merge on where the repository allows it; this repository's check
decides. The same sync reaches coordbench, sdlc-marketplace and sdlc-app:
sdlc-protocol's ecosystem.json lists which repository takes which modules,
and its ECOSYSTEM.md, generated from that list, maps all five.

What is this repository's own changes here as usual: the shims
tools/board.py, check_protocol.py, team.py and guard_push.py, the workflows
and the hooks. To vendor by hand, from a clone of sdlc-protocol:
`python3 <sdlc-protocol>/scripts/vendor.py <this repository>`. A repository
made from the template is not on the sync's list, so its owner adds
`--consumer OpenSpineConsortium/sdlc-template` to the same command. The
owner's one-time setup for the sync is docs/setup/owner-checklist.md,
section 6.

Source: the pull request from the branch claude/festive-edison-al7xu2 that
brought the sync and sdlc-protocol 0.2.0 to all five repositories.
