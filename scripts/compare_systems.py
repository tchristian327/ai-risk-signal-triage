#!/usr/bin/env python3
"""CLI: side-by-side comparison of LLM judge v1 vs logistic regression baseline.

Loads both metrics files and prints a table to console and writes COMPARISON.md.

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
LLM_METRICS_PATH = EVAL_DIR / "metrics_llm_judge_v1.json"
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


def build_comparison(llm: dict, baseline: dict) -> list[tuple[str, str, str]]:
    """Return rows as (metric, llm_value, baseline_value) strings."""
    llm_meta = llm["run_metadata"]
    bl_meta = baseline["run_metadata"]

    n_llm = llm.get("n_pairs", llm_meta.get("eval_set_size", 49))
    n_bl = baseline.get("n_pairs", bl_meta.get("n_folds", 49))

    rows = [
        (
            "Exact match accuracy",
            _fmt_pct(llm["exact_match_accuracy"]),
            _fmt_pct(baseline["exact_match_accuracy"]),
        ),
        (
            "Off-by-one accuracy",
            _fmt_pct(llm["off_by_one_accuracy"]),
            _fmt_pct(baseline["off_by_one_accuracy"]),
        ),
        (
            "Recall @ score ≥ 3 (headline)",
            _fmt_recall(llm["recall_at_threshold_3"]),
            _fmt_recall(baseline["recall_at_threshold_3"]),
        ),
        (
            "Confusion matrix",
            _fmt_confusion(llm["confusion_matrix"]),
            _fmt_confusion(baseline["confusion_matrix"]),
        ),
        (
            "Eval set size",
            f"{n_llm} pairs",
            f"{n_bl} pairs (LOO CV)",
        ),
        (
            "Avg latency / pair",
            f"{llm_meta['avg_latency_ms']} ms",
            f"{bl_meta['avg_latency_ms']} ms",
        ),
        (
            "Cost / 1k pairs",
            _cost_per_1k(llm_meta["estimated_cost_usd"], n_llm),
            _cost_per_1k(bl_meta["estimated_cost_usd"], n_bl),
        ),
        (
            "Model",
            llm_meta.get("model_id", "claude-haiku"),
            bl_meta.get("model", "logistic_regression"),
        ),
    ]
    return rows


def _print_table(rows: list[tuple[str, str, str]]) -> None:
    col1 = max(len(r[0]) for r in rows)
    col2 = max(len(r[1]) for r in rows)
    col3 = max(len(r[2]) for r in rows)

    header = f"{'Metric':<{col1}}  {'LLM Judge v1':<{col2}}  {'Logistic Regression':<{col3}}"
    sep = "-" * len(header)
    print(sep)
    print(header)
    print(sep)
    for metric, llm_val, bl_val in rows:
        print(f"{metric:<{col1}}  {llm_val:<{col2}}  {bl_val:<{col3}}")
    print(sep)


def _markdown_table(rows: list[tuple[str, str, str]]) -> str:
    lines = []
    lines.append("| Metric | LLM Judge v1 | Logistic Regression |")
    lines.append("|--------|-------------|---------------------|")
    for metric, llm_val, bl_val in rows:
        lines.append(f"| {metric} | {llm_val} | {bl_val} |")
    return "\n".join(lines)


def main() -> None:
    if not LLM_METRICS_PATH.exists():
        print(f"ERROR: LLM judge metrics not found at {LLM_METRICS_PATH}. Run run_eval.py first.")
        sys.exit(1)
    if not BASELINE_METRICS_PATH.exists():
        print(f"ERROR: Baseline metrics not found at {BASELINE_METRICS_PATH}. Run train_baseline.py first.")
        sys.exit(1)

    llm = json.loads(LLM_METRICS_PATH.read_text())
    baseline = json.loads(BASELINE_METRICS_PATH.read_text())

    rows = build_comparison(llm, baseline)

    print("\n  LLM JUDGE v1  vs.  LOGISTIC REGRESSION BASELINE\n")
    _print_table(rows)

    md = _markdown_table(rows)
    COMPARISON_OUT.write_text(md + "\n")
    print(f"\nComparison written to {COMPARISON_OUT}")


if __name__ == "__main__":
    main()
