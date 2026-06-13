"""Promo ROI Serving API."""

from __future__ import annotations

from fastapi import FastAPI



try:
    from schemas import PredictionResponse, PromotionRequest      # Docker context
except ModuleNotFoundError:
    from serving.schemas import PredictionResponse, PromotionRequest  # test context

app = FastAPI(title="Promo ROI Serving API")


@app.get("/health")
def health() -> dict[str, str]:
    """Liveness probe — is the container alive?"""
    return {"status": "ok"}


@app.get("/ready")
def ready() -> dict[str, str]:
    """Readiness probe — is the container ready to serve traffic?"""
    # In Phase 3 we'll check if model is loaded here
    # For now just return ready
    return {"status": "ready"}


@app.post("/predict", response_model=PredictionResponse)
def predict(payload: PromotionRequest) -> PredictionResponse:
    """Predict promotion ROI — stub for now, real logic added in Phase 3."""
    return PredictionResponse(
        store_id=payload.store_id,
        sales_lift_pct=0.0,
        margin_impact=0.0,
        top_features=["promo", "day_of_week", "month"],
    )