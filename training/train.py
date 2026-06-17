"""Training entry point for the Promotion ROI model.

Reads engineered features from BigQuery, trains two XGBoost regressors
(sales_lift_pct and margin_impact), logs everything to MLflow,
computes SHAP values, and saves artifacts to GCS.
"""

from __future__ import annotations

import os
import pickle
import tempfile

import mlflow
import mlflow.xgboost
import numpy as np
import pandas as pd
import shap
import xgboost as xgb
from google.cloud import bigquery, storage
from sklearn.metrics import mean_squared_error, r2_score
from feature_utils import ALL_FEATURE_COLS, CATEGORICAL_COLS, FEATURE_COLS, TARGET_COLS


# ─────────────────────────────────────────────
# Configuration — all values from environment variables
# Never hardcode project IDs or bucket names
# ─────────────────────────────────────────────
PROJECT_ID = os.environ.get("PROJECT_ID", "promo-roi-platform-2026")
DATASET_ID = os.environ.get("DATASET_ID", "promo_roi")
TABLE_ID = os.environ.get("TABLE_ID", "promo_features")
GCS_BUCKET = os.environ.get("GCS_BUCKET", "promo-roi-platform-2026-data")
MLFLOW_TRACKING_URI = os.environ.get("MLFLOW_TRACKING_URI", "sqlite:////tmp/mlflow.db")
MLFLOW_ARTIFACT_URI = os.environ.get(
    "MLFLOW_ARTIFACT_URI",
    f"gs://{GCS_BUCKET}/mlflow/artifacts"
)
EXPERIMENT_NAME = os.environ.get("EXPERIMENT_NAME", "promo-roi-xgboost")

# Feature columns the model uses as input
# These must match exactly what's in the promo_features BigQuery table
FEATURE_COLS_justforseeing = [
    "DayOfWeek",
    "competition_distance",
    "store_enrolled_in_promo2",
    "is_school_holiday",
    "is_state_holiday",
    "baseline_sales_30d",
    "lag_7_sales",
    "lag_30_sales",
    "days_since_last_promo",
]

# Categorical columns that need encoding
# XGBoost can't handle raw strings — we convert to integers
#CATEGORICAL_COLS = ["StoreType", "Assortment"]

# The two targets we predict simultaneously
#TARGET_COLS = ["sales_lift_pct", "margin_impact"]

# XGBoost hyperparameters, per target.
# sales_lift_pct: original defaults — not yet tuned.
# margin_impact: tuned via Optuna (50-trial study, Phase 9).
#   Baseline RMSE=271.7008 -> Tuned RMSE=258.8130 (~4.7% improvement)
#   Search revealed deeper trees (max_depth 9-10) and lower
#   colsample_bytree (~0.60-0.70) consistently outperformed the
#   original shallower defaults — suggesting more complex feature
#   interactions for this target than initially modeled.
XGBOOST_PARAMS = {
    "sales_lift_pct": {
        "n_estimators": 500,
        "learning_rate": 0.05,
        "max_depth": 6,
        "subsample": 0.8,
        "colsample_bytree": 0.8,
        "random_state": 42,
        "n_jobs": -1,  # use all available CPU cores
    },
    "margin_impact": {
        "n_estimators": 800,
        "learning_rate": 0.03982009645961388,
        "max_depth": 10,
        "subsample": 0.985652684899661,
        "colsample_bytree": 0.6088786911506849,
        "random_state": 42,
        "n_jobs": -1,
    },
}


def load_features() -> pd.DataFrame:
    """Load engineered features from BigQuery.
    
    Returns a DataFrame with feature columns and target columns.
    Only loads open-store promo events (already filtered in BigQuery).
    """
    print(f"Loading features from {PROJECT_ID}.{DATASET_ID}.{TABLE_ID}...")
    
    client = bigquery.Client(project=PROJECT_ID)
    
    query = f"""
        SELECT
            Store,
            Date,
            DayOfWeek,
            StoreType,
            Assortment,
            competition_distance,
            store_enrolled_in_promo2,
            is_school_holiday,
            is_state_holiday,
            baseline_sales_30d,
            lag_7_sales,
            lag_30_sales,
            days_since_last_promo,
            sales_lift_pct,
            margin_impact,
            split
        FROM `{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}`
        WHERE sales_lift_pct IS NOT NULL
          AND margin_impact IS NOT NULL
    """
    
    # to_dataframe() uses pyarrow under the hood for fast transfer
    df = client.query(query).to_dataframe(create_bqstorage_client=False)
    print(f"Loaded {len(df):,} rows, {df.shape[1]} columns")
    return df


def encode_categoricals(df: pd.DataFrame) -> pd.DataFrame:
    """Encode categorical columns as integers.
    
    XGBoost requires numeric inputs. StoreType (a/b/c/d) and
    Assortment (a/b/c) are strings — we convert to integer codes.
    
    Example:
        StoreType: a→0, b→1, c→2, d→3
        Assortment: a→0, b→1, c→2
    """
    df = df.copy()
    for col in CATEGORICAL_COLS:
        df[col] = df[col].astype("category").cat.codes
    return df


def split_data(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split into train and validation sets using the pre-computed split column.
    
    We use time-based split (not random) to prevent data leakage.
    Train: 2013-01-01 to 2015-03-31
    Validation: 2015-04-01 to 2015-07-31
    """
    train_df = df[df["split"] == "train"].copy()
    val_df = df[df["split"] == "validation"].copy()
    
    print(f"Train set: {len(train_df):,} rows")
    print(f"Validation set: {len(val_df):,} rows")
    
    return train_df, val_df


def get_features_and_targets(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Separate feature matrix X from target matrix y."""
    all_feature_cols = FEATURE_COLS + CATEGORICAL_COLS
    X = df[all_feature_cols]
    y = df[TARGET_COLS]
    return X, y


def train_models(
    X_train: pd.DataFrame,
    y_train: pd.DataFrame,
) -> dict[str, xgb.XGBRegressor]:
    """Train one XGBoost regressor per target.
    
    Why two separate models instead of one multi-output model?
    XGBoost's multi-output mode uses the same tree structure for both
    targets, which is efficient but less accurate than training
    separately when the two targets have different signal patterns.
    sales_lift_pct and margin_impact have different drivers — separate
    models capture this better.

    Each target now uses its OWN hyperparameters (see XGBOOST_PARAMS
    above) — margin_impact uses Optuna-tuned params from Phase 9,
    while sales_lift_pct still uses the original defaults.
    """
    models = {}
    
    for target in TARGET_COLS:
        print(f"\nTraining model for: {target}")
        print(f"  Params: {XGBOOST_PARAMS[target]}")
        
        model = xgb.XGBRegressor(**XGBOOST_PARAMS[target])
        model.fit(
            X_train,
            y_train[target],
            eval_set=[(X_train, y_train[target])],
            verbose=100,  # print progress every 100 trees
        )
        models[target] = model
        print(f"  ✓ {target} model trained")
    
    return models


def evaluate_models(
    models: dict[str, xgb.XGBRegressor],
    X_val: pd.DataFrame,
    y_val: pd.DataFrame,
) -> dict[str, dict[str, float]]:
    """Evaluate both models on validation set.
    
    Metrics:
    - RMSE: Root Mean Squared Error — in the same units as the target
    - R²: how much variance the model explains (1.0 = perfect, 0.0 = useless)
    """
    metrics = {}
    
    for target, model in models.items():
        y_pred = model.predict(X_val)
        y_true = y_val[target].values
        
        rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
        r2 = float(r2_score(y_true, y_pred))
        
        metrics[target] = {"rmse": rmse, "r2": r2}
        print(f"\n{target}:")
        print(f"  RMSE: {rmse:.4f}")
        print(f"  R²:   {r2:.4f}")
    
    return metrics


def compute_shap_values(
    models: dict[str, xgb.XGBRegressor],
    X_sample: pd.DataFrame,
) -> dict[str, np.ndarray]:
    """Compute SHAP values on a sample of validation data.
    
    Why a sample and not the full dataset?
    SHAP computation is O(n * trees). On 50k validation rows it would
    take too long. A 500-row sample gives reliable feature importance
    estimates — the distribution stabilizes quickly.
    
    We save the SHAP explainer objects (not just values) so the
    serving container can compute SHAP for individual predictions.
    """
    explainers = {}
    shap_values = {}
    
    for target, model in models.items():
        print(f"\nComputing SHAP for: {target}")
        explainer = shap.TreeExplainer(model)
        sv = explainer.shap_values(X_sample)
        explainers[target] = explainer
        shap_values[target] = sv
        print(f"  ✓ SHAP computed, shape: {sv.shape}")
    
    return explainers, shap_values


def save_artifacts(
    models: dict[str, xgb.XGBRegressor],
    explainers: dict,
    feature_names: list[str],
    run_id: str,
) -> dict[str, str]:
    """Save model and SHAP explainer artifacts to GCS.
    
    Artifacts are saved under:
    gs://bucket/models/<run_id>/model_<target>.pkl
    gs://bucket/models/<run_id>/explainer_<target>.pkl
    gs://bucket/models/<run_id>/feature_names.pkl
    
    Using run_id in the path means every training run has its own
    artifacts — no overwriting, full history preserved.
    """
    client = storage.Client(project=PROJECT_ID)
    bucket = client.bucket(GCS_BUCKET)
    
    artifact_paths = {}
    
    with tempfile.TemporaryDirectory() as tmpdir:
        for target in TARGET_COLS:
            # Save model
            model_path = f"{tmpdir}/model_{target}.pkl"
            with open(model_path, "wb") as f:
                pickle.dump(models[target], f)
            
            gcs_model_path = f"models/{run_id}/model_{target}.pkl"
            bucket.blob(gcs_model_path).upload_from_filename(model_path)
            artifact_paths[f"model_{target}"] = f"gs://{GCS_BUCKET}/{gcs_model_path}"
            
            # Save SHAP explainer
            explainer_path = f"{tmpdir}/explainer_{target}.pkl"
            with open(explainer_path, "wb") as f:
                pickle.dump(explainers[target], f)
            
            gcs_explainer_path = f"models/{run_id}/explainer_{target}.pkl"
            bucket.blob(gcs_explainer_path).upload_from_filename(explainer_path)
            artifact_paths[f"explainer_{target}"] = f"gs://{GCS_BUCKET}/{gcs_explainer_path}"
        
        # Save feature names — serving container needs this for SHAP output
        feature_path = f"{tmpdir}/feature_names.pkl"
        with open(feature_path, "wb") as f:
            pickle.dump(feature_names, f)
        
        gcs_feature_path = f"models/{run_id}/feature_names.pkl"
        bucket.blob(gcs_feature_path).upload_from_filename(feature_path)
        artifact_paths["feature_names"] = f"gs://{GCS_BUCKET}/{gcs_feature_path}"
    
    print(f"\nArtifacts saved to GCS under: gs://{GCS_BUCKET}/models/{run_id}/")
    return artifact_paths

def main() -> None:
    """Main training entry point."""
    
    print("=" * 60)
    print("PROMO ROI TRAINING JOB")
    print("=" * 60)
    
    # ── 1. Configure MLflow ──────────────────────────────────────
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    mlflow.set_experiment(EXPERIMENT_NAME)
    
    with mlflow.start_run(tags={"project": "promo-roi-platform", "phase": "training"}) as run:
        run_id = run.info.run_id
        print(f"\nMLflow run ID: {run_id}")
        
        # ── 2. Log hyperparameters ───────────────────────────────
        # Logged per-target with a prefix, since each target now has
        # its own params (margin_impact is Optuna-tuned, Phase 9)
        for target, params in XGBOOST_PARAMS.items():
            for param_name, value in params.items():
                mlflow.log_param(f"{target}_{param_name}", value)
        mlflow.log_param("feature_cols", FEATURE_COLS)
        mlflow.log_param("target_cols", TARGET_COLS)
        
        # ── 3. Load data ─────────────────────────────────────────
        df = load_features()
        df = encode_categoricals(df)
        train_df, val_df = split_data(df)
        
        X_train, y_train = get_features_and_targets(train_df)
        X_val, y_val = get_features_and_targets(val_df)
        
        mlflow.log_param("train_rows", len(X_train))
        mlflow.log_param("val_rows", len(X_val))
        
        # ── 4. Train ─────────────────────────────────────────────
        models = train_models(X_train, y_train)
        
        # ── 5. Evaluate ──────────────────────────────────────────
        metrics = evaluate_models(models, X_val, y_val)
        
        # Log metrics to MLflow
        for target, target_metrics in metrics.items():
            for metric_name, value in target_metrics.items():
                mlflow.log_metric(f"{target}_{metric_name}", value)
        
        # ── 6. SHAP ──────────────────────────────────────────────
        X_sample = X_val.sample(n=min(500, len(X_val)), random_state=42)
        explainers, shap_values = compute_shap_values(models, X_sample)
        
        # ── 7. Save artifacts to GCS ─────────────────────────────
        feature_names = FEATURE_COLS + CATEGORICAL_COLS
        artifact_paths = save_artifacts(models, explainers, feature_names, run_id)
        
        # Log artifact paths to MLflow so we can find them later
        for name, path in artifact_paths.items():
            mlflow.log_param(f"artifact_{name}", path)
        
        print("\n" + "=" * 60)
        print("TRAINING COMPLETE")
        print(f"MLflow run: {run_id}")
        for target, m in metrics.items():
            print(f"{target}: RMSE={m['rmse']:.4f}, R²={m['r2']:.4f}")
        print("=" * 60)

    # ── 8. Upload MLflow SQLite database to GCS ──────────────────
    # Runs AFTER the `with` block exits, so MLflow has closed
    # its connection to the SQLite file — safe to upload
    mlflow_db_path = "/tmp/mlflow.db"
    if os.path.exists(mlflow_db_path):
        client = storage.Client(project=PROJECT_ID)
        bucket = client.bucket(GCS_BUCKET)
        gcs_mlflow_path = f"mlflow/runs/{run_id}/mlflow.db"
        bucket.blob(gcs_mlflow_path).upload_from_filename(mlflow_db_path)
        print(f"\nMLflow database uploaded to: gs://{GCS_BUCKET}/{gcs_mlflow_path}")


if __name__ == "__main__":
    main()