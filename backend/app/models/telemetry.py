from datetime import datetime

from sqlalchemy import String, Float, Integer, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class TelemetryReading(Base):
    __tablename__ = "telemetry_readings"
    __table_args__ = (
        Index("ix_telemetry_device_time", "device_id", "recorded_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    device_id: Mapped[str] = mapped_column(String(36), ForeignKey("devices.id", ondelete="CASCADE"), index=True)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)

    voltage: Mapped[float] = mapped_column(Float)
    fan_speed: Mapped[float] = mapped_column(Float)
    power_consumption: Mapped[float] = mapped_column(Float)
    vibration: Mapped[float] = mapped_column(Float)

    temperature: Mapped[float] = mapped_column(Float)
    cpu_utilization: Mapped[float] = mapped_column(Float)
    battery_health: Mapped[float] = mapped_column(Float)    
    operating_hours: Mapped[float] = mapped_column(Float)
    usage_count: Mapped[int] = mapped_column(Integer)
    network_status: Mapped[bool] = mapped_column(Boolean, default=True)
    calibration_status: Mapped[bool] = mapped_column(Boolean, default=True)

    device: Mapped["Device"] = relationship(back_populates="telemetry")
