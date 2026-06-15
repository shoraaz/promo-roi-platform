"""Pydantic schemas for the Promo ROI Serving API."""

from __future__ import annotations

from pydantic import BaseModel, Field


class PromotionRequest(BaseModel):
    """Input features for one promotion prediction.

    Field names and meanings match feature_utils.ALL_FEATURE_COLS
    exactly. StoreType and Assortment are accepted as their
    integer-encoded form (matching training: a=0, b=1, c=2, d=3).
    """

    # Identifiers — not used as model features, but useful in the response
    store_id: int = Field(..., description="Store identifier")

    # Numeric features (FEATURE_COLS)
    DayOfWeek: int = Field(..., ge=1, le=7, description="1=Monday ... 7=Sunday")
    competition_distance: float = Field(..., ge=0, description="Meters to nearest competitor")
    store_enrolled_in_promo2: int = Field(..., ge=0, le=1, description="1 if enrolled in Promo2")
    is_school_holiday: int = Field(..., ge=0, le=1)
    is_state_holiday: int = Field(..., ge=0, le=1)
    baseline_sales_30d: float = Field(..., ge=0, description="30-day rolling avg non-promo sales")
    lag_7_sales: float = Field(..., ge=0, description="Sales 7 days ago")
    lag_30_sales: float = Field(..., ge=0, description="Sales 30 days ago")
    days_since_last_promo: int = Field(..., ge=0, description="999 if never promoted")

    # Categorical features (CATEGORICAL_COLS), integer-encoded
    StoreType: int = Field(..., ge=0, le=3, description="0=a, 1=b, 2=c, 3=d")
    Assortment: int = Field(..., ge=0, le=2, description="0=a, 1=b, 2=c")

    class Config:
        json_schema_extra = {
            "example": {
                "store_id": 1,
                "DayOfWeek": 5,
                "competition_distance": 1270,
                "store_enrolled_in_promo2": 0,
                "is_school_holiday": 1,
                "is_state_holiday": 0,
                "baseline_sales_30d": 4835.0,
                "lag_7_sales": 7176,
                "lag_30_sales": 7176,
                "days_since_last_promo": 999,
                "StoreType": 2,
                "Assortment": 0,
            }
        }


class TargetPrediction(BaseModel):
    """Prediction and SHAP explanation for one target variable."""

    prediction: float
    top_features: list[dict[str, float | str]]


class PredictionResponse(BaseModel):
    """Full prediction response — both targets with explanations."""

    store_id: int
    sales_lift_pct: TargetPrediction
    margin_impact: TargetPrediction
    roi_verdict: str = Field(..., description="'POSITIVE' or 'NEGATIVE'")