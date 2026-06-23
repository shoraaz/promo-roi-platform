# mini_exercise/submit_batch_job.py
from google.cloud import aiplatform

PROJECT_ID = "promo-roi-platform-2026"
REGION = "us-central1"
MODEL_RESOURCE_NAME = "projects/949988804732/locations/us-central1/models/3149811092264321024"  # the FIXED model

aiplatform.init(project=PROJECT_ID, location=REGION)

model = aiplatform.Model(MODEL_RESOURCE_NAME)

batch_job = model.batch_predict(
    job_display_name="margin-impact-batch-mini-exercise",
    gcs_source="gs://promo-roi-platform-2026-data/mini-exercise/batch-input/batch_input.jsonl",
    gcs_destination_prefix="gs://promo-roi-platform-2026-data/mini-exercise/batch-output/",
    machine_type="n1-standard-2",
    sync=True,
)

print(f"Batch job: {batch_job.resource_name}")