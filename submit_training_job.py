"""Submit a Vertex AI Custom Training Job for the Promo ROI model."""

from google.cloud import aiplatform

# Configuration
PROJECT_ID = "promo-roi-platform-2026"
REGION = "us-central1"
BUCKET = "promo-roi-platform-2026-data"
IMAGE_URI = "us-central1-docker.pkg.dev/promo-roi-platform-2026/ml-repo/promo-training:v8"
SERVICE_ACCOUNT = "vertex-training-sa@promo-roi-platform-2026.iam.gserviceaccount.com"

def submit_job():
    # Initialize Vertex AI SDK
    aiplatform.init(
        project=PROJECT_ID,
        location=REGION,
        staging_bucket=f"gs://{BUCKET}",
    )

    job = aiplatform.CustomContainerTrainingJob(
        display_name="promo-roi-training-v8",
        container_uri=IMAGE_URI,
    )

    print(f"Submitting training job...")
    print(f"Image: {IMAGE_URI}")

    model = job.run(
        machine_type="n1-standard-4",
        replica_count=1,
        service_account=SERVICE_ACCOUNT,
        environment_variables={
            "PROJECT_ID": PROJECT_ID,
            "GCS_BUCKET": BUCKET,
            "DATASET_ID": "promo_roi",
            "TABLE_ID": "promo_features",
            "EXPERIMENT_NAME": "promo-roi-xgboost",
            "MLFLOW_ARTIFACT_URI": f"gs://{BUCKET}/mlflow/artifacts",
        },
        sync=True,  # wait for job to complete before returning
    )

    print("Training job complete.")
    return model

if __name__ == "__main__":
    submit_job()