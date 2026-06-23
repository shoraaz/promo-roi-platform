<div align="center">

# 🏪 Promo ROI Platform

**End-to-end MLOps platform that predicts promotional sales lift and margin impact for FMCG retail stores — trained on GCP Vertex AI, served on GKE, monitored with Prometheus/Grafana.**

[![Python](https://img.shields.io/badge/Python-3.14-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![GCP](https://img.shields.io/badge/Cloud-GCP-4285F4?style=flat&logo=google-cloud&logoColor=white)](https://cloud.google.com/)
[![XGBoost](https://img.shields.io/badge/ML-XGBoost-orange?style=flat)](https://xgboost.readthedocs.io/)
[![FastAPI](https://img.shields.io/badge/Serving-FastAPI-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat)](LICENSE)
[![Demo](https://img.shields.io/badge/Live%20Demo-Vercel-black?style=flat&logo=vercel&logoColor=white)](https://promo-roi.vercel.app)

</div>

---

## 🚀 Live Demo

> **[→ View the interactive demo on Vercel](https://promo-roi.vercel.app)**

An interactive dashboard showcasing the platform's capabilities — live architecture diagram, model metrics, and a promotion ROI prediction simulator. No GCP account needed.

---

## What This Project Does

A retail merchandising team runs dozens of promotions per week. Before this system, approvals were gut-feel decisions. After: a structured ROI verdict — `POSITIVE_ROI` or `NEGATIVE_ROI` — backed by a multi-output XGBoost model that predicts both **sales lift %** and **margin impact**, plus SHAP-driven explanations for each decision.

The entire pipeline — from raw BigQuery data to a live GKE endpoint with drift detection and CI/CD — is production-grade and battle-tested.

---

## System Architecture

```
BigQuery (raw sales/promo data)
        │
        ▼
┌─────────────────────────────────┐
│  Vertex AI Pipelines (KFP v2)   │  ← feature engineering, train, evaluate, register
│  · Data validation              │
│  · XGBoost multi-output train   │
│  · Optuna hyperparameter tuning │
│  · SHAP feature validation      │
│  · Evidently drift check        │
└────────────────┬────────────────┘
                 │  model artifact → GCS
                 ▼
┌─────────────────────────────────┐
│  GKE Autopilot (serving)        │
│  · FastAPI + Uvicorn            │
│  · Pydantic v2 validation       │
│  · Prometheus /metrics endpoint │
│  · HPA (CPU-based autoscaling)  │
└────────────────┬────────────────┘
                 │
        ┌────────┴────────┐
        ▼                 ▼
  Grafana dashboards   Evidently
  (latency, preds)     drift reports
```

**CI/CD:** Cloud Build triggers on every push → builds Docker images with SHA tags → deploys to GKE via `kubectl rollout`.

---

## Key Features

- **Multi-output prediction** — single XGBoost model predicts `sales_lift_pct` and `margin_impact` simultaneously
- **SHAP explanations** — every prediction includes top contributing features with impact values
- **Optuna tuning** — automated hyperparameter search logged to MLflow
- **Drift detection** — Evidently AI compares current feature distributions against training baseline
- **Kubeflow Pipelines** — reproducible, cacheable training pipeline as code
- **Workload Identity** — GKE pods access GCS/BigQuery without service account key files
- **Prometheus + Grafana** — request count, latency histograms, prediction distribution metrics

---

## Project Structure

```
promo-roi-platform/
├── training/               # Vertex AI custom training job (Docker)
│   ├── Dockerfile
│   ├── train.py            # XGBoost multi-output trainer
│   └── requirements.txt
├── serving/                # FastAPI inference server (Docker)
│   ├── Dockerfile
│   ├── app.py              # /predict, /health, /metrics endpoints
│   ├── model_utils.py      # GCS model loading, feature engineering
│   └── schemas.py          # Pydantic request/response models
├── pipelines/              # Kubeflow Pipeline definitions (KFP v2)
├── k8s/                    # Kubernetes manifests (Deployment, Service, Ingress, HPA)
├── tests/                  # pytest suite
├── data/                   # Local data samples / schemas
├── demo/                   # Interactive demo app (Next.js → deployed on Vercel)
├── mlflow_local/           # Local MLflow tracking server config
├── check_drift.py          # Standalone Evidently drift report
├── check_shap_importance.py # Standalone SHAP feature importance
├── submit_training_job.py  # Trigger Vertex AI Custom Training Job
├── submit_tuning_job.py    # Trigger Optuna tuning job on Vertex AI
├── load_test.py            # Locust-style load test against /predict
├── cloudbuild.yaml         # Cloud Build CI/CD pipeline
└── pyproject.toml          # uv-managed Python project config
```

---

## Quick Start

### Prerequisites

- Python 3.14+ with [`uv`](https://github.com/astral-sh/uv)
- GCP project with these APIs enabled: **Vertex AI, GKE, BigQuery, Artifact Registry, GCS, Cloud Build**
- Authenticated CLI: `gcloud auth application-default login`

### 1. Clone & install

```bash
git clone https://github.com/shoraaz/promo-roi-platform.git
cd promo-roi-platform
uv sync
```

### 2. Run training locally (Docker)

```bash
docker build -t promo-training ./training
docker run --rm \
  -v ~/.config/gcloud:/root/.config/gcloud \
  promo-training
```

### 3. Submit to Vertex AI

```bash
# Custom Training Job
uv run python submit_training_job.py

# Optuna hyperparameter tuning
uv run python submit_tuning_job.py
```

### 4. Validate the model

```bash
# SHAP feature importance
uv run python check_shap_importance.py

# Evidently drift report
uv run python check_drift.py
```

### 5. Run the test suite

```bash
uv run pytest tests/ -v
```

---

## API Reference

### `POST /predict`

Predict sales lift and ROI verdict for a proposed promotion.

```json
// Request
{
  "store_id": 42,
  "promo_type": "Promo2",
  "baseline_sales_30d": 8500.0,
  "competition_distance": 1200,
  "days_since_last_promo": 21,
  "store_type": "A",
  "month": 11
}

// Response
{
  "sales_lift_pct": 14.7,
  "margin_impact": 312.5,
  "verdict": "POSITIVE_ROI",
  "top_factors": [
    {"feature": "baseline_sales_30d",               "shap_value": 124.3},
    {"feature": "days_since_last_promo_x_baseline", "shap_value":  89.1},
    {"feature": "month_cos",                        "shap_value": -41.2}
  ]
}
```

### `GET /health`

Returns `200 OK` with service status and loaded model version.

### `GET /metrics`

Prometheus-format scrape endpoint — request counts, latency histogram, prediction distribution.

---

## Engineering Documentation

Detailed engineering notes for this project — decisions made, bugs hit, and tradeoffs — are kept locally and not published in this repo. The README and inline code comments serve as the primary reference for reviewers.

---

## Tech Stack

| Layer | Tools |
|-------|-------|
| **ML / Training** | XGBoost (multi-output), Optuna, SHAP, Evidently AI, MLflow |
| **Serving** | FastAPI, Pydantic v2, Uvicorn, Docker |
| **Cloud** | GCP: Vertex AI, GKE Autopilot, BigQuery, GCS, Artifact Registry, Cloud Build |
| **Orchestration** | Kubeflow Pipelines (KFP v2), Vertex AI Pipelines |
| **Kubernetes** | Deployments, Services, Ingress, HPA, Workload Identity |
| **Monitoring** | Prometheus, Grafana |
| **Dev Tooling** | uv, Ruff, Black, pytest |
| **Demo** | Next.js 14, Tailwind CSS, Vercel |

---

## Honest Limitations

This project is built to understand the real tradeoffs — not to paper over them.

- **No feedback loop.** Predictions are never reconciled against realized outcomes. A true production system would close this loop with a delayed label ingestion pipeline.
- **Drift detection uses a fixed historical split**, not genuinely live, continuously-arriving traffic. This is a meaningful gap from production behavior.
- **Cloud Build rebuilds both images on every push** regardless of which changed. Path-filtered triggers would fix this; accepted as an acceptable inefficiency at this scale.

---

## License

MIT — see [LICENSE](LICENSE).

---

<div align="center">
Built by <a href="https://github.com/shoraaz">@shoraaz</a> · Delhi, India
</div>
