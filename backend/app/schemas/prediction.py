from datetime import date, datetime
from pydantic import BaseModel, ConfigDict

from app.models.prediction import RiskLevel
from app.models.alert import AlertSeverity, AlertType
from app.models.event import Subsystem


class ShapExplanation(BaseModel):
    feature: str
    impact: float
    explanation: str


class PredictionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    device_id: str
    predicted_at: datetime
    failure_probability: float
    risk_level: RiskLevel
    remaining_useful_life_days: float
    prob_failure_7d: float
    prob_failure_30d: float
    prob_failure_90d: float
    predicted_subsystem: str | None
    model_version: str
    shap_explanations: list[ShapExplanation]
    recommendations: list[str]


class AlertRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    device_id: str
    alert_type: AlertType
    severity: AlertSeverity
    message: str
    created_at: datetime
    acknowledged: bool
    acknowledged_by: str | None


class ErrorLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    device_id: str
    occurred_at: datetime
    error_code: str
    message: str


class MaintenanceRecordRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    device_id: str
    performed_at: datetime
    subsystem: Subsystem
    description: str
    technician: str


class FailureEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    device_id: str
    occurred_at: datetime
    subsystem: Subsystem
    resolved: bool



