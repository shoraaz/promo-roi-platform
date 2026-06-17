"""Submit the real training pipeline to Vertex AI."""

from google.cloud import aiplatform

PROJECT_ID = "promo-roi-platform-2026"
REGION = "us-central1"
PIPELINE_ROOT = "gs://promo-roi-platform-2026-data/pipeline-runs"

aiplatform.init(project=PROJECT_ID, location=REGION)

job = aiplatform.PipelineJob(
    display_name="promo-roi-training-pipeline",
    template_path="pipelines/promo_pipeline.yaml",
    pipeline_root=PIPELINE_ROOT,
)

job.run(sync=True)