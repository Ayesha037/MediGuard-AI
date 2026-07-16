"""
MediGuard AI Prediction Service — standalone, deployable model-serving API.

Run locally:    uvicorn app.main:app --reload
Run in prod:     gunicorn -c gunicorn_conf.py app.main:app
"""
import logging
import time
import uuid

from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.auth import require_api_key
from app.inference import load_engine, get_engine, ModelNotLoadedError
from app.schemas import (
    DeviceFeatures, PredictionResponse, BatchPredictionRequest, BatchPredictionResponse,
    HealthResponse, ModelInfoResponse,
)

logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("mediguard.api")

limiter = Limiter(key_func=lambda request: request.headers.get("X-API-Key", get_remote_address(request)))


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        load_engine()
    except Exception:
        logger.exception("FATAL: model failed to load at startup.")
        raise
    yield


app = FastAPI(
    title=settings.SERVICE_NAME,
    description=(
        "Predicts medical equipment failure probability, remaining useful life, "
        "and generates explainable, actionable maintenance recommendations. "
        "Every prediction includes SHAP-based reasons -- never a bare number."
    ),
    version="1.0.0",
    lifespan=lifespan,
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_context(request: Request, call_next):
    """Attach a request ID to every response and log request timing -- the
    baseline observability a medical-equipment company's ops team would
    expect for tracing an issue back to a specific prediction call."""
    request_id = str(uuid.uuid4())
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - start) * 1000
    response.headers["X-Request-ID"] = request_id
    logger.info(
        "request_id=%s method=%s path=%s status=%d duration_ms=%.1f",
        request_id, request.method, request.url.path, response.status_code, duration_ms,
    )
    return response


@app.exception_handler(ModelNotLoadedError)
async def model_not_loaded_handler(request: Request, exc: ModelNotLoadedError):
    return JSONResponse(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content={"detail": str(exc)})


# --- Health & readiness -----------------------------------------------------
# Separate liveness (is the process up?) from readiness (is the model
# loaded and able to serve traffic?) -- standard practice for any
# orchestrator (Kubernetes, ECS, Cloud Run) doing rolling deploys.

@app.get("/health/live", response_model=HealthResponse, tags=["Health"])
def liveness():
    return HealthResponse(status="ok", service=settings.SERVICE_NAME)


@app.get("/health/ready", response_model=HealthResponse, tags=["Health"])
def readiness():
    engine = get_engine()  # raises 503 via the exception handler if not loaded
    return HealthResponse(status="ready", service=settings.SERVICE_NAME, model_version=engine.version)


# --- Model info --------------------------------------------------------------

@app.get("/model-info", response_model=ModelInfoResponse, tags=["Model"], dependencies=[Depends(require_api_key)])
def model_info():
    engine = get_engine()
    meta = engine.metadata
    return ModelInfoResponse(
        version=meta["version"],
        trained_at=meta["trained_at"],
        feature_columns=meta["feature_columns"],
        classifier_metrics=meta["classifier_metrics"],
        rul_metrics=meta["rul_metrics"],
    )


# --- Prediction ---------------------------------------------------------------

@app.post("/predict", response_model=PredictionResponse, tags=["Prediction"], dependencies=[Depends(require_api_key)])
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
def predict(request: Request, payload: DeviceFeatures):
    engine = get_engine()
    result = engine.predict(payload.model_dump())
    return PredictionResponse(device_id=payload.device_id, **result)


@app.post("/predict/batch", response_model=BatchPredictionResponse, tags=["Prediction"], dependencies=[Depends(require_api_key)])
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
def predict_batch(request: Request, payload: BatchPredictionRequest):
    engine = get_engine()
    predictions = [
        PredictionResponse(device_id=device.device_id, **engine.predict(device.model_dump()))
        for device in payload.devices
    ]
    return BatchPredictionResponse(predictions=predictions, model_version=engine.version, count=len(predictions))
