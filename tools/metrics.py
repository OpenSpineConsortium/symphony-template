"""Field metrics: how the claim protocol runs in this repository, as numbers.

OpenSpineConsortium/coordbench measures ways of coordinating coding agents
on CooperBench's task pairs, this protocol among them; this tool measures
the same protocol where it is used for real, in aggregates only, so a
project can share how the protocol ran without sharing anything of its
own. docs/setup/metrics.md is the reader's page: every key, a sample of
each file, how each measure lines up with the benchmark's, and the switch.

  collect  run daily by .github/workflows/metrics.yml with GITHUB_TOKEN
           alone. It reads the window's pull requests, reviews, check
           runs, claim branches and comments from GitHub's REST API and
           writes METRICS.json: counts, durations in seconds and two rates,
           under the keys below and no other. No name, login, title, branch
           name, URL, issue number or text is ever written, so the file says
           how the protocol ran and nothing about what was built or by whom.
           The workflow puts it on the branch metrics, where
           OpenSpineConsortium's collector reads it, and only where the
           repository installed the OpenSpine SDLC App.
  judge    run by a maintainer on their own machine, with their own gh and
           their own Claude Code (claude -p) on their own subscription, never
           with ANTHROPIC_API_KEY. It reads each recent pull request's
           conversation, has the local model code it with CooperBench's App F
           taxonomy of communication errors, and keeps only how many
           conversations fell in each code. The conversation text goes to the
           maintainer's local claude process and nowhere else, which asks the
           model on their own account as any of their sessions does: JUDGE.json
           holds counts alone, and --push puts it on the branch metrics beside
           METRICS.json as an ordinary commit, never a forced one.
  unchanged OLD NEW  exit 0 when two METRICS.json files differ in nothing
           but generated_at, so the workflow writes only when something moved.

The switch: sharing is on unless the file .github/sdlc-metrics or the
repository variable SDLC_METRICS (handed to the workflow's environment)
says otherwise. Off from either wins, and an off run writes exactly
{"schema": "sdlc-metrics/1", "sharing": "off"} without a single API call.

Standard library only, like every tool here. GitHub's REST calls go through
the vendored protocol library's client, the one the board uses, so there is
one way of calling GitHub; the judge reads through gh instead, because it
runs as the maintainer, signed in as themselves.
"""

import argparse
import json
import math
import os
import re
import shlex
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
import urllib.parse
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import NamedTuple

TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))

from sdlc_protocol import board, claims  # noqa: E402
from sdlc_protocol.adapters.github import GitHub, GitHubError, settled  # noqa: E402

SCHEMA = "sdlc-metrics/1"
JUDGE_SCHEMA = "sdlc-judge/1"
ON, OFF = "on", "off"
OFF_RECORD = {"schema": SCHEMA, "sharing": OFF}
SWITCH_FILE = ".github/sdlc-metrics"
SWITCH_VARIABLE = "SDLC_METRICS"
METRICS_BRANCH = "metrics"
METRICS_FILE = "METRICS.json"
JUDGE_FILE = "JUDGE.json"
VENDORED = TOOLS / "VENDORED"
WINDOW_DAYS = 30

# The keys of METRICS.json, in order; the file holds these and nothing else.
COUNT_KEYS = ("claims", "pull_requests_opened", "merged", "closed_unmerged", "reviews", "changes_requested",
              "check_runs_passed", "check_runs_failed", "conflicts_seen", "released_claims", "contributors")
DURATIONS = ("claim_to_first_pull_request", "open_to_merge", "first_review")
DURATION_KEYS = tuple(f"{name}_{kind}" for name in DURATIONS for kind in ("median", "p90"))
RATE_KEYS = ("merge_rate", "first_check_pass_rate")
RECORD_KEYS = ("schema", "generated_at", "window_days", "sharing", "protocol_version", "counts",
               "durations_seconds", "rates")

# A check run counts as passed or failed by its conclusion; neutral,
# skipped, cancelled, stale and action_required say neither, and a run
# still going has no conclusion yet.
PASSED = {"success"}
FAILED = {"failure", "timed_out"}
# A commit's date is the committer's clock, not GitHub's: a minute's grace
# keeps a slightly fast clock from hiding the head a pull request opened with.
CLOCK_GRACE = timedelta(seconds=60)
# The coordinator routine starts every release comment with this line
# (docs/agents/routines/coordinator.md, step 2), so releases can be counted
# without reading what the comment says.
RELEASE_MARKER = "<!-- sdlc-coordinator: claim-released -->"
# The board's "main moved" comment carries a marker and says "behind" or
# "conflicting with"; only the second is a conflict. Both pieces come from
# the vendored board, so a change of its words there changes them here.
MAIN_MOVED_PREFIX = board.MAIN_MOVED_MARKER.split("{sha}")[0]
CONFLICT_WORDS = board.main_moved_text("conflicting", "{base}", "{sha}").split("{base}")[0]
DIRTY = "dirty"


