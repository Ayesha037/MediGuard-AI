from fastapi import APIRouter

from app.api.v1 import devices, telemetry, alerts, digital_twin, analytics

api_router = APIRouter()
api_router.include_router(devices.router)
api_router.include_router(telemetry.router)
api_router.include_router(alerts.router)
api_router.include_router(digital_twin.router)
api_router.include_router(analytics.router)
