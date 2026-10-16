"""backlog.py hands each (instance, arm) item to one lane and keeps the
pairs together."""

import tempfile
import threading
import unittest
from pathlib import Path

from flowbench import backlog


def counted(path):
    return {state: count for state, count in backlog.status(path)["states"].items() if count}


class TheBacklog(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "backlog.jsonl"
        backlog.add(self.path, "t", ["i1", "i2"], ["symphony", "script"], {"builders": "1"})

    def tearDown(self):
        self.temp.cleanup()

    def test_items_are_ordered_instance_by_instance_then_arm_by_arm(self):
        keys = [(item["instance"], item["arm"]) for item in backlog.read_items(self.path)]
        self.assertEqual(keys, [("i1", "symphony"), ("i1", "script"), ("i2", "symphony"), ("i2", "script")])
        self.assertEqual(backlog.read_items(self.path)[0]["options"], {"builders": "1"})

    def test_adding_again_adds_nothing_twice(self):
        self.assertEqual(backlog.add(self.path, "t", ["i1", "i3"], ["symphony"]), 1)
        self.assertEqual(len(backlog.read_items(self.path)), 5)

    def test_a_take_runs_the_first_pending_item_and_counts_its_attempt(self):
        first = backlog.take(self.path, "lane-1")
        self.assertEqual((first["instance"], first["arm"], first["state"], first["attempt"], first["lane"]),
                         ("i1", "symphony", "running", 1, "lane-1"))
        second = backlog.take(self.path, "lane-2")
        self.assertEqual((second["instance"], second["arm"]), ("i1", "script"))

    def test_a_finish_with_the_wrong_attempt_is_refused(self):
        backlog.take(self.path, "lane-1")
        with self.assertRaises(backlog.BacklogError):
            backlog.finish(self.path, "i1", "symphony", 2, "resolved")

    def test_a_finished_item_keeps_its_verdict_and_run_directory(self):
        item = backlog.take(self.path, "lane-1")
        done = backlog.finish(self.path, item["instance"], item["arm"], item["attempt"], "resolved", "/logs/x")
        self.assertEqual((done["state"], done["verdict"], done["run_dir"]), ("done", "resolved", "/logs/x"))
        failed = backlog.take(self.path, "lane-1")
        backlog.finish(self.path, failed["instance"], failed["arm"], failed["attempt"], "error", None, True)
        self.assertEqual(counted(self.path), {"done": 1, "failed": 1, "pending": 2})

    def test_requeue_puts_the_harness_errors_back_first(self):
        first = backlog.take(self.path, "lane-1")
        backlog.finish(self.path, first["instance"], first["arm"], first["attempt"], "error", None, True)
        second = backlog.take(self.path, "lane-1")
        backlog.finish(self.path, second["instance"], second["arm"], second["attempt"], "error", None, False)
        self.assertEqual(backlog.requeue(self.path, harness_only=True), {"requeued": 1, "kept": 0})
        self.assertEqual(counted(self.path), {"failed": 1, "pending": 3})
        self.assertEqual(backlog.requeue(self.path), {"requeued": 1, "kept": 0})
        taken = backlog.take(self.path, "lane-1")
        self.assertEqual(taken["attempt"], 2)

    def test_requeue_stops_at_the_attempt_cap(self):
        for _ in range(3):
            item = backlog.take(self.path, "lane-1")
            backlog.finish(self.path, item["instance"], item["arm"], item["attempt"], "error", None, True)
            self.assertEqual(backlog.requeue(self.path)["requeued"], 1 if item["attempt"] < 3 else 0)
        self.assertEqual(backlog.requeue(self.path), {"requeued": 0, "kept": 1})
        self.assertEqual(backlog.requeue(self.path, max_attempts=4), {"requeued": 1, "kept": 0})

    def test_a_dead_lanes_running_items_are_reset_to_pending(self):
        mine = backlog.take(self.path, "lane-1")
        backlog.take(self.path, "lane-2")
        self.assertEqual(backlog.reset(self.path, "lane-1"), 1)
        self.assertEqual(counted(self.path), {"pending": 3, "running": 1})
        taken = backlog.take(self.path, "lane-3")
        self.assertEqual((taken["instance"], taken["arm"], taken["attempt"]), (mine["instance"], mine["arm"], 2))

    def test_paused_items_are_not_taken_until_resumed(self):
        self.assertEqual(backlog.pause(self.path), 4)
        self.assertIsNone(backlog.take(self.path, "lane-1"))
        self.assertEqual(backlog.resume(self.path, ["i2"]), 2)
        self.assertEqual(backlog.take(self.path, "lane-1")["instance"], "i2")

    def test_a_shuffle_is_the_seeds_and_keeps_each_instances_items_together(self):
        backlog.shuffle(self.path, 1)
        first = [(i["instance"], i["arm"]) for i in backlog.read_items(self.path)]
        backlog.shuffle(self.path, 1)
        self.assertEqual(first, [(i["instance"], i["arm"]) for i in backlog.read_items(self.path)])
        self.assertEqual([i for i, _ in first], ["i1", "i1", "i2", "i2"])
        self.assertEqual(sorted(first), sorted([("i1", "symphony"), ("i1", "script"), ("i2", "symphony"), ("i2", "script")]))

    def test_lanes_taking_at_once_never_take_the_same_item(self):
        taken = []
        lock = threading.Lock()

        def lane(name):
            while True:
                item = backlog.take(self.path, name)
                if item is None:
                    return
                with lock:
                    taken.append((item["instance"], item["arm"]))

        threads = [threading.Thread(target=lane, args=(f"lane-{n}",)) for n in range(4)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        self.assertEqual(len(taken), 4)
        self.assertEqual(len(set(taken)), 4)

    def test_an_instance_is_open_while_any_of_its_items_is_to_run_or_running(self):
        for arm in ("symphony", "script"):
            item = backlog.take(self.path, "lane-1")
            self.assertTrue(backlog.instance_open(self.path, "i1"))
            backlog.finish(self.path, item["instance"], item["arm"], item["attempt"], "resolved")
        self.assertFalse(backlog.instance_open(self.path, "i1"))
        self.assertTrue(backlog.instance_open(self.path, "i2"))

    def test_options_parse_as_key_value_pairs(self):
        self.assertEqual(backlog.parse_options(["builders=3", "route=session"]), {"builders": "3", "route": "session"})
        with self.assertRaises(backlog.BacklogError):
            backlog.parse_options(["builders"])


if __name__ == "__main__":
    unittest.main()
