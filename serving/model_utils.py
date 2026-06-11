"""Serving helpers for model loading and SHAP explainability."""

from __future__ import annotations


def load_model(model_path: str):
    """Placeholder loader for the trained model artifact."""
    return {"model_path": model_path, "status": "placeholder"}


def explain_prediction(model, features: list[float]) -> list[str]:
    """Return a placeholder SHAP-style explanation list."""
    return [f"feature_{index}: {value:.3f}" for index, value in enumerate(features[:3])]
