from datetime import datetime
from pydantic import BaseModel, ConfigDict


class TelemetryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    device_id: str
    recorded_at: datetime
    voltage: float
    fan_speed: float
    power_consumption: float
    vibration: float
    temperature: float
    cpu_utilization: float
    battery_health: float
    operating_hours: float
    usage_count: int
    network_status: bool
    calibration_status: bool


class TelemetryLatest(BaseModel):
    device_id: str
    recorded_at: datetime
    voltage: float
    fan_speed: float
    power_consumption: float
    vibration: float
    temperature: float
    cpu_utilization: float
    battery_health: float
    network_status: bool
