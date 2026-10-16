"""tasks.py reads the task repository and draws the pre-registered order."""

import tempfile
import unittest
from pathlib import Path

from flowbench import tasks

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "tasks"


class ReadingTasks(unittest.TestCase):
    def test_every_fixture_instance_is_read_with_its_fields(self):
        found = tasks.read_tasks(FIXTURES)
        self.assertEqual([t.instance_id for t in found], ["fake__alpha-1", "fake__alpha-2", "fake__beta-1"])
        first = found[0]
        self.assertEqual(first.repo, "alpha/alpha")
        self.assertEqual(first.owner, "alpha")
        self.assertEqual(first.base_commit, "0" * 39 + "1")
        self.assertEqual(first.image, "swebench/sweb.eval.x86_64.fake_1776_alpha-1:latest")
        self.assertEqual(first.difficulty, "<15 min fix")
        self.assertEqual(first.created_at, "2020-01-01T00:00:00Z")
        self.assertIn("SWE-bench/SWE-bench_Lite", first.datasets)
        self.assertTrue(first.in_dataset("lite"))
        self.assertFalse(found[1].in_dataset("lite"))
        self.assertIn("add(2, 2)", first.problem_statement)
        self.assertEqual(first.fail_to_pass, 1)
        self.assertGreater(first.gold_patch_lines, 0)
        self.assertEqual(first.hidden_tests, (), "the fixture adds no test, so nothing is hidden")

    def test_the_hidden_tests_are_the_failing_tests_the_test_patch_adds(self):
        patch = "+++ b/tests/test_core.py\n+def test_add_new(x):\n+    pass\n+    def test_inner():\n"
        names = tasks.hidden_test_names(["tests/test_core.py::test_add_new[1]", "tests/test_core.py::test_add_new[2]",
                                         "tests/test_core.py::test_add", "test_inner (tests.Core)"], patch)
        self.assertEqual(names, ("tests/test_core.py::test_add_new", "test_inner"))
        self.assertEqual(tasks.test_name_of("a/test_b.py::TestC::test_d[x y]"), ("a/test_b.py::TestC::test_d", "test_d"))
        self.assertEqual(tasks.hidden_test_names(["a::test_x"], ""), ())

    def test_the_default_pool_is_the_instances_in_verified_and_lite(self):
        found = tasks.read_tasks(FIXTURES)
        self.assertEqual([t.instance_id for t in tasks.pool(found)], ["fake__alpha-1", "fake__beta-1"])
        self.assertEqual(len(tasks.pool(found, ("full",))), 3)

    def test_a_directory_whose_task_names_another_instance_is_refused(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp) / "tasks" / "fake__gamma-1"
            directory.mkdir(parents=True)
            (directory / "task.yaml").write_text("instance_id: fake__gamma-2\nrepo: g/g\nbase_commit: abc\nimage: i\n",
                                                 encoding="utf-8")
            (directory / "problem_statement.md").write_text("x\n", encoding="utf-8")
            with self.assertRaises(tasks.TaskError):
                tasks.read_task(directory)

    def test_a_task_file_with_a_nested_mapping_is_refused_rather_than_misread(self):
        with self.assertRaises(tasks.TaskError):
            tasks.read_yaml_flat("instance_id: a\nnested:\n  key: value\n", "task.yaml")

    def test_a_task_file_with_a_required_key_missing_is_refused(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp) / "tasks" / "fake__gamma-1"
            directory.mkdir(parents=True)
            (directory / "task.yaml").write_text("instance_id: fake__gamma-1\nrepo: g/g\n", encoding="utf-8")
            (directory / "problem_statement.md").write_text("x\n", encoding="utf-8")
            with self.assertRaises(tasks.TaskError):
                tasks.read_task(directory)


class DrawingTheOrder(unittest.TestCase):
    def test_strata_are_the_repository_and_the_difficulty_band(self):
        found = tasks.pool(tasks.read_tasks(FIXTURES), ("full",))
        groups = tasks.strata(found)
        self.assertEqual(sorted(groups), ["alpha/15 min - 1 hour", "alpha/<15 min fix", "beta/<15 min fix"])

    def test_the_size_key_buckets_by_the_pools_terciles(self):
        found = tasks.pool(tasks.read_tasks(FIXTURES), ("full",))
        groups = tasks.strata(found, ("size",))
        self.assertTrue(all(name.startswith("size:") for name in groups))
        self.assertEqual(sum(len(members) for members in groups.values()), 3)

    def test_the_order_is_the_seeds_and_holds_every_instance_once(self):
        found = tasks.pool(tasks.read_tasks(FIXTURES), ("full",))
        first = [t.instance_id for t in tasks.order(found, seed=0)]
        again = [t.instance_id for t in tasks.order(found, seed=0)]
        self.assertEqual(first, again)
        self.assertEqual(sorted(first), sorted(t.instance_id for t in found))

    def test_the_strata_come_in_an_order_drawn_from_the_seed_not_by_name(self):
        found = tasks.pool(tasks.read_tasks(FIXTURES), ("full",))
        first_named = sorted(tasks.strata(found))[0]
        firsts = {tasks.stratum_of(tasks.order(found, seed=seed)[0], tasks.DEFAULT_STRATA, (0, 0)) for seed in range(20)}
        self.assertGreater(len(firsts), 1)
        self.assertNotEqual(firsts, {first_named})

    def test_the_order_interleaves_the_strata(self):
        found = tasks.pool(tasks.read_tasks(FIXTURES), ("full",))
        ordered = tasks.order(found, seed=0, keys=("repo",))
        self.assertNotEqual(ordered[0].owner, ordered[1].owner)

    def test_an_unknown_stratum_key_is_refused(self):
        found = tasks.read_tasks(FIXTURES)
        with self.assertRaises(tasks.TaskError):
            tasks.strata(found, ("colour",))


class TheCommandLine(unittest.TestCase):
    def test_order_prints_the_pool_in_the_seeds_order(self):
        import contextlib
        import io
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = tasks.main([str(FIXTURES), "order", "--seed", "0"])
        self.assertEqual(code, 0)
        self.assertEqual(sorted(out.getvalue().split()), ["fake__alpha-1", "fake__beta-1"])

    def test_show_prints_the_instance(self):
        import contextlib
        import io
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = tasks.main([str(FIXTURES), "show", "fake__beta-1"])
        self.assertEqual(code, 0)
        self.assertIn("beta/beta", out.getvalue())


if __name__ == "__main__":
    unittest.main()