# --- time --------------------------------------------------------------------

def parse_time(text):
    """GitHub's ISO time as an aware datetime, or None for none."""
    if not text:
        return None
    try:
        moment = datetime.fromisoformat(str(text).replace("Z", "+00:00"))
    except ValueError:
        return None
    return moment if moment.tzinfo else moment.replace(tzinfo=timezone.utc)


def iso(moment):
    return moment.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class Window(NamedTuple):
    """The days a run looks back over, ending at its own moment."""

    start: datetime
    end: datetime
    days: int

    @classmethod
    def ending(cls, end, days):
        return cls(end - timedelta(days=days), end, days)

    def holds(self, moment):
        return moment is not None and self.start <= moment <= self.end


def time_of(item, key):
    return parse_time((item or {}).get(key))


def seconds_between(earlier, later):
    """Whole seconds from one moment to a later one; None when either is
    missing or the order is wrong, which a skewed clock can make it."""
    if earlier is None or later is None or later < earlier:
        return None
    return int((later - earlier).total_seconds())


# --- the switch --------------------------------------------------------------

def first_word(text):
    words = (text or "").split()
    return words[0].lower() if words else ""


def sharing(root, environ):
    """'on' or 'off'. The variable turns sharing off with any word but on,
    and says nothing when empty; the file says on only with the word on
    first, is on when missing, and is off when it says anything else or
    cannot be read. Each doubt falls to off, since off shares nothing."""
    said = first_word(environ.get(SWITCH_VARIABLE))
    if said and said != ON:
        return OFF
    try:
        text = (Path(root) / SWITCH_FILE).read_text(encoding="utf-8")
    except FileNotFoundError:
        return ON
    except (OSError, UnicodeDecodeError):
        return OFF
    return ON if first_word(text) == ON else OFF


def protocol_version(path=VENDORED):
    """The vendored protocol's release and short commit, "0.2.0 f530a66",
    from tools/VENDORED's first line; None when it cannot be read."""
    try:
        first = path.read_text(encoding="ascii").splitlines()[0].split()
    except (OSError, UnicodeDecodeError, IndexError):
        return None
    if len(first) != 3 or first[0] != "sdlc-protocol":
        return None
    return f"{first[1]} {first[2][:7]}"


# --- reading GitHub ----------------------------------------------------------

def window_pulls(api, window):
    """Every pull request changed in the window. GitHub lists them by last
    update, newest first, so the listing stops at the first one older than
    the window; a creation, a merge, a close or a review in the window each
    moves the update time into it."""
    found = []
    for page in api.pages(f"/repos/{api.repo}/pulls", {"state": "all", "sort": "updated", "direction": "desc"}):
        for pull in page:
            updated = time_of(pull, "updated_at")
            if updated is not None and updated < window.start:
                return found
            found.append(pull)
    return found


@dataclass
class PullFacts:
    """What one pull request contributes: the pull as listed, its commits
    (oldest first), its submitted reviews, the check runs on its head, the
    check runs on the head it was opened with (None when that head cannot
    be told) and, while it is open, GitHub's mergeable_state."""

    pull: dict
    commits: list = field(default_factory=list)
    reviews: list = field(default_factory=list)
    head_runs: list = field(default_factory=list)
    first_runs: list = None
    mergeable_state: str = None


def commit_time(commit, who):
    return time_of(((commit or {}).get("commit") or {}).get(who), "date")


def first_head_sha(pull, commits):
    """The head the pull request was opened with. GitHub keeps no record of
    it, so it is the newest of the pull request's commits committed by the
    time it opened; None when a rebase has replaced them all, and the pull
    request then stays out of the first-check rate."""
    cutoff = time_of(pull, "created_at")
    if cutoff is None:
        return None
    before = [c for c in commits if (when := commit_time(c, "committer")) and when <= cutoff + CLOCK_GRACE]
    return max(before, key=lambda c: commit_time(c, "committer"))["sha"] if before else None


def pull_facts(api, pull, window):
    """The calls one pull request takes: its commits, its reviews, the runs
    on its head, the runs on its first head when it opened in the window,
    and its detail while it is open, for the mergeable_state the list
    leaves out."""
    path = f"/repos/{api.repo}/pulls/{pull['number']}"
    facts = PullFacts(pull, api.get_all(path + "/commits"),
                      [r for r in api.get_all(path + "/reviews") if r.get("state") != "PENDING"])
    head = (pull.get("head") or {}).get("sha")
    facts.head_runs = api.check_runs(head) if head else []
    if window.holds(time_of(pull, "created_at")):
        first = first_head_sha(pull, facts.commits)
        facts.first_runs = facts.head_runs if first == head else (api.check_runs(first) if first else None)
    if pull.get("state") == "open":
        facts.mergeable_state = settled(api, api.get(path)).get("mergeable_state")
    return facts


def claim_number(pull):
    return claims.number_of((pull.get("head") or {}).get("ref") or "")


