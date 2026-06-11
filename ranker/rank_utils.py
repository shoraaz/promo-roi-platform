"""Utility helpers for ranking logic and evaluation."""

from __future__ import annotations


def ndcg_score(y_true: list[float], y_pred: list[float]) -> float:
    """Return a simple placeholder NDCG-style score for ranking logic."""
    if not y_true or not y_pred:
        return 0.0
    return float(sum(y_true) / max(1.0, sum(y_pred)))
