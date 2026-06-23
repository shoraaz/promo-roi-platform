# mini_exercise/register_model.py
from google.cloud import aiplatform

PROJECT_ID = "promo-roi-platform-2026"
REGION = "us-central1"
BUCKET = "promo-roi-platform-2026-data"

aiplatform.init(project=PROJECT_ID, location=REGION)

model = aiplatform.Model.upload(
    display_name="margin-impact-mini-exercise",
    artifact_uri=f"gs://{BUCKET}/mini-exercise/model-registry/",
    serving_container_image_uri="us-docker.pkg.dev/vertex-ai/prediction/xgboost-cpu.1-7:latest",
    sync=True,
)

print(f"Model registered: {model.resource_name}")