def branch_claims(api, window, known):
    """The issue numbers of claude/<n> branches with no pull request among
    the window's whose head commit was made in the window. GitHub's REST API
    says when a commit was made, never when a branch was."""
    found = set()
    for branch in api.get_all(f"/repos/{api.repo}/branches"):
        number = claims.number_of(branch.get("name") or "")
        sha = (branch.get("commit") or {}).get("sha")
        if number is None or number in known or not sha:
            continue
        if window.holds(commit_time(api.get(f"/repos/{api.repo}/commits/{sha}", missing_ok=True), "committer")):
            found.add(number)
    return found


def window_comments(api, window):
    """The issue and pull request comments made in the window. GitHub's
    since is the last update, so an old comment edited lately is listed and
    then left out here."""
    listed = api.get_all(f"/repos/{api.repo}/issues/comments",
                         {"since": iso(window.start), "sort": "created", "direction": "asc"})
    return [c for c in listed if window.holds(time_of(c, "created_at"))]


def read_repository(api, window):
    """Everything collect measures, read from GitHub."""
    facts = [pull_facts(api, pull, window) for pull in window_pulls(api, window)]
    known = {n for f in facts if (n := claim_number(f.pull)) is not None}
    return facts, branch_claims(api, window, known), window_comments(api, window)


# --- measuring ---------------------------------------------------------------

def median_seconds(values):
    """The median, rounded half up to whole seconds; None for no values."""
    return int(math.floor(statistics.median(values) + 0.5)) if values else None


def p90_seconds(values):
    """The 90th percentile by nearest rank: the smallest value at or above
    nine tenths of them; None for no values."""
    if not values:
        return None
    ordered = sorted(values)
    return ordered[math.ceil(0.9 * len(ordered)) - 1]


def ratio(part, whole):
    return round(part / whole, 4) if whole else None


def is_bot(user):
    login = (user or {}).get("login") or ""
    return (user or {}).get("type") == "Bot" or login.endswith("[bot]")


def person(user):
    """Who a GitHub user is, for counting alone: None for an app or a bot,
    which is no contributor."""
    if not isinstance(user, dict) or not user.get("login") or is_bot(user):
        return None
    return "login:" + user["login"].lower()


def commit_author(commit):
    """Who made a commit: its GitHub account when it has one, else the
    author's email, so an agent that commits under a name of its own counts
    once whichever account ran it."""
    account = commit.get("author")
    if isinstance(account, dict) and account.get("login"):
        return person(account)
    email = ((((commit.get("commit") or {}).get("author")) or {}).get("email") or "").lower()
    return "email:" + email if email and "[bot]" not in email else None


def contributors(facts):
    """How many people wrote the window's pull requests, reviews and
    commits; the identities are counted here and never leave."""
    found = set()
    for f in facts:
        found.add(person(f.pull.get("user")))
        found.update(person(r.get("user")) for r in f.reviews)
        found.update(commit_author(c) for c in f.commits)
    return len(found - {None})


def issue_number(comment):
    tail = (comment.get("issue_url") or "").rstrip("/").rsplit("/", 1)[-1]
    return int(tail) if tail.isdecimal() else None


def conflicts(facts, comments):
    """The pull requests seen in conflict: open ones GitHub calls dirty
    now, and any the board's "main moved" comment called conflicting in
    the window. A pull request only behind is no conflict."""
    dirty = {f.pull["number"] for f in facts if f.mergeable_state == DIRTY}
    marked = {issue_number(c) for c in comments
              if MAIN_MOVED_PREFIX in (c.get("body") or "") and CONFLICT_WORDS in (c.get("body") or "")}
    return len((dirty | marked) - {None})


def window_runs(facts, window):
    """The check runs on the window's heads that finished in the window,
    each once."""
    runs = {}
    for f in facts:
        for run in f.head_runs:
            if window.holds(time_of(run, "completed_at")):
                runs[run.get("id") or id(run)] = run
    return list(runs.values())


def claim_time(f):
    """When the claim was made: the earliest author date among the pull
    request's commits, which on a claude/<n> branch is the claim file's own
    commit; a rebase keeps author dates and changes committer dates."""
    dates = [d for c in f.commits if (d := commit_time(c, "author"))]
    return min(dates) if dates else None


def claim_waits(opened):
    """Seconds from each claim to its first pull request opened in the
    window, one per claimed issue."""
    first = {}
    for f in sorted(opened, key=lambda f: time_of(f.pull, "created_at")):
        number = claim_number(f.pull)
        if number is not None and number not in first:
            first[number] = f
    return [s for f in first.values()
            if (s := seconds_between(claim_time(f), time_of(f.pull, "created_at"))) is not None]


def others_reviews(f):
    """The reviews by anyone but the pull request's author: an author's
    answer in a review thread is filed by GitHub as a review of their own."""
    author = (f.pull.get("user") or {}).get("login")
    return [r for r in f.reviews if not author or (r.get("user") or {}).get("login") != author]


