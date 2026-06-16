"""Submit the compiled pipeline to Vertex AI Pipelines."""

from google.cloud import aiplatform

PROJECT_ID = "promo-roi-platform-2026"
REGION = "us-central1"
PIPELINE_ROOT = "gs://promo-roi-platform-2026-data/pipeline-runs"

aiplatform.init(project=PROJECT_ID, location=REGION)

job = aiplatform.PipelineJob(
    display_name="promo-roi-hello-pipeline",
    template_path="pipelines/hello_pipeline_v3.yaml",
    pipeline_root=PIPELINE_ROOT,
    parameter_values={"name": "Ram"},
)

job.run(sync=True)