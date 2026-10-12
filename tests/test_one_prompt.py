"""One prompt for every worker and one for the coordinator, wherever they
run: a routine pastes the short prompt of docs/agents/routines/worker.md or
coordinator.md, and .github/workflows/workers.yml and coordinator.yml pass
the same words, with GitHub's own values where the page has placeholders,
so a worker in Actions and a routine read the same full prompt and do the
same thing. The workflows also read the registry the way the library
reads it, so a worker's file decides its model, turns and rounds."""

import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORKFLOWS = ROOT / ".github" / "workflows"
ROUTINES = ROOT / "docs" / "agents" / "routines"
P = {"REPO": "{{" + "REPO" + "}}", "DEFAULT_BRANCH": "{{" + "DEFAULT_BRANCH" + "}}"}
sys.path.insert(0, str(ROOT / "tools"))


def short_prompt(page):
    return (ROUTINES / page).read_text(encoding="utf-8").split("```")[1].strip("\n")


def in_actions(prompt, name=None):
    """A page's short prompt as a workflow passes it: the repository and the
    default branch from GitHub, and the worker's name from the matrix."""
    text = prompt.replace(P["REPO"], "${{ github.repository }}")
    text = text.replace(P["DEFAULT_BRANCH"], "${{ env.DEFAULT_BRANCH }}")
    return text.replace("<name>", name) if name else text


def prompt_of(workflow, step_id):
    """The prompt input of the step with this id, as one line."""
    text = (WORKFLOWS / workflow).read_text(encoding="utf-8")
    step = text.split(f"id: {step_id}\n", 1)[1]
    block = step.split("prompt: |\n", 1)[1]
    lines = []
    for line in block.splitlines():
        if line.strip() and not line.startswith(" " * 12):
            break
        lines.append(line.strip())
    return " ".join(line for line in lines if line)


class TheWorkerPrompt(unittest.TestCase):
    def test_a_worker_in_actions_gets_the_routines_short_prompt_with_its_name(self):
        routine = in_actions(short_prompt("worker.md"), "${{ matrix.worker }}")
        sent = prompt_of("workers.yml", "claude")
        keep = routine.split(" Read it again on every run")[0]
        self.assertTrue(sent.startswith(keep), (sent, keep))
        self.assertIn("This run, ${{ steps.next.outputs.move }} issue #${{ steps.next.outputs.issue }}", sent)

    def test_the_full_prompt_reads_the_workers_file_and_its_given_issues_first(self):
        full = (ROUTINES / "worker.md").read_text(encoding="utf-8").split("```")[-2]
        self.assertIn("worker:NAME", full)
        self.assertIn('"- Worker: NAME"', full)
        self.assertIn(".github/symphony/workers/NAME.json", full)
        self.assertIn('the board\'s "Given to workers" section', full)
        self.assertLess(full.index("If whoever started this run named an issue, take that one."),
                        full.index("Given to workers"))

    def test_the_workflow_reads_the_registry_and_the_workers_own_settings(self):
        text = (WORKFLOWS / "workers.yml").read_text(encoding="utf-8")
        self.assertIn("python3 tools/workers.py list --runs actions", text)
        self.assertIn('python3 tools/team.py next --agent "$WORKER" --registry "$REGISTRY" --label "worker:$WORKER"', text)
        self.assertIn("for setting in model max_turns rounds; do", text)
        self.assertIn("--max-turns ${{ steps.next.outputs.max_turns }}", text)
        self.assertIn("ROUNDS: ${{ steps.next.outputs.rounds }}", text)
        from sdlc_protocol import workers
        for setting in ("model", "max_turns", "rounds"):
            self.assertIn(setting, workers.KEYS)


class TheCoordinatorPrompt(unittest.TestCase):
    def test_the_weekly_run_passes_the_routines_short_prompt(self):
        self.assertEqual(prompt_of("coordinator.yml", "tidy"), in_actions(short_prompt("coordinator.md")))

    def test_the_full_prompt_leaves_releases_and_overlaps_to_the_board(self):
        full = (ROUTINES / "coordinator.md").read_text(encoding="utf-8").split("```")[-2]
        self.assertIn("The board's own run releases idle claims and tells open work that overlaps", full)
        self.assertNotIn("claim-released", full)
        self.assertEqual(re.findall(r"^(\d)\. ", full, re.MULTILINE), ["1", "2"])

    def test_the_plan_asks_for_the_clerks_schema_and_names_the_workers(self):
        text = (WORKFLOWS / "coordinator.yml").read_text(encoding="utf-8")
        self.assertIn('python3 tools/team.py schema --registry "$REGISTRY"', text)
        self.assertIn('python3 tools/workers.py --dir "$REGISTRY" describe', text)
        self.assertIn("--json-schema '${{ steps.due.outputs.schema }}'", text)
        self.assertIn('python3 tools/team.py seed --epic "$EPIC" --plan "$RUNNER_TEMP/plan.json" --registry "$REGISTRY"',
                      text)


if __name__ == "__main__":
    unittest.main()