def review_waits(opened):
    """Seconds from opening to the first review by someone other than the
    author, for each pull request opened in the window that has one."""
    waits = []
    for f in opened:
        times = [t for r in others_reviews(f) if (t := time_of(r, "submitted_at"))]
        wait = seconds_between(time_of(f.pull, "created_at"), min(times)) if times else None
        if wait is not None:
            waits.append(wait)
    return waits


def merge_waits(merged):
    """Seconds from opening to merging, for each pull request merged in the
    window."""
    return [s for f in merged
            if (s := seconds_between(time_of(f.pull, "created_at"), time_of(f.pull, "merged_at"))) is not None]


def first_check_passed(f):
    """Whether every counted check run on the head the pull request opened
    with passed; None when that head is unknown or none of its runs counted."""
    counted = [r for r in f.first_runs or [] if r.get("conclusion") in PASSED | FAILED]
    return all(r["conclusion"] in PASSED for r in counted) if counted else None


def summary(values):
    return median_seconds(values), p90_seconds(values)


def measures(facts, extra_claims, comments, window):
    """The counts, the durations and the rates over what was read."""
    opened = [f for f in facts if window.holds(time_of(f.pull, "created_at"))]
    merged = [f for f in facts if window.holds(time_of(f.pull, "merged_at"))]
    closed = [f for f in facts if not f.pull.get("merged_at") and window.holds(time_of(f.pull, "closed_at"))]
    reviews = [r for f in facts for r in others_reviews(f) if window.holds(time_of(r, "submitted_at"))]
    runs = window_runs(facts, window)
    claimed = {n for f in facts if (n := claim_number(f.pull)) is not None} | set(extra_claims)
    counts = dict(zip(COUNT_KEYS, (
        len(claimed), len(opened), len(merged), len(closed), len(reviews),
        sum(1 for r in reviews if r.get("state") == "CHANGES_REQUESTED"),
        sum(1 for r in runs if r.get("conclusion") in PASSED),
        sum(1 for r in runs if r.get("conclusion") in FAILED),
        conflicts(facts, comments),
        sum(1 for c in comments if RELEASE_MARKER in (c.get("body") or "")),
        contributors(facts),
    )))
    durations = dict(zip(DURATION_KEYS, (*summary(claim_waits(opened)), *summary(merge_waits(merged)),
                                         *summary(review_waits(opened)))))
    verdicts = [v for f in opened if (v := first_check_passed(f)) is not None]
    rates = {"merge_rate": ratio(len(merged), len(merged) + len(closed)),
             "first_check_pass_rate": ratio(sum(verdicts), len(verdicts))}
    return {"counts": counts, "durations_seconds": durations, "rates": rates}


def metrics_record(measured, window, version):
    return {"schema": SCHEMA, "generated_at": iso(window.end), "window_days": window.days, "sharing": ON,
            "protocol_version": version, **measured}


def write_json(path, record):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, indent=2) + "\n", encoding="ascii")


def same_apart_from_time(old_text, new_text):
    """Whether two METRICS.json texts hold the same record once
    generated_at is set aside."""
    try:
        old, new = json.loads(old_text), json.loads(new_text)
    except ValueError:
        return False
    if not isinstance(old, dict) or not isinstance(new, dict):
        return False
    old.pop("generated_at", None)
    new.pop("generated_at", None)
    return old == new


# --- the judge: App F, on the maintainer's own Claude Code --------------------

# App F's codes, their names and their three groups, as
# OpenSpineConsortium/coordbench's coordbench/judge.py has them (its
# APPF_7, ERROR_NAMES and ERROR_GROUPS), which follow CooperBench's paper.
APPF_CODES = ("C1a", "C1b", "C2", "C3a", "C3b", "C4a", "C4b")
APPF_NAMES = {"C1a": "Unanswered direct question (no reply)", "C1b": "Unanswered direct question (ignored)",
              "C2": "Non-answer or vague answer", "C3a": "Incorrect claim (uncorrected)",
              "C3b": "Incorrect claim (corrected)", "C4a": "Spammy repetition (repeats same information)",
              "C4b": "Spammy repetition (near-duplicate status blocks)"}
GROUPS = ("unresponsiveness", "hallucination", "repetition")
APPF_GROUPS = {"C1a": "unresponsiveness", "C1b": "unresponsiveness", "C2": "unresponsiveness",
               "C3a": "hallucination", "C3b": "hallucination", "C4a": "repetition", "C4b": "repetition"}
