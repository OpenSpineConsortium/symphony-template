#!/usr/bin/env bash
# The project's fast checks, run by CI (.github/workflows/ci.yml, the job
# "check" that branch protection requires) and by hand before a pull
# request. The documents come first because they are the Claude project's
# instructions and memory: a broken import or a stray secret is a broken
# project. Add the project's own lines where marked below.
set -eu
cd "$(dirname "$0")/.."

python3 tools/check_docs.py
python3 tools/project_export.py --check
python3 -m unittest discover -s tests -v

# The project's own checks go here: its linter, its test runner, its build.

echo "checks ok"
