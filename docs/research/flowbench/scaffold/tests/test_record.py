"""record.py reads tokens from transcripts and streams and prices them."""

import json
import tempfile
import unittest
from pathlib import Path

from flowbench import record


def lines(path, entries):
    Path(path).write_text("".join(json.dumps(entry) + "\n" for entry in entries) + "not json\n", encoding="utf-8")


def usage(input_tokens, output_tokens, cache_read=0, cache_write=0):
    return {"input_tokens": input_tokens, "output_tokens": output_tokens, "cache_read_input_tokens": cache_read,
            "cache_creation_input_tokens": cache_write}


class Transcripts(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "transcript.jsonl"

    def tearDown(self):
        self.temp.cleanup()

    def test_each_message_counts_once_with_its_final_output(self):
        lines(self.path, [
            {"type": "assistant", "message": {"id": "m1", "usage": usage(100, 2, cache_read=50)}},
            {"type": "assistant", "message": {"id": "m1", "usage": usage(100, 40, cache_read=50), "stop_reason": "end_turn"}},
            {"type": "assistant", "message": {"id": "m2", "usage": usage(10, 5), "stop_reason": "tool_use"}},
            {"type": "user", "message": {"usage": usage(999, 999)}},
        ])
        totals = record.transcript_usage(self.path)
        self.assertEqual((totals["input"], totals["cache_read"], totals["output"], totals["messages"]), (110, 50, 45, 2))
        self.assertEqual(totals["messages_without_final"], 0)

    def test_a_message_without_its_final_line_leaves_the_output_unknown_with_a_lower_bound(self):
        lines(self.path, [
            {"type": "assistant", "message": {"id": "m1", "usage": usage(100, 3)}},
            {"type": "assistant", "message": {"id": "m2", "usage": usage(10, 5), "stop_reason": "end_turn"}},
        ])
        totals = record.transcript_usage(self.path)
        self.assertIsNone(totals["output"])
        self.assertEqual((totals["output_lower_bound"], totals["messages_without_final"]), (8, 1))

    def test_a_missing_transcript_is_none(self):
        self.assertIsNone(record.transcript_usage(self.path))


class Prices(unittest.TestCase):
    def test_the_price_is_the_list_price_per_million(self):
        tokens = {"input": 1_000_000, "output": 100_000, "cache_read": 2_000_000, "cache_write": 0}
        self.assertEqual(record.price(tokens, "claude-sonnet-5-5"), 2.0 + 1.0 + 0.4)
        self.assertIsNone(record.price(tokens, "a-model-without-a-price"))

    def test_an_unknown_output_count_has_no_price_but_a_lower_bound(self):
        tokens = {"input": 1_000_000, "output": None, "output_lower_bound": 100_000, "cache_read": 0, "cache_write": 0}
        self.assertIsNone(record.price(tokens, "claude-sonnet-5-5"))
        self.assertEqual(record.price_lower_bound(tokens, "claude-sonnet-5-5"), 3.0)

    def test_summing_agents_keeps_the_output_unknown_when_any_is(self):
        known = {"input": 1, "output": 2, "cache_read": 3, "cache_write": 4, "output_lower_bound": 2}
        unknown = {"input": 1, "output": None, "cache_read": 0, "cache_write": 0, "output_lower_bound": 7}
        total = record.sum_tokens([known, known])
        self.assertEqual((total["input"], total["output"], total["cache_write"]), (2, 4, 8))
        total = record.sum_tokens([known, unknown, None])
        self.assertEqual((total["input"], total["output"], total["output_lower_bound"]), (2, None, 9))
        self.assertIsNone(record.sum_tokens([None]))


class Streams(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "agent.stream.jsonl"

    def tearDown(self):
        self.temp.cleanup()

    def test_the_result_event_gives_the_end_the_cost_and_the_tokens(self):
        lines(self.path, [
            {"type": "system", "subtype": "init", "model": "claude-sonnet-5-5", "session_id": "s1"},
            {"type": "assistant", "message": {"id": "m1", "usage": usage(5, 5), "stop_reason": "end_turn"}},
            {"type": "result", "subtype": "success", "is_error": False, "num_turns": 3, "duration_ms": 1200,
             "total_cost_usd": 0.12345, "usage": usage(1000, 100, cache_read=400), "result": "done"},
        ])
        summary = record.stream_summary(self.path)
        self.assertEqual((summary["model"], summary["session_id"], summary["end"], summary["is_error"]),
                         ("claude-sonnet-5-5", "s1", "success", False))
        self.assertEqual((summary["turns"], summary["duration_ms"], summary["cost_usd"], summary["cost_source"]),
                         (3, 1200, 0.1235, "claude code"))
        self.assertEqual(summary["tokens"]["input"], 1000)
        self.assertEqual(summary["tokens"]["cache_read"], 400)
        self.assertEqual(summary["result_text"], "done")

    def test_a_stream_cut_off_before_its_result_is_an_error_with_the_messages_tokens(self):
        lines(self.path, [
            {"type": "system", "subtype": "init", "model": "claude-sonnet-5-5"},
            {"type": "assistant", "message": {"id": "m1", "usage": usage(50, 7), "stop_reason": "end_turn"}},
        ])
        summary = record.stream_summary(self.path)
        self.assertEqual((summary["end"], summary["is_error"], summary["cost_usd"]), ("no result event", True, None))
        self.assertEqual((summary["tokens"]["input"], summary["tokens"]["output"]), (50, 7))

    def test_a_missing_stream_is_none(self):
        self.assertIsNone(record.stream_summary(self.path))


class EventLogs(unittest.TestCase):
    def test_a_second_process_carries_the_sequence_on(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "events.jsonl"
            first = record.Events(path)
            first.emit("a")
            first.emit("b", stage="x")
            second = record.Events(path)
            event = second.emit("c")
            self.assertEqual(event["seq"], 2)
            entries = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
            self.assertEqual([e["kind"] for e in entries], ["a", "b", "c"])
            self.assertEqual(entries[1]["stage"], "x")

    def test_records_are_written_as_sorted_ascii_json(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "deep" / "result.json"
            record.write_json(path, {"b": "caf\u00e9", "a": 1})
            self.assertEqual(path.read_text(encoding="utf-8"), '{\n  "a": 1,\n  "b": "caf\\u00e9"\n}\n')
            self.assertEqual(record.read_json(path), {"a": 1, "b": "caf\u00e9"})
            self.assertIsNone(record.read_json(path.parent / "missing.json"))


if __name__ == "__main__":
    unittest.main()
