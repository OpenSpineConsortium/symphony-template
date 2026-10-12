"""What the work cost and how coordination paid, as aggregates for the
field metrics (tools/metrics.py, docs/setup/metrics.md, Economics).

tools/usage.py records what Claude spends beside the work: a session's
usage on each commit as a Symphony-Usage trailer, a run in GitHub Actions
as an artifact. This module adds those records up per pull request and
over the window: the tokens by kind and by model family, the estimated
price at Anthropic's API list prices, the time Claude was at work, and
the commits and failed checks it took. Then it compares the pull requests
that were worked alone, with no other work going on beside them, with
those worked in parallel with other work, which is what coordination is
for, and gives each comparison as a ratio over 1 when working in parallel
did better: fewer tokens and dollars per merge, a shorter wait to merge,
more merges per hour of work, more first checks passed, fewer commits per
merge and fewer failed checks.

It is pure: the caller reads GitHub and hands in plain values, and every
answer is a dict of numbers with fixed keys, so the record says what the
work cost and nothing about what was built or by whom. Standard library
only, like every tool here.
"""

import math
import re
import statistics
from dataclasses import dataclass, field
from datetime import timedelta

import usage

# Anthropic's API list prices in US dollars per million tokens, as of
# PRICES_AS_OF: uncached input, cache writes kept five minutes (1.25 times
# input) and an hour (2 times input), cache reads, and output. The
# estimate is what the same tokens would cost on the API, whatever plan
# actually paid for them; a model this table does not know is left out of
# the estimate and its tokens counted as unpriced.
PRICES_AS_OF = "2026-10-06"
PRICES = {
    "claude-fable-5-1": (10.0, 12.5, 20.0, 0.25, 50.0),
    "claude-opus-5-5": (4.0, 5.0, 8.0, 0.20, 20.0),
    "claude-opus-5": (5.0, 6.25, 10.0, 0.50, 25.0),
    "claude-opus-4-8": (5.0, 6.25, 10.0, 0.50, 25.0),
    "claude-opus-4-7": (5.0, 6.25, 10.0, 0.50, 25.0),
    "claude-opus-4-6": (5.0, 6.25, 10.0, 0.50, 25.0),
    "claude-opus-4-5": (5.0, 6.25, 10.0, 0.50, 25.0),
    "claude-opus-4-1": (15.0, 18.75, 30.0, 1.50, 75.0),
    "claude-opus-4": (15.0, 18.75, 30.0, 1.50, 75.0),
    "claude-sonnet-5-5": (2.0, 2.5, 4.0, 0.20, 10.0),
    "claude-sonnet-5": (2.0, 2.5, 4.0, 0.20, 10.0),
    "claude-sonnet-4-6": (3.0, 3.75, 6.0, 0.30, 15.0),
    "claude-sonnet-4-5": (3.0, 3.75, 6.0, 0.30, 15.0),
    "claude-sonnet-4": (3.0, 3.75, 6.0, 0.30, 15.0),
    "claude-haiku-5-5": (0.10, 0.125, 0.20, 0.01, 0.50),
    "claude-haiku-4-5": (1.0, 1.25, 2.0, 0.10, 5.0),
    "claude-haiku-3-5": (0.80, 1.0, 1.6, 0.08, 4.0),
}
FAMILIES = ("fable", "opus", "sonnet", "haiku", "other")
TOKEN_KINDS = ("input", "cache_write", "cache_read", "output")
DATE_SUFFIX = re.compile(r"-20[0-9]{6}$")
BRACKETS = re.compile(r"\[[^\]]*\]$")
# Two pieces of work were at work beside each other when their spans met
# for longer than this, the field metrics' clock grace.
GRACE = timedelta(seconds=60)
# The kinds of work that count as coordinated or alone: people's and the
# repository's own Claude workflows'; automation, such as dependabot, is
# neither.
WORKING_KINDS = ("person", "workflow_agents")
GROUP_KEYS = ("pull_requests", "merged", "measured", "measured_merged", "tokens", "estimated_usd", "claude_seconds",
              "commits", "check_failures", "first_check_passed", "first_check_counted", "open_to_merge_median",
              "active_seconds")
