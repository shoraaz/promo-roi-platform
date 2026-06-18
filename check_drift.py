"""Evidently AI drift detection: compare training data vs validation
data (a chronologically later period) for promo_features.

This is Phase 9 Part 3 — a separate concern from Prometheus/Grafana
(service health) and from hyperparameter/feature tuning (model fit).
This checks whether the DATA ITSELF looks different between the
period the model learned from and a later period it's evaluated on.
"""

import sys

from google.cloud import bigquery
from evidently import Report
from evidently.presets import DataDriftPreset

sys.path.insert(0, "training")
from feature_utils import CATEGORICAL_COLS, FEATURE_COLS

PROJECT_ID = "promo-roi-platform-2026"

client = bigquery.Client(project=PROJECT_ID)

query = f"""
    SELECT
        {", ".join(FEATURE_COLS + CATEGORICAL_COLS)},
        split
    FROM `{PROJECT_ID}.promo_roi.promo_features`
    WHERE sales_lift_pct IS NOT NULL AND margin_impact IS NOT NULL
"""
df = client.query(query).to_dataframe(create_bqstorage_client=False)

reference = df[df["split"] == "train"].drop(columns=["split"])
current = df[df["split"] == "validation"].drop(columns=["split"])

# BigQuery's to_dataframe() returns nullable Int64/Float64 extension
# dtypes by default. Evidently's type inference doesn't recognize
# these — cast to plain numpy dtypes explicitly.
numeric_cols = [
    "DayOfWeek", "competition_distance", "baseline_sales_30d",
    "lag_7_sales", "lag_30_sales", "days_since_last_promo",
]
for col in numeric_cols:
    reference[col] = reference[col].astype("float64")
    current[col] = current[col].astype("float64")

# Binary flags and categoricals — keep as explicit strings
categorical_cols = [
    "store_enrolled_in_promo2", "is_school_holiday", "is_state_holiday",
    "StoreType", "Assortment",
]
for col in categorical_cols:
    reference[col] = reference[col].astype(str)
    current[col] = current[col].astype(str)

print(f"Reference (train) rows: {len(reference):,}")
print(f"Current (validation) rows: {len(current):,}")
print(f"Columns being compared: {list(reference.columns)}")
print("\nColumn dtypes:")
print(reference.dtypes)
print("\nAny all-null columns in reference?")
print(reference.isnull().all())
print("\nAny all-null columns in current?")
print(current.isnull().all())
report = Report(
    [DataDriftPreset(method="psi", columns=list(reference.columns))],
    include_tests=True,
)
result = report.run(current_data=current, reference_data=reference)

result.save_html("drift_report.html")
print("\nDrift report saved to drift_report.html")

# Also print a quick summary to the console
result_dict = result.dict()
print("\nSummary:")
print(result_dict)