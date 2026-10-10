A change to the claim protocol is made in OpenSpineConsortium/sdlc-protocol, whose sync pull request brings it to OpenSpineConsortium/sdlc-template and whose scripts/vendor.py brings it, by hand, to a repository made from the template; tools/sdlc_protocol is never edited in place.

tools/sdlc_protocol is a vendored copy of the package sdlc_protocol, and
tools/VENDORED records it: the release and the commit on the first line,
then the sha256 of every copied file. scripts/check.sh runs
`python3 tools/sdlc_protocol/vendoring.py verify tools` before the tests, so
a pull request that edits the copy by hand, adds a file to it or loses one
fails the required check, offline. A fix to the board, the protocol check,
team mode's clerk or the push guard is therefore a pull request to
sdlc-protocol.

The template itself, OpenSpineConsortium/sdlc-template, then receives the
change with nothing done by hand. sdlc-protocol's CI runs the template's own
check against the change (the job `downstream (sdlc-template)`) before it
merges, and the push to its main starts its workflow Sync, which vendors the
change into the template and opens, or updates, the pull request from the
branch `sdlc-protocol/sync`, made with the App OpenSpine SDLC's token so the
template's CI runs on it, with auto-merge on where the repository allows it;
the template's check decides. The same sync reaches coordbench,
sdlc-marketplace and sdlc-app: sdlc-protocol's ecosystem.json lists which
repository takes which modules, and its ECOSYSTEM.md, generated from that
list, maps all five.

A repository made from the template is not on that list, so no sync pull
request reaches it, and none is worth waiting for. Its owner, or a session
asked to, vendors a release from a clone of sdlc-protocol with
`python3 <sdlc-protocol>/scripts/vendor.py <this repository> --consumer OpenSpineConsortium/sdlc-template`,
which copies what the template takes, and lands it by pull request. In the
template the same command needs no `--consumer`, since its remote names it.

What is this repository's own changes here as usual: the shims
tools/board.py, check_protocol.py, team.py and guard_push.py, the workflows
and the hooks. The owner's one-time setup for the sync is
docs/setup/owner-checklist.md, section 6.

Source: sdlc-protocol 0.2.0, its ecosystem.json and its README's sections
"How a change reaches the other repositories" and "The owner's one-time
setup for the sync".
