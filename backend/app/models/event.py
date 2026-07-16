import enum
from datetime import datetime

from sqlalchemy import String, DateTime, ForeignKey, Enum, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Subsystem(str, enum.Enum):
    COOLING_FAN = "Cooling Fan"
    POWER_SUPPLY = "Power Supply Unit"
    SENSOR_CALIBRATION = "Sensor Calibration Module"
    BATTERY = "Battery"


class ErrorLog(Base):
    __tablename__ = "error_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    device_id: Mapped[str] = mapped_column(String(36), ForeignKey("devices.id", ondelete="CASCADE"), index=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    error_code: Mapped[str] = mapped_column(String(20))      
    message: Mapped[str] = mapped_column(Text)    

    device: Mapped["Device"] = relationship(back_populates="error_logs")


class MaintenanceRecord(Base):
    __tablename__ = "maintenance_records"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    device_id: Mapped[str] = mapped_column(String(36), ForeignKey("devices.id", ondelete="CASCADE"), index=True)
    performed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    subsystem: Mapped[Subsystem] = mapped_column(Enum(Subsystem))
    description: Mapped[str] = mapped_column(Text, default="Preventive component replacement")
    technician: Mapped[str] = mapped_column(String(100), default="Biomedical Engineering Team")

    device: Mapped["Device"] = relationship(back_populates="maintenance_records")


class FailureEvent(Base):
    __tablename__ = "failure_events"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    device_id: Mapped[str] = mapped_column(String(36), ForeignKey("devices.id", ondelete="CASCADE"), index=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    subsystem: Mapped[Subsystem] = mapped_column(Enum(Subsystem))
    resolved: Mapped[bool] = mapped_column(default=True)

    device: Mapped["Device"] = relationship(back_populates="failure_events")
