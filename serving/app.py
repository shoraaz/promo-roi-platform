"""Promo ROI Serving API."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException

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
    """Load model artifacts from GCS once at startup.
    
    FastAPI's lifespan context manager runs this code before
    the app starts accepting requests, and again on shutdown
    (we have nothing to clean up, so the 'after yield' part is empty).
    """
    print("Starting up — loading model artifacts...")
    model_registry.load_from_gcs()
    yield
    print("Shutting down.")


app = FastAPI(title="Promo ROI Serving API", lifespan=lifespan)


@app.get("/health")
def health() -> dict[str, str]:
    """Liveness probe — is the container alive?
    
    Always returns ok if the process is running, regardless
    of whether models are loaded. Kubernetes uses this to decide
    whether to RESTART the container.
    """
    return {"status": "ok"}


@app.get("/ready")
def ready() -> dict[str, str]:
    """Readiness probe — is the container ready to serve traffic?
    
    Returns 'ready' only once models are loaded from GCS.
    Kubernetes uses this to decide whether to SEND TRAFFIC
    to this pod. During the ~5-10 seconds of model loading
    at startup, this returns 'loading' and no traffic is sent.
    """
    if model_registry.is_ready:
        return {"status": "ready"}
    return {"status": "loading"}


@app.post("/predict", response_model=PredictionResponse)
def predict(payload: PromotionRequest) -> PredictionResponse:
    """Predict promotion ROI with SHAP explanations.

    Builds a feature dictionary from the request, passes it to
    the model registry, and returns predictions for both targets
    plus the top 3 SHAP feature contributions for each.
    """
    if not model_registry.is_ready:
        raise HTTPException(status_code=503, detail="Models still loading")

    # Build feature dict — keys must match feature_names.pkl exactly
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