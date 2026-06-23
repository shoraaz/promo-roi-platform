"""Undeploy all models from the mini-exercise Endpoint to stop
ongoing billing. Run once you're done reviewing the exercise."""

from google.cloud import aiplatform

aiplatform.init(project="promo-roi-platform-2026", location="us-central1")

endpoint = aiplatform.Endpoint(
    "projects/949988804732/locations/us-central1/endpoints/1926863891107676160"
)

for dm in endpoint.gca_resource.deployed_models:
    print(f"Undeploying {dm.id} ({dm.display_name})...")
    endpoint.undeploy(deployed_model_id=dm.id, sync=True)

print("All models undeployed.")