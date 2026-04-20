from __future__ import annotations

import hashlib
import logging
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer

from src.schemas import AISystem, Signal, SimilarityPair

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent
CACHE_DIR = PROJECT_ROOT / "data" / "cache" / "embeddings"

# Module-level model cache. Loaded once on first call and reused for the
# lifetime of the process — sentence-transformer models are expensive to load.
_model: SentenceTransformer | None = None


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        logger.info("Loading sentence-transformer model (first call only)...")
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def _cache_path(text: str) -> Path:
    # SHA-256 of the input text is the cache key. Deterministic across runs
    # and automatically invalidates when the text content changes.
    hash_key = hashlib.sha256(text.encode()).hexdigest()
    return CACHE_DIR / f"{hash_key}.npy"


def get_embedding(text: str) -> np.ndarray:
    """Return the embedding for text, reading from disk cache when available."""
    path = _cache_path(text)
    if path.exists():
        return np.load(path)

    embedding = _get_model().encode(text)

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    np.save(path, embedding)
    return embedding


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    # Direct numpy dot/norm — no scipy dependency for a single formula.
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def _system_text(system: AISystem) -> str:
    # Known risks are the most signal-dense field for our use case: they name
    # the failure modes we're trying to match external incidents against.
    return (
        system.purpose
        + " "
        + " ".join(system.data_inputs)
        + " "
        + " ".join(system.known_risks)
    )


def _signal_text(signal: Signal) -> str:
    return signal.title + " " + signal.description


def compute_similarities(
    systems: list[AISystem],
    signals: list[Signal],
) -> list[SimilarityPair]:
    """
    Compute cosine similarity for every (signal, system) pair.

    Embeddings are computed once per unique text and cached to disk. The pair
    loop is O(signals x systems) but no embedding calls happen inside it —
    all embedding work is done in the two dict-comprehension passes above.
    """
    logger.info("Embedding %d systems...", len(systems))
    system_embeddings: dict[str, np.ndarray] = {
        s.id: get_embedding(_system_text(s)) for s in systems
    }

    logger.info("Embedding %d signals...", len(signals))
    signal_embeddings: dict[str, np.ndarray] = {
        s.id: get_embedding(_signal_text(s)) for s in signals
    }

    logger.info("Computing %d similarity pairs...", len(systems) * len(signals))
    pairs: list[SimilarityPair] = []
    for system in systems:
        for signal in signals:
            sim = _cosine_similarity(
                system_embeddings[system.id],
                signal_embeddings[signal.id],
            )
            pairs.append(
                SimilarityPair(
                    signal_id=signal.id,
                    system_id=system.id,
                    cosine_similarity=sim,
                )
            )

    return pairs
