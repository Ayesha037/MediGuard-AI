import enum
import uuid
from datetime import date, datetime

from sqlalchemy import String, Integer, Date, DateTime, Enum, Float, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class DeviceType(str, enum.Enum):
    VENTILATOR = "Ventilator"
    MRI_SCANNER = "MRI Scanner"
    INFUSION_PUMP = "Infusion Pump"
    PATIENT_MONITOR = "Patient Monitor"


class DeviceStatus(str, enum.Enum):
    HEALTHY = "Healthy"
    WARNING = "Warning"
    CRITICAL = "Critical"
    OFFLINE = "Offline"
    UNDER_MAINTENANCE = "Under Maintenance"


class Device(Base):
    __tablename__ = "devices"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    source_machine_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)

    device_name: Mapped[str] = mapped_column(String(100))
    device_type: Mapped[DeviceType] = mapped_column(Enum(DeviceType), index=True)
    manufacturer: Mapped[str] = mapped_column(String(100))
    model: Mapped[str] = mapped_column(String(50))  

    department: Mapped[str] = mapped_column(String(100))
    location: Mapped[str] = mapped_column(String(150))

    purchase_date: Mapped[date] = mapped_column(Date)
    warranty_expiry: Mapped[date] = mapped_column(Date)
    expected_lifespan_years: Mapped[int] = mapped_column(Integer)
    age_years: Mapped[int] = mapped_column(Integer)  
    last_maintenance_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    next_maintenance_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    status: Mapped[DeviceStatus] = mapped_column(Enum(DeviceStatus), default=DeviceStatus.HEALTHY, index=True)
    current_failure_probability: Mapped[float] = mapped_column(Float, default=0.0)
    current_rul_days: Mapped[float | None] = mapped_column(Float, nullable=True)  
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    telemetry: Mapped[list["TelemetryReading"]] = relationship(back_populates="device", cascade="all, delete-orphan")
    error_logs: Mapped[list["ErrorLog"]] = relationship(back_populates="device", cascade="all, delete-orphan")
    maintenance_records: Mapped[list["MaintenanceRecord"]] = relationship(back_populates="device", cascade="all, delete-orphan")
    failure_events: Mapped[list["FailureEvent"]] = relationship(back_populates="device", cascade="all, delete-orphan")
    predictions: Mapped[list["Prediction"]] = relationship(back_populates="device", cascade="all, delete-orphan")
    alerts: Mapped[list["Alert"]] = relationship(back_populates="device", cascade="all, delete-orphan")

from app.models.telemetry import TelemetryReading  
from app.models.event import ErrorLog, MaintenanceRecord, FailureEvent 
from app.models.prediction import Prediction  
from app.models.alert import Alert 
