# FMCG Promotion ROI Intelligence Platform

A production-style MLOps platform that predicts whether a planned retail promotion will generate positive or negative ROI, deployed end-to-end on GCP with dual-pathway infrastructure, full CI/CD automation, live monitoring, and a validated, three-layer model improvement story.

**Built for:** ML Engineer (FAANG L4/L5) interview preparation
**Cloud:** Google Cloud Platform (`promo-roi-platform-2026`, `us-central1`)
**Dataset:** Rossmann Store Sales (Kaggle) — 376,875 promo-eligible rows across 3 years, 140 stores

---

## What This Project Demonstrates

This is not a notebook that trains a model and stops. It's a working system: data lands in BigQuery, gets trained on Vertex AI, serves live predictions from a GKE cluster behind an autoscaling Kubernetes deployment, gets continuously rebuilt and redeployed by Cloud Build on every push, and is observed in real time by a Prometheus/Grafana stack — with every claimed improvement backed by a verification step, not just a reported number.

```
BigQuery (features) -> Vertex AI (training) -> GCS (artifacts)
                                                      |
                                                      v
GitHub push -> Cloud Build -> Artifact Registry -> GKE (serving)
                                                      |
                                                      v
                                          Prometheus -> Grafana (monitoring)
```

---

## The Business Problem

FMCG companies spend a significant share of revenue on trade promotions, and a large fraction of them lose money once discount cost is netted against the sales lift they generate. This project predicts, for a given store/promo scenario, two things simultaneously:

- **`sales_lift_pct`** — how much sales increase the promotion will produce
- **`margin_impact`** — the net profit/loss impact after discount cost, in currency units

A positive/negative `margin_impact` verdict, with a SHAP-based explanation of the top contributing factors, is returned per prediction.

---

## Architecture

**Dual-pathway design**: every core component exists in two forms — GCP-native managed services AND open-source/self-managed equivalents — built deliberately to demonstrate vendor-agnostic system design judgment rather than dependence on one cloud's specific tooling.

| Layer | GCP-Native | Self-Managed / Open-Source |
|---|---|---|
| Compute (training) | Vertex AI Custom Training Jobs | Same Docker image, runnable anywhere |
| Orchestration | Vertex AI Pipelines (KFP) | Kubeflow-compatible SDK, portable |
| Serving | *(see note below)* | GKE + FastAPI + Kubernetes |
| CI/CD | Cloud Build | Portable `cloudbuild.yaml`, GitHub-triggered |
| Monitoring | *(mini-exercise only)* Vertex AI Model Monitoring | Prometheus + Grafana |
| Data drift | *(mini-exercise only)* Vertex AI Model Monitoring | Evidently AI |

**Note on serving:** this project deliberately built serving on GKE rather than Vertex AI Endpoints, prioritizing hands-on Kubernetes depth (Pods, Services, HPA, Ingress, Workload Identity, rolling updates) — directly more relevant to how most large companies' internal ML platforms actually look, even when not literally GKE. A separate, fully hands-on exercise with Vertex AI's managed alternative (Model Registry, Endpoints, Batch Prediction, Model Monitoring) was completed afterward specifically to validate this choice with direct experience of both paths, not just from documentation. See `10_mini_exercise_vertex_ai_managed_services.md`.

---

## Results — Model Improvement, Three Validated Layers

Every number below was independently reproduced through the standard training pipeline (not just reported from a tuning script), and the overall accuracy ceiling was checked against a real alternative explanation (train/validation data drift) before being accepted as a genuine modeling limit.

| | Baseline | + Hyperparameter Tuning (Optuna) | + Interaction Features (SHAP-validated) | + Seasonality (cyclical month encoding) |
|---|---|---|---|---|
| **margin_impact RMSE** | 271.70 | 258.81 | 256.66 | **240.99** |
| **margin_impact R²** | 0.632 | 0.666 | 0.672 | **0.711** |
| **sales_lift_pct RMSE** | 22.13 | 20.87 | 21.99* | **19.85** |
| **sales_lift_pct R²** | 0.433 | 0.496 | 0.440* | **0.544** |

*sales_lift_pct received interaction features but not hyperparameter tuning at that stage — isolating the features' effect cleanly, since this target's R² still improved with zero other changes.

**Total improvement:** margin_impact -11.3% RMSE / +0.079 R²; sales_lift_pct -10.3% RMSE / +0.111 R².

### What Each Layer Actually Contributed (Not Just "It Helped")

