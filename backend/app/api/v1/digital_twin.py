from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.device import Device
from app.models.telemetry import TelemetryReading
from app.models.event import ErrorLog, MaintenanceRecord, FailureEvent
from app.models.prediction import Prediction
from app.schemas.digital_twin import DigitalTwinResponse

router = APIRouter(prefix="/digital-twin", tags=["Digital Twin"])


@router.get("/{device_id}", response_model=DigitalTwinResponse)
def get_digital_twin(device_id: str, db: Session = Depends(get_db), telemetry_hours: int = Query(72, le=2000)):
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    telemetry = (
        db.query(TelemetryReading)
        .filter(TelemetryReading.device_id == device_id)
        .order_by(TelemetryReading.recorded_at.desc())
        .limit(telemetry_hours)
        .all()
    )
    predictions = (
        db.query(Prediction)
        .filter(Prediction.device_id == device_id)
        .order_by(Prediction.predicted_at.desc())
        .limit(50)
        .all()
    )
    errors = (
        db.query(ErrorLog)
        .filter(ErrorLog.device_id == device_id)
        .order_by(ErrorLog.occurred_at.desc())
        .limit(50)
        .all()
    )
    maintenance = (
        db.query(MaintenanceRecord)
        .filter(MaintenanceRecord.device_id == device_id)
        .order_by(MaintenanceRecord.performed_at.desc())
        .all()
    )
    failures = (
        db.query(FailureEvent)
        .filter(FailureEvent.device_id == device_id)
        .order_by(FailureEvent.occurred_at.desc())
        .all()
    )

    return DigitalTwinResponse(
        device=device,
        telemetry_trend=list(reversed(telemetry)),
        prediction_history=list(reversed(predictions)),
        error_logs=errors,
        maintenance_history=maintenance,
        failure_history=failures,
    )
