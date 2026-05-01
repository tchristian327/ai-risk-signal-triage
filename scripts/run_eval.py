#!/usr/bin/env python3
"""CLI: evaluate the LLM judge against the hand-labeled eval set.

Runs a fresh LLM call for every pair in data/eval/labeled_pairs.json,
then computes metrics and writes results to data/eval/.

Usage:
    python scripts/run_eval.py          # full eval (~49 pairs)
    python scripts/run_eval.py --limit 5    # smoke test
    python scripts/run_eval.py --yes        # skip cost confirmation
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
load_dotenv(PROJECT_ROOT / ".env")

from src.evaluation import compute_all_metrics
from src.ingest import load_all_signals
from src.portfolio import load_portfolio
from src.schemas import LabeledPair
from src.scoring import BEDROCK_MODEL_ID, ANTHROPIC_MODEL_NAME, get_llm_client, score_pair

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

EVAL_DIR = PROJECT_ROOT / "data" / "eval"
LABELED_PATH = EVAL_DIR / "labeled_pairs.json"
PORTFOLIO_PATH = PROJECT_ROOT / "data" / "portfolio" / "systems.yaml"
METRICS_OUT = EVAL_DIR / "metrics_llm_judge_v1.json"
PREDICTIONS_OUT = EVAL_DIR / "predictions_llm_judge_v1.json"

# Approximate Haiku cost per scoring call
_COST_PER_PAIR = 0.00168


def _print_confusion_matrix(matrix: list[list[int]]) -> None:
    """Print the 5x5 confusion matrix as a plain ASCII grid."""
    header = "                    Human Label"
    col_labels = "                  0    1    2    3    4"
    print(header)
    print(col_labels)
    row_labels = ["          0", "Predicted 1", "Score     2", "          3", "          4"]
    for i, (label, row) in enumerate(zip(row_labels, matrix)):
        cells = []
        for j, val in enumerate(row):
            # Surround diagonal cells with * to distinguish correct predictions
            if i == j:
                cells.append(f"[{val:2d}]")
            else:
                cells.append(f" {val:2d} ")
        print(f"  {label}  {'  '.join(cells)}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate LLM judge against labeled eval set.")
    parser.add_argument("--limit", type=int, default=None,
                        help="Cap number of pairs to evaluate (for smoke tests)")
    parser.add_argument("--yes", action="store_true",
                        help="Skip cost confirmation prompt")
    args = parser.parse_args()

    # --- Load eval set ---
    if not LABELED_PATH.exists():
        logger.error("Labeled pairs not found at %s. Run Day 6 labeling first.", LABELED_PATH)
        sys.exit(1)

    labeled_raw = json.loads(LABELED_PATH.read_text())
    labeled_pairs = [LabeledPair.model_validate(r) for r in labeled_raw]

    if args.limit:
        labeled_pairs = labeled_pairs[: args.limit]

    n = len(labeled_pairs)
    logger.info("Loaded %d labeled pairs for evaluation.", n)

    # --- Load portfolio and signals for full text ---
    systems = load_portfolio(PORTFOLIO_PATH)
    signals = load_all_signals()

    system_map = {s.id: s for s in systems}
    signal_map = {s.id: s for s in signals}

    # Check all labeled pairs are resolvable
    missing = [
        lp for lp in labeled_pairs
        if lp.signal_id not in signal_map or lp.system_id not in system_map
    ]
    if missing:
        logger.error("%d labeled pairs reference unknown signal/system IDs.", len(missing))
        for lp in missing[:5]:
            logger.error("  signal=%s system=%s", lp.signal_id, lp.system_id)
        sys.exit(1)

    # --- Cost check ---
    estimated_cost = n * _COST_PER_PAIR
    logger.info("Estimated cost: $%.4f for %d pairs.", estimated_cost, n)
    if not args.yes:
        confirm = input(f"Run eval on {n} pairs (est. ${estimated_cost:.4f})? [y/N] ")
        if confirm.strip().lower() != "y":
            logger.info("Aborted.")
            sys.exit(0)

    # --- Run eval ---
    client = get_llm_client()
    import os
    provider = os.getenv("LLM_PROVIDER", "bedrock").lower()
    model_id = BEDROCK_MODEL_ID if provider == "bedrock" else ANTHROPIC_MODEL_NAME

    predictions: list[int] = []
    labels: list[int] = []
    prediction_records: list[dict] = []
    errors: list[str] = []

    start = time.time()

    for i, lp in enumerate(labeled_pairs):
        if i > 0 and i % 10 == 0:
            elapsed = time.time() - start
            logger.info("Progress: %d/%d pairs scored (%.1fs elapsed)", i, n, elapsed)

        system = system_map[lp.system_id]
        signal = signal_map[lp.signal_id]

        try:
            pair_start = time.time()
            result = score_pair(system, signal, client)
            latency_ms = round((time.time() - pair_start) * 1000)
            predictions.append(result.score)
            labels.append(lp.human_label)
            prediction_records.append({
                "signal_id": lp.signal_id,
                "system_id": lp.system_id,
                "human_label": lp.human_label,
                "human_note": lp.human_note,
                "llm_score": result.score,
                "llm_reasoning": result.reasoning,
                "llm_justification": result.justification,
                "abs_error": abs(result.score - lp.human_label),
                "latency_ms": latency_ms,
            })
        except Exception as e:
            logger.error("Failed to score pair %s / %s: %s", lp.signal_id, lp.system_id, e)
            errors.append(f"{lp.signal_id}/{lp.system_id}: {e}")

    elapsed = time.time() - start
    actual_cost = len(predictions) * _COST_PER_PAIR

    logger.info("Eval complete: %d scored, %d failed in %.1fs. Est. cost: $%.4f",
                len(predictions), len(errors), elapsed, actual_cost)

    # --- Compute metrics ---
    metrics = compute_all_metrics(predictions, labels)

    latencies = [r["latency_ms"] for r in prediction_records]
    avg_latency_ms = round(sum(latencies) / len(latencies)) if latencies else 0

    run_meta = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "model_id": model_id,
        "provider": provider,
        "temperature": 0.0,
        "eval_set_size": n,
        "n_scored": len(predictions),
        "n_failed": len(errors),
        "elapsed_seconds": round(elapsed, 1),
        "avg_latency_ms": avg_latency_ms,
        "estimated_cost_usd": round(actual_cost, 4),
    }
    metrics["run_metadata"] = run_meta

    # --- Write outputs ---
    METRICS_OUT.write_text(json.dumps(metrics, indent=2))
    PREDICTIONS_OUT.write_text(json.dumps(prediction_records, indent=2))
    logger.info("Metrics written to %s", METRICS_OUT)
    logger.info("Predictions written to %s", PREDICTIONS_OUT)

    # --- Console summary ---
    print("\n" + "=" * 60)
    print("  LLM JUDGE EVALUATION — v1")
    print("=" * 60)
    print(f"  Model:            {model_id}")
    print(f"  Eval set size:    {n} pairs ({len(predictions)} scored, {len(errors)} failed)")
    print(f"  Elapsed:          {elapsed:.1f}s")
    print(f"  Estimated cost:   ${actual_cost:.4f}")
    print()
    print(f"  Exact match accuracy:    {metrics['exact_match_accuracy']:.1%}")
    print(f"  Off-by-one accuracy:     {metrics['off_by_one_accuracy']:.1%}")
    rec = metrics["recall_at_threshold_3"]
    print(f"  Recall at score >= 3:    {rec['recall']:.1%}  ({rec['description']})")
    print()
    print("  Confusion matrix (rows=predicted, cols=human label):")
    _print_confusion_matrix(metrics["confusion_matrix"])
    print("=" * 60)

    if errors:
        print(f"\n  WARNING: {len(errors)} pairs failed to score:")
        for err in errors:
            print(f"    {err}")


if __name__ == "__main__":
    main()
