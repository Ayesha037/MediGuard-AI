import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.v1.router import api_router
from app.simulator.iot_simulator import run_simulator_loop

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.SIMULATOR_ENABLED:
        task = asyncio.create_task(run_simulator_loop())
        logger.info("IoT simulator background task started.")
    yield
    if settings.SIMULATOR_ENABLED:
        task.cancel()


app = FastAPI(
    title=settings.APP_NAME,
    description="AI-powered predictive maintenance platform for hospital medical equipment.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/health")
def health_check():
    return {"status": "ok", "app": settings.APP_NAME}