PROMPT_VARIANT = "appF-7"
DEFAULT_MODEL = "claude-sonnet-5-5"
# App F's text word for word, as coordbench's prompts/commerrors-appF-7.txt
# holds it, up to its Output paragraph. That paragraph asked for quotes and
# a description; here the answer is the codes alone, so no text of the
# conversation comes back even into the reply this tool reads and drops.
APPF_PROMPT = "\n".join([
    "You are a careful reviewer of two agent collaboration conversations. This is a precision-first detector of "
    "bad conversation patterns. Prefer returning no issue unless the evidence is strong and explicit.",
    "Important exclusion. Do not label state mismatch or visibility confusion itself as an error (e.g., agents on "
    "separate branches unable to see each other's changes). Bad conversation patterns around these topics should "
    "still be labeled.",
    "Taxonomy. Label at most one category per conversation.",
    *(f"- {code} {APPF_NAMES[code]}" for code in APPF_CODES),
    "Evidence requirements. Include at least two exact quotes that make the issue undeniable. C1a/C1b require the "
    "question plus demonstration of missing or irrelevant response. C3a requires the incorrect claim and later "
    "contradiction. C4a/C4b require two quotes showing the repetition.",
    'Output. The quotes are for your own check and stay out of the answer: return only the JSON object '
    '{"codes": ["<category id>"]} naming the one category the evidence makes undeniable, or {"codes": []} when '
    'it is weak. No other key and no other text.',
])
CODE = re.compile(r"\bC([1-4])([ab])?\b", re.IGNORECASE)
FENCE = re.compile(r"^```(?:json)?\s*|\s*```$", re.IGNORECASE)
MENTION = re.compile(r"@([A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?)")
# coordbench's bounds: a conversation above 100,000 characters keeps its
# first and last 50,000.
CONVERSATION_LIMIT = 100_000
CONVERSATION_KEEP = 50_000
EMPTY_MCP = '{"mcpServers": {}}'
CALL_TIMEOUT = 600
API_VERSION = "2022-11-28"
PER_PAGE = 100
REVIEW_WORDS = {"APPROVED": "review: approved", "CHANGES_REQUESTED": "review: changes requested",
                "COMMENTED": "review: commented", "DISMISSED": "review: dismissed"}
HEADER = ("Conversation of a pull request: {count} messages in time order, each as [message id] time sender -> "
          "recipient (all for a broadcast): content. The people are named A, B, C and so on in the order they "
          "first speak; bot is any app or bot account.")


class JudgeError(Exception):
    """A judge step that failed outright; the message says which."""


class Gh:
    """GitHub's REST API through the maintainer's own gh, signed in as
    them; the shape of the protocol library's client, so the window's
    pull requests are read by the same code collect uses."""

    def __init__(self, repo=None, run=subprocess.run, binary="gh"):
        self.repo, self.run, self.binary = repo, run, binary

    def call(self, *args):
        done = self.run([self.binary, *args], capture_output=True, text=True, encoding="utf-8")
        if done.returncode != 0:
            raise JudgeError(f"gh {args[0]} {args[-1]}: {(done.stderr or done.stdout or '').strip()[:300]}")
        return done.stdout

    def get(self, path, params=None):
        query = "?" + urllib.parse.urlencode(params) if params else ""
        text = self.call("api", "-H", "Accept: application/vnd.github+json",
                         "-H", f"X-GitHub-Api-Version: {API_VERSION}", path.lstrip("/") + query)
        try:
            return json.loads(text) if text.strip() else None
        except ValueError:
            raise JudgeError(f"gh api {path}: the answer was not JSON") from None

    def pages(self, path, params=None):
        """A list endpoint page by page, until a page comes back short."""
        page = 1
        while True:
            items = self.get(path, {**(params or {}), "per_page": PER_PAGE, "page": page}) or []
            yield items
            if len(items) < PER_PAGE:
                return
            page += 1

    def get_all(self, path, params=None):
        return [item for page in self.pages(path, params) for item in page]

    def default_repo(self):
        return self.call("repo", "view", "--json", "nameWithOwner", "--jq", ".nameWithOwner").strip()


@dataclass
class Message:
    when: datetime
    user: dict
    note: str
    text: str


def pull_messages(pull, comments, review_comments, reviews):
    """A pull request's conversation in time order: its description, its
    comments, its review comments and its reviews. A review with no words
    still says something when it approves or asks for changes."""
    messages = []
    if (pull.get("body") or "").strip():
        messages.append(Message(time_of(pull, "created_at"), pull.get("user"), "description", pull["body"]))
    messages += [Message(time_of(c, "created_at"), c.get("user"), None, c.get("body") or "") for c in comments]
    messages += [Message(time_of(c, "created_at"), c.get("user"), "review comment", c.get("body") or "")
                 for c in review_comments]
    for review in reviews:
        state = review.get("state")
        if state in REVIEW_WORDS and ((review.get("body") or "").strip() or state != "COMMENTED"):
            messages.append(Message(time_of(review, "submitted_at"), review.get("user"), REVIEW_WORDS[state],
                                    review.get("body") or ""))
    epoch = datetime.min.replace(tzinfo=timezone.utc)
    return sorted((m for m in messages if m.text.strip() or m.note), key=lambda m: m.when or epoch)