- **Seasonality (largest single contribution):** cyclical `month_sin`/`month_cos` encoding, added because raw month numbers wrongly treat December and January as maximally different. SHAP analysis confirmed it ranks 6th-7th of 15 features — and notably, adding it caused `days_since_last_promo` to DROP in relative importance, evidence the model had been using that feature as an indirect seasonal proxy before a cleaner direct signal was available.
- **Hyperparameter tuning (Optuna, 50-trial Bayesian search per target):** found that both targets consistently benefit from deeper trees (max_depth 9-10, vs. original default of 6) and lower `colsample_bytree` (~0.6-0.65, vs. 0.8) — a consistent cross-target pattern, not a coincidence specific to one run.
- **Interaction features (hypothesis-driven, SHAP-validated):** `days_since_last_promo × baseline_sales_30d` (hypothesis: promo timing's effect scales with store size) ranked 3rd of 13 features — strongly validated. `competition_distance × StoreType` (hypothesis: competitive pressure affects store formats differently) ranked 11th — only weakly supported. Both hypotheses were tested; only one held up under scrutiny, and that distinction is reported honestly rather than only mentioning the win.
- **Drift detection (Evidently AI, PSI method):** confirmed across all 11 original features that the training and validation periods show no meaningful distribution shift (highest PSI = 0.039, threshold = 0.10) — ruling out train/test mismatch as an alternative explanation for the model's remaining error.

---

## Infrastructure Highlights

- **GKE Autopilot serving**, with a full Workload Identity chain (KSA ↔ GSA binding), a `startupProbe`/`livenessProbe` split fixed after a real production-pattern incident (a new Pod was SIGKILLed during a load test because `initialDelaySeconds` was too short for cold-start GCS model loading under concurrent CPU contention).
- **HPA-driven autoscaling**, load-tested with 1,720/1,720 requests succeeding across a real 2-to-3 replica scaling event.
- **Full CI/CD loop**: a `git push` to `main` triggers Cloud Build, which builds and SHA-tags both training and serving images, pushes to Artifact Registry, and runs `kubectl set image` to trigger a zero-downtime rolling deployment — verified end-to-end multiple times.
- **Vertex AI Pipelines**: a real 3-component DAG (load → train → evaluate) wrapping the same training code used standalone, with live-observed caching behavior (identical inputs skip re-execution) and metrics reproduced to 4 decimal places against the standalone script's baseline.
- **Prometheus + Grafana**, hand-deployed (not the bundled `kube-prometheus-stack`, which hits real permission blockers on GKE Autopilot) and scraping a Prometheus-instrumented FastAPI service, visualized in a live 3-panel dashboard.

---

## Repository Structure

```
training/        Training entrypoint, tuning script, feature definitions, Dockerfile
serving/          FastAPI serving app, model registry loader, Pydantic schemas, Dockerfile
pipelines/        Vertex AI Pipeline definitions (KFP components + compiled YAML)
k8s/               Deployment, Service, Ingress, HPA, Prometheus manifests
mini_exercise/      Vertex AI Model Registry / Endpoints / Batch Prediction / Monitoring
cloudbuild.yaml     CI/CD pipeline definition
check_drift.py       Evidently AI drift detection script
check_shap_importance.py   Standalone SHAP feature-importance verification utility
```

---

## Documentation

Each phase of the build has a corresponding detailed writeup, including real bugs hit, root causes diagnosed, and fixes applied — not idealized walkthroughs:

1. Data Layer — BigQuery, label/feature engineering
2. Docker — multi-stage builds, layer caching
3. Vertex AI Training — Custom Training Jobs, the v6/v7 mistagging bug
4. GKE Deployment — Workload Identity, probes, the SIGKILL incident
5. Kubernetes Advanced — HPA, Ingress, Helm on Autopilot's constraints
6. Vertex AI Pipelines — KFP components, caching, artifact passing
7. CI/CD — Cloud Build, SHA-tagging, the dedicated-service-account pattern (×3)
8. Monitoring — Prometheus/Grafana, histogram mechanics, debugging detours
9. Model Improvement (3 parts) — Optuna tuning, SHAP-validated features, Evidently drift
10. Mini-Exercise — Vertex AI Model Registry / Endpoints / Batch Prediction / Monitoring
11. End-to-End Map — full lifecycle trace, recurring architectural patterns named explicitly

---

## Known, Honestly-Stated Limitations

- No ground-truth feedback loop: predictions are never compared against realized outcomes after the fact.
- Cloud Build rebuilds both training and serving images on every push regardless of which changed — an accepted inefficiency at this project's scale; path-filtered triggers would fix this in production.
- Drift detection compares a fixed historical train/validation split, not genuinely live, continuously-arriving production traffic.
- A learning-to-rank (LambdaMART) phase was scoped conceptually but deliberately deferred — ranking is a meaningfully different problem formulation, and shipping a half-understood version would weaken, not strengthen, an otherwise consistently well-understood project.