RATIO_KEYS = ("tokens_per_merge", "usd_per_merge", "latency", "throughput", "first_check_pass", "commits_per_merge",
              "failures_per_pull_request")
ECONOMICS_KEYS = ("prices_as_of", "pull_requests", "pull_requests_measured", "merged", "sessions", "actions_runs",
                  "actions_runs_unread", "tokens_input", "tokens_cache_write", "tokens_cache_read", "tokens_output",
                  "tokens_total", "tokens_unpriced", "estimated_usd", "coordinator_usd", "claude_seconds", "commits",
                  "check_failures", "reverts", "tokens_by_family", "tokens_per_merge", "usd_per_merge",
                  "claude_seconds_per_merge", "commits_per_merge")


# --- prices ---------------------------------------------------------------------

def normalized(model):
    """A model's name as the price table spells it: lower case, without a
    note in brackets such as [1m] or a release date."""
    name = BRACKETS.sub("", str(model or "").strip().lower())
    return DATE_SUFFIX.sub("", name)


def family(model):
    name = normalized(model)
    return next((f for f in FAMILIES[:-1] if f in name), "other")


def price(model):
    return PRICES.get(normalized(model))


def priced(models):
    """The estimated price of a usage, by model the five counts, and the
    tokens of models the table does not know."""
    usd, unpriced = 0.0, 0
    for model, counts in models.items():
        rates = price(model)
        if rates is None:
            unpriced += sum(counts)
        else:
            usd += sum(count * rate for count, rate in zip(counts, rates)) / 1_000_000
    return usd, unpriced


def by_kind(models):
    """The tokens of a usage by kind: input, cache writes of both lengths
    together, cache reads, output."""
    totals = dict.fromkeys(TOKEN_KINDS, 0)
    for counts in models.values():
        totals["input"] += counts[0]
        totals["cache_write"] += counts[1] + counts[2]
        totals["cache_read"] += counts[3]
        totals["output"] += counts[4]
    return totals


def merge(into, models):
    for model, counts in models.items():
        row = into.setdefault(model, [0] * len(usage.FIELDS))
        for index, count in enumerate(counts):
            row[index] += count
    return into


# --- the records ----------------------------------------------------------------

def actions_record(data):
    """An Actions run's record as the economics read it, or None when it is
    not one: its counts by model must be whole numbers, its times numbers,
    and its words the workflows' own."""
    if not isinstance(data, dict) or data.get("v") != 1 or data.get("source") != "actions":
        return None
    models = {}
    for model, counts in (data.get("models") or {}).items():
        if (isinstance(model, str) and isinstance(counts, list) and len(counts) == len(usage.FIELDS)
                and all(isinstance(c, int) and not isinstance(c, bool) and 0 <= c < 2 ** 53 for c in counts)):
            models[model] = counts
    seconds = data.get("seconds")
    return {
        "workflow": str(data.get("workflow") or ""), "job": str(data.get("job") or ""),
        "issue": data.get("issue") if isinstance(data.get("issue"), int) else None,
        "pull": data.get("pull") if isinstance(data.get("pull"), int) else None,
        "seconds": float(seconds) if isinstance(seconds, (int, float)) and seconds >= 0 else 0.0,
        "models": models,
    }


@dataclass
class Work:
    """One pull request that ended in the window, as the economics read it:
    its number and claim, its kind, when its work began and ended, when it
    merged (None when it did not), when it opened, its commits as GitHub
    lists them, its failed check runs, and whether its first check passed
    (None when that cannot be told)."""

    number: int
    claim: int = None
    kind: str = "person"
    start: object = None
    end: object = None
    merged: object = None
    opened: object = None
    commits: list = field(default_factory=list)
    check_failures: int = 0
    first_check: bool = None


@dataclass
class Spent:
    """What one pull request cost: tokens by model, seconds at work, the
    sessions that worked on it and the Actions runs."""

    models: dict = field(default_factory=dict)
    seconds: float = 0.0
    sessions: set = field(default_factory=set)
    runs: int = 0

    @property
    def tokens(self):
        return sum(sum(counts) for counts in self.models.values())

    @property
    def usd(self):
        return priced(self.models)[0]


def add_trailers(spent, commits):
    """Add to spent the Symphony-Usage trailers of the commits."""
    for commit in commits:
        message = ((commit or {}).get("commit") or {}).get("message") or ""
        for session, seconds, models in usage.parse_trailer(message):
            merge(spent.models, models)
            spent.seconds += seconds
            if session:
                spent.sessions.add(session)
    return spent


def add_runs(spent, records):
    """Add to spent the Actions runs of the records."""
    for record in records:
        merge(spent.models, record["models"])
        spent.seconds += record["seconds"]
        spent.runs += 1
    return spent


def names(record, work):
    """Whether an Actions run's record names the pull request, by its number
    or by its claim's issue."""
    return record["pull"] == work.number or (work.claim is not None and record["issue"] == work.claim)


def spent_on(work, records):
    """What a pull request cost: the trailers on its commits and the Actions
    runs whose record names it, or names its claim's issue."""
    spent = add_trailers(Spent(), work.commits)
    return add_runs(spent, [r for r in records if names(r, work)])


def unattributed(works, records):
    """The Actions records that name no pull request of the window, by
    neither number nor claim: the coordinator's planning and tidying, and
    any run whose pull request did not end in the window."""
    return [r for r in records if not any(names(r, w) for w in works)]


# --- the window -------------------------------------------------------------------

def per(part, whole):
    return round(part / whole, 6) if whole else None


def economics(works, commits, window_records, records, reverts=0, unread=0):
    """The window's economics. What Claude spent in it, its bill: the
    trailers on the commits made in it and the Actions runs recorded in it
    (window_records). What it delivered: the pull requests of people and of
    the repository's Claude workflows that ended in it (works), with their
    commits, failed checks and reverts. The rates divide the one by the
    other, and pull_requests_measured, the pull requests with any usage
    recorded against them, from all the records read (records), says how
    much of the delivery the bill covers. unread is how many usage records
    were left unread, None when they could not be listed at all."""
    bill = add_runs(add_trailers(Spent(), commits), window_records)
    usd, unpriced = priced(bill.models)
    kinds = by_kind(bill.models)
    merged = [w for w in works if w.merged is not None]
    tokens = sum(kinds.values())
    families = dict.fromkeys(FAMILIES, 0)
    for model, counts in bill.models.items():
        families[family(model)] += sum(counts)
    delivered_commits = sum(len(w.commits) for w in works)
    return dict(zip(ECONOMICS_KEYS, (
        PRICES_AS_OF, len(works), sum(1 for w in works if spent_on(w, records).tokens), len(merged),
        len(bill.sessions), bill.runs, unread,
        kinds["input"], kinds["cache_write"], kinds["cache_read"], kinds["output"], tokens, unpriced,
        round(usd, 4), round(priced(coordinator_models(window_records))[0], 4),
        int(bill.seconds), delivered_commits, sum(w.check_failures for w in works), reverts, families,
        per(tokens, len(merged)), per(round(usd, 4), len(merged)), per(int(bill.seconds), len(merged)),
        per(delivered_commits, len(merged)),
    )))


def coordinator_models(records):
    models = {}
    for record in records:
        if record["workflow"] == "coordinator":
            merge(models, record["models"])
    return models


# --- alone and in parallel --------------------------------------------------------

def beside(a, b, now):
    """Whether two pieces of work were at work at once for longer than the
    grace."""
    end_a, end_b = a.end or now, b.end or now
    return a is not b and min(end_a, end_b) - max(a.start, b.start) > GRACE


