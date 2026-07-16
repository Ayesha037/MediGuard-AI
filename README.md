# MediGuard AI

**AI-powered predictive maintenance platform for hospital medical equipment.**

MediGuard AI does not predict diseases — it predicts *equipment failures* before they happen, so biomedical engineering teams can act before a ventilator, MRI scanner, infusion pump, or patient monitor goes down.


---

## What's in this repo

| Area | Stack | Status |
|---|---|---|
| Frontend | React + TypeScript + Tailwind + Recharts + Framer Motion | ✅ Working |
| Backend | FastAPI + SQLAlchemy + PostgreSQL | ✅ Working |
| ML Pipeline | XGBoost, LightGBM, Isolation Forest, SHAP | ✅ Trained on real data |
| Standalone Model Service | FastAPI, API-key auth, rate limiting, health probes | ✅ Deployable on its own |
| Deployment | Docker Compose, GitHub Actions CI | ✅ Working |

This repo has three deployable pieces:
- **`backend/`** — the full application API (devices, telemetry, alerts, analytics) backed by PostgreSQL
- **`frontend/`** — the React dashboard
- **`model-service/`** — a separate, standalone prediction-only API (no database) with its own Docker image, auth, and deploy configs for Render/Railway/Fly/AWS/GCP/Azure. Useful if you want the AI model available as its own microservice, independent of the rest of the platform — see [`model-service/README.md`](model-service/README.md).

This is a **working MVP**, trained and verified end-to-end against a real 100-device, full-year telemetry dataset (see [Data Source](#data-source) below) — not a scaffold with mocked data.

## Features

- **Equipment Inventory** — full device registry (manufacturer, department, warranty, lifespan)
- **Live Monitoring Dashboard** — real-time sensor telemetry over WebSocket, instrument-panel styled readouts
- **AI Failure Prediction** — failure probability (Low/Medium/High), remaining useful life, 7/30/90-day failure probability
- **Explainable AI** — SHAP-based "top 5 reasons this device may fail," in plain language
- **Predictive Maintenance Recommendations** — actionable, auditable, rule-based on risk + subsystem
- **Digital Twin** — per-device page: sensor history, prediction history, risk trend, maintenance/failure log
- **Analytics Dashboard** — hospital-wide health, department comparison, manufacturer comparison, monthly failure trends
- **Smart Alerts** — threshold-based, acknowledgeable
- **AI Chat Assistant** — ask about specific devices, maintenance needs, or alerts, grounded in live API data
- **Equipment Ranking** — healthiest to most critical
- **Simulated IoT Data** — realistic live sensor stream layered on top of real historical telemetry

## Quick start

See [`docs/installation.md`](docs/installation.md) for full setup. TL;DR with Docker:

```bash
git clone <this-repo>
cd mediguard-ai
docker compose up --build
```

Then, in a separate terminal, seed the database with real data and train the models (one-time):

```bash
docker compose exec backend python -m app.ml.data_ingestion --csv-dir /path/to/csvs
docker compose exec backend python -m app.ml.train
docker compose exec backend python -m app.ml.backfill_predictions
```

- Frontend: http://localhost:5173
- Backend API docs (Swagger): http://localhost:8000/docs

## Documentation

- [`docs/architecture.md`](docs/architecture.md) — system architecture, ER diagram, folder structure
- [`docs/installation.md`](docs/installation.md) — full setup guide (Docker and local)
- [`docs/api.md`](docs/api.md) — API reference
- [`docs/model_documentation.md`](docs/model_documentation.md) — what the models are, how they were trained, honest performance numbers
- [`docs/future_improvements.md`](docs/future_improvements.md) — known gaps and what's next
- [`model-service/README.md`](model-service/README.md) — standalone prediction service: deploy configs, API reference, auth setup

## Data source

Real hospital equipment failure data isn't publicly available (liability/privacy). This project uses the **Microsoft Azure Predictive Maintenance dataset** (100 industrial machines, hourly telemetry, error logs, maintenance records, and failure events over one year) and the **AI4I 2020 Predictive Maintenance dataset**, relabeled into a medical-equipment vocabulary — see [`docs/model_documentation.md`](docs/model_documentation.md) for the full mapping and an honest discussion of what this means for model quality.

