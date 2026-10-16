"""The arms side by side: resolved rates with intervals, the paired
comparisons, cost and time, the flow tables, one row per instance.

A run's logs hold <logs>/<tag>/<arm>/<instance>/attempt-<n>/result.json.
For each (arm, instance) the report takes the newest attempt that was
scored and that the audit did not call a harness error, else the newest
scored one, else the newest; a harness error is left out of every figure
and named (PLAN.md, Resume). The statistics are coordbench's: the Wilson
interval, the exact McNemar test on the discordant instances, and a
bootstrap over repositories, since instances of one repository are not
independent. Nothing here calls a model.

    python3 flowbench/report.py --logs LOGS --tag TAG [--arms symphony,script,solo] [--primary symphony] [--json]
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
    with replacement; each cluster is a list of 0/1 outcomes."""
    clusters = [c for c in clusters if c]
    if not clusters:
        return (0.0, 0.0)
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
    """Every result.json of the arm, by instance, newest attempt last."""
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
                result["_dir"] = str(attempt_dir)
                records.append(result)
        if records:
            found[instance_dir.name] = records
    return found


def scored(result):
    return bool(result.get("scoring")) and result["scoring"].get("reason") not in (None, "error", "incomplete")


def choose(records):
    """The attempt the report counts, by PLAN.md's rule: the newest attempt
    that was scored with no harness error; None when there is none, since
    a run the harness broke is left out and named, never counted as the
    arm's failure."""
    clean = [r for r in records if scored(r) and not r["_harness_error"]]
    return clean[-1] if clean else None


def resolved(result):
    return bool(result.get("scoring", {}).get("resolved"))


def tokens_of(result):
    return (result.get("tokens") or {})


def total_tokens(result):
    tokens = tokens_of(result)
    if not tokens:
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


class Arm:
    def __init__(self, name, chosen, harness_errors):
        self.name = name
        self.chosen = chosen
        self.harness_errors = harness_errors

    @property
    def n(self):
        return len(self.chosen)

    @property
    def k(self):
        return sum(1 for r in self.chosen.values() if resolved(r))

    def clusters(self):
        groups = {}
        for result in self.chosen.values():
            groups.setdefault(repository_of(result), []).append(1 if resolved(result) else 0)
        return list(groups.values())

    def orchestration_failures(self):
        return sum(1 for r in self.chosen.values() if (r.get("flow") or {}).get("orchestration_failure"))

    def review(self):
        raised = confirmed = fixed = 0
        with_finding = []
        without = []
        seen = False
        for result in self.chosen.values():
            flow = result.get("flow") or {}
            if "findings_raised" not in flow:
                continue
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


def load(logs, tag, names):
    arms = []
    for name in names:
        records = attempts(logs, tag, name)
        chosen = {instance: choose(found) for instance, found in records.items()}
        chosen = {instance: result for instance, result in chosen.items() if result is not None}
        errors = {instance: [r["_dir"] for r in found if r["_harness_error"]] for instance, found in records.items()}
        errors = {i: dirs for i, dirs in errors.items() if dirs}
        arms.append(Arm(name, chosen, errors))
    return arms


def percent(k, n):
    return f"{100 * k / n:.1f}%" if n else "-"


def interval_text(low, high):
    return f"{100 * low:.0f} to {100 * high:.0f}"


def table(header, rows):
    lines = ["| " + " | ".join(header) + " |", "| " + " | ".join("---" for _ in header) + " |"]
    lines += ["| " + " | ".join(str(c) for c in row) + " |" for row in rows]
    return "\n".join(lines)


def rates_section(arms, seed):
    rows = []
    for arm in arms:
        low, high = wilson(arm.k, arm.n)
        boot = bootstrap_rate(arm.clusters(), seed=seed)
        rows.append([arm.name, arm.n, arm.k, percent(arm.k, arm.n), interval_text(low, high), interval_text(*boot),
                     arm.orchestration_failures(), len(arm.harness_errors)])
    return "## Resolved\n\n" + table(["arm", "n", "resolved", "rate", "Wilson 95%", "bootstrap over repositories",
                                      "orchestration failures", "harness errors left out"], rows)


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


def cost_section(arms):
    rows = []
    for arm in arms:
        results = list(arm.chosen.values())
        tokens = [total_tokens(r) for r in results]
        costs = [r.get("cost_usd") for r in results]
        seconds = [(r.get("timings") or {}).get("agents_seconds") for r in results]
        rows.append([arm.name, len([t for t in tokens if t is not None]),
                     f"{median(tokens):,.0f}" if median(tokens) is not None else "-",
                     f"{mean(tokens):,.0f}" if mean(tokens) is not None else "-",
                     f"{mean(costs):.2f}" if mean(costs) is not None else "-",
                     f"{median(seconds):.0f}" if median(seconds) is not None else "-"])
    return "## Cost and time per instance\n\n" + table(
        ["arm", "measured", "tokens, median", "tokens, mean", "est. USD, mean", "agents' seconds, median"], rows)


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
        return "## Review\n\nNo arm recorded a review stage."
    return "## Review\n\n" + table(["arm", "findings raised", "confirmed", "fixed",
                                   "resolved, with a confirmed finding", "resolved, with none"], rows)


def instances_section(arms):
    instances = sorted(set(i for a in arms for i in a.chosen))
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


def render(logs, tag, names, primary, seed=0):
    arms = load(logs, tag, names)
    parts = [f"# flowbench report: {tag}", "", f"Arms: {', '.join(names)}; primary {primary}; logs {logs}.", "",
             rates_section(arms, seed), "", comparisons_section(arms, primary), "", cost_section(arms), "",
             flow_section(arms), "", instances_section(arms)]
    for arm in arms:
        if arm.harness_errors:
            parts += ["", f"Harness errors left out of {arm.name}: " +
                      ", ".join(f"{i} ({len(d)})" for i, d in sorted(arm.harness_errors.items()))]
    return "\n".join(parts) + "\n"


def as_data(logs, tag, names, primary, seed=0):
    arms = load(logs, tag, names)
    data = {"tag": tag, "primary": primary, "arms": {}}
    for arm in arms:
        low, high = wilson(arm.k, arm.n)
        data["arms"][arm.name] = {"n": arm.n, "resolved": arm.k, "wilson": [low, high],
                                  "bootstrap": list(bootstrap_rate(arm.clusters(), seed=seed)),
                                  "orchestration_failures": arm.orchestration_failures(),
                                  "harness_errors": arm.harness_errors, "review": arm.review()}
    first = next((a for a in arms if a.name == primary), None)
    data["comparisons"] = {}
    if first:
        for second in arms:
            if second is not first:
                both, only_first, only_second = paired(first, second)
                data["comparisons"][second.name] = {"n": len(both), "only_primary": only_first,
                                                    "only_other": only_second, "p": mcnemar_exact(only_first, only_second)}
    return data


def main(argv=None):
    parser = argparse.ArgumentParser(description="Set flowbench's arms side by side.")
    parser.add_argument("--logs", required=True)
    parser.add_argument("--tag", required=True)
    parser.add_argument("--arms", default=",".join(DEFAULT_ARMS))
    parser.add_argument("--primary", default=DEFAULT_ARMS[0])
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    names = [n.strip() for n in args.arms.split(",") if n.strip()]
    if args.json:
        print(json.dumps(as_data(args.logs, args.tag, names, args.primary, args.seed), indent=2, sort_keys=True))
    else:
        print(render(args.logs, args.tag, names, args.primary, args.seed), end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
