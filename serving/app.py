"""Promo ROI Serving API."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from prometheus_fastapi_instrumentator import Instrumentator

try:
    from model_utils import model_registry          # Docker context
    from schemas import (
        PredictionResponse,
        PromotionRequest,
        TargetPrediction,
    )
except ModuleNotFoundError:
    from serving.model_utils import model_registry  # test context
    from serving.schemas import (
        PredictionResponse,
        PromotionRequest,
        TargetPrediction,
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load model artifacts from GCS once at startup."""
    print("Starting up — loading model artifacts...")
    model_registry.load_from_gcs()
    yield
    print("Shutting down.")


app = FastAPI(title="Promo ROI Serving API", lifespan=lifespan)

# Attach Prometheus instrumentation — this adds a /metrics endpoint
# automatically tracking request count, latency, and status codes
# for every route, with zero per-endpoint code changes needed.
Instrumentator().instrument(app).expose(app)


@app.get("/health")
def health() -> dict[str, str]:
    """Liveness probe — is the container alive?"""
    return {"status": "ok"}


@app.get("/ready")
def ready() -> dict[str, str]:
    """Readiness probe — is the container ready to serve traffic?"""
    if model_registry.is_ready:
        return {"status": "ready"}
    return {"status": "loading"}


@app.post("/predict", response_model=PredictionResponse)
def predict(payload: PromotionRequest) -> PredictionResponse:
    """Predict promotion ROI with SHAP explanations."""
    if not model_registry.is_ready:
        raise HTTPException(status_code=503, detail="Models still loading")

    feature_dict = {
        "DayOfWeek": payload.DayOfWeek,
        "competition_distance": payload.competition_distance,
        "store_enrolled_in_promo2": payload.store_enrolled_in_promo2,
        "is_school_holiday": payload.is_school_holiday,
        "is_state_holiday": payload.is_state_holiday,
        "baseline_sales_30d": payload.baseline_sales_30d,
        "lag_7_sales": payload.lag_7_sales,
        "lag_30_sales": payload.lag_30_sales,
        "days_since_last_promo": payload.days_since_last_promo,
        "StoreType": payload.StoreType,
        "Assortment": payload.Assortment,
    }

    results = model_registry.predict_with_explanation(feature_dict)
    margin_impact = results["margin_impact"]["prediction"]
    roi_verdict = "POSITIVE" if margin_impact >= 0 else "NEGATIVE"

    return PredictionResponse(
        store_id=payload.store_id,
        sales_lift_pct=TargetPrediction(**results["sales_lift_pct"]),
        margin_impact=TargetPrediction(**results["margin_impact"]),
        roi_verdict=roi_verdict,
    )