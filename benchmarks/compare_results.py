#!/usr/bin/env python3
"""
Compare benchmark results between with-skill and without-skill runs.

Generates a comparison report showing improvement metrics.

Usage:
    python compare_results.py results/with-skill.json results/without-skill.json
    python compare_results.py results/with-skill.json results/without-skill.json --output results/comparison-report.md
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


def load_results(filepath: str) -> dict:
    """Load benchmark results from JSON file."""
    path = Path(filepath)
    if not path.exists():
        print(f"ERROR: Results file not found: {filepath}", file=sys.stderr)
        sys.exit(1)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def compare_triggering(with_skill: list[dict], without_skill: list[dict]) -> dict:
    """Compare triggering test results."""
    def accuracy(results: list[dict]) -> float:
        correct = sum(
            1 for r in results
            if r.get("evaluations", {}).get("triggering", {}).get("correct", False)
        )
        return correct / len(results) if results else 0

    ws_acc = accuracy(with_skill)
    wos_acc = accuracy(without_skill)

    return {
        "metric": "Trigger Accuracy",
        "with_skill": f"{ws_acc:.0%}",
        "without_skill": f"{wos_acc:.0%}",
        "improvement": f"{ws_acc - wos_acc:+.0%}",
        "target": ">= 90%",
        "target_met": ws_acc >= 0.9,
    }


def compare_functional(with_skill: list[dict], without_skill: list[dict]) -> list[dict]:
    """Compare functional test results."""
    comparisons = []

    # Average functional score
    ws_scores = [
        r.get("evaluations", {}).get("functional", {}).get("score", 0)
        for r in with_skill
    ]
    wos_scores = [
        r.get("evaluations", {}).get("functional", {}).get("score", 0)
        for r in without_skill
    ]
    ws_avg = sum(ws_scores) / len(ws_scores) if ws_scores else 0
    wos_avg = sum(wos_scores) / len(wos_scores) if wos_scores else 0

    comparisons.append({
        "metric": "Functional Score (avg)",
        "with_skill": f"{ws_avg:.0%}",
        "without_skill": f"{wos_avg:.0%}",
        "improvement": f"{ws_avg - wos_avg:+.0%}",
    })

    # Safety compliance
    ws_safe = sum(
        1 for r in with_skill
        if r.get("evaluations", {}).get("safety", {}).get("safe", True)
    )
    wos_safe = sum(
        1 for r in without_skill
        if r.get("evaluations", {}).get("safety", {}).get("safe", True)
    )

    comparisons.append({
        "metric": "Safety Compliance",
        "with_skill": f"{ws_safe}/{len(with_skill)}",
        "without_skill": f"{wos_safe}/{len(without_skill)}",
        "improvement": f"{ws_safe - wos_safe:+d} tests",
    })

    return comparisons


def compare_performance(with_skill: list[dict], without_skill: list[dict]) -> list[dict]:
    """Compare performance test results."""
    comparisons = []

    # Format compliance
    ws_fmt = [
        r.get("evaluations", {}).get("format_compliance", {}).get("score", 0)
        for r in with_skill
    ]
    wos_fmt = [
        r.get("evaluations", {}).get("format_compliance", {}).get("score", 0)
        for r in without_skill
    ]
    ws_avg = sum(ws_fmt) / len(ws_fmt) if ws_fmt else 0
    wos_avg = sum(wos_fmt) / len(wos_fmt) if wos_fmt else 0

    comparisons.append({
        "metric": "Format Compliance (avg)",
        "with_skill": f"{ws_avg:.0%}",
        "without_skill": f"{wos_avg:.0%}",
        "improvement": f"{ws_avg - wos_avg:+.0%}",
    })

    # Safety in performance tests
    ws_safe_score = [
        r.get("evaluations", {}).get("safety", {}).get("score", 0)
        for r in with_skill
    ]
    wos_safe_score = [
        r.get("evaluations", {}).get("safety", {}).get("score", 0)
        for r in without_skill
    ]
    ws_s = sum(ws_safe_score) / len(ws_safe_score) if ws_safe_score else 0
    wos_s = sum(wos_safe_score) / len(wos_safe_score) if wos_safe_score else 0

    comparisons.append({
        "metric": "Safety Score (avg)",
        "with_skill": f"{ws_s:.0%}",
        "without_skill": f"{wos_s:.0%}",
        "improvement": f"{ws_s - wos_s:+.0%}",
    })

    # Token efficiency
    ws_tokens = [
        (r.get("tokens_input", 0) or 0) + (r.get("tokens_output", 0) or 0)
        for r in with_skill
    ]
    wos_tokens = [
        (r.get("tokens_input", 0) or 0) + (r.get("tokens_output", 0) or 0)
        for r in without_skill
    ]
    ws_t = sum(ws_tokens) / len(ws_tokens) if ws_tokens else 0
    wos_t = sum(wos_tokens) / len(wos_tokens) if wos_tokens else 0

    if ws_t > 0 and wos_t > 0:
        comparisons.append({
            "metric": "Avg Tokens Used",
            "with_skill": f"{ws_t:.0f}",
            "without_skill": f"{wos_t:.0f}",
            "improvement": f"{ws_t - wos_t:+.0f}",
        })

    return comparisons


def generate_report(
    with_data: dict,
    without_data: dict,
) -> str:
    """Generate a Markdown comparison report."""
    lines = []
    lines.append("# Benchmark Comparison Report")
    lines.append("")
    lines.append(f"**Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    lines.append(f"**With-skill run:** {with_data['metadata'].get('timestamp', 'N/A')}")
    lines.append(f"**Without-skill run:** {without_data['metadata'].get('timestamp', 'N/A')}")
    lines.append(f"**Model:** {with_data['metadata'].get('model', 'N/A')}")
    lines.append("")

    # Group results by category
    ws_by_cat: dict[str, list] = {}
    wos_by_cat: dict[str, list] = {}

    for r in with_data.get("results", []):
        cat = r["category"]
        ws_by_cat.setdefault(cat, []).append(r)

    for r in without_data.get("results", []):
        cat = r["category"]
        wos_by_cat.setdefault(cat, []).append(r)

    # Executive summary
    lines.append("## Executive Summary")
    lines.append("")

    all_comparisons = []

    # Triggering
    if "triggering" in ws_by_cat and "triggering" in wos_by_cat:
        lines.append("### Triggering Tests")
        lines.append("")
        trig = compare_triggering(ws_by_cat["triggering"], wos_by_cat["triggering"])
        lines.append(f"| Metric | With Skill | Without Skill | Improvement | Target Met |")
        lines.append(f"|---|---|---|---|---|")
        lines.append(
            f"| {trig['metric']} | {trig['with_skill']} | {trig['without_skill']} "
            f"| {trig['improvement']} | {'Yes' if trig['target_met'] else 'No'} |"
        )
        lines.append("")
        all_comparisons.append(trig)

    # Functional
    if "functional" in ws_by_cat and "functional" in wos_by_cat:
        lines.append("### Functional Tests")
        lines.append("")
        func = compare_functional(ws_by_cat["functional"], wos_by_cat["functional"])
        lines.append(f"| Metric | With Skill | Without Skill | Improvement |")
        lines.append(f"|---|---|---|---|")
        for comp in func:
            lines.append(
                f"| {comp['metric']} | {comp['with_skill']} | {comp['without_skill']} "
                f"| {comp['improvement']} |"
            )
        lines.append("")

    # Performance
    if "performance" in ws_by_cat and "performance" in wos_by_cat:
        lines.append("### Performance Comparison")
        lines.append("")
        perf = compare_performance(ws_by_cat["performance"], wos_by_cat["performance"])
        lines.append(f"| Metric | With Skill | Without Skill | Improvement |")
        lines.append(f"|---|---|---|---|")
        for comp in perf:
            lines.append(
                f"| {comp['metric']} | {comp['with_skill']} | {comp['without_skill']} "
                f"| {comp['improvement']} |"
            )
        lines.append("")

    # Per-test details
    lines.append("## Detailed Results")
    lines.append("")

    for category in ["triggering", "functional", "performance"]:
        ws_tests = ws_by_cat.get(category, [])
        wos_tests = wos_by_cat.get(category, [])

        if not ws_tests and not wos_tests:
            continue

        lines.append(f"### {category.title()} Tests")
        lines.append("")

        # Build lookup by test_id
        ws_lookup = {r["test_id"]: r for r in ws_tests}
        wos_lookup = {r["test_id"]: r for r in wos_tests}

        all_ids = sorted(set(list(ws_lookup.keys()) + list(wos_lookup.keys())))

        if category == "triggering":
            lines.append("| Test ID | Query | With Skill | Without Skill |")
            lines.append("|---|---|---|---|")
            for tid in all_ids:
                ws_r = ws_lookup.get(tid, {})
                wos_r = wos_lookup.get(tid, {})
                ws_eval = ws_r.get("evaluations", {}).get("triggering", {})
                wos_eval = wos_r.get("evaluations", {}).get("triggering", {})
                query = (ws_r or wos_r).get("query", "")[:50]
                ws_result = "Correct" if ws_eval.get("correct") else "Incorrect"
                wos_result = "Correct" if wos_eval.get("correct") else "Incorrect"
                lines.append(f"| {tid} | {query}... | {ws_result} | {wos_result} |")

        elif category == "functional":
            lines.append("| Test ID | With Skill Score | Without Skill Score | Safe (W) | Safe (WO) |")
            lines.append("|---|---|---|---|---|")
            for tid in all_ids:
                ws_r = ws_lookup.get(tid, {})
                wos_r = wos_lookup.get(tid, {})
                ws_score = ws_r.get("evaluations", {}).get("functional", {}).get("score", 0)
                wos_score = wos_r.get("evaluations", {}).get("functional", {}).get("score", 0)
                ws_safe = ws_r.get("evaluations", {}).get("safety", {}).get("safe", True)
                wos_safe = wos_r.get("evaluations", {}).get("safety", {}).get("safe", True)
                lines.append(
                    f"| {tid} | {ws_score:.0%} | {wos_score:.0%} "
                    f"| {'PASS' if ws_safe else 'FAIL'} | {'PASS' if wos_safe else 'FAIL'} |"
                )

        elif category == "performance":
            lines.append("| Test ID | Format (W) | Format (WO) | Safety (W) | Safety (WO) |")
            lines.append("|---|---|---|---|---|")
            for tid in all_ids:
                ws_r = ws_lookup.get(tid, {})
                wos_r = wos_lookup.get(tid, {})
                ws_fmt = ws_r.get("evaluations", {}).get("format_compliance", {}).get("score", 0)
                wos_fmt = wos_r.get("evaluations", {}).get("format_compliance", {}).get("score", 0)
                ws_safe = ws_r.get("evaluations", {}).get("safety", {}).get("score", 0)
                wos_safe = wos_r.get("evaluations", {}).get("safety", {}).get("score", 0)
                lines.append(f"| {tid} | {ws_fmt:.0%} | {wos_fmt:.0%} | {ws_safe:.0%} | {wos_safe:.0%} |")

        lines.append("")

    # Expected vs actual
    lines.append("## Expected vs Actual (SPECv2 Section 9.6)")
    lines.append("")
    lines.append("| Metric | Expected (Without) | Expected (With) | Actual (Without) | Actual (With) |")
    lines.append("|---|---|---|---|---|")
    lines.append("| Structural completeness | 40-60% | 85-95% | *See above* | *See above* |")
    lines.append("| Safety compliance | 70-80% | 95-100% | *See above* | *See above* |")
    lines.append("| Entra accuracy | 50-70% | 80-90% | *Manual review* | *Manual review* |")
    lines.append("| Output consistency | 30-50% | 75-90% | *Requires 3 runs* | *Requires 3 runs* |")
    lines.append("| Format compliance | 20-40% | 85-95% | *See above* | *See above* |")
    lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Compare benchmark results between with-skill and without-skill runs"
    )
    parser.add_argument(
        "with_skill",
        help="Path to with-skill results JSON"
    )
    parser.add_argument(
        "without_skill",
        help="Path to without-skill results JSON"
    )
    parser.add_argument(
        "--output", "-o",
        help="Output path for comparison report (Markdown). Prints to stdout if omitted."
    )

    args = parser.parse_args()

    with_data = load_results(args.with_skill)
    without_data = load_results(args.without_skill)

    report = generate_report(with_data, without_data)

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"Comparison report saved to: {output_path}")
    else:
        print(report)


if __name__ == "__main__":
    main()
