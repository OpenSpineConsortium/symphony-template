#!/usr/bin/env bash
# The checks CI runs: every text file ASCII with LF endings, every arm's
# prompts filled by the runner's placeholders, and the tests. Run it
# before a pull request is marked ready.
set -euo pipefail
cd "$(dirname "$0")/.."

status=0
while IFS= read -r -d '' file; do
    case "$file" in
        ./.git/*|*/__pycache__/*) continue ;;
    esac
    if LC_ALL=C grep -q -P '[^\x00-\x7F]' "$file" 2>/dev/null; then
        echo "$file: not ASCII"
        status=1
    fi
    if LC_ALL=C grep -q $'\r' "$file" 2>/dev/null; then
        echo "$file: CRLF line endings"
        status=1
    fi
done < <(find . -type f \( -name '*.py' -o -name '*.md' -o -name '*.json' -o -name '*.yml' -o -name '*.sh' -o -name '*.yaml' -o -name '*.patch' -o -name 'LICENSE' \) -print0)

for arm in flowbench/arms/*/; do
    python3 flowbench/run.py arm "$(basename "$arm")" > /dev/null || status=1
done

python3 -m unittest discover -s tests -t . || status=1
exit $status