def covered_seconds(works, now):
    """The seconds at least one of the works was at work: the union of
    their spans, so two at once count once."""
    spans = sorted((w.start, w.end or now) for w in works if w.start is not None)
    total, current_start, current_end = 0.0, None, None
    for start, end in spans:
        if current_end is None or start > current_end:
            if current_end is not None:
                total += (current_end - current_start).total_seconds()
            current_start, current_end = start, end
        else:
            current_end = max(current_end, end)
    if current_end is not None:
        total += (current_end - current_start).total_seconds()
    return total


def group(works, spent, now, extra_usd=0.0, extra_tokens=0):
    """One side of the comparison, as GROUP_KEYS. Its tokens and dollars are
    those of its measured pull requests, the ones with usage recorded, and
    what it costs beside them (extra_usd, extra_tokens), so they are divided
    by its measured merges and never by merges whose cost is unknown."""
    merged = [w for w in works if w.merged is not None]
    measured = [w for w in works if spent[w.number].tokens]
    waits = [(w.merged - w.opened).total_seconds() for w in merged if w.opened is not None]
    verdicts = [w.first_check for w in works if w.first_check is not None]
    usd = sum(spent[w.number].usd for w in measured) + extra_usd
    return dict(zip(GROUP_KEYS, (
        len(works), len(merged), len(measured), sum(1 for w in measured if w.merged is not None),
        sum(spent[w.number].tokens for w in measured) + extra_tokens, round(usd, 4),
        int(sum(spent[w.number].seconds for w in works)), sum(len(w.commits) for w in works),
        sum(w.check_failures for w in works), sum(verdicts), len(verdicts),
        int(statistics.median(waits)) if waits else None, int(covered_seconds(works, now)),
    )))


def inverse(numerator, denominator):
    """numerator / denominator, or None when either is missing or the
    denominator is zero."""
    if numerator is None or denominator is None or not denominator:
        return None
    value = numerator / denominator
    return round(value, 4) if math.isfinite(value) else None


def ratios(alone, parallel):
    """Each comparison as a ratio over 1 when working in parallel did
    better, None where either side has nothing to compare."""
    def per_merge(side, key):
        return per(side[key], side["measured_merged" if key in ("tokens", "estimated_usd") else "merged"])

    def per_hour(side):
        return side["merged"] / (side["active_seconds"] / 3600) if side["active_seconds"] else None

    def rate(side):
        return per(side["first_check_passed"], side["first_check_counted"])

    def smoothed_failures(side):
        return (side["check_failures"] + 1) / (side["pull_requests"] + 1) if side["pull_requests"] else None

    return dict(zip(RATIO_KEYS, (
        inverse(per_merge(alone, "tokens"), per_merge(parallel, "tokens")),
        inverse(per_merge(alone, "estimated_usd"), per_merge(parallel, "estimated_usd")),
        inverse(alone["open_to_merge_median"], parallel["open_to_merge_median"]),
        inverse(per_hour(parallel), per_hour(alone)),
        inverse(rate(parallel), rate(alone)),
        inverse(per_merge(alone, "commits"), per_merge(parallel, "commits")),
        inverse(smoothed_failures(alone), smoothed_failures(parallel)),
    )))


def coordination(works, records, now, others=(), window_records=()):
    """The comparison: the window's pull requests of people and of the
    repository's Claude workflows that ended in it, split by whether other
    such work was at work beside them, the window's or work that did not
    end in it (others), and the ratios. The coordinator's runs recorded in
    the window that name none of them are the cost of working in parallel,
    so they count on that side."""
    working = [w for w in works if w.kind in WORKING_KINDS and w.start is not None]
    everyone = working + [o for o in others if o.kind in WORKING_KINDS and o.start is not None]
    alone = [w for w in working if not any(beside(w, o, now) for o in everyone)]
    parallel = [w for w in working if w not in alone]
    spent = {w.number: spent_on(w, records) for w in working}
    overhead = coordinator_models(unattributed(works, window_records))
    alone_side = group(alone, spent, now)
    parallel_side = group(parallel, spent, now, priced(overhead)[0], sum(sum(c) for c in overhead.values()))
    return {"alone": alone_side, "parallel": parallel_side, "ratios": ratios(alone_side, parallel_side)}
