"""Pure label-engineering helpers for promotion ROI modeling."""

from __future__ import annotations

MARGIN_RATE = 0.20       # assume 20% gross margin on FMCG products
PROMO_COST_RATE = 0.15   # assume promo costs 15% of baseline revenue


def compute_sales_lift_pct(current_sales: float, baseline_sales: float) -> float:
    """Return percentage sales lift over a baseline value.
    
    Example: baseline=100, current=120 → returns 20.0 (meaning 20% lift)
    """
    if baseline_sales == 0:
        return 0.0
    return ((current_sales - baseline_sales) / baseline_sales) * 100.0


def compute_margin_impact(current_sales: float, baseline_sales: float) -> float:
    """Return absolute margin impact (INR) of running a promotion.

    Positive = promotion was profitable.
    Negative = promotion lost money.

    Logic:
    - incremental_sales = sales gained FROM the promotion
    - incremental_margin = profit from those extra sales (at 20% margin)
    - promo_cost = what the promotion itself cost (15% of baseline)
    - margin_impact = what we gained minus what we spent
    """
    if baseline_sales == 0:
        return 0.0
    incremental_sales = current_sales - baseline_sales
    incremental_margin = incremental_sales * MARGIN_RATE
    promo_cost = baseline_sales * PROMO_COST_RATE
    return incremental_margin - promo_cost