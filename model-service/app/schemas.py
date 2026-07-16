"""
Request/response contracts for the prediction API.

The input is the ENGINEERED feature vector (daily-aggregated sensor stats,
trends, error counts, days-since-maintenance) — the same shape the
MediGuard feature-engineering pipeline produces. This service deliberately
does NOT do feature engineering itself: in a real deployment, a separate
feature pipeline (streaming or batch) owns that responsibility, and this
service's only job is model inference. That separation is what lets the
model service scale, version, and get audited independently of the data
pipeline — standard MLOps practice, not an arbitrary choice.
"""
from pydantic import BaseModel, Field, field_validator


class DeviceFeatures(BaseModel):
    """One device's current engineered feature snapshot."""

    device_id: str = Field(..., description="Caller's own identifier for the device, echoed back in the response.")

    voltage: float = Field(..., ge=0, le=400, description="Volts")
    fan_speed: float = Field(..., ge=0, le=1000, description="RPM")
    power_consumption: float = Field(..., ge=0, le=500, description="Watts")
    vibration: float = Field(..., ge=0, le=200)
    temperature: float = Field(..., ge=-20, le=100, description="Celsius")
    cpu_utilization: float = Field(..., ge=0, le=100, description="Percent")
    battery_health: float = Field(..., ge=0, le=100, description="Percent")

    temperature_7d_mean: float
    temperature_7d_trend_pct: float = Field(..., description="Percent change vs prior 7-day window")
    vibration_7d_mean: float
    vibration_7d_trend_pct: float
    power_consumption_7d_mean: float
    power_consumption_7d_trend_pct: float
    battery_health_7d_mean: float
    battery_health_7d_trend_pct: float

    errors_7d: int = Field(..., ge=0)
    errors_30d: int = Field(..., ge=0)
    days_since_maint_cooling: float = Field(..., ge=0)
    days_since_maint_power: float = Field(..., ge=0)
    days_since_maint_sensor: float = Field(..., ge=0)
    days_since_maint_battery: float = Field(..., ge=0)

    age_years: float = Field(..., ge=0, le=50)

    @field_validator("device_id")
    @classmethod
    def device_id_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("device_id must not be blank")
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "device_id": "ventilator-023",
                "voltage": 191.3, "fan_speed": 410.0, "power_consumption": 108.2,
                "vibration": 48.5, "temperature": 39.1, "cpu_utilization": 62.0,
                "battery_health": 45.3,
                "temperature_7d_mean": 38.4, "temperature_7d_trend_pct": 4.2,
                "vibration_7d_mean": 46.0, "vibration_7d_trend_pct": 6.1,
                "power_consumption_7d_mean": 102.0, "power_consumption_7d_trend_pct": 8.6,
                "battery_health_7d_mean": 47.0, "battery_health_7d_trend_pct": -3.4,
                "errors_7d": 3, "errors_30d": 9,
                "days_since_maint_cooling": 210, "days_since_maint_power": 60,
                "days_since_maint_sensor": 45, "days_since_maint_battery": 300,
                "age_years": 17,
            }
        }
    }


class ShapReason(BaseModel):
    feature: str
    impact: float
    explanation: str


class PredictionResponse(BaseModel):
    device_id: str
    failure_probability: float
    risk_level: str
    remaining_useful_life_days: float
    prob_failure_7d: float
    prob_failure_30d: float
    prob_failure_90d: float
    predicted_subsystem: str
    is_anomaly: bool
    shap_explanations: list[ShapReason]
    recommendations: list[str]
    model_version: str


class BatchPredictionRequest(BaseModel):
    devices: list[DeviceFeatures] = Field(..., min_length=1, max_length=500)


class BatchPredictionResponse(BaseModel):
    predictions: list[PredictionResponse]
    model_version: str
    count: int


class HealthResponse(BaseModel):
    status: str
    service: str
    model_version: str | None = None


class ModelInfoResponse(BaseModel):
    version: str
    trained_at: str
    feature_columns: list[str]
    classifier_metrics: dict
    rul_metrics: dict
