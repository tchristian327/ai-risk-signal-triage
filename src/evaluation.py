from __future__ import annotations


def exact_match_accuracy(predictions: list[int], labels: list[int]) -> float:
    """Fraction of pairs where LLM score exactly equals the human label."""
    if not predictions:
        return 0.0
    return sum(p == l for p, l in zip(predictions, labels)) / len(predictions)


def off_by_one_accuracy(predictions: list[int], labels: list[int]) -> float:
    """Fraction where abs(prediction - label) <= 1. More forgiving than exact match
    and more informative for a graded 0-4 scale where boundary disagreement is common."""
    if not predictions:
        return 0.0
    return sum(abs(p - l) <= 1 for p, l in zip(predictions, labels)) / len(predictions)


def recall_at_threshold(
    predictions: list[int], labels: list[int], threshold: int = 3
) -> tuple[float, int, int]:
    """Of all pairs the human labeled >= threshold, what fraction did the model also score >= threshold.

    This is the headline metric for this project because the costs are asymmetric: missing a
    real risk (false negative) is far more damaging than over-flagging something irrelevant.
    See DECISIONS.md for the full reasoning. We use threshold=3 ("action recommended") as the
    boundary because that's where governance action becomes obligatory, not optional.

    Returns (recall, true_positives, total_positives) so callers can report "17 of 20 caught"
    rather than just a percentage, which obscures a tiny denominator.
    """
    positives = [(p, l) for p, l in zip(predictions, labels) if l >= threshold]
    total = len(positives)
    if total == 0:
        return 0.0, 0, 0
    true_pos = sum(p >= threshold for p, l in positives)
    return true_pos / total, true_pos, total


def confusion_matrix(
    predictions: list[int], labels: list[int], num_classes: int = 5
) -> list[list[int]]:
    """5x5 confusion matrix as a nested list.

    matrix[i][j] = count of items where prediction=i and label=j.
    Rows are predicted scores (0 at top), columns are human labels (0 on left).
    """
    matrix = [[0] * num_classes for _ in range(num_classes)]
    for p, l in zip(predictions, labels):
        matrix[p][l] += 1
    return matrix


def compute_all_metrics(predictions: list[int], labels: list[int]) -> dict:
    """Run all four metric functions and return a single dict ready for JSON serialization."""
    recall, tp, total_pos = recall_at_threshold(predictions, labels, threshold=3)
    return {
        "exact_match_accuracy": exact_match_accuracy(predictions, labels),
        "off_by_one_accuracy": off_by_one_accuracy(predictions, labels),
        "recall_at_threshold_3": {
            "recall": recall,
            "true_positives": tp,
            "total_positives": total_pos,
            "description": f"{tp} of {total_pos} high-relevance pairs caught",
        },
        "confusion_matrix": confusion_matrix(predictions, labels),
        "n_pairs": len(predictions),
    }
