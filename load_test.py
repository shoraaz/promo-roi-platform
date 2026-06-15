"""Simple concurrent load test against the promo-serving API."""

import time
import requests
from concurrent.futures import ThreadPoolExecutor

URL = "http://35.253.184.68/predict"

PAYLOAD = {
    "store_id": 1,
    "DayOfWeek": 5,
    "competition_distance": 1270,
    "store_enrolled_in_promo2": 0,
    "is_school_holiday": 1,
    "is_state_holiday": 0,
    "baseline_sales_30d": 4835.0,
    "lag_7_sales": 7176,
    "lag_30_sales": 7176,
    "days_since_last_promo": 999,
    "StoreType": 2,
    "Assortment": 0,
}

DURATION_SECONDS = 120
CONCURRENCY = 20


def send_request(_):
    try:
        r = requests.post(URL, json=PAYLOAD, timeout=10)
        return r.status_code
    except Exception as e:
        return f"error: {e}"


def main():
    print(f"Load testing {URL} for {DURATION_SECONDS}s with {CONCURRENCY} concurrent workers...")
    end_time = time.time() + DURATION_SECONDS
    total_requests = 0
    status_counts = {}

    with ThreadPoolExecutor(max_workers=CONCURRENCY) as executor:
        while time.time() < end_time:
            results = list(executor.map(send_request, range(CONCURRENCY)))
            total_requests += len(results)
            for status in results:
                status_counts[status] = status_counts.get(status, 0) + 1
            print(f"Total requests: {total_requests} | Status counts: {status_counts}")

    print("\nDone.")
    print(f"Total requests: {total_requests}")
    print(f"Status counts: {status_counts}")


if __name__ == "__main__":
    main()