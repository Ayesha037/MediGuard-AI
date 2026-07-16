<div align="center">

# 🛡️ MediGuard AI

**Predictive maintenance for hospital medical equipment — powered by explainable ML.**

MediGuard AI doesn't predict diseases. It predicts *equipment failures* — before a ventilator, MRI scanner, infusion pump, or patient monitor goes down and puts a patient's care at risk.

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-TypeScript-61DAFB?logo=react&logoColor=black)](https://react.dev/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)
[![CI](https://img.shields.io/badge/CI-GitHub_Actions-2088FF?logo=githubactions&logoColor=white)](https://github.com/Ayesha037/MediGuard-AI/actions)
[![License](https://img.shields.io/badge/License-MIT-lightgrey.svg)](#license)

[Live Demo](#-quick-start) · [Documentation](#-documentation) · [API Reference](#-api-reference) · [Model Details](#-the-ml-pipeline)

</div>

---

## 📸 See it in action

<table>
<tr>
<td width="50%">

**Hospital-wide health at a glance**
Real-time risk ranking, critical device counts, and unacknowledged alerts — all on one screen.

</td>
<td width="50%">

**Live sensor telemetry**
100 devices streaming temperature, vibration, battery, and voltage over WebSocket.

</td>
</tr>
</table>

> 💡 *Add your screenshots here — drop them in `docs/screenshots/` and reference them like:*
> `![Overview Dashboard](docs/screenshots/overview.png)`
> *(Lead with the Overview and Live Monitoring views — they sell the project in one glance.)*

---

## 🩺 The problem

Hospitals run thousands of dollars of critical equipment per bed, and most maintenance is still **reactive or calendar-based** — engineers find out a ventilator failed *after* it fails, or service equipment on a fixed schedule regardless of actual condition. Both approaches are expensive, and the first one is dangerous.

**MediGuard AI flips that model**: it continuously scores every device's failure risk from live sensor telemetry, tells biomedical engineering teams *why* a device is at risk in plain language, and surfaces the devices that need attention — before they become an emergency.

---

## ✨ Features

| | |
|---|---|
| 🏥 **Equipment Inventory** | Full device registry — manufacturer, department, warranty, lifespan, searchable and filterable |
| 📡 **Live Monitoring** | Real-time telemetry over WebSocket across 100 simulated devices, instrument-panel styled |
| 🤖 **AI Failure Prediction** | Failure probability (Low / Medium / High), Remaining Useful Life, 7/30/90-day risk windows |
| 🔍 **Explainable AI** | SHAP-based "top 5 reasons this device may fail" — no black-box scores |
| 🛠️ **Maintenance Recommendations** | Actionable, auditable, rule-based on risk + subsystem |
| 👥 **Digital Twin** | Per-device page: sensor history, prediction history, risk trend, maintenance/failure log |
| 📊 **Analytics** | Hospital-wide trends, department comparison, manufacturer comparison, monthly failure trends |
| 🚨 **Smart Alerts** | Threshold-based, acknowledgeable, prioritized by severity |
| 💬 **AI Chat Assistant** | Ask natural-language questions about devices, maintenance, or alerts — grounded in live API data |
| 🏆 **Equipment Ranking** | Healthiest to most critical, hospital-wide |

---

## 🏗️ Architecture

```
                        ┌─────────────────────┐
                        │   React Frontend     │
                        │  (TS · Tailwind ·     │
                        │  Recharts · Framer)   │
                        └──────────┬────────────┘
                                   │ REST + WebSocket
                        ┌──────────▼────────────┐
                        │   FastAPI Backend      │
                        │  (devices · telemetry  │
                        │   alerts · analytics)  │
                        └──────────┬────────────┘
                                   │
                     ┌─────────────┼─────────────┐
                     │                            │
          ┌──────────▼──────────┐      ┌─────────▼──────────┐
          │     PostgreSQL       │      │   Model Service     │
          │  (device state,      │      │  (standalone API,   │
          │   history, alerts)   │      │   XGBoost/LightGBM, │
          └───────────────────────┘      │   SHAP, own auth)   │
                                          └──────────────────────┘
```

This repo ships **three independently deployable pieces**:

| Component | Stack | Purpose |
|---|---|---|
| [`backend/`](./backend) | FastAPI + SQLAlchemy + PostgreSQL | The full application API — devices, telemetry, alerts, analytics |
| [`frontend/`](./frontend) | React + TypeScript + Tailwind + Recharts | The dashboard shown above |
| [`model-service/`](./model-service) | FastAPI, API-key auth, rate limiting, health probes | Prediction-only microservice, no database, deployable standalone on Render/Railway/Fly/AWS/GCP/Azure |

Splitting the model into its own service means the ML layer can scale, deploy, and version **independently** of the rest of the platform — the same pattern you'd use to put a model behind a stable internal API in a real hospital IT environment.

---

## 🚀 Quick start

### With Docker (recommended)

```bash
git clone https://github.com/Ayesha037/MediGuard-AI.git
cd MediGuard-AI
docker compose up --build
```

Then, in a separate terminal, seed the database and train the models (one-time):

```bash
docker compose exec backend python -m app.ml.data_ingestion --csv-dir /path/to/csvs
docker compose exec backend python -m app.ml.train
docker compose exec backend python -m app.ml.backfill_predictions
```

| Service | URL |
|---|---|
| 🖥️ Frontend | http://localhost:5173 |
| ⚙️ Backend API (Swagger) | http://localhost:8000/docs |
| 🧠 Model Service (standalone) | see [`model-service/README.md`](./model-service/README.md) |

Full setup guide (Docker and local, no-Docker): [`docs/installation.md`](./docs/installation.md)

---

## 🧠 The ML pipeline

| Stage | Details |
|---|---|
| **Models** | XGBoost, LightGBM, Isolation Forest (anomaly detection) |
| **Explainability** | SHAP values surfaced per-prediction as human-readable reasons |
| **Targets** | Failure probability, Remaining Useful Life (RUL), 7/30/90-day failure windows |
| **Validation** | Trained and evaluated end-to-end against a full-year, 100-device telemetry dataset |

Full model card — training methodology, feature engineering, and **honest performance numbers** — is in [`docs/model_documentation.md`](./docs/model_documentation.md).

### A note on data — read this before you judge the numbers

Real hospital equipment failure data isn't publicly available (liability and privacy reasons — as you'd expect). This project uses the **Microsoft Azure Predictive Maintenance dataset** (100 industrial machines, hourly telemetry, error logs, maintenance records, and failure events over one year) and the **AI4I 2020 Predictive Maintenance dataset**, relabeled into a medical-equipment vocabulary.

That means: the pipeline, architecture, and explainability layer are production-grade — but the specific probabilities are **simulation-grade, not clinically validated**. This is a deliberate, disclosed tradeoff, not an oversight. The full mapping and its implications are documented transparently in [`docs/model_documentation.md`](./docs/model_documentation.md).

---

## 📁 Documentation

| Doc | Covers |
|---|---|
| [`docs/architecture.md`](./docs/architecture.md) | System architecture, ER diagram, folder structure |
| [`docs/installation.md`](./docs/installation.md) | Full setup guide (Docker and local) |
| [`docs/api.md`](./docs/api.md) | API reference |
| [`docs/model_documentation.md`](./docs/model_documentation.md) | Model training, evaluation, honest limitations |
| [`docs/future_improvements.md`](./docs/future_improvements.md) | Known gaps and roadmap |
| [`model-service/README.md`](./model-service/README.md) | Standalone prediction service — deploy configs, API, auth |

---

## 🧪 Testing & CI

```bash
docker compose exec backend pytest
docker compose exec model-service pytest
```

Every push runs the full suite via GitHub Actions — see [`.github/workflows`](./.github/workflows).

---

## 🗺️ Roadmap

- [ ] Role-based access control on the dashboard
- [ ] Integration adapter for real CMMS (computerized maintenance management systems)
- [ ] Model calibration report + confidence intervals on predictions
- [ ] Hosted one-click demo (no local Docker required)

Full list: [`docs/future_improvements.md`](./docs/future_improvements.md)

---

## ⚠️ Disclaimer

MediGuard AI is a portfolio / research project. It is **not** a certified medical device, has **not** undergone clinical validation, and is **not** intended for use in production hospital environments without substantial further validation, real-world data, and regulatory review.

---

## 📄 License

MIT — see [`LICENSE`](./LICENSE) for details.

---

<div align="center">

Built by [Ayesha037](https://github.com/Ayesha037) — feedback and PRs welcome.

</div>
