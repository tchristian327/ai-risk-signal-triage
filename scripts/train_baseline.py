#!/usr/bin/env python3
"""CLI: train the logistic regression baseline and evaluate it on the labeled eval set.

Uses leave-one-out cross-validation to produce predictions for all 49 labeled pairs,
then computes the same metrics as run_eval.py for a direct comparison.

Usage:
    python scripts/train_baseline.py
"""
from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.baseline_classifier import build_features, cross_validated_predictions
from src.evaluation import compute_all_metrics
from src.ingest import load_all_signals
from src.portfolio import load_portfolio
from src.schemas import AISystem, LabeledPair, Signal

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent
EVAL_DIR = PROJECT_ROOT / "data" / "eval"
LABELED_PATH = EVAL_DIR / "labeled_pairs.json"
PORTFOLIO_PATH = PROJECT_ROOT / "data" / "portfolio" / "systems.yaml"
METRICS_OUT = EVAL_DIR / "metrics_baseline.json"
PREDICTIONS_OUT = EVAL_DIR / "predictions_baseline.json"


def _signal_text(signal: Signal) -> str:
    # Must match retrieval.py's _signal_text to get cache hits on embeddings.
    return signal.title + " " + signal.description


def _system_text(system: AISystem) -> str:
    # Must match retrieval.py's _system_text.
    return (
        system.purpose
        + " "
        + " ".join(system.data_inputs)
        + " "
        + " ".join(system.known_risks)
    )


def _print_confusion_matrix(matrix: list[list[int]]) -> None:
    header = "                    Human Label"
    col_labels = "                  0    1    2    3    4"
    print(header)
    print(col_labels)
    row_labels = ["          0", "Predicted 1", "Score     2", "          3", "          4"]
    for i, (label, row) in enumerate(zip(row_labels, matrix)):
        cells = []
        for j, val in enumerate(row):
            if i == j:
                cells.append(f"[{val:2d}]")
            else:
                cells.append(f" {val:2d} ")
        print(f"  {label}  {'  '.join(cells)}")


def main() -> None:
    # --- Load eval set ---
    if not LABELED_PATH.exists():
        logger.error("Labeled pairs not found at %s. Run Day 6 labeling first.", LABELED_PATH)
        sys.exit(1)

    labeled_raw = json.loads(LABELED_PATH.read_text())
    labeled_pairs = [LabeledPair.model_validate(r) for r in labeled_raw]
    n = len(labeled_pairs)
    logger.info("Loaded %d labeled pairs.", n)

    # --- Load portfolio and signals ---
    systems = load_portfolio(PORTFOLIO_PATH)
    signals = load_all_signals()
    system_map = {s.id: s for s in systems}
    signal_map = {s.id: s for s in signals}

    missing = [
        lp for lp in labeled_pairs
        if lp.signal_id not in signal_map or lp.system_id not in system_map
    ]
    if missing:
        logger.error("%d labeled pairs reference unknown IDs.", len(missing))
        sys.exit(1)

    # --- Build feature matrix ---
    logger.info("Building feature matrix (%d pairs)...", n)
    feature_rows: list[np.ndarray] = []
    labels: list[int] = []

    for lp in labeled_pairs:
        sig_text = _signal_text(signal_map[lp.signal_id])
        sys_text = _system_text(system_map[lp.system_id])
        feature_rows.append(build_features(sig_text, sys_text))
        labels.append(lp.human_label)

    X = np.stack(feature_rows)
    y = np.array(labels, dtype=int)
    logger.info("Feature matrix shape: %s, label distribution: %s", X.shape, dict(zip(*np.unique(y, return_counts=True))))

    # --- Cross-validated predictions ---
    logger.info("Running leave-one-out cross-validation...")
    oof_preds, cv_meta = cross_validated_predictions(X, y)

    # --- Compute metrics ---
    predictions_list = oof_preds.tolist()
    labels_list = y.tolist()
    metrics = compute_all_metrics(predictions_list, labels_list)

    run_meta = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "model": "logistic_regression",
        "features": "signal_emb + system_emb + element_wise_product (1152-dim)",
        "embedder": "all-MiniLM-L6-v2",
        "cv_strategy": cv_meta["cv_strategy"],
        "n_folds": cv_meta["n_folds"],
        "elapsed_seconds": cv_meta["elapsed_seconds"],
        "avg_latency_ms": cv_meta["avg_latency_ms"],
        # Classifier training + inference is CPU-only; no API cost.
        "estimated_cost_usd": 0.0,
    }
    metrics["run_metadata"] = run_meta

    # --- Build per-pair prediction records ---
    prediction_records = []
    for lp, pred in zip(labeled_pairs, predictions_list):
        prediction_records.append({
            "signal_id": lp.signal_id,
            "system_id": lp.system_id,
            "human_label": lp.human_label,
            "baseline_score": pred,
            "abs_error": abs(pred - lp.human_label),
        })

    # --- Write outputs ---
    METRICS_OUT.write_text(json.dumps(metrics, indent=2))
    PREDICTIONS_OUT.write_text(json.dumps(prediction_records, indent=2))
    logger.info("Metrics written to %s", METRICS_OUT)
    logger.info("Predictions written to %s", PREDICTIONS_OUT)

    # --- Console summary ---
    print("\n" + "=" * 60)
    print("  BASELINE EVALUATION — Logistic Regression")
    print("=" * 60)
    print(f"  Eval set size:    {n} pairs (leave-one-out CV)")
    print(f"  Feature dims:     {X.shape[1]}")
    print(f"  Elapsed:          {cv_meta['elapsed_seconds']:.3f}s")
    print(f"  Avg latency/pair: {cv_meta['avg_latency_ms']:.2f}ms")
    print(f"  Est. cost:        $0.00")
    print()
    print(f"  Exact match accuracy:    {metrics['exact_match_accuracy']:.1%}")
    print(f"  Off-by-one accuracy:     {metrics['off_by_one_accuracy']:.1%}")
    rec = metrics["recall_at_threshold_3"]
    print(f"  Recall at score >= 3:    {rec['recall']:.1%}  ({rec['description']})")
    print()
    print("  Confusion matrix (rows=predicted, cols=human label):")
    _print_confusion_matrix(metrics["confusion_matrix"])
    print("=" * 60)


if __name__ == "__main__":
    main()
