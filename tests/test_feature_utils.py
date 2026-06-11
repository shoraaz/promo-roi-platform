from training.feature_utils import select_feature_columns


def test_select_feature_columns_excludes_targets() -> None:
    columns = ["promo", "store_id", "sales_lift_pct", "margin_impact", "sales", "customers"]
    assert select_feature_columns(columns) == ["promo", "store_id"]
