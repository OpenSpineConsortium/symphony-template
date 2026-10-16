# flowbench

A benchmark of workflows on SWE-bench's issues: the arms under
flowbench/arms/ are the flows under test, and everything else holds
still. README.md says what runs; the design, the pre-registration
(PLAN.md) and the parity table (PARITY.md) are the contract, and a
change to what is measured changes them first.

## Rules

- Nothing here holds or reads an API key or a Claude credential: the
  agents run as `claude -p` on the login's own subscription, and run.py
  drops ANTHROPIC_API_KEY and every other setting that would bill
  something else from their environment.
- No run that spends usage without the owner's word and the count; the
  fake modes (`--fake`, `--fake-agents`) are for everything before that.
- The task repository (the gold patch, the hidden tests) is never
  mounted, copied or named to an agent, and the prompts stay that way;
  the audit excludes a run whose agents' streams name it.
- SWE-bench's harness scores from the dataset `score.py build` compiles,
  never with `--task-repo`, which rebuilds the instance's image.
- Every arm's agents get the same prompt where their role is the same:
  the review lens texts are one file content in every arm that reviews.
- Transcripts and prompts never leave the host; a bundle carries result,
  prediction, events, audit and the harness's log.
- Python 3.12 or later with its standard library, git and Docker; no new
  dependency without an issue first. ASCII and LF in every text file;
  plain prose that says why.
- `bash scripts/check.sh` passes before a pull request is marked ready.
