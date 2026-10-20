---
name: scratchpad-shadows-stdlib
description: "A scratchpad script named like a stdlib module (numbers.py, io.py, pdb.py) hijacks every python run from that directory; symptom is a stray \"MISS ...\" line and exit 1 with no other output"
metadata:
  node_type: memory
  type: feedback
  originSessionId: f1bdbd78-151f-470b-b703-dd9af9b3fecc
  modified: 2026-09-26T00:07:30.161Z
---

2026-09-25: `python <script in scratchpad>` and `python -` with cwd = scratchpad both died with
`MISS '| threshold 0.74 ...' 0` and exit 1, twice, before the real script ran. Cause: the scratchpad held
`numbers.py` (an old NUMBERS.md patch script), `io.py` and `pdb.py`; python puts the script's directory (or '') first
on sys.path, so `import numbers` (pulled in by PIL, matplotlib and python-pptx) executed the patch script instead.
Moved them to `scratchpad/_shadowing/`.

**Why:** the symptom looks like a hook or a broken library and cost three tool calls to locate.

**How to apply:** never name a scratchpad script after a stdlib or installed module (numbers, io, pdb, types, copy,
json, re, tables, ...); when a python run from the scratchpad prints an unrelated line and exits 1, run
`python -c "import os,sys; print(sorted(set(f[:-3] for f in os.listdir('.') if f.endswith('.py')) & set(sys.stdlib_module_names)))"`
there first. Related: [[bash-heredoc-backslashes]].
