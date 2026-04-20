#!/usr/bin/env python3
"""CLI: score candidate (signal, system) pairs using the LLM judge.

Reads similarities.json, filters to candidates, calls the LLM scorer,
and writes scored_pairs.json. Includes a cost estimate prompt before
running so the operator can sanity-check before committing API credits.

NOTE: scored_pairs.json is a dev/debug artifact. digest.json (written by
run_pipeline.py) is the canonical output consumed by the dashboard and eval.

Usage:
    python scripts/run_scoring.py                # full run
    python scripts/run_scoring.py --limit 5      # smoke test on 5 pairs
    python scripts/run_scoring.py --yes          # skip cost confirmation
    python scripts/run_scoring.py --threshold 0.4 --top-n 5
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
load_dotenv(PROJECT_ROOT / ".env")

# Must come after load_dotenv so LLM_PROVIDER is set before importing scoring
from src.portfolio import load_portfolio
from src.schemas import ScoredPair
from src.scoring import get_llm_client, score_pair

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# Haiku pricing (USD per 1M tokens, approximate)
HAIKU_INPUT_COST_PER_1M = 0.80
HAIKU_OUTPUT_COST_PER_1M = 4.00
# Rough estimate: scoring prompt is ~600 tokens in, ~300 tokens out
EST_TOKENS_IN_PER_CALL = 600
EST_TOKENS_OUT_PER_CALL = 300


def estimate_cost(n_pairs: int) -> float:
    cost_in = (EST_TOKENS_IN_PER_CALL * n_pairs / 1_000_000) * HAIKU_INPUT_COST_PER_1M
    cost_out = (EST_TOKENS_OUT_PER_CALL * n_pairs / 1_000_000) * HAIKU_OUTPUT_COST_PER_1M
    return cost_in + cost_out


def load_similarities(path: Path) -> list[dict]:
    with open(path) as f:
        return json.load(f)


def load_signals(path: Path) -> dict[str, dict]:
    with open(path) as f:
        raw = json.load(f)
    return {s["id"]: s for s in raw}


def filter_candidates(
    similarities: list[dict],
    threshold: float,
    top_n: int,
) -> list[dict]:
    """Keep pairs where cosine >= threshold OR (per system) top-N by similarity.

    The OR prevents zero-coverage systems when nothing clears the threshold.
    """
    # Group by system
    by_system: dict[str, list[dict]] = defaultdict(list)
    for pair in similarities:
        by_system[pair["system_id"]].append(pair)

    selected: dict[tuple[str, str], dict] = {}

    for system_id, pairs in by_system.items():
        sorted_pairs = sorted(pairs, key=lambda p: p["cosine_similarity"], reverse=True)

        # Top-N always included
        for pair in sorted_pairs[:top_n]:
            key = (pair["signal_id"], pair["system_id"])
            selected[key] = pair

        # Threshold pass for anything above it
        for pair in sorted_pairs:
            if pair["cosine_similarity"] >= threshold:
                key = (pair["signal_id"], pair["system_id"])
                selected[key] = pair

    return list(selected.values())


def main() -> None:
    parser = argparse.ArgumentParser(description="Score candidate signal-system pairs.")
    parser.add_argument("--threshold", type=float, default=0.3,
                        help="Cosine similarity threshold (default: 0.3)")
    parser.add_argument("--top-n", type=int, default=8,
                        help="Top-N per system always scored regardless of threshold (default: 8)")
    parser.add_argument("--limit", type=int, default=None,
                        help="Cap total pairs scored (for smoke tests)")
    parser.add_argument("--yes", action="store_true",
                        help="Skip cost confirmation prompt")
    args = parser.parse_args()

    similarities_path = PROJECT_ROOT / "data" / "outputs" / "similarities.json"
    signals_path = PROJECT_ROOT / "data" / "signals" / "processed" / "aiid_signals.json"
    portfolio_path = PROJECT_ROOT / "data" / "portfolio" / "systems.yaml"
    output_path = PROJECT_ROOT / "data" / "outputs" / "scored_pairs.json"

    # --- Load inputs ---
    logger.info("Loading portfolio from %s", portfolio_path)
    systems = {s.id: s for s in load_portfolio(portfolio_path)}
    logger.info("Loaded %d systems", len(systems))

    logger.info("Loading signals from %s", signals_path)
    signals_raw = load_signals(signals_path)
    logger.info("Loaded %d signals", len(signals_raw))

    logger.info("Loading similarities from %s", similarities_path)
    similarities = load_similarities(similarities_path)
    logger.info("Loaded %d total similarity pairs", len(similarities))

    # --- Filter to candidates ---
    candidates = filter_candidates(similarities, args.threshold, args.top_n)
    logger.info(
        "Filtered to %d candidates (threshold=%.2f, top_n=%d)",
        len(candidates), args.threshold, args.top_n,
    )

    if args.limit:
        candidates = candidates[: args.limit]
        logger.info("--limit applied: scoring %d pairs", len(candidates))

    n_pairs = len(candidates)

    # --- Cost estimate and confirmation ---
    est_cost = estimate_cost(n_pairs)
    print(f"\nAbout to score {n_pairs} pairs (~${est_cost:.4f} estimated at Haiku prices).")

    if not args.yes:
        answer = input("Continue? [y/N] ").strip().lower()
        if answer != "y":
            print("Aborted.")
            sys.exit(0)

    # --- Build client once ---
    logger.info("Initializing LLM client")
    client = get_llm_client()

    # --- Scoring loop ---
    scored: list[ScoredPair] = []
    failed: list[dict] = []
    start_time = time.time()

    for i, pair in enumerate(candidates, start=1):
        signal_id = pair["signal_id"]
        system_id = pair["system_id"]
        cosine = pair["cosine_similarity"]

        if signal_id not in signals_raw:
            logger.warning("Signal %s not found in signals file, skipping", signal_id)
            continue
        if system_id not in systems:
            logger.warning("System %s not found in portfolio, skipping", system_id)
            continue

        from src.schemas import Signal
        signal = Signal.model_validate(signals_raw[signal_id])
        system = systems[system_id]

        t0 = time.time()
        try:
            result = score_pair(system, signal, client)
            elapsed = time.time() - t0
            logger.info(
                "[%d/%d] %s × %s → score=%d (%.1fs)",
                i, n_pairs, signal_id, system_id, result.score, elapsed,
            )
            scored.append(ScoredPair(
                signal_id=signal_id,
                system_id=system_id,
                cosine_similarity=cosine,
                relevance_score=result.score,
                justification=result.justification,
                suggested_action=result.suggested_action,
                reasoning=result.reasoning,
            ))
        except Exception as e:
            elapsed = time.time() - t0
            logger.error(
                "[%d/%d] FAILED %s × %s after %.1fs: %s",
                i, n_pairs, signal_id, system_id, elapsed, e,
            )
            failed.append({"signal_id": signal_id, "system_id": system_id, "error": str(e)})

        # Progress log every 10 pairs
        if i % 10 == 0:
            done = len(scored) + len(failed)
            remaining = n_pairs - done
            elapsed_total = time.time() - start_time
            logger.info(
                "Progress: %d done, %d remaining, %.0fs elapsed",
                done, remaining, elapsed_total,
            )

    # --- Write output ---
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump([p.model_dump() for p in scored], f, indent=2)
    logger.info("Wrote %d scored pairs to %s", len(scored), output_path)

    # --- Summary ---
    total_elapsed = time.time() - start_time
    score_dist = Counter(p.relevance_score for p in scored)
    print(f"\n=== Scoring complete in {total_elapsed:.0f}s ===")
    print(f"Scored: {len(scored)} | Failed: {len(failed)}")
    print("Score distribution:")
    for s in range(5):
        print(f"  {s}: {score_dist.get(s, 0)} pairs")
    if failed:
        print(f"\nFailed pairs ({len(failed)}):")
        for f_pair in failed:
            print(f"  {f_pair['signal_id']} × {f_pair['system_id']}: {f_pair['error']}")


if __name__ == "__main__":
    main()
