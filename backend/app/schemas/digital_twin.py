from pydantic import BaseModel

from app.schemas.device import DeviceRead
from app.schemas.telemetry import TelemetryRead
from app.schemas.prediction import PredictionRead, ErrorLogRead, MaintenanceRecordRead, FailureEventRead


class DigitalTwinResponse(BaseModel):
    device: DeviceRead
    telemetry_trend: list[TelemetryRead]
    prediction_history: list[PredictionRead]
    error_logs: list[ErrorLogRead]
    maintenance_history: list[MaintenanceRecordRead]
    failure_history: list[FailureEventRead]
