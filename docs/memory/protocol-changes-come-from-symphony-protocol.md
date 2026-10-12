A change to the claim protocol is made in OpenSpineConsortium/symphony-protocol, whose sync pull request brings it to OpenSpineConsortium/symphony-template and whose release tags a repository made from the template takes by its own workflow, protocol.yml; tools/sdlc_protocol is never edited in place.

tools/sdlc_protocol is a vendored copy of the package sdlc_protocol, and
tools/VENDORED records it: the release and the commit on the first line,
then the sha256 of every copied file. scripts/check.sh runs
`python3 tools/sdlc_protocol/vendoring.py verify tools` before the tests, so
a pull request that edits the copy by hand, adds a file to it or loses one,
and leaves VENDORED as it was, fails the required check, offline. VENDORED
sits in the same tree, so the same pull request could rewrite it to match;
CI therefore clones symphony-protocol, which is public, and names the clone in
SDLC_PROTOCOL, and tests/test_vendored.py compares every file of the copy
with the library's at the commit VENDORED names, failing when they differ
or when the clone has no such commit. A fix to the board, the protocol
check, team mode's clerk or the push guard is therefore a pull request to
symphony-protocol.

The template itself, OpenSpineConsortium/symphony-template, then receives the
change with nothing done by hand. symphony-protocol's CI runs the template's own
check against the change (the job `downstream (symphony-template)`) before it
merges, and the push to its main starts its workflow Sync, which vendors the
change into the template and opens, or updates, the pull request from the
branch `symphony-protocol/sync`, made with the App Symphony's token so the
template's CI runs on it, with auto-merge on where the repository allows it;
the template's check decides. The same sync reaches coordbench,
symphony-marketplace and symphony-app: symphony-protocol's ecosystem.json lists which
repository takes which modules, and its ECOSYSTEM.md, generated from that
list, maps all five.

A repository made from the template is not on that list, so no sync pull
request reaches it. Its own .github/workflows/protocol.yml takes each
release instead: symphony-protocol tags every version that reaches its main
by itself (its release.yml), and the copy's workflow, weekly and by hand,
vendors the newest tag when it is newer than tools/VENDORED, on the branch
`symphony-protocol/sync`, and opens the pull request with GITHUB_TOKEN, or
an issue linking it where GitHub Actions may not open pull requests. A
push or pull request made with GITHUB_TOKEN starts no workflow, so the run
starts ci.yml on the branch (its workflow_dispatch) for the required
check, and arms auto-merge, which lands it once the check is green where
the repository allows it. tools/protocol_update.py holds what it decides
and says. By hand it is
`python3 <symphony-protocol>/scripts/vendor.py <this repository> --consumer OpenSpineConsortium/symphony-template`,
which copies what the template takes, and a pull request; in the template
the same command needs no `--consumer`, since its remote names it.

What is this repository's own changes here as usual: the shims
tools/board.py, check_protocol.py, team.py and guard_push.py, the workflows
and the hooks. The owner's one-time setup for the sync is
docs/setup/owner-checklist.md, section 6.

Source: symphony-protocol 0.3.1, its ecosystem.json and its README's sections
"How a change reaches the other repositories", "The owner's one-time setup
for the sync" and "Releases"; this repository's .github/workflows/protocol.yml.
