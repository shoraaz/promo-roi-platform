"""Feature-loading utilities for training and evaluation."""

from __future__ import annotations

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

# Target columns — what the model predicts
TARGET_COLS = ["sales_lift_pct", "margin_impact"]

# All columns the model uses as input
ALL_FEATURE_COLS = FEATURE_COLS + CATEGORICAL_COLS

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


def select_feature_columns(columns: list[str]) -> list[str]:
    """Return model input feature columns from a raw column list.
    
    Filters out targets, ID columns, and any leaky columns.
    Only returns columns that are in our defined feature set.
    
    Example:
        Input:  ["Store", "DayOfWeek", "sales_lift_pct", "baseline_sales_30d"]
        Output: ["DayOfWeek", "baseline_sales_30d"]
    """
    return [col for col in columns if col in set(ALL_FEATURE_COLS)]


def get_feature_names() -> list[str]:
    """Return the ordered list of all feature names.
    
    Order matters for SHAP — the serving container uses this
    to map SHAP values back to feature names.
    """
    return ALL_FEATURE_COLS.copy()