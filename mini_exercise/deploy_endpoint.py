# mini_exercise/deploy_endpoint.py
from google.cloud import aiplatform

PROJECT_ID = "promo-roi-platform-2026"
REGION = "us-central1"
MODEL_RESOURCE_NAME = "projects/949988804732/locations/us-central1/models/3149811092264321024"
ENDPOINT_RESOURCE_NAME = "projects/949988804732/locations/us-central1/endpoints/1926863891107676160"

aiplatform.init(project=PROJECT_ID, location=REGION)

model = aiplatform.Model(MODEL_RESOURCE_NAME)
endpoint = aiplatform.Endpoint(ENDPOINT_RESOURCE_NAME)

endpoint.deploy(
    model=model,
    deployed_model_display_name="margin-impact-mini-endpoint-v2",
    machine_type="n1-standard-2",
    min_replica_count=1,
    max_replica_count=1,
    sync=True,
)

print(f"Deployed to endpoint: {endpoint.resource_name}")