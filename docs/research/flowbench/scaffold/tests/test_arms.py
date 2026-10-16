"""The arms under arms/ hold together: every stage table loads, every
prompt's placeholders are the runner's, and the review is the same text
in every arm that reviews, so a difference between arms is never a
difference in what the reviewer was told."""

import json
import tempfile
import unittest
from pathlib import Path

from flowbench import run

ARMS = sorted(p.name for p in run.ARMS_DIR.iterdir() if p.is_dir())


class EveryArm(unittest.TestCase):
    def test_the_three_arms_are_there(self):
        self.assertEqual(ARMS, ["script", "solo", "symphony"])

    def test_every_arm_loads_and_every_prompt_uses_only_known_placeholders(self):
        for name in ARMS:
            arm = run.load_arm(name)
            self.assertEqual(arm["name"], name)
            for stage in arm["stages"]:
                template = (Path(arm["dir"]) / stage["prompt"]).read_text(encoding="utf-8")
                self.assertEqual(run.unknown_placeholders(template), [], f"{name}/{stage['prompt']}")
                self.assertIn("{run_token}", template, f"{name}/{stage['prompt']}")
                self.assertIn("use no web", template, f"{name}/{stage['prompt']}")
                self.assertIn("{test_shell}", template, f"{name}/{stage['prompt']}")

    def test_every_stage_that_leaves_a_file_leaves_it_under_the_flow_directory(self):
        for name in ARMS:
            for stage in run.load_arm(name)["stages"]:
                if "writes" in stage:
                    self.assertTrue(stage["writes"].startswith("{flow_dir}/") or stage["writes"] in ("{findings_file}", "{verdict_file}"),
                                    f"{name}/{stage['name']}: {stage['writes']}")

    def test_the_review_is_the_same_text_in_the_script_and_symphony_arms(self):
        script = run.load_arm("script")
        symphony = run.load_arm("symphony")
        script_review = next(s for s in script["stages"] if s["kind"] == "review")
        symphony_review = next(s for s in symphony["stages"] if s["kind"] == "review")
        self.assertEqual(script_review["lenses"], symphony_review["lenses"])
        self.assertEqual(sorted(script_review["lenses"]), ["conventions", "correctness", "path"])
        self.assertEqual((Path(script["dir"]) / script_review["prompt"]).read_text(encoding="utf-8"),
                         (Path(symphony["dir"]) / symphony_review["prompt"]).read_text(encoding="utf-8"))

    def test_the_arm_command_checks_an_arm(self):
        self.assertEqual(run.main(["arm", "script"]), 0)
        self.assertEqual(run.main(["arm", "no-such-arm"]), 1)


class ABrokenArm(unittest.TestCase):
    def write(self, config, prompt="x {run_token}"):
        self.temp = tempfile.TemporaryDirectory()
        arm_dir = Path(self.temp.name) / "arm"
        (arm_dir / "prompts").mkdir(parents=True)
        (arm_dir / "prompts" / "p.md").write_text(prompt, encoding="utf-8")
        (arm_dir / "stages.json").write_text(json.dumps(config), encoding="utf-8")
        return arm_dir

    def tearDown(self):
        if hasattr(self, "temp"):
            self.temp.cleanup()

    def test_a_stage_without_a_known_kind_is_refused(self):
        arm_dir = self.write({"name": "x", "stages": [{"name": "a", "kind": "dance", "prompt": "prompts/p.md"}]})
        with self.assertRaises(run.RunError):
            run.load_arm(arm_dir)

    def test_a_stage_whose_prompt_is_missing_is_refused(self):
        arm_dir = self.write({"name": "x", "stages": [{"name": "a", "kind": "work", "prompt": "prompts/none.md"}]})
        with self.assertRaises(run.RunError):
            run.load_arm(arm_dir)

    def test_an_agent_count_that_is_neither_a_number_nor_a_word_is_refused(self):
        arm_dir = self.write({"name": "x", "stages": [{"name": "a", "kind": "work", "prompt": "prompts/p.md", "agents": "many"}]})
        with self.assertRaises(run.RunError):
            run.load_arm(arm_dir)

    def test_two_stages_of_one_name_are_refused(self):
        arm_dir = self.write({"name": "x", "stages": [{"name": "a", "kind": "work", "prompt": "prompts/p.md"},
                                                      {"name": "a", "kind": "fix", "prompt": "prompts/p.md"}]})
        with self.assertRaises(run.RunError):
            run.load_arm(arm_dir)

    def test_a_prompt_with_an_unknown_placeholder_fails_the_arm_check(self):
        arm_dir = self.write({"name": "x", "stages": [{"name": "a", "kind": "work", "prompt": "prompts/p.md"}]},
                             prompt="{run_token} {nobody}")
        self.assertEqual(run.main(["arm", str(arm_dir)]), 1)

    def test_a_good_arm_passes_the_arm_check(self):
        arm_dir = self.write({"name": "x", "stages": [{"name": "a", "kind": "work", "prompt": "prompts/p.md"}]})
        self.assertEqual(run.main(["arm", str(arm_dir)]), 0)


if __name__ == "__main__":
    unittest.main()
