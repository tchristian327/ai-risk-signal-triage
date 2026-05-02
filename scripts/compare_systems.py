#!/usr/bin/env python3
"""CLI: side-by-side comparison of LLM judge v1, LLM judge v2, and logistic regression baseline.

Loads all three metrics files and prints a table to console, then writes COMPARISON.md.

Usage:
    python scripts/compare_systems.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

EVAL_DIR = PROJECT_ROOT / "data" / "eval"
LLM_V1_PATH = EVAL_DIR / "metrics_llm_judge_v1.json"
LLM_V2_PATH = EVAL_DIR / "metrics_llm_judge_v2.json"
BASELINE_METRICS_PATH = EVAL_DIR / "metrics_baseline.json"
COMPARISON_OUT = EVAL_DIR / "COMPARISON.md"


def _fmt_pct(v: float) -> str:
    return f"{v:.1%}"


def _fmt_recall(rec_dict: dict) -> str:
    r = rec_dict["recall"]
    desc = rec_dict["description"]
    return f"{r:.1%}  ({desc})"


def _fmt_confusion(matrix: list[list[int]]) -> str:
    """Compact one-liner: true-positive counts on the diagonal."""
    diag = [matrix[i][i] for i in range(len(matrix))]
    total = sum(sum(row) for row in matrix)
    correct = sum(diag)
    return f"{correct}/{total} on diagonal — per-class: {diag}"


def _cost_per_1k(cost_usd: float, n_pairs: int) -> str:
    if n_pairs == 0:
        return "N/A"
    per_1k = (cost_usd / n_pairs) * 1000
    if per_1k == 0.0:
        return "$0.00"
    return f"${per_1k:.2f}"


def build_comparison(v1: dict, v2: dict, baseline: dict) -> list[tuple[str, str, str, str]]:
    """Return rows as (metric, v1_value, v2_value, baseline_value) strings."""
    v1_meta = v1["run_metadata"]
    v2_meta = v2["run_metadata"]
    bl_meta = baseline["run_metadata"]

    n_v1 = v1.get("n_pairs", v1_meta.get("eval_set_size", 49))
    n_v2 = v2.get("n_pairs", v2_meta.get("eval_set_size", 49))
    n_bl = baseline.get("n_pairs", bl_meta.get("n_folds", 49))

    rows = [
        (
            "Exact match accuracy",
            _fmt_pct(v1["exact_match_accuracy"]),
            _fmt_pct(v2["exact_match_accuracy"]),
            _fmt_pct(baseline["exact_match_accuracy"]),
        ),
        (
            "Off-by-one accuracy",
            _fmt_pct(v1["off_by_one_accuracy"]),
            _fmt_pct(v2["off_by_one_accuracy"]),
            _fmt_pct(baseline["off_by_one_accuracy"]),
        ),
        (
            "Recall @ score ≥ 3 (headline)",
            _fmt_recall(v1["recall_at_threshold_3"]),
            _fmt_recall(v2["recall_at_threshold_3"]),
            _fmt_recall(baseline["recall_at_threshold_3"]),
        ),
        (
            "Confusion matrix",
            _fmt_confusion(v1["confusion_matrix"]),
            _fmt_confusion(v2["confusion_matrix"]),
            _fmt_confusion(baseline["confusion_matrix"]),
        ),
        (
            "Eval set size",
            f"{n_v1} pairs",
            f"{n_v2} pairs",
            f"{n_bl} pairs (LOO CV)",
        ),
        (
            "Avg latency / pair",
            f"{v1_meta['avg_latency_ms']} ms",
            f"{v2_meta['avg_latency_ms']} ms",
            f"{bl_meta['avg_latency_ms']} ms",
        ),
        (
            "Cost / 1k pairs",
            _cost_per_1k(v1_meta["estimated_cost_usd"], n_v1),
            _cost_per_1k(v2_meta["estimated_cost_usd"], n_v2),
            _cost_per_1k(bl_meta["estimated_cost_usd"], n_bl),
        ),
        (
            "Model",
            v1_meta.get("model_id", "claude-haiku"),
            v2_meta.get("model_id", "claude-haiku"),
            bl_meta.get("model", "logistic_regression"),
        ),
    ]
    return rows


def _print_table(rows: list[tuple[str, str, str, str]]) -> None:
    col1 = max(len(r[0]) for r in rows)
    col2 = max(len(r[1]) for r in rows)
    col3 = max(len(r[2]) for r in rows)
    col4 = max(len(r[3]) for r in rows)

    header = (
        f"{'Metric':<{col1}}  {'LLM Judge v1':<{col2}}  "
        f"{'LLM Judge v2':<{col3}}  {'Logistic Regression':<{col4}}"
    )
    sep = "-" * len(header)
    print(sep)
    print(header)
    print(sep)
    for metric, v1_val, v2_val, bl_val in rows:
        print(f"{metric:<{col1}}  {v1_val:<{col2}}  {v2_val:<{col3}}  {bl_val:<{col4}}")
    print(sep)


def _markdown_table(rows: list[tuple[str, str, str, str]]) -> str:
    lines = []
    lines.append("| Metric | LLM Judge v1 | LLM Judge v2 | Logistic Regression |")
    lines.append("|--------|-------------|-------------|---------------------|")
    for metric, v1_val, v2_val, bl_val in rows:
        lines.append(f"| {metric} | {v1_val} | {v2_val} | {bl_val} |")
    return "\n".join(lines)


def main() -> None:
    missing = []
    for path in (LLM_V1_PATH, LLM_V2_PATH, BASELINE_METRICS_PATH):
        if not path.exists():
            missing.append(str(path))
    if missing:
        for p in missing:
            print(f"ERROR: metrics file not found: {p}")
        sys.exit(1)

    v1 = json.loads(LLM_V1_PATH.read_text())
    v2 = json.loads(LLM_V2_PATH.read_text())
    baseline = json.loads(BASELINE_METRICS_PATH.read_text())

    rows = build_comparison(v1, v2, baseline)

    print("\n  LLM JUDGE v1  vs.  LLM JUDGE v2  vs.  LOGISTIC REGRESSION\n")
    _print_table(rows)

    md = _markdown_table(rows)
    COMPARISON_OUT.write_text(md + "\n")
    print(f"\nComparison written to {COMPARISON_OUT}")


if __name__ == "__main__":
    main()
