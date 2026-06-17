"""Check feature importance ranking for the margin_impact model
from the Phase 9 (tuning + features) training run.

Computes a fresh SHAP sample against real BigQuery data and ranks
features by mean absolute SHAP value — consistent with how this
project already uses SHAP for explanations elsewhere.
"""

import pickle
import sys

import numpy as np
from google.cloud import bigquery, storage

sys.path.insert(0, "training")

RUN_ID = "31f76f91af79479880eb270cb11fde42"
BUCKET = "promo-roi-platform-2026-data"
PROJECT_ID = "promo-roi-platform-2026"

client = storage.Client(project=PROJECT_ID)
bucket = client.bucket(BUCKET)

bucket.blob(f"models/{RUN_ID}/explainer_margin_impact.pkl").download_to_filename(
    "explainer.pkl"
)
bucket.blob(f"models/{RUN_ID}/feature_names.pkl").download_to_filename(
    "feature_names.pkl"
)

with open("explainer.pkl", "rb") as f:
    explainer = pickle.load(f)
with open("feature_names.pkl", "rb") as f:
    feature_names = pickle.load(f)

# Pull a small, real sample to compute fresh SHAP values against —
# same encode + interaction-feature steps train.py applies.
from feature_utils import add_interaction_features

bq_client = bigquery.Client(project=PROJECT_ID)
query = f"""
    SELECT
        DayOfWeek, StoreType, Assortment, competition_distance,
        store_enrolled_in_promo2, is_school_holiday, is_state_holiday,
        baseline_sales_30d, lag_7_sales, lag_30_sales,
        days_since_last_promo
    FROM `{PROJECT_ID}.promo_roi.promo_features`
    WHERE sales_lift_pct IS NOT NULL AND margin_impact IS NOT NULL
    LIMIT 500
"""
df = bq_client.query(query).to_dataframe(create_bqstorage_client=False)

for col in ["StoreType", "Assortment"]:
    df[col] = df[col].astype("category").cat.codes

df = add_interaction_features(df)
X_sample = df[feature_names]

shap_values = explainer.shap_values(X_sample)
mean_abs_shap = np.abs(shap_values).mean(axis=0)

ranked = sorted(zip(feature_names, mean_abs_shap), key=lambda x: -x[1])
print("\nSHAP feature importance ranking (margin_impact, mean |SHAP value|):")
for name, score in ranked:
    marker = (
        "  <-- NEW (Phase 9)"
        if name in ("promo_gap_x_baseline", "competition_x_storetype")
        else ""
    )
    print(f"  {name}: {score:.4f}{marker}")