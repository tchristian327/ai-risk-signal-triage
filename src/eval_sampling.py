from __future__ import annotations

import math
import random

from src.schemas import SimilarityPair


def select_eval_pairs(
    similarities: list[SimilarityPair],
    n_pairs: int = 50,
) -> list[tuple[str, str]]:
    """Return n_pairs (signal_id, system_id) tuples using stratified equal-rank terciles.

    Stratification is by index position over the sorted list, not by value range.
    The cosine similarity distribution across all pairs is tight (roughly 0.25-0.53),
    so equal-width value buckets risk producing skewed or empty strata. Equal-rank
    terciles guarantee roughly n_pairs/3 candidates per stratum regardless of
    distribution shape, and keep the high/medium/low labels meaningful relative to
    what the retriever actually produces.

    The random seed is fixed at 42. Changing it produces a different set of n_pairs
    that is not directly comparable to results labeled on this run.

    Assumes `similarities` is sorted descending by cosine_similarity (as written by
    run_retrieval.py). If unsorted, sampling is still stratified by index position
    but the high/medium/low labels will not map to actual similarity ranks.
    """
    n = len(similarities)
    bucket_size = n // 3

    high = similarities[:bucket_size]
    medium = similarities[bucket_size : 2 * bucket_size]
    # Low bucket absorbs the remainder when n is not divisible by 3
    low = similarities[2 * bucket_size :]

    per_bucket = math.ceil(n_pairs / 3)
    # e.g. n_pairs=50 → 17, 17, 16
    counts = [per_bucket, per_bucket, n_pairs - 2 * per_bucket]

    random.seed(42)

    selected: list[tuple[str, str]] = []
    for bucket, count in zip([high, medium, low], counts):
        sampled = random.sample(bucket, min(count, len(bucket)))
        selected.extend((p.signal_id, p.system_id) for p in sampled)

    return selected
