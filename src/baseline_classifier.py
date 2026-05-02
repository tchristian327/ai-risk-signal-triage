from __future__ import annotations

import time

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import LeaveOneOut

from src.retrieval import get_embedding


def build_features(signal_text: str, system_text: str) -> np.ndarray:
    """Embed both texts and return a single feature vector.

    Feature = [signal_emb | system_emb | signal_emb * system_emb]
    The element-wise product gives the classifier cheap interaction features
    without adding a second learned layer. Each sub-vector is 384-dim
    (all-MiniLM-L6-v2), so the full vector is 1152-dim.

    Embeddings are loaded from the disk cache populated by Day 2 retrieval —
    all pairs in the eval set will be cache hits.
    """
    sig_emb = get_embedding(signal_text)
    sys_emb = get_embedding(system_text)
    return np.concatenate([sig_emb, sys_emb, sig_emb * sys_emb])


def train_classifier(X: np.ndarray, y: np.ndarray) -> LogisticRegression:
    """Fit a multinomial logistic regression for 0-4 relevance prediction.

    class_weight='balanced' compensates for the label imbalance in the eval set
    (most pairs are low-relevance). Without it, the model would learn to always
    predict 0 or 1 and appear accurate while missing every urgent signal.
    """
    clf = LogisticRegression(
        solver="lbfgs",
        max_iter=1000,
        class_weight="balanced",
        random_state=42,
    )
    clf.fit(X, y)
    return clf


def cross_validated_predictions(
    X: np.ndarray,
    y: np.ndarray,
) -> tuple[np.ndarray, dict]:
    """Leave-one-out cross-validated predictions for every example.

    LOO is used instead of k-fold because the eval set has only 49 examples —
    an 80/20 split would leave ~10 in the test set, which is too few for stable
    metrics. LOO gives us a prediction for every example while still respecting
    the train/test boundary (the held-out example is never in training).

    Returns:
        oof_preds: int array of shape (n,) with out-of-fold predicted labels
        meta: timing and fold-count metadata
    """
    loo = LeaveOneOut()
    n = len(y)
    oof_preds = np.zeros(n, dtype=int)

    start = time.perf_counter()
    for train_idx, test_idx in loo.split(X):
        X_train, X_test = X[train_idx], X[test_idx]
        y_train = y[train_idx]

        # With LOO on 49 examples, some score classes may be absent from the
        # training fold. That's a known limitation documented in REPORT_WEEK2.md.
        clf = train_classifier(X_train, y_train)
        oof_preds[test_idx] = clf.predict(X_test)

    elapsed = time.perf_counter() - start
    avg_latency_ms = round((elapsed / n) * 1000, 2)

    meta = {
        "n_folds": n,
        "cv_strategy": "leave-one-out",
        "elapsed_seconds": round(elapsed, 3),
        "avg_latency_ms": avg_latency_ms,
    }
    return oof_preds, meta
