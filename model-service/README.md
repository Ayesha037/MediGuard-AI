# MediGuard AI — Prediction Service

A standalone, production-ready API that serves the trained MediGuard failure-prediction models. Deploy it anywhere that runs a Docker container — no database, no frontend, no other dependencies. Give it a device's current sensor readings, get back a failure probability, remaining useful life, explainable reasons, and maintenance recommendations.

This is the model-serving layer extracted from the full MediGuard AI platform, hardened for real deployment: API-key auth, rate limiting, structured request logging, liveness/readiness probes, input validation, and a non-root multi-stage Docker build.

## What you get

```
POST /predict         -> one device's prediction
POST /predict/batch    -> up to 500 devices at once
GET  /model-info        -> model version + training metrics (auth required)
GET  /health/live        -> is the process running?
GET  /health/ready       -> is the model loaded and able to serve traffic?
```

Every prediction includes:
- Failure probability + risk level (Low/Medium/High)
- 7/30/90-day failure probability breakdown
- Remaining useful life estimate (days)
- Most likely subsystem to fail
- Anomaly flag (Isolation Forest)
- **Top 5 SHAP-based reasons**, in plain language — never a bare number
- **Actionable recommendations** (e.g. "Replace battery", "Schedule preventive maintenance within 5 days")

## Quick start (local)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # edit API_KEYS to a real value
uvicorn app.main:app --reload
```

Visit `http://localhost:8000/docs` for interactive API docs with a working example payload pre-filled.

Test it:
```bash
curl -X POST http://localhost:8000/predict \
  -H "X-API-Key: changeme-generate-a-real-key" \
  -H "Content-Type: application/json" \
  -d @example_payload.json
```

## Deploying

The image is a standard Docker container — deploy it to whichever platform your organization already uses.

### Render
1. Push this repo to GitHub.
2. In Render: **New -> Blueprint**, point at this repo (`render.yaml` is already configured).
3. Set the `API_KEYS` secret in the Render dashboard (don't put real keys in the repo).
4. Deploy. Render handles the rest (health checks, TLS, restarts).

### Railway
```bash
railway login
railway init
railway up
railway variables set API_KEYS=your-real-key-here
```
Railway auto-detects the `Procfile`.

### Fly.io
```bash
fly launch --no-deploy   # uses fly.toml already in this repo
fly secrets set API_KEYS=your-real-key-here
fly deploy
```

### AWS (ECS Fargate / App Runner)
```bash
docker build -t mediguard-model-service .
docker tag mediguard-model-service:latest <your-ecr-repo-uri>:latest
docker push <your-ecr-repo-uri>:latest
```
Then point an ECS Fargate service or App Runner at that image. Set `API_KEYS` via AWS Secrets Manager, injected as an environment variable. Health check path: `/health/live`.

### Google Cloud Run
```bash
gcloud builds submit --tag gcr.io/<your-project>/mediguard-model-service
gcloud run deploy mediguard-model-service \
  --image gcr.io/<your-project>/mediguard-model-service \
  --port 8080 \
  --set-secrets API_KEYS=mediguard-api-keys:latest
```

### Azure Container Apps
```bash
az acr build --registry <your-registry> --image mediguard-model-service .
az containerapp create \
  --name mediguard-model-service \
  --image <your-registry>.azurecr.io/mediguard-model-service \
  --target-port 8080 \
  --secrets api-keys=your-real-key-here \
  --env-vars API_KEYS=secretref:api-keys
```

## Configuration

All settings are environment variables — see `.env.example`. The important ones:

| Variable | What it does |
|---|---|
| `API_KEYS` | Comma-separated valid keys. **Change the default before deploying anywhere real.** |
| `CORS_ORIGINS` | Restrict to your actual frontend domain(s) in production; `*` is fine for server-to-server calls |
| `RATE_LIMIT_PER_MINUTE` | Per-API-key request limit |
| `FAILURE_PROB_HIGH_THRESHOLD` / `_MEDIUM_THRESHOLD` | Risk-level cutoffs — must match what the model was calibrated against |

## Updating the model

This service ships with the trained models baked into the Docker image (`app/artifacts/`). To deploy a newly retrained model:

1. Retrain using the main MediGuard ML pipeline: `cd ../backend && python -m app.ml.train`.
2. Copy the new versioned folder into `app/artifacts/` here, and update `app/artifacts/latest.json` to point at it.
3. **If the feature set changed**, update `app/constants.py`'s `FEATURE_COLUMNS` to match exactly — the service asserts this matches the model's training metadata at startup and will refuse to start if they diverge, rather than silently serving wrong predictions.
4. Rebuild and redeploy the image.

## Important: what this service does *not* do

- **No feature engineering.** It expects the caller to send already-computed daily-aggregated features (sensor means, 7-day trends, error counts, days-since-maintenance). In a real deployment, a separate pipeline (streaming or batch) owns turning raw telemetry into these features — see [`../backend/app/ml/feature_engineering.py`](../backend/app/ml/feature_engineering.py) for a reference implementation. Keeping these separate is standard MLOps practice: it lets you scale, version, and audit the model independently of the data pipeline.
- **No database.** Stateless by design — every request is self-contained.
- **No authentication beyond a shared API key.** Fine behind a hospital's internal network or an API gateway; add OAuth2/JWT with per-customer identity if this becomes a multi-tenant public service.

## Honest note on model quality

The shipped model was trained on a relabeled industrial IoT dataset (see [`../docs/model_documentation.md`](../docs/model_documentation.md) for the full discussion). AUC is modest (0.54–0.67) — a real property of that dataset's weak telemetry-to-failure signal, not a bug in this service. Retrain on your own institution's real equipment data before using this for actual maintenance decisions.

## License

MIT
