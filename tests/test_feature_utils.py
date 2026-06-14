from training.feature_utils import (
    ALL_FEATURE_COLS,
    CATEGORICAL_COLS,
    FEATURE_COLS,
    TARGET_COLS,
    get_feature_names,
    select_feature_columns,
)


def test_select_feature_columns_returns_only_known_features() -> None:
    # Only columns in ALL_FEATURE_COLS should pass through
    columns = ["DayOfWeek", "baseline_sales_30d", "sales_lift_pct", "Store", "Date"]
    result = select_feature_columns(columns)
    assert result == ["DayOfWeek", "baseline_sales_30d"]


def test_select_feature_columns_excludes_targets() -> None:
    # Target columns must never appear in features
    columns = ALL_FEATURE_COLS + ["sales_lift_pct", "margin_impact"]
    result = select_feature_columns(columns)
    assert "sales_lift_pct" not in result
    assert "margin_impact" not in result


def test_select_feature_columns_excludes_id_columns() -> None:
    # ID and leaky columns must never appear
    columns = ALL_FEATURE_COLS + ["Store", "Date", "promo_sales", "split"]
    result = select_feature_columns(columns)
    assert "Store" not in result
    assert "Date" not in result
    assert "promo_sales" not in result


def test_feature_lists_are_consistent() -> None:
    # ALL_FEATURE_COLS must equal FEATURE_COLS + CATEGORICAL_COLS
    assert ALL_FEATURE_COLS == FEATURE_COLS + CATEGORICAL_COLS


def test_no_overlap_between_features_and_targets() -> None:
    # Features and targets must be completely separate
    overlap = set(ALL_FEATURE_COLS) & set(TARGET_COLS)
    assert overlap == set(), f"Overlap found: {overlap}"


def test_get_feature_names_returns_copy() -> None:
    # get_feature_names() must return a copy, not the original list
    # Modifying the returned list must not affect the original
    names = get_feature_names()
    names.append("fake_feature")
    assert "fake_feature" not in get_feature_names()