"""Serving helpers for model loading and SHAP explainability.

Loads trained XGBoost models, SHAP explainers, and feature names
from GCS once at startup, then provides functions to make
predictions with SHAP explanations for individual requests.
"""

from __future__ import annotations

import os
import pickle
import tempfile

import numpy as np
import shap
import xgboost as xgb
from google.cloud import storage

# ─────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────
GCS_BUCKET = os.environ.get("GCS_BUCKET", "promo-roi-platform-2026-data")
MODEL_RUN_ID = os.environ.get("MODEL_RUN_ID", "5b88b989d6c64e75908f48254c262a72")
PROJECT_ID = os.environ.get("PROJECT_ID", "promo-roi-platform-2026")
TARGET_COLS = ["sales_lift_pct", "margin_impact"]


class ModelRegistry:
    """Holds loaded models, explainers, and feature names in memory.
    
    Created once at FastAPI startup. All prediction requests
    use this same in-memory registry — no repeated GCS calls.
    """

    def __init__(self) -> None:
        self.models: dict[str, xgb.XGBRegressor] = {}
        self.explainers: dict[str, shap.TreeExplainer] = {}
        self.feature_names: list[str] = []
        self.is_ready: bool = False

    def load_from_gcs(self) -> None:
        """Download and load all artifacts from GCS.
        
        Called once at startup. Downloads to a temp directory,
        unpickles each artifact, stores in memory.
        """
        print(f"Loading model artifacts from run: {MODEL_RUN_ID}")
        client = storage.Client(project=PROJECT_ID)
        bucket = client.bucket(GCS_BUCKET)

        with tempfile.TemporaryDirectory() as tmpdir:
            # Download feature names first — needed to build feature vectors
            feature_path = f"{tmpdir}/feature_names.pkl"
            bucket.blob(f"models/{MODEL_RUN_ID}/feature_names.pkl").download_to_filename(feature_path)
            with open(feature_path, "rb") as f:
                self.feature_names = pickle.load(f)
            print(f"  Loaded feature names: {self.feature_names}")

            # Download model + explainer for each target
            for target in TARGET_COLS:
                model_path = f"{tmpdir}/model_{target}.pkl"
                bucket.blob(f"models/{MODEL_RUN_ID}/model_{target}.pkl").download_to_filename(model_path)
                with open(model_path, "rb") as f:
                    self.models[target] = pickle.load(f)
                print(f"  Loaded model: {target}")

                explainer_path = f"{tmpdir}/explainer_{target}.pkl"
                bucket.blob(f"models/{MODEL_RUN_ID}/explainer_{target}.pkl").download_to_filename(explainer_path)
                with open(explainer_path, "rb") as f:
                    self.explainers[target] = pickle.load(f)
                print(f"  Loaded explainer: {target}")

        self.is_ready = True
        print("All model artifacts loaded successfully.")

    def predict_with_explanation(
        self, feature_dict: dict[str, float]
    ) -> dict[str, dict]:
        """Predict both targets and return SHAP explanations.

        Args:
            feature_dict: maps feature name -> value, must contain
                           all names in self.feature_names

        Returns:
            {
                "sales_lift_pct": {"prediction": float, "top_features": [...]},
                "margin_impact": {"prediction": float, "top_features": [...]},
            }
        """
        if not self.is_ready:
            raise RuntimeError("Models not loaded yet")

        # Build feature vector in the EXACT order the model was trained on
        # This ordering is critical — must match feature_names.pkl exactly
        X = np.array([[feature_dict[name] for name in self.feature_names]])

        results = {}
        for target in TARGET_COLS:
            model = self.models[target]
            explainer = self.explainers[target]

            prediction = float(model.predict(X)[0])

            # Compute SHAP values for THIS ONE prediction
            shap_values = explainer.shap_values(X)[0]  # shape: (n_features,)

            # Pair each feature name with its SHAP value, sort by magnitude
            feature_contributions = list(zip(self.feature_names, shap_values))
            feature_contributions.sort(key=lambda x: abs(x[1]), reverse=True)

            top_features = [
                {"feature": name, "shap_value": round(float(val), 4)}
                for name, val in feature_contributions[:3]
            ]

            results[target] = {
                "prediction": round(prediction, 4),
                "top_features": top_features,
            }

        return results


# Single global instance — shared across all requests
model_registry = ModelRegistry()