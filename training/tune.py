"""Hyperparameter tuning for the margin_impact model using Optuna.

Reuses data loading from train.py; runs an Optuna study with each
trial logged as a nested MLflow run for later comparison.
"""

from __future__ import annotations
from train import add_interaction_features
import os
import numpy as np

import mlflow
import optuna
import xgboost as xgb
from sklearn.metrics import mean_squared_error, r2_score

from train import (
    load_features,
    encode_categoricals,
    split_data,
    get_features_and_targets,
    MLFLOW_TRACKING_URI,
)


EXPERIMENT_NAME = "promo-roi-tuning"
TARGET = os.environ.get("TUNING_TARGET", "margin_impact")
N_TRIALS = 50


def objective(trial: optuna.Trial, X_train, y_train, X_val, y_val) -> float:
    """One Optuna trial: train with suggested params, return validation RMSE."""
    params = {
        "n_estimators": trial.suggest_int("n_estimators", 100, 800),
        "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
        "max_depth": trial.suggest_int("max_depth", 3, 10),
        "subsample": trial.suggest_float("subsample", 0.6, 1.0),
        "colsample_bytree": trial.suggest_float("colsample_bytree", 0.6, 1.0),
        "random_state": 42,
        "n_jobs": -1,
    }

    with mlflow.start_run(nested=True, run_name=f"trial_{trial.number}"):
        mlflow.log_params(params)

        model = xgb.XGBRegressor(**params)
        model.fit(X_train, y_train[TARGET])

        preds = model.predict(X_val)
        rmse = float(np.sqrt(mean_squared_error(y_val[TARGET], preds)))
        r2 = r2_score(y_val[TARGET], preds)

        mlflow.log_metric("rmse", rmse)
        mlflow.log_metric("r2", r2)

    return rmse


def main() -> None:
    print("=" * 60)
    print(f"OPTUNA TUNING: {TARGET}")
    print("=" * 60)

    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    mlflow.set_experiment(EXPERIMENT_NAME)

    print("Loading features...")
    df = load_features()
    df = encode_categoricals(df)
    df = add_interaction_features(df)
    train_df, val_df = split_data(df)
    X_train, y_train = get_features_and_targets(train_df)
    X_val, y_val = get_features_and_targets(val_df)
    print(f"Train: {len(X_train)} rows, Val: {len(X_val)} rows")

    with mlflow.start_run(run_name="optuna_tuning_parent"):
        mlflow.log_param("n_trials", N_TRIALS)
        mlflow.log_param("target", TARGET)

        study = optuna.create_study(direction="minimize")
        study.optimize(
            lambda trial: objective(trial, X_train, y_train, X_val, y_val),
            n_trials=N_TRIALS,
        )

        mlflow.log_params({f"best_{k}": v for k, v in study.best_params.items()})
        mlflow.log_metric("best_rmse", study.best_value)

        print("\n" + "=" * 60)
        print("TUNING COMPLETE")
        print(f"Best RMSE: {study.best_value:.4f}")
        print(f"Best params: {study.best_params}")
        print("=" * 60)

    # Upload MLflow database to GCS, same pattern as train.py
    mlflow_db_path = "/tmp/mlflow.db"
    if os.path.exists(mlflow_db_path):
        from google.cloud import storage
        from train import PROJECT_ID, GCS_BUCKET

        client = storage.Client(project=PROJECT_ID)
        bucket = client.bucket(GCS_BUCKET)
        gcs_path = f"mlflow/tuning/{study.study_name}/mlflow.db"
        bucket.blob(gcs_path).upload_from_filename(mlflow_db_path)
        print(f"\nMLflow database uploaded to: gs://{GCS_BUCKET}/{gcs_path}")


if __name__ == "__main__":
    main()