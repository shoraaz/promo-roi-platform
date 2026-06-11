"""Feature-loading utilities for training and evaluation."""

from __future__ import annotations


def select_feature_columns(columns: list[str]) -> list[str]:
    """Return the model input feature columns from a raw feature list."""
    excluded = {"sales_lift_pct", "margin_impact", "sales", "customers"}
    return [column for column in columns if column not in excluded]
