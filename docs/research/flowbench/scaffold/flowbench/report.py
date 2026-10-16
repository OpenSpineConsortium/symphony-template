"""The arms side by side: resolved rates with intervals, the paired
comparisons, cost and time, the review table, one row per instance.

A run's logs hold <logs>/<tag>/<arm>/<instance>/attempt-<n>/result.json.
For each (arm, instance) the report takes the newest attempt that was
scored, that the audit did not call a harness error and that it did not
exclude (an agent whose transcript names the benchmark's files); a
harness error or an exclusion is left out of every figure and named
(PLAN.md, Resume). An arm's timeouts and turn limits are counted apart
from its orchestration failures, since an agent that ran out of time is
a different failure from a flow that broke. Given the sample the run was
to cover (--instances), the report gives beside the rate over the runs
finished the rate over the sample, an instance with no clean scored run
counting as not resolved, so a run cut short cannot read as a better one.
The statistics are coordbench's: the Wilson interval, the exact McNemar
test on the discordant instances, and a bootstrap over repositories,
since instances of one repository are not independent (an arm with one
repository gets no bootstrap interval, and the report says so). The
primary cost comparison (PLAN.md) is the primary arm's tokens against
each other arm's on the instances both measured, as the ratio of the two
sums with the same bootstrap. Nothing here calls a model.

    python3 flowbench/report.py --logs LOGS --tag TAG [--arms symphony,script,solo] [--primary symphony]
        [--instances a,b | @FILE] [--json]
"""

import argparse
import json
import math
import random
import sys
from pathlib import Path

BOOTSTRAP_ITERATIONS = 2000
DEFAULT_ARMS = ("symphony", "script", "solo")


def wilson(passed, total, z=1.96):
    """The 95% Wilson score interval, as two fractions."""
    if total == 0:
        return (0.0, 0.0)
    rate = passed / total
    centre = (rate + z * z / (2 * total)) / (1 + z * z / total)
    half = z * math.sqrt(rate * (1 - rate) / total + z * z / (4 * total * total)) / (1 + z * z / total)
    return (max(0.0, centre - half), min(1.0, centre + half))


def mcnemar_exact(only_first, only_second):
    """Two-sided exact McNemar p-value from the discordant counts."""
    n = only_first + only_second
    if n == 0:
        return 1.0
    tail = sum(math.comb(n, k) for k in range(min(only_first, only_second) + 1)) / 2 ** n
    return min(1.0, 2 * tail)


def bootstrap_rate(clusters, iterations=BOOTSTRAP_ITERATIONS, seed=0):
    """A 95% interval for the rate by resampling clusters (repositories)
    with replacement; each cluster is a list of 0/1 outcomes. None with
    fewer than two clusters, since resampling one says nothing."""
    clusters = [c for c in clusters if c]
    if len(clusters) < 2:
        return None
    draw = random.Random(seed)
    rates = []
    for _ in range(iterations):
        chosen = [clusters[draw.randrange(len(clusters))] for _ in clusters]
        outcomes = [o for c in chosen for o in c]
        rates.append(sum(outcomes) / len(outcomes))
    rates.sort()
    return (rates[int(0.025 * (len(rates) - 1))], rates[int(0.975 * (len(rates) - 1))])


