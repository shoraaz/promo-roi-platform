from training.label_engineering import compute_margin_impact, compute_sales_lift_pct


def test_compute_sales_lift_pct_normal() -> None:
    # 120 sales vs 100 baseline = 20% lift
    assert compute_sales_lift_pct(120, 100) == 20.0


def test_compute_sales_lift_pct_zero_baseline() -> None:
    # Should never divide by zero — returns 0 safely
    assert compute_sales_lift_pct(100, 0) == 0.0


def test_compute_margin_impact_profitable() -> None:
    # current=100, baseline=40
    # incremental=60, margin=12.0, promo_cost=6.0 → impact=6.0
    assert compute_margin_impact(100, 40) == 6.0


def test_compute_margin_impact_loss_making() -> None:
    # current=100, baseline=100 → no lift, but promo still cost money
    # incremental=0, margin=0, promo_cost=15.0 → impact=-15.0
    assert compute_margin_impact(100, 100) == -15.0


def test_compute_margin_impact_zero_baseline() -> None:
    # Should never divide by zero — returns 0 safely
    assert compute_margin_impact(100, 0) == 0.0