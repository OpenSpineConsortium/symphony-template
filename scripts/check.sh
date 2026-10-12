#!/usr/bin/env bash
# The project's fast checks, run by CI (.github/workflows/ci.yml, the job
# "check" that branch protection requires) and by hand before a pull
# request. The documents come first because they are the Claude project's
# instructions and memory: a broken import or a stray secret is a broken
# project. Add the project's own lines where marked below.
set -eu
cd "$(dirname "$0")/.."

python3 tools/check_docs.py
# The claim protocol's copy must be byte for byte what tools/VENDORED
# records: a change to it is made in OpenSpineConsortium/symphony-protocol and
# arrives by that repository's sync pull request in the template, or by its
# scripts/vendor.py in a repository made from it, so a hand edit fails here.
# A hand edit that rewrote VENDORED to match passes this line and fails
# tests/test_vendored.py, which compares the copy with the library itself
# in the clone SDLC_PROTOCOL names (CI clones it; .github/workflows/ci.yml).
python3 tools/sdlc_protocol/vendoring.py verify tools
# Every worker's file under .github/symphony/workers/ must hold together
# (docs/agents/WORKERS.md): a misspelt setting or a name that is no label
# fails here, before the workflows that read the registry would.
python3 tools/workers.py check
python3 -m unittest discover -s tests -v

# The project's own checks go here: its linter, its test runner, its build.

echo "checks ok"
