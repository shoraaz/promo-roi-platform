"""Small standalone training script producing a model artifact in
the exact format Vertex AI's pre-built XGBoost container expects.

Breadth exercise covering: Model Registry, Endpoints, Batch Prediction,
Model Monitoring — NOT a replacement for the main project's GKE-based
serving architecture.

Vertex AI's pre-built XGBoost container loads exactly one file:
  model.bst  (XGBoost binary format, saved via model.save_model())
The artifact_uri passed to Model.upload() must point to the GCS
FOLDER containing that file, not the file itself.
"""

import sys

import xgboost as xgb
from google.cloud import bigquery

sys.path.insert(0, "..")  # reach training/feature_utils from mini_exercise/
from training.feature_utils import (
    CATEGORICAL_COLS,
    FEATURE_COLS,
    add_interaction_features,
)

PROJECT_ID = "promo-roi-platform-2026"
OUTPUT_FILE = "model.bst"

client = bigquery.Client(project=PROJECT_ID)
query = f"""
    SELECT
        DayOfWeek,
        competition_distance,
        store_enrolled_in_promo2,
        is_school_holiday,
        is_state_holiday,
        baseline_sales_30d,
        lag_7_sales,
        lag_30_sales,
        days_since_last_promo,
        StoreType,
        Assortment,
        margin_impact
    FROM `{PROJECT_ID}.promo_roi.promo_features`
    WHERE split = 'train' AND margin_impact IS NOT NULL
    LIMIT 50000
"""

print("Fetching training data from BigQuery...")
df = client.query(query).to_dataframe(create_bqstorage_client=False)
print(f"  Rows: {len(df):,}")

# Encode categoricals to int (same convention as main training pipeline)
for col in CATEGORICAL_COLS:
    df[col] = df[col].astype("category").cat.codes.astype("float64")

df = add_interaction_features(df)

all_feature_cols = FEATURE_COLS + CATEGORICAL_COLS + [
    "promo_gap_x_baseline",
    "competition_x_storetype",
]
for col in all_feature_cols:
    df[col] = df[col].astype("float64")

X = df[all_feature_cols]
y = df["margin_impact"]

print("Training XGBoost model...")
model = xgb.XGBRegressor(
    n_estimators=200,
    max_depth=6,
    learning_rate=0.1,
    random_state=42,
    tree_method="hist",
)
model.fit(X, y, verbose=False)
print("  Training complete.")

model.save_model(OUTPUT_FILE)
print(f"Saved {OUTPUT_FILE}")
print()
print("Next: upload to GCS and register in Vertex AI Model Registry.")
print(f"  gcloud storage cp {OUTPUT_FILE} gs://{PROJECT_ID}-data/mini-exercise/model-registry/{OUTPUT_FILE}")
