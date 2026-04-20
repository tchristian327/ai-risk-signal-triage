from __future__ import annotations

import json
import logging
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from src.ingest import load_all_signals
from src.portfolio import load_portfolio
from src.retrieval import compute_similarities
from src.schemas import Digest, RunMetadata, ScoredPair, SimilarityPair, Signal, AISystem
from src.scoring import BEDROCK_MODEL_ID, get_llm_client, score_pair

logger = logging.getLogger(__name__)


def select_candidates(
    similarities: list[SimilarityPair],
    threshold: float,
    top_k_per_system: int,
) -> list[SimilarityPair]:
    """Return candidate pairs for LLM scoring.

    A pair is included if its cosine similarity >= threshold OR it is in the
    top-k for its system. The OR prevents zero-coverage systems when nothing
    clears the threshold — we still want to score each system's best matches.
    """
    by_system: dict[str, list[SimilarityPair]] = defaultdict(list)
    for pair in similarities:
        by_system[pair.system_id].append(pair)

    selected: dict[tuple[str, str], SimilarityPair] = {}
    for system_id, pairs in by_system.items():
        sorted_pairs = sorted(pairs, key=lambda p: p.cosine_similarity, reverse=True)
        for pair in sorted_pairs[:top_k_per_system]:
            selected[(pair.signal_id, pair.system_id)] = pair
        for pair in sorted_pairs:
            if pair.cosine_similarity >= threshold:
                selected[(pair.signal_id, pair.system_id)] = pair

    return list(selected.values())


def run_pipeline(
    portfolio_path: Path,
    output_path: Path,
    signals_path: Path | None = None,
    retrieval_threshold: float = 0.3,
    top_k_per_system: int = 8,
    confirm_fn=None,
) -> Digest:
    """Orchestrate the full triage pipeline and write a Digest to disk.

    Args:
        portfolio_path: Path to systems.yaml.
        output_path: Where to write digest.json.
        signals_path: Optional path to a specific signals JSON. If None (default),
            load_all_signals() is called to combine all signal sources. Pass a
            path only for smoke tests or custom signal subsets.
        retrieval_threshold: Cosine similarity floor for candidate filtering.
        top_k_per_system: Number of top candidates per system always included.
        confirm_fn: Optional callable(n_pairs, model_name) -> bool. If provided,
            called before scoring starts. Return False to abort.

    Returns:
        The validated Digest object.
    """
    run_start = time.time()

    # --- Load portfolio ---
    systems: list[AISystem] = load_portfolio(portfolio_path)
    logger.info("Loaded %d systems from portfolio", len(systems))

    # --- Load signals ---
    if signals_path is not None:
        from src.ingest import load_signals_from_json
        signals: list[Signal] = load_signals_from_json(signals_path)
    else:
        signals = load_all_signals()
    logger.info("Loaded %d signals", len(signals))

    # --- Retrieval ---
    logger.info(
        "Computing similarity matrix... (%d x %d = %d pairs)",
        len(systems), len(signals), len(systems) * len(signals),
    )
    similarities = compute_similarities(systems, signals)

    # --- Candidate filtering ---
    candidates = select_candidates(similarities, retrieval_threshold, top_k_per_system)
    logger.info(
        "After filtering: %d pairs above threshold=%.2f or in top-%d, scoring...",
        len(candidates), retrieval_threshold, top_k_per_system,
    )

    # --- Cost confirmation ---
    if confirm_fn is not None:
        proceed = confirm_fn(len(candidates), BEDROCK_MODEL_ID)
        if not proceed:
            raise RuntimeError("Scoring aborted by operator.")

    # --- Scoring ---
    client = get_llm_client()
    signal_lookup: dict[str, Signal] = {s.id: s for s in signals}
    system_lookup: dict[str, AISystem] = {s.id: s for s in systems}

    scored_pairs: list[ScoredPair] = []
    num_failed = 0

    for i, candidate in enumerate(candidates, start=1):
        signal = signal_lookup[candidate.signal_id]
        system = system_lookup[candidate.system_id]

        if i % 10 == 1 or i == 1:
            logger.info(
                "Scoring pair %d of %d: signal_id=%s system_id=%s",
                i, len(candidates), candidate.signal_id, candidate.system_id,
            )

        try:
            result = score_pair(system, signal, client)
            scored_pairs.append(ScoredPair(
                signal_id=candidate.signal_id,
                system_id=candidate.system_id,
                cosine_similarity=candidate.cosine_similarity,
                relevance_score=result.score,
                justification=result.justification,
                suggested_action=result.suggested_action,
                reasoning=result.reasoning,
            ))
        except Exception as e:
            logger.error(
                "FAILED pair %s x %s: %s",
                candidate.signal_id, candidate.system_id, e,
            )
            num_failed += 1

    elapsed = time.time() - run_start
    logger.info(
        "Scoring complete: %d pairs scored, %d failed, elapsed %.1fs",
        len(scored_pairs), num_failed, elapsed,
    )

    # --- Build Digest ---
    metadata = RunMetadata(
        run_timestamp=datetime.now(tz=timezone.utc),
        model_name=BEDROCK_MODEL_ID,
        retrieval_threshold=retrieval_threshold,
        num_signals=len(signals),
        num_systems=len(systems),
        num_pairs_after_retrieval=len(candidates),
        num_pairs_scored=len(scored_pairs),
        num_pairs_failed=num_failed,
        elapsed_seconds=round(elapsed, 2),
    )

    digest = Digest(
        metadata=metadata,
        systems=systems,
        signals=signals,
        scored_pairs=scored_pairs,
    )

    # --- Write to disk ---
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        # model_dump with mode="json" serializes datetime to ISO string
        json.dump(digest.model_dump(mode="json"), f, indent=2)
    logger.info("Wrote digest to %s", output_path)

    # --- Validation round-trip ---
    # Re-read from disk to verify the file is well-formed before returning.
    # Catches any serialization drift before Day 5 depends on this file.
    with open(output_path) as f:
        raw = json.load(f)
    Digest.model_validate(raw)
    logger.info("Digest validation passed.")

    return digest
