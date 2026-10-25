A change to the claim protocol is made in OpenSpineConsortium/symphony-protocol, whose sync pull request brings it to OpenSpineConsortium/symphony-template and whose release tags a repository made from the template takes by its own workflow, protocol.yml; tools/sdlc_protocol is never edited in place.

tools/sdlc_protocol is a vendored copy of the package sdlc_protocol, and
tools/VENDORED records it: the version and the commit on the first line,
then the sha256 of every copied file. scripts/check.sh runs
`python3 tools/sdlc_protocol/vendoring.py verify tools` before the tests, so
a pull request that edits the copy by hand, adds a file to it or loses one,
and leaves VENDORED as it was, fails the required check, offline. VENDORED
sits in the same tree, so the same pull request could rewrite it to match;
CI therefore clones symphony-protocol, which is public, and names the clone in
SDLC_PROTOCOL, and tests/test_vendored.py compares every file of the copy
with the library's at the commit VENDORED names, failing when they differ
or when the clone has no such commit. A fix to the board, the
coordinator's releases and overlaps, the registry of workers, the protocol
check, the clerk or the push guard is therefore a pull request to
symphony-protocol.

The template itself, OpenSpineConsortium/symphony-template, then receives the
change with nothing done by hand. symphony-protocol's CI runs the template's own
check against the change (the job `downstream (symphony-template)`) before it
merges. A change reaches the consumers in a release, with one exception:
a change the template's own check must answer, a rendered string its tests
pin or a function it calls that changes, comes here first, by a pull
request that vendors the library's branch (symphony-protocol's README, "A
change a consumer must answer"). From 0.4.1 to 0.5.1 each release waited
for the owner's approval in symphony-protocol's environment release (its
release.yml); since 2026-10-20 the merge that raises the version releases
on its own, and the approval comes back only in Developer mode (the
variable SYMPHONY_DEVELOPER_MODE on, symphony-protocol's README,
Releases). Its workflow Sync, which follows the Release run, weekly
and by hand, carries only the newest published release, from the commit
that raised main to its version, never main's head. Sync
vendors that release into the template and opens, or updates, the pull
request from the branch `symphony-protocol/sync`, made with the App Symphony's token so the
template's CI runs on it, with auto-merge on where the repository allows it;
the template's check decides. The same sync reaches coordbench,
symphony-marketplace and symphony-app: symphony-protocol's ecosystem.json lists which
repository takes which modules, and its ECOSYSTEM.md, generated from that
list, maps all five.

So between such a pull request and the release that carries its change,
the template runs ahead of the newest release. Its VENDORED then names
the version symphony-protocol's main raised and the last commit that
changed the package, since symphony-protocol's scripts/vendor.py records
that commit and not the one it copies from, so the sync of that release
finds the copy level, opens nothing and closes a sync pull request still
open; the template ran ahead so from symphony-template#78 (2026-10-14)
until 0.5.0 was published. A sync pull request that brings a release
newer than the version VENDORED names merges once the template's check
is green, as 0.7.0's did on 2026-10-25 (symphony-template#472). One that
would take the copy back below that version, as the sync of 0.4.1 did
while 0.5.0 waited for its approval, is a downgrade: close it each time
it comes back, and never turn it green, by regenerating a fixture or
otherwise.

A repository made from the template is not on that list, so no sync pull
request of symphony-protocol's reaches it, and the template's own offer to
adopted repositories (tools/sync_adopted.py) leaves a whole template's
copy alone. Its own .github/workflows/protocol.yml takes each
release instead: symphony-protocol's release.yml tags each version that
reaches its main, after the owner's approval in Developer mode, and the
copy's workflow, weekly and by hand,
vendors the newest tag when it is newer than tools/VENDORED, on the branch
`symphony-protocol/sync`, and opens the pull request with GITHUB_TOKEN, or
an issue linking it where GitHub Actions may not open pull requests. A
push or pull request made with GITHUB_TOKEN starts no workflow, so the run
starts ci.yml on the branch (its workflow_dispatch) for the required
check, and arms auto-merge, which lands it once the check is green where
the repository allows it. tools/protocol_update.py holds what it decides
and says. It reads tags, not releases, so a tag pushed by hand reaches the
copies before any approval (symphony-protocol's README, Releases). By hand
it is
`python3 <symphony-protocol>/scripts/vendor.py <this repository> --consumer OpenSpineConsortium/symphony-template`,
which copies what the template takes, and a pull request; in the template
the same command needs no `--consumer`, since its remote names it.
protocol.yml brings only tools/, so a release that changes what a copy's
tests pin reaches that copy by hand, with the template's answer to the
change copied in (docs/start/protocol.md, step 7): 0.5.0 changes the
board's Given to workers heading, which tests/fixtures/board-STATE.md
pins in a copy made before symphony-template#78.

In a copy whose ruleset requires more than the check, such as
SchwingNet's, which also requires gate, standards (every group green) and
owner-ok, the update's pull request does not land by itself: on
2026-10-25 GitHub created the pull_request runs of the one GITHUB_TOKEN
opened there (SchwingNet#313, 0.5.1 to 0.7.0) as action_required, with no
job run until someone who may write approved them on the pull request's
page, and owner-ok asks for the owner's tap on any pull request a bot
opened. Only the check that protocol.yml starts on the branch runs
without them, so such an update waits for the owner.

The template's push guard hook, tools/guard_push.py, calls the library's
simple_commands, push_arguments and refusal itself, never
guard.refused_push, so a guard fix that lives in refused_push's readings
(F21's clone, F24's substitutions, F25's here-document bodies and limits)
does not reach the hook until the shim calls guard.refused_push; that
switch is part of the template's follow-up for 0.5.1
(docs/research/protocol-fixes-after-0-5-0/README.md).

What is this repository's own changes here as usual: the shims
tools/board.py, check_protocol.py, team.py, workers.py and guard_push.py,
the workflows and the hooks. The owner's one-time setup for the sync is
docs/setup/owner-checklist.md, section 6.

Source: symphony-protocol 0.5.0, its ecosystem.json, scripts/vendor.py,
sync.yml and its README's sections "How a change reaches the other
repositories", "The owner's one-time setup for the sync" and "Releases";
this repository's .github/workflows/protocol.yml and
tools/protocol_update.py. The releases' paragraphs were brought up to date
on 2026-10-25, after 0.7.0's release and sync, from symphony-protocol's
README, Releases, and this repository's tools/sync_adopted.py.
