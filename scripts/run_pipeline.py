#!/usr/bin/env python3
"""CLI: run the full AI risk triage pipeline end to end.

Loads the portfolio and signals, runs retrieval, scores candidates with the
LLM judge, and writes digest.json. All expensive work happens here; the
Streamlit dashboard only reads the output file.

Usage:
    python scripts/run_pipeline.py                  # full run
    python scripts/run_pipeline.py --limit-signals 10  # smoke test
    python scripts/run_pipeline.py --yes            # skip cost confirmation
    python scripts/run_pipeline.py --threshold 0.35 --top-k 6
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
load_dotenv(PROJECT_ROOT / ".env")

from src.ingest import load_all_signals
from src.pipeline import run_pipeline

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

PORTFOLIO_PATH = PROJECT_ROOT / "data" / "portfolio" / "systems.yaml"
OUTPUT_PATH = PROJECT_ROOT / "data" / "outputs" / "digest.json"

# Approximate Haiku cost per scoring call (USD)
_COST_PER_PAIR = 0.00168  # ~600 tokens in @ $0.80/M + ~300 tokens out @ $4.00/M


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the AI risk triage pipeline.")
    parser.add_argument("--threshold", type=float, default=0.3,
                        help="Cosine similarity threshold (default: 0.3)")
    parser.add_argument("--top-k", type=int, default=8,
                        help="Top-K candidates per system (default: 8)")
    parser.add_argument("--limit-signals", type=int, default=None,
                        help="Cap signals loaded (for smoke tests)")
    parser.add_argument("--yes", action="store_true",
                        help="Skip cost confirmation prompt")
    args = parser.parse_args()

    # Optionally truncate signals for quick smoke tests (truncates combined corpus)
    signals_path = None
    if args.limit_signals:
        logger.info("--limit-signals %d: loading only first %d signals from combined corpus",
                    args.limit_signals, args.limit_signals)
        subset = load_all_signals()[: args.limit_signals]

        import json, tempfile, atexit, os
        tmp = tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, dir=PROJECT_ROOT / "data" / "outputs"
        )
        json.dump([s.model_dump() for s in subset], tmp)
        tmp.close()
        signals_path = Path(tmp.name)
        atexit.register(os.unlink, signals_path)  # clean up on exit

    def confirm(n_pairs: int, model_name: str) -> bool:
        est_cost = n_pairs * _COST_PER_PAIR
        print(
            f"\nAbout to score {n_pairs} pairs using model {model_name}. "
            f"Estimated cost: ${est_cost:.4f}. Continue? [y/N] ",
            end="",
            flush=True,
        )
        if args.yes:
            print("yes (--yes flag)")
            return True
        answer = input().strip().lower()
        return answer == "y"

    digest = run_pipeline(
        portfolio_path=PORTFOLIO_PATH,
        signals_path=signals_path,
        output_path=OUTPUT_PATH,
        retrieval_threshold=args.threshold,
        top_k_per_system=args.top_k,
        confirm_fn=confirm,
    )

    # Summary
    m = digest.metadata
    print(f"\n=== Pipeline complete ===")
    print(f"Systems: {m.num_systems}  |  Signals: {m.num_signals}")
    print(f"Pairs after retrieval: {m.num_pairs_after_retrieval}")
    print(f"Scored: {m.num_pairs_scored}  |  Failed: {m.num_pairs_failed}")
    print(f"Elapsed: {m.elapsed_seconds:.1f}s")
    print(f"Output: {OUTPUT_PATH}")

    from collections import Counter
    dist = Counter(p.relevance_score for p in digest.scored_pairs)
    print("Score distribution:", dict(sorted(dist.items())))


if __name__ == "__main__":
    main()
