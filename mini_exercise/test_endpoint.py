# mini_exercise/test_endpoint.py
from google.cloud import aiplatform

PROJECT_ID = "promo-roi-platform-2026"
REGION = "us-central1"
ENDPOINT_RESOURCE_NAME = "projects/949988804732/locations/us-central1/endpoints/1926863891107676160"

aiplatform.init(project=PROJECT_ID, location=REGION)

endpoint = aiplatform.Endpoint(ENDPOINT_RESOURCE_NAME)

# Feature order MUST match training exactly:
# DayOfWeek, competition_distance, store_enrolled_in_promo2,
# is_school_holiday, is_state_holiday, baseline_sales_30d,
# lag_7_sales, lag_30_sales, days_since_last_promo
DayOfWeek = 5.0
competition_distance = 1270.0
store_enrolled_in_promo2 = 0.0
is_school_holiday = 1.0
is_state_holiday = 0.0
baseline_sales_30d = 4835.0
lag_7_sales = 7176.0
lag_30_sales = 7176.0
days_since_last_promo = 999.0
StoreType = 2.0
Assortment = 0.0
promo_gap_x_baseline = days_since_last_promo * baseline_sales_30d
competition_x_storetype = competition_distance * StoreType

instance = [
    DayOfWeek, competition_distance, store_enrolled_in_promo2,
    is_school_holiday, is_state_holiday, baseline_sales_30d,
    lag_7_sales, lag_30_sales, days_since_last_promo,
    StoreType, Assortment, promo_gap_x_baseline, competition_x_storetype,
]

prediction = endpoint.predict(instances=[instance])
print(f"Prediction: {prediction}")
