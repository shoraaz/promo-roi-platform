"""Feature-loading utilities for training and evaluation."""

from __future__ import annotations

import pandas as pd

# Numeric feature columns — used directly by XGBoost
FEATURE_COLS = [
    "DayOfWeek",
    "competition_distance",
    "store_enrolled_in_promo2",
    "is_school_holiday",
    "is_state_holiday",
    "baseline_sales_30d",
    "lag_7_sales",
    "lag_30_sales",
    "days_since_last_promo",
]

# Categorical columns — encoded to integers before training
CATEGORICAL_COLS = ["StoreType", "Assortment"]

# Engineered interaction features (Phase 9) — computed from columns
# above, AFTER categorical encoding. See add_interaction_features().
INTERACTION_COLS = [
    "promo_gap_x_baseline",
    "competition_x_storetype",
]

# Target columns — what the model predicts
TARGET_COLS = ["sales_lift_pct", "margin_impact"]

# All columns the model uses as input
ALL_FEATURE_COLS = FEATURE_COLS + CATEGORICAL_COLS + INTERACTION_COLS

# Columns that must never be used as features
# (they either ARE the target or leak the answer)
EXCLUDED_COLS = {
    "sales_lift_pct",   # target 1
    "margin_impact",    # target 2
    "promo_sales",      # raw sales — leaks the answer
    "Store",            # ID column, not a feature
    "Date",             # raw date — we use engineered date features instead
    "split",            # train/val flag, not a feature
}


def add_interaction_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add engineered interaction features (Phase 9).

    MUST be called AFTER categorical encoding, since
    competition_x_storetype multiplies against StoreType's
    integer-encoded form, not its raw string form.

    promo_gap_x_baseline: captures that the EFFECT of time-since-
        last-promo likely scales with a store's typical sales volume
        — pent-up demand at a high-volume store means something
        different than at a low-volume one.

    competition_x_storetype: captures that competitive pressure
        from nearby stores likely affects different store FORMATS
        differently.
    """
    df = df.copy()
    df["promo_gap_x_baseline"] = (
        df["days_since_last_promo"] * df["baseline_sales_30d"]
    )
    df["competition_x_storetype"] = df["competition_distance"] * df["StoreType"]
    return df


def select_feature_columns(columns: list[str]) -> list[str]:
    """Return model input feature columns from a raw column list."""
    return [col for col in columns if col in set(ALL_FEATURE_COLS)]


def get_feature_names() -> list[str]:
    """Return the ordered list of all feature names.

    Order matters for SHAP — the serving container uses this
    to map SHAP values back to feature names.
    """
    return ALL_FEATURE_COLS.copy()