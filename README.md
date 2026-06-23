
---

## 🚀 Quick Start

### Prerequisites

- Python 3.14+ with [`uv`](https://github.com/astral-sh/uv)
- GCP project with Vertex AI, GKE, BigQuery, Artifact Registry, GCS enabled
- `gcloud` CLI authenticated: `gcloud auth application-default login`

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
uv run python submit_training_job.py
```

### 4. Check feature importance

```bash
uv run python check_shap_importance.py
```

### 5. Run drift detection

```bash
uv run python check_drift.py
```

### 6. Run tests

```bash
uv run pytest tests/
```

---

## 📡 API Reference

### `POST /predict`

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

Returns `200 OK` with service status and model version.

### `GET /metrics`

Prometheus-format metrics endpoint — request count, latency histogram, prediction distribution.

---

## 📚 Documentation

Each phase has a detailed writeup in [`docs/`](docs/) — real bugs encountered, root causes diagnosed, fixes applied. Not idealized walkthroughs.

| # | Phase | Key Topics |
|---|---|---|
| 01 | Data Layer | BigQuery schema, label engineering, feature SQL |
| 02 | Docker | Multi-stage builds, layer caching strategy |
| 03 | Vertex AI Training | Custom Training Jobs, the v6/v7 mistagging bug |
| 04 | GKE Deployment | Workload Identity, probes, the SIGKILL incident |
| 05 | Kubernetes Advanced | HPA, Ingress, Helm constraints on Autopilot |
| 06 | Vertex AI Pipelines | KFP components, caching, artifact passing |
| 07 | CI/CD | Cloud Build, SHA-tagging, dedicated-service-account pattern |
| 08 | Monitoring | Prometheus/Grafana, histogram mechanics, debugging detours |
| 09 | Model Improvement | Optuna tuning, SHAP-validated features, Evidently drift (3 parts) |
| 10 | Mini-Exercise | Vertex AI Model Registry, Endpoints, Batch Prediction, Monitoring |
| 11 | End-to-End Map | Full lifecycle trace, recurring architectural patterns named explicitly |

---

## ⚠️ Known Limitations (Honestly Stated)

- **No ground-truth feedback loop.** Predictions are never compared against realized outcomes — a genuine production system would close this loop.
- **Cloud Build rebuilds both images on every push** regardless of which changed. Path-filtered triggers would fix this at scale; accepted as an inefficiency here.
- **Drift detection uses a fixed historical split**, not genuinely live, continuously-arriving production traffic.
- **Learning-to-rank (LambdaMART) was scoped but deferred.** Ranking is a meaningfully different problem formulation — shipping a half-understood version would weaken an otherwise consistently well-understood project.

---

## 🛠️ Tech Stack

| Category | Tools |
|---|---|
| **ML / Training** | XGBoost (multi-output), Optuna, SHAP, Evidently AI, MLflow |
| **Serving** | FastAPI, Pydantic, Uvicorn, Docker |
| **Cloud** | GCP: Vertex AI, GKE Autopilot, BigQuery, GCS, Artifact Registry, Cloud Build |
| **Orchestration** | Kubeflow Pipelines (KFP v2), Vertex AI Pipelines |
| **Kubernetes** | Deployments, Services, Ingress, HPA, Workload Identity |
| **Monitoring** | Prometheus, Grafana |
| **Dev tooling** | uv, Ruff, Black, pytest |

---

## 📄 License

MIT — see [LICENSE](LICENSE).

---

<div align="center">
Built by <a href="https://github.com/shoraaz">@shoraaz</a> · Delhi, India
</div>