def letters(index):
    """A, B, ... Z, then AA, AB and on, for the index-th speaker."""
    name = ""
    index += 1
    while index:
        index, rest = divmod(index - 1, 26)
        name = chr(ord("A") + rest) + name
    return name


def speaker_names(messages):
    """Each person's letter, by login, in the order they first speak."""
    names = {}
    for m in messages:
        login = ((m.user or {}).get("login") or "ghost").lower()
        if not is_bot(m.user) and login not in names:
            names[login] = letters(len(names))
    return names


def speaker(user, names):
    return "bot" if is_bot(user) else names[((user or {}).get("login") or "ghost").lower()]


def anonymised(text, names):
    """The text with every mention of a speaker made their letter."""
    return MENTION.sub(lambda m: "@" + names.get(m.group(1).lower(), m.group(1)), text)


def bounded(text):
    """coordbench's cut: the text whole, or its two ends with a line saying
    how much is left out between them."""
    if len(text) <= CONVERSATION_LIMIT:
        return text
    left_out = len(text) - 2 * CONVERSATION_KEEP
    note = (f"\n[this conversation is {len(text):,} characters long; the {left_out:,} characters after the "
            f"first {CONVERSATION_KEEP:,} are left out here, and the last {CONVERSATION_KEEP:,} follow.]\n")
    return text[:CONVERSATION_KEEP] + note + text[-CONVERSATION_KEEP:]


def render(messages):
    """The conversation as the local model reads it, or "" when there is
    none, which no call is made for."""
    if not messages:
        return ""
    names = speaker_names(messages)
    lines = [HEADER.format(count=len(messages)), ""]
    for number, m in enumerate(messages, start=1):
        note = f"({m.note}) " if m.note else ""
        when = iso(m.when) if m.when else "-"
        lines.append(f"[{number}] {when} {speaker(m.user, names)} -> all: {note}{anonymised(m.text, names)}")
    return bounded("\n".join(lines) + "\n")


def conversation_text(gh, pull):
    """One pull request's conversation, read with gh and rendered."""
    path = f"/repos/{gh.repo}"
    number = pull["number"]
    return render(pull_messages(pull, gh.get_all(f"{path}/issues/{number}/comments"),
                                gh.get_all(f"{path}/pulls/{number}/comments"),
                                gh.get_all(f"{path}/pulls/{number}/reviews")))


def claude_command(binary, model):
    """claude -p with App F as the whole system prompt, one turn, no tool,
    no MCP server, no settings (so no hook), no skill and no session kept;
    it runs in an empty folder, so no project's CLAUDE.md is read either."""
    return [binary, "-p", "--output-format", "json", "--model", model, "--max-turns", "1",
            "--system-prompt", APPF_PROMPT, "--tools", "", "--strict-mcp-config", "--mcp-config", EMPTY_MCP,
            "--setting-sources", "", "--disable-slash-commands", "--no-session-persistence"]


class LocalClaude:
    """The maintainer's own Claude Code, signed in to their own account.
    The conversation goes to this one process on stdin and nowhere else."""

    def __init__(self, model, run=subprocess.run, binary="claude"):
        self.model, self.run, self.binary = model, run, binary

    def command(self):
        return claude_command(self.binary, self.model)

    def ask(self, conversation):
        with tempfile.TemporaryDirectory(prefix="sdlc-judge-") as empty:
            try:
                done = self.run(self.command(), input=conversation, capture_output=True, text=True,
                                encoding="utf-8", cwd=empty, timeout=CALL_TIMEOUT, env=judge_environment(os.environ))
            except (OSError, subprocess.SubprocessError) as problem:
                raise JudgeError(f"claude did not run: {problem}") from None
        return claude_result(done)


def judge_environment(environ):
    """The maintainer's environment, which holds their sign-in, without an
    API key, which the refusal has already kept out."""
    return {name: value for name, value in environ.items() if name != "ANTHROPIC_API_KEY"}


def claude_result(done):
    """The reply's text from claude's JSON result."""
    try:
        result = json.loads(done.stdout)
    except (TypeError, ValueError):
        raise JudgeError(f"claude exited {done.returncode} without a JSON result: "
                         f"{(done.stderr or '').strip()[-300:]}") from None
    if done.returncode != 0 or not isinstance(result, dict) or result.get("is_error") \
            or not isinstance(result.get("result"), str):
        subtype = result.get("subtype") if isinstance(result, dict) else None
        raise JudgeError(f"claude failed ({subtype}); nothing is written")
    return result["result"]


def reply_object(text):
    """The reply's JSON object, from the whole text, a fenced block or the
    span between its outer braces; None when there is none."""
    text = FENCE.sub("", (text or "").strip())
    for candidate in (text, text[text.find("{"): text.rfind("}") + 1]):
        try:
            value = json.loads(candidate)
        except ValueError:
            continue
        if isinstance(value, dict):
            return value
    return None


def reply_code(value):
    """The one App F code a reply names, or None. App F labels at most one
    category per conversation, so the first code of the taxonomy counts;
    anything else in the reply is dropped here and never kept."""
    codes = value.get("codes") if isinstance(value, dict) else None
    for item in codes if isinstance(codes, list) else []:
        match = CODE.search(str(item))
        code = match and f"C{match.group(1)}{(match.group(2) or '').lower()}"
        if code in APPF_CODES:
            return code
    return None


def judged_code(claude, conversation):
    """(readable, code) for one conversation: one call, and one more when
    the reply is not JSON, as coordbench's judge allows."""
    for _ in range(2):
        value = reply_object(claude.ask(conversation))
        if value is not None:
            return True, reply_code(value)
    return False, None


def judge_record(model, conversations, counts, now):
    return {"schema": JUDGE_SCHEMA, "generated_at": iso(now), "model": model, "prompt_variant": PROMPT_VARIANT,
            "conversations": conversations, "counts": {code: counts.get(code, 0) for code in APPF_CODES},
            "groups": {group: sum(counts.get(code, 0) for code in APPF_CODES if APPF_GROUPS[code] == group)
                       for group in GROUPS}}


def judge_refusal(environ, which):
    """Why the judge will not run here, or None."""
    if environ.get("ANTHROPIC_API_KEY"):
        return ("judge: ANTHROPIC_API_KEY is set, and claude would bill the API with it, which this project never "
                "does. Unset it (`unset ANTHROPIC_API_KEY`) and run again: claude then runs on your own "
                "subscription, signed in with `claude` as usual.")
    for tool, why in (("gh", "reads the pull requests as you"), ("claude", "is the model that codes them")):
        if not which(tool):
            return f"judge: {tool} is not on PATH; it {why}. Install it, sign in, and run again."
    return None


def show_dry_run(claude, conversations, pulls, record, out):
    """What a run would send and write, and nothing sent or written."""
    print(f"judge: a dry run; nothing is sent, written or pushed. {len(conversations)} of {pulls} pull requests "
          "have a conversation, and a run would send each to your local claude, one call each.", file=out)
    command = claude.command()
    shown = [word if word != APPF_PROMPT else "<the system prompt below>" for word in command]
    print("--- the command, run in an empty temporary folder ---", file=out)
    print(shlex.join(shown), file=out)
    print("--- the system prompt ---", file=out)
    print(APPF_PROMPT, file=out)
    print("--- stdin: the first conversation ---", file=out)
    print(conversations[0] if conversations else "(no conversation in the window)", file=out)
    print("--- the JUDGE.json a run would write (its counts are the model's to fill) ---", file=out)
    print(json.dumps(record, indent=2), file=out)
    return 0


def judge(args, environ, gh, claude, which=shutil.which, git=None, out=sys.stdout):
    """The judge command over injected gh, claude and git, for the tests."""
    refusal = judge_refusal(environ, which)
    if refusal:
        print(refusal, file=sys.stderr)
        return 1
    gh.repo = args.repo or gh.default_repo()
    now = parse_time(args.now) if args.now else datetime.now(timezone.utc)
    pulls = window_pulls(gh, Window.ending(now, args.window_days))[:args.limit or None]
    conversations = [text for pull in pulls if (text := conversation_text(gh, pull))]
    if args.dry_run:
        record = judge_record(claude.model, len(conversations), {}, now)
        return show_dry_run(claude, conversations, len(pulls), record, out)
    counts, judged, unreadable = {}, 0, 0
    for number, conversation in enumerate(conversations, start=1):
        readable, code = judged_code(claude, conversation)
        judged += readable
        unreadable += not readable
        if code:
            counts[code] = counts.get(code, 0) + 1
        print(f"judge: {number} of {len(conversations)} coded", file=sys.stderr)
    if unreadable:
        print(f"judge: {unreadable} replies were not JSON after one retry and are left out", file=sys.stderr)
    write_json(args.out, judge_record(claude.model, judged, counts, now))
    print(f"judge: {args.out} written: {judged} conversations, counts only", file=out)
    if args.push:
        print(f"judge: pushed to {METRICS_BRANCH} as {push_judge(Path(args.out), git or run_git)}", file=out)
    return 0


# --- the judge's push: an ordinary commit on the branch metrics ----------------

REMOTE = "origin"
TRACKING = f"refs/remotes/{REMOTE}/{METRICS_BRANCH}"


def run_git(*args, input=None):
    """One git command in the current clone; its output, or JudgeError."""
    done = subprocess.run(["git", *args], input=input, capture_output=True, text=True, encoding="utf-8")
    if done.returncode != 0:
        raise JudgeError(f"git {args[0]}: {(done.stderr or '').strip()[:300]}")
    return done.stdout


def fetched_metrics(git):
    """The branch metrics' commit on origin, or None when it has none yet.
    The tracking ref is dropped first, so a branch deleted since the last
    fetch is not mistaken for one still there."""
    for step in (("update-ref", "-d", TRACKING), ("fetch", "--quiet", "--no-tags", REMOTE,
                                                   f"+refs/heads/{METRICS_BRANCH}:{TRACKING}")):
        try:
            git(*step)
        except JudgeError:
            if step[0] == "fetch":
                return None
    return git("rev-parse", "--verify", "--quiet", TRACKING + "^{commit}").strip() or None