def read_result(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def attempts(logs, tag, arm):
    """Every result.json of the arm, by instance, newest attempt last,
    each marked with what its audit says."""
    found = {}
    root = Path(logs) / tag / arm
    if not root.is_dir():
        return found
    for instance_dir in sorted(root.iterdir()):
        if not instance_dir.is_dir():
            continue
        records = []
        for attempt_dir in sorted(instance_dir.glob("attempt-*"), key=lambda p: int(p.name.split("-")[1])):
            result = read_result(attempt_dir / "result.json")
            if result:
                audit = read_result(attempt_dir / "audit.json") or {}
                result["_harness_error"] = bool(audit.get("harness_error")) or bool(result.get("harness_error"))
                result["_excluded"] = bool(audit.get("excluded")) or bool(result.get("excluded"))
                result["_dir"] = str(attempt_dir)
                records.append(result)
        if records:
            found[instance_dir.name] = records
    return found


def scored(result):
    return bool(result.get("scoring")) and result["scoring"].get("reason") not in (None, "error", "incomplete")


def clean(result):
    return scored(result) and not result["_harness_error"] and not result["_excluded"]


def choose(records):
    """The attempt the report counts, by PLAN.md's rule: the newest attempt
    that was scored with no harness error and no exclusion; None when
    there is none, since a run the harness broke, or one that went
    looking, is left out and named, never counted as the arm's failure."""
    kept = [r for r in records if clean(r)]
    return kept[-1] if kept else None


def resolved(result):
    return bool(result.get("scoring", {}).get("resolved"))


def tokens_of(result):
    return (result.get("tokens") or {})


def total_tokens(result):
    """The run's tokens, the output's lower bound standing in where the
    count is unknown; None where an agent left no count at all."""
    tokens = tokens_of(result)
    if not tokens or tokens.get("agents_uncounted"):
        return None
    output = tokens.get("output") if tokens.get("output") is not None else tokens.get("output_lower_bound")
    return sum(int(tokens.get(k) or 0) for k in ("input", "cache_read", "cache_write")) + int(output or 0)


def median(values):
    values = sorted(v for v in values if v is not None)
    if not values:
        return None
    middle = len(values) // 2
    return values[middle] if len(values) % 2 else (values[middle - 1] + values[middle]) / 2


def mean(values):
    values = [v for v in values if v is not None]
    return sum(values) / len(values) if values else None


def repository_of(result):
    return (result.get("repo") or result.get("instance", "")).split("__")[0]


def ratio_interval(clusters, iterations=BOOTSTRAP_ITERATIONS, seed=0):
    """A 95% interval for sum(a) / sum(b) over (a, b) pairs, resampling
    clusters (repositories) with replacement; None with fewer than two."""
    clusters = [c for c in clusters if c]
    if len(clusters) < 2:
        return None
    draw = random.Random(seed)
    ratios = []
    for _ in range(iterations):
        chosen = [clusters[draw.randrange(len(clusters))] for _ in clusters]
        below = sum(b for c in chosen for _, b in c)
        if below:
            ratios.append(sum(a for c in chosen for a, _ in c) / below)
    if not ratios:
        return None
    ratios.sort()
    return (ratios[int(0.025 * (len(ratios) - 1))], ratios[int(0.975 * (len(ratios) - 1))])


def paired_tokens(first, second, seed=0):
    """The first arm's tokens over the second's on the instances both
    measured: {"n", "ratio", "bootstrap"}, or None with none to pair."""
    clusters = {}
    for instance in sorted(set(first.chosen) & set(second.chosen)):
        a, b = total_tokens(first.chosen[instance]), total_tokens(second.chosen[instance])
        if a is not None and b is not None:
            clusters.setdefault(repository_of(first.chosen[instance]), []).append((a, b))
    pairs = [pair for cluster in clusters.values() for pair in cluster]
    below = sum(b for _, b in pairs)
    if not pairs or not below:
        return None
    return {"n": len(pairs), "ratio": sum(a for a, _ in pairs) / below,
            "bootstrap": ratio_interval(list(clusters.values()), seed=seed)}


def ran_review(result):
    """Whether a review stage ran in the run, read from its stages, so the
    review table counts no arm that has no review to count."""
    return any(stage.get("kind") == "review" and not stage.get("skipped") for stage in result.get("stages") or [])


class Arm:
    def __init__(self, name, chosen, harness_errors, excluded, sample=None):
        self.name = name
        self.chosen = chosen
        self.harness_errors = harness_errors
        self.excluded = excluded
        self.sample = list(sample) if sample else None

    @property
    def n(self):
        return len(self.chosen)

    @property
    def k(self):
        return sum(1 for r in self.chosen.values() if resolved(r))

    def unfinished(self):
        """The sample's instances with no clean scored run."""
        return [i for i in self.sample or [] if i not in self.chosen]

    def clusters(self):
        groups = {}
        for result in self.chosen.values():
            groups.setdefault(repository_of(result), []).append(1 if resolved(result) else 0)
        return list(groups.values())

    def flow_count(self, key):
        return sum(int((r.get("flow") or {}).get(key) or 0) for r in self.chosen.values())

    def orchestration_failures(self):
        return sum(1 for r in self.chosen.values() if (r.get("flow") or {}).get("orchestration_failure"))

    def cost_sources(self):
        return sorted({r.get("cost_source") or "none" for r in self.chosen.values()})

    def tokens_per_resolved(self):
        """The tokens of the runs measured over the instances they resolved."""
        measured = [r for r in self.chosen.values() if total_tokens(r) is not None]
        solved = sum(1 for r in measured if resolved(r))
        return sum(total_tokens(r) for r in measured) / solved if solved else None

    def review(self):
        raised = confirmed = fixed = 0
        with_finding = []
        without = []
        seen = False
        for result in self.chosen.values():
            if not ran_review(result):
                continue
            flow = result.get("flow") or {}
            seen = True
            raised += int(flow.get("findings_raised") or 0)
            confirmed += int(flow.get("findings_confirmed") or 0)
            fixed += int(flow.get("findings_fixed") or 0)
            (with_finding if int(flow.get("findings_confirmed") or 0) else without).append(1 if resolved(result) else 0)
        if not seen:
            return None
        return {"raised": raised, "confirmed": confirmed, "fixed": fixed,
                "resolved_with_confirmed": (sum(with_finding), len(with_finding)),
                "resolved_without": (sum(without), len(without))}


def load(logs, tag, names, sample=None):
    arms = []
    for name in names:
        records = attempts(logs, tag, name)
        chosen = {instance: choose(found) for instance, found in records.items()}
        chosen = {instance: result for instance, result in chosen.items() if result is not None}
        errors = {instance: [r["_dir"] for r in found if r["_harness_error"]] for instance, found in records.items()}
        excluded = {instance: [r["_dir"] for r in found if r["_excluded"]] for instance, found in records.items()}
        arms.append(Arm(name, chosen, {i: d for i, d in errors.items() if d}, {i: d for i, d in excluded.items() if d},
                        sample))
    return arms


def percent(k, n):
    return f"{100 * k / n:.1f}%" if n else "-"


def interval_text(interval):
    if interval is None:
        return "-"
    low, high = interval
    return f"{100 * low:.0f} to {100 * high:.0f}"


def table(header, rows):
    lines = ["| " + " | ".join(header) + " |", "| " + " | ".join("---" for _ in header) + " |"]
    lines += ["| " + " | ".join(str(c) for c in row) + " |" for row in rows]
    return "\n".join(lines)


def rates_section(arms, seed):
    with_sample = any(arm.sample for arm in arms)
    rows = []
    for arm in arms:
        row = [arm.name, arm.n, arm.k, percent(arm.k, arm.n), interval_text(wilson(arm.k, arm.n)),
               interval_text(bootstrap_rate(arm.clusters(), seed=seed))]
        if with_sample:
            row.append(f"{arm.k}/{len(arm.sample)} ({percent(arm.k, len(arm.sample))})" if arm.sample else "-")
        row += [arm.orchestration_failures(), arm.flow_count("timeouts"), arm.flow_count("turn_limits"),
                len(arm.harness_errors), len(arm.excluded)]
        rows.append(row)
    header = ["arm", "n", "resolved", "rate", "Wilson 95%", "bootstrap over repositories"]
    if with_sample:
        header.append("of the sample")
    header += ["orchestration failures", "timeouts", "turn limits", "harness errors left out", "excluded"]
    return "## Resolved\n\n" + table(header, rows)


def paired(first, second):
    both = sorted(set(first.chosen) & set(second.chosen))
    only_first = sum(1 for i in both if resolved(first.chosen[i]) and not resolved(second.chosen[i]))
    only_second = sum(1 for i in both if resolved(second.chosen[i]) and not resolved(first.chosen[i]))
    return both, only_first, only_second


def comparisons_section(arms, primary):
    first = next((a for a in arms if a.name == primary), None)
    if first is None:
        return f"## Comparisons\n\n{primary} has no runs."
    rows = []
    for second in arms:
        if second is first:
            continue
        both, only_first, only_second = paired(first, second)
        if not both:
            rows.append([f"{first.name} vs {second.name}", 0, "-", "-", "-", "-"])
            continue
        gap = 100 * (sum(resolved(first.chosen[i]) for i in both) - sum(resolved(second.chosen[i]) for i in both)) / len(both)
        rows.append([f"{first.name} vs {second.name}", len(both), only_first, only_second, f"{gap:+.1f}",
                     f"{mcnemar_exact(only_first, only_second):.3f}"])
    return "## Comparisons (instances both arms scored)\n\n" + table(
        ["comparison", "n", f"only {primary}", "only the other", "gap in points", "exact McNemar p"], rows)


def number(value, form):
    return format(value, form) if value is not None else "-"


def cost_section(arms):
    rows = []
    for arm in arms:
        results = list(arm.chosen.values())
        tokens = [total_tokens(r) for r in results]
        costs = [r.get("cost_usd") for r in results]
        seconds = [(r.get("timings") or {}).get("agents_seconds") for r in results]
        wall = [(r.get("timings") or {}).get("wall_seconds") for r in results]
        rows.append([arm.name, len([t for t in tokens if t is not None]), number(median(tokens), ",.0f"),
                     number(mean(tokens), ",.0f"), number(arm.tokens_per_resolved(), ",.0f"), number(mean(costs), ".2f"),
                     ", ".join(arm.cost_sources()) or "-", number(median(seconds), ".0f"), number(median(wall), ".0f")])
    return "## Cost and time per instance\n\n" + table(
        ["arm", "measured", "tokens, median", "tokens, mean", "tokens per resolved", "est. USD, mean", "cost source",
         "agents' seconds, median", "wall seconds, median"], rows)


def paired_cost_section(arms, primary, seed):
    first = next((a for a in arms if a.name == primary), None)
    if first is None:
        return f"## Cost, paired\n\n{primary} has no runs."
    rows = []
    for second in arms:
        if second is first:
            continue
        found = paired_tokens(first, second, seed)
        if found is None:
            rows.append([f"{first.name} / {second.name}", 0, "-", "-"])
        else:
            rows.append([f"{first.name} / {second.name}", found["n"], f"{found['ratio']:.2f}",
                         "-" if found["bootstrap"] is None else f"{found['bootstrap'][0]:.2f} to {found['bootstrap'][1]:.2f}"])
    return "## Cost, paired (instances both arms measured)\n\n" + table(
        ["tokens", "n", "ratio of the sums", "bootstrap over repositories"], rows)


def flow_section(arms):
    rows = []
    for arm in arms:
        review = arm.review()
        if review is None:
            continue
        with_k, with_n = review["resolved_with_confirmed"]
        without_k, without_n = review["resolved_without"]
        rows.append([arm.name, review["raised"], review["confirmed"], review["fixed"],
                     f"{with_k}/{with_n}", f"{without_k}/{without_n}"])
    if not rows:
        return "## Review\n\nNo arm ran a review stage."
    return "## Review (arms that ran one)\n\n" + table(["arm", "findings raised", "confirmed", "fixed",
                                                        "resolved, with a confirmed finding", "resolved, with none"], rows)


def instances_section(arms):
    instances = sorted(set(i for a in arms for i in a.chosen) | set(i for a in arms if a.sample for i in a.sample))
    rows = []
    for instance in instances:
        cells = [instance]
        for arm in arms:
            result = arm.chosen.get(instance)
            if result is None:
                cells.append("-")
            else:
                mark = "pass" if resolved(result) else (result.get("scoring") or {}).get("reason") or "?"
                cells.append(mark)
        rows.append(cells)
    return "## Instances\n\n" + table(["instance"] + [a.name for a in arms], rows)


def notes(arms):
    lines = []
    for arm in arms:
        if arm.harness_errors:
            lines.append(f"Harness errors left out of {arm.name}: " +
                         ", ".join(f"{i} ({len(d)})" for i, d in sorted(arm.harness_errors.items())))
        if arm.excluded:
            lines.append(f"Excluded from {arm.name}, the transcript naming the benchmark's files: " +
                         ", ".join(f"{i} ({len(d)})" for i, d in sorted(arm.excluded.items())))
        if arm.n and len(arm.clusters()) < 2:
            lines.append(f"No bootstrap interval for {arm.name}: its instances are of one repository.")
        if arm.sample and arm.unfinished():
            lines.append(f"Of the sample's {len(arm.sample)} instances, {arm.name} has no clean run for: " +
                         ", ".join(arm.unfinished()) + " (counted as not resolved in the sample's rate).")
    return lines


def render(logs, tag, names, primary, seed=0, sample=None):
    arms = load(logs, tag, names, sample)
    parts = [f"# flowbench report: {tag}", "", f"Arms: {', '.join(names)}; primary {primary}; logs {logs}.", "",
             rates_section(arms, seed), "", comparisons_section(arms, primary), "", cost_section(arms), "",
             paired_cost_section(arms, primary, seed), "", flow_section(arms), "", instances_section(arms)]
    for line in notes(arms):
        parts += ["", line]
    return "\n".join(parts) + "\n"


def as_data(logs, tag, names, primary, seed=0, sample=None):
    arms = load(logs, tag, names, sample)
    data = {"tag": tag, "primary": primary, "sample": list(sample) if sample else None, "arms": {}}
    for arm in arms:
        boot = bootstrap_rate(arm.clusters(), seed=seed)
        data["arms"][arm.name] = {"n": arm.n, "resolved": arm.k, "wilson": list(wilson(arm.k, arm.n)),
                                  "bootstrap": list(boot) if boot else None,
                                  "of_sample": {"n": len(arm.sample), "resolved": arm.k, "unfinished": arm.unfinished()}
                                  if arm.sample else None,
                                  "orchestration_failures": arm.orchestration_failures(),
                                  "timeouts": arm.flow_count("timeouts"), "turn_limits": arm.flow_count("turn_limits"),
                                  "harness_errors": arm.harness_errors, "excluded": arm.excluded,
                                  "cost_sources": arm.cost_sources(), "tokens_per_resolved": arm.tokens_per_resolved(),
                                  "review": arm.review()}
    first = next((a for a in arms if a.name == primary), None)
    data["comparisons"] = {}
    if first:
        for second in arms:
            if second is not first:
                both, only_first, only_second = paired(first, second)
                data["comparisons"][second.name] = {"n": len(both), "only_primary": only_first,
                                                    "only_other": only_second, "p": mcnemar_exact(only_first, only_second),
                                                    "tokens": paired_tokens(first, second, seed)}
    return data


def read_sample(text):
    """The sample's instances: comma separated, or @FILE with one per line."""
    if not text:
        return None
    if text.startswith("@"):
        return [line.strip() for line in Path(text[1:]).read_text(encoding="utf-8").splitlines() if line.strip()]
    return [part.strip() for part in text.split(",") if part.strip()]


def main(argv=None):
    parser = argparse.ArgumentParser(description="Set flowbench's arms side by side.")
    parser.add_argument("--logs", required=True)
    parser.add_argument("--tag", required=True)
    parser.add_argument("--arms", default=",".join(DEFAULT_ARMS))
    parser.add_argument("--primary", default=DEFAULT_ARMS[0])
    parser.add_argument("--instances", help="the sample the run was to cover: comma separated, or @FILE with one per line")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    names = [n.strip() for n in args.arms.split(",") if n.strip()]
    try:
        sample = read_sample(args.instances)
    except OSError as error:
        print(error, file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(as_data(args.logs, args.tag, names, args.primary, args.seed, sample), indent=2, sort_keys=True))
    else:
        print(render(args.logs, args.tag, names, args.primary, args.seed, sample), end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
