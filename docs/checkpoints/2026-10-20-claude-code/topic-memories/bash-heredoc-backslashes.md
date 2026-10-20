---
name: bash-heredoc-backslashes
description: "The Bash tool's heredocs collapse `\\\\` to `\\` in inline Python (regex/LaTeX strings break); write scripts with the Write tool and run them by path"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: e44eca96-f48c-494d-ba1f-7dae68bdf06d
  modified: 2026-09-13T13:17:46.251Z
---

Inline `python - <<'EOF'` in the Bash tool is not safe for code that contains
backslashes: `\\,` arrived in Python as `\,`, `(?<!\\)` became an invalid regex, and
LaTeX-editing scripts silently failed or raised. The same happened with nested ssh quoting.

**Why:** the heredoc body passes through a layer that unescapes backslashes before Python
sees it; single-quoted `'EOF'` does not protect it here.

**How to apply:** for anything with backslashes (regex, LaTeX text, Windows paths), write
the script to the scratchpad with the Write tool and run `python <path>` / scp it to the
grid and `bash <path>`. Plain shell heredocs of data (a .bib append) were fine.
