from __future__ import annotations

from pydantic import BaseModel, Field


class PromotionRequest(BaseModel):
    store_id: int = Field(..., description="Store identifier")
    promo: int = Field(..., description="Promotion flag")
    day_of_week: int = Field(..., description="Day of week")
    month: int = Field(..., description="Month of year")


class PredictionResponse(BaseModel):
    store_id: int
    sales_lift_pct: float
    margin_impact: float
    top_features: list[str]
