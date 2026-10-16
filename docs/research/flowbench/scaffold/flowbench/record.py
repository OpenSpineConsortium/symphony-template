"""A run's record: result.json, events.jsonl, the tokens read from the
agents' transcripts and what they would cost at list prices.

Every file is written as ASCII JSON with sorted keys, so a bundle of
results passes the repository's plain-text rule and two writers of the
same record produce the same bytes.

Tokens come from each agent's transcript, a Claude Code session file
(JSON lines). Claude Code writes an assistant message's usage on every
line of the message as it streams, and the final output count only on the
line that carries the message's stop_reason, so each message is counted
once, by its id, with the input and cache counts from any of its lines and
the output count from the stop_reason line; a message that never got one
leaves the output count unknown, and the record keeps a lower bound
beside it, as coordbench's session driver does. The transcripts stay on
the host that made them and are never bundled: they hold the run token.
"""

import json
import time
from pathlib import Path

# Dollars per million tokens, Anthropic's list prices as coordbench's
# summary.py recorded them in 2026-10, with a cache write priced as a
# five-minute entry. A model outside the table has no price, and the
# record says so rather than guessing one.
PRICES = {
    "claude-sonnet-5-5": {"input": 2.0, "output": 10.0, "cache_read": 0.20, "cache_write": 2.50},
    "claude-haiku-5-5": {"input": 0.10, "output": 0.50, "cache_read": 0.01, "cache_write": 0.125},
}
TOKEN_KINDS = ("input", "output", "cache_read", "cache_write")
USAGE_KEYS = {"input": "input_tokens", "output": "output_tokens",
              "cache_read": "cache_read_input_tokens", "cache_write": "cache_creation_input_tokens"}


def write_json(path, record):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8")


def read_json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


class Events:
    """events.jsonl: one line per event, with seq, t (seconds since this
    process opened the log, monotonic) and ts (epoch), appended as they
    happen; a process that opens an existing log carries its seq on, so
    the stages of one run read in order whichever process ran them."""

    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.started = time.monotonic()
        self.seq = 0
        if self.path.is_file():
            self.seq = sum(1 for line in self.path.read_text(encoding="utf-8", errors="replace").splitlines() if line.strip())

    def emit(self, kind, **fields):
        event = {"seq": self.seq, "t": round(time.monotonic() - self.started, 3), "ts": round(time.time(), 3),
                 "kind": kind, **fields}
        self.seq += 1
        with self.path.open("a", encoding="utf-8") as out:
            out.write(json.dumps(event, sort_keys=True, ensure_ascii=True) + "\n")
        return event


def transcript_usage(path):
    """The tokens of one transcript, each message counted once by its id:
    {"input", "cache_read", "cache_write", "output" (None when any message
    lacks its stop_reason line), "output_lower_bound", "messages",
    "messages_without_final"}; None for a file that is not there."""
    path = Path(path)
    if not path.is_file():
        return None
    messages = {}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            entry = json.loads(line)
        except ValueError:
            continue
        if not isinstance(entry, dict) or entry.get("type") != "assistant":
            continue
        message = entry.get("message") or {}
        usage = message.get("usage") or {}
        if not isinstance(usage, dict):
            continue
        key = message.get("id") or f"line:{len(messages)}"
        record = messages.setdefault(key, {"input": 0, "cache_read": 0, "cache_write": 0, "output": None, "output_seen": 0})
        for kind in ("input", "cache_read", "cache_write"):
            record[kind] = max(record[kind], int(usage.get(USAGE_KEYS[kind]) or 0))
        record["output_seen"] = max(record["output_seen"], int(usage.get(USAGE_KEYS["output"]) or 0))
        if message.get("stop_reason"):
            record["output"] = int(usage.get(USAGE_KEYS["output"]) or 0)
    totals = {"input": 0, "cache_read": 0, "cache_write": 0, "output": 0, "output_lower_bound": 0,
              "messages": len(messages), "messages_without_final": 0}
    for record in messages.values():
        for kind in ("input", "cache_read", "cache_write"):
            totals[kind] += record[kind]
        if record["output"] is None:
            totals["messages_without_final"] += 1
            totals["output_lower_bound"] += record["output_seen"]
        else:
            totals["output"] += record["output"]
            totals["output_lower_bound"] += record["output"]
    if totals["messages_without_final"]:
        totals["output"] = None
    return totals


def price(tokens, model):
    """The estimated dollars for the tokens at the model's list price;
    None when the model has no price or the output count is unknown."""
    prices = PRICES.get(model)
    if not prices or not tokens or tokens.get("output") is None:
        return None
    return round(sum(int(tokens.get(kind) or 0) * prices[kind] for kind in TOKEN_KINDS) / 1e6, 4)


def price_lower_bound(tokens, model):
    prices = PRICES.get(model)
    if not prices or not tokens:
        return None
    counted = {kind: tokens.get(kind) or 0 for kind in ("input", "cache_read", "cache_write")}
    counted["output"] = tokens.get("output") if tokens.get("output") is not None else tokens.get("output_lower_bound") or 0
    return round(sum(int(counted[kind]) * prices[kind] for kind in TOKEN_KINDS) / 1e6, 4)


def sum_tokens(records):
    """The run's tokens over its agents' records, None where any agent's
    count is unknown, as coordbench's totals are."""
    totals = {kind: 0 for kind in TOKEN_KINDS}
    totals["output_lower_bound"] = 0
    known = False
    for record in records:
        if not record:
            continue
        known = True
        for kind in ("input", "cache_read", "cache_write", "output_lower_bound"):
            totals[kind] += int(record.get(kind) or 0)
        if totals["output"] is not None and record.get("output") is not None:
            totals["output"] += int(record["output"])
        else:
            totals["output"] = None
    return totals if known else None


def stream_summary(path):
    """What one agent's stream-json output says about its run: the model it
    ran with and its session id (the init event); how it ended, its turns,
    its wall time and Claude Code's own cost (the result event); and its
    tokens, from the result event's usage when there is one, else summed
    once per message from the assistant lines, which are shaped as a
    transcript's (transcript_usage). A stream with no result event is an
    agent that was cut off, and says so. None for a file that is not there."""
    path = Path(path)
    if not path.is_file():
        return None
    summary = {"model": None, "session_id": None, "end": None, "is_error": None, "turns": None,
               "duration_ms": None, "cost_usd": None, "cost_source": None, "tokens": None, "result_text": None}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            entry = json.loads(line)
        except ValueError:
            continue
        if not isinstance(entry, dict):
            continue
        if entry.get("type") == "system" and entry.get("subtype") == "init":
            summary["model"] = entry.get("model")
            summary["session_id"] = entry.get("session_id")
        elif entry.get("type") == "result":
            summary["end"] = entry.get("subtype") or "result"
            summary["is_error"] = bool(entry.get("is_error"))
            summary["turns"] = entry.get("num_turns")
            summary["duration_ms"] = entry.get("duration_ms")
            if entry.get("total_cost_usd") is not None:
                summary["cost_usd"] = round(float(entry["total_cost_usd"]), 4)
                summary["cost_source"] = "claude code"
            usage = entry.get("usage")
            if isinstance(usage, dict):
                tokens = {kind: int(usage.get(USAGE_KEYS[kind]) or 0) for kind in TOKEN_KINDS}
                tokens["output_lower_bound"] = tokens["output"]
                summary["tokens"] = tokens
            text = entry.get("result")
            summary["result_text"] = text[:2000] if isinstance(text, str) else None
    if summary["tokens"] is None:
        summary["tokens"] = transcript_usage(path)
    if summary["end"] is None:
        summary["end"] = "no result event"
        summary["is_error"] = True
    return summary
