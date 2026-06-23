# mini_exercise/create_batch_input.py
import json

from google.cloud import bigquery

PROJECT_ID = "promo-roi-platform-2026"

client = bigquery.Client(project=PROJECT_ID)
query = f"""
    SELECT
        DayOfWeek, competition_distance, store_enrolled_in_promo2,
        is_school_holiday, is_state_holiday, baseline_sales_30d,
        lag_7_sales, lag_30_sales, days_since_last_promo,
        StoreType, Assortment
    FROM `{PROJECT_ID}.promo_roi.promo_features`
    WHERE split = 'validation' AND margin_impact IS NOT NULL
    LIMIT 100
"""
df = client.query(query).to_dataframe(create_bqstorage_client=False)

for col in ["StoreType", "Assortment"]:
    df[col] = df[col].astype("category").cat.codes
df["promo_gap_x_baseline"] = df["days_since_last_promo"] * df["baseline_sales_30d"]
df["competition_x_storetype"] = df["competition_distance"] * df["StoreType"]

with open("batch_input.jsonl", "w") as f:
    for _, row in df.iterrows():
        f.write(json.dumps(row.tolist()) + "\n")

print(f"Wrote {len(df)} rows to batch_input.jsonl")