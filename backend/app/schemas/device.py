from datetime import date, datetime
from pydantic import BaseModel, ConfigDict

from app.models.device import DeviceType, DeviceStatus


class DeviceBase(BaseModel):
    device_name: str
    device_type: DeviceType
    manufacturer: str
    model: str
    department: str
    location: str
    purchase_date: date
    warranty_expiry: date
    expected_lifespan_years: int


class DeviceCreate(DeviceBase):
    source_machine_id: int
    age_years: int


class DeviceRead(DeviceBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    source_machine_id: int
    age_years: int
    last_maintenance_date: date | None
    next_maintenance_date: date | None
    status: DeviceStatus
    current_failure_probability: float
    current_rul_days: float | None
    created_at: datetime
    updated_at: datetime


class DeviceSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    device_name: str
    device_type: DeviceType
    department: str
    status: DeviceStatus
    current_failure_probability: float
    current_rul_days: float | None
