"""Submit a Vertex AI Custom Training Job to run Optuna hyperparameter tuning."""

from google.cloud import aiplatform

PROJECT_ID = "promo-roi-platform-2026"
REGION = "us-central1"
BUCKET = "promo-roi-platform-2026-data"
IMAGE_URI = "us-central1-docker.pkg.dev/promo-roi-platform-2026/ml-repo/promo-training:v9"
SERVICE_ACCOUNT = "vertex-training-sa@promo-roi-platform-2026.iam.gserviceaccount.com"


def submit_job():
    aiplatform.init(
        project=PROJECT_ID,
        location=REGION,
        staging_bucket=f"gs://{BUCKET}",
    )

    job = aiplatform.CustomContainerTrainingJob(
        display_name="promo-roi-tuning-v9",
        container_uri=IMAGE_URI,
        command=["python", "tune.py"],  # override default CMD (train.py)
    )

    print("Submitting tuning job...")
    print(f"Image: {IMAGE_URI}")
    print("Command: python tune.py")

    job.run(
        machine_type="n1-standard-4",
        replica_count=1,
        service_account=SERVICE_ACCOUNT,
        environment_variables={
            "PROJECT_ID": PROJECT_ID,
            "GCS_BUCKET": BUCKET,
            "DATASET_ID": "promo_roi",
            "TABLE_ID": "promo_features",
        },
        sync=True,
    )

    print("Tuning job complete.")


if __name__ == "__main__":
    submit_job()
    