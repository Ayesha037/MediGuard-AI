from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.device import Device
from app.models.telemetry import TelemetryReading
from app.schemas.telemetry import TelemetryRead
from app.simulator.connection_manager import connection_manager

router = APIRouter(prefix="/telemetry", tags=["Telemetry"])


@router.get("/{device_id}", response_model=list[TelemetryRead])
def get_telemetry_history(
    device_id: str,
    db: Session = Depends(get_db),
    hours: int = Query(24, le=24 * 90, description="How many hours of history to return"),
):
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    readings = (
        db.query(TelemetryReading)
        .filter(TelemetryReading.device_id == device_id)
        .order_by(TelemetryReading.recorded_at.desc())
        .limit(hours)
        .all()
    )
    return list(reversed(readings))


@router.get("/{device_id}/latest", response_model=TelemetryRead)
def get_latest_telemetry(device_id: str, db: Session = Depends(get_db)):
    reading = (
        db.query(TelemetryReading)
        .filter(TelemetryReading.device_id == device_id)
        .order_by(TelemetryReading.recorded_at.desc())
        .first()
    )
    if not reading:
        raise HTTPException(status_code=404, detail="No telemetry found for this device")
    return reading


@router.websocket("/ws/live")
async def telemetry_live_feed(websocket: WebSocket):
    await connection_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        connection_manager.disconnect(websocket)