def judge_commit(git, path, parent):
    """A commit whose tree is the parent's with JUDGE.json put in, so the
    METRICS.json the workflow wrote stays exactly as it is."""
    blob = git("hash-object", "-w", str(path)).strip()
    kept = [line for line in (git("ls-tree", parent).splitlines() if parent else [])
            if not line.endswith("\t" + JUDGE_FILE)]
    tree = git("mktree", input="\n".join(kept + [f"100644 blob {blob}\t{JUDGE_FILE}"]) + "\n").strip()
    message = f"Judge counts as of {iso(datetime.now(timezone.utc))}"
    return git("commit-tree", tree, *(("-p", parent) if parent else ()), "-m", message).strip()


def push_arguments(commit):
    """The push: a plain one, which only a fast-forward passes, so the push
    guard (tools/guard_push.py) lets it through and the workflow's lease
    sees it."""
    return ["push", "--quiet", REMOTE, f"{commit}:refs/heads/{METRICS_BRANCH}"]


def push_judge(path, git):
    """Push JUDGE.json onto the branch metrics; when the workflow rewrote
    the branch in between, read it again and try once more."""
    refused = None
    for _ in range(2):
        commit = judge_commit(git, path, fetched_metrics(git))
        try:
            git(*push_arguments(commit))
            return commit
        except JudgeError as problem:
            refused = problem
    raise JudgeError(f"the push to {METRICS_BRANCH} was refused twice, the last time with: {refused}; "
                     f"{path} is written, so run the push again with --push")


# --- the command line -----------------------------------------------------------

def collect(args, environ, opener=None, sleep=time.sleep):
    if sharing(args.root, environ) == OFF:
        write_json(args.out, OFF_RECORD)
        print(f"metrics: sharing is off ({SWITCH_FILE} or {SWITCH_VARIABLE}); {args.out} says so and nothing else")
        return 0
    now = parse_time(args.now) if args.now else datetime.now(timezone.utc)
    window = Window.ending(now, args.window_days)
    api = GitHub(environ.get("GITHUB_TOKEN"), args.repo, opener=opener, sleep=sleep)
    facts, extra_claims, comments = read_repository(api, window)
    write_json(args.out, metrics_record(measures(facts, extra_claims, comments, window), window, protocol_version()))
    print(f"metrics: {args.out} written over {args.window_days} days")
    return 0


def unchanged(args):
    try:
        old, new = Path(args.old).read_text(encoding="utf-8"), Path(args.new).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return 1
    return 0 if same_apart_from_time(old, new) else 1


def positive(text):
    value = int(text)
    if value < 1:
        raise argparse.ArgumentTypeError("must be 1 or more")
    return value


def parse_args(argv):
    parser = argparse.ArgumentParser(description="Field metrics of the claim protocol (docs/setup/metrics.md).")
    commands = parser.add_subparsers(dest="command", required=True)
    gather = commands.add_parser("collect", help="write METRICS.json from GitHub's REST API (GITHUB_TOKEN)")
    gather.add_argument("--repo", required=True, help="OWNER/NAME")
    gather.add_argument("--out", required=True, help="where METRICS.json goes")
    gather.add_argument("--root", default=".", help=f"the checkout holding {SWITCH_FILE} (default: here)")
    code = commands.add_parser("judge", help="code recent pull request conversations with your own claude -p")
    code.add_argument("--repo", help="OWNER/NAME (default: the repository gh sees here)")
    code.add_argument("--limit", type=positive, help="judge at most this many pull requests, newest first")
    code.add_argument("--dry-run", action="store_true", help="show what would be sent and written; send nothing")
    code.add_argument("--model", default=DEFAULT_MODEL, help=f"the model claude runs (default: {DEFAULT_MODEL})")
    code.add_argument("--out", default=JUDGE_FILE, help=f"where JUDGE.json goes (default: ./{JUDGE_FILE})")
    code.add_argument("--push", action="store_true", help=f"commit JUDGE.json onto the branch {METRICS_BRANCH}")
    for each in (gather, code):
        each.add_argument("--window-days", type=positive, default=WINDOW_DAYS, help="days to look back (default: 30)")
        each.add_argument("--now", help="the window's end, an ISO time (default: now; for tests)")
    same = commands.add_parser("unchanged", help="exit 0 when two METRICS.json differ only in generated_at")
    same.add_argument("old")
    same.add_argument("new")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    try:
        if args.command == "collect":
            return collect(args, os.environ)
        if args.command == "judge":
            return judge(args, os.environ, Gh(), LocalClaude(args.model))
        return unchanged(args)
    except (GitHubError, JudgeError) as problem:
        print(f"metrics: {problem}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
