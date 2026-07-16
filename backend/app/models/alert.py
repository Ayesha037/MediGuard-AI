import enum
from datetime import datetime

from sqlalchemy import String, DateTime, ForeignKey, Enum, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class AlertSeverity(str, enum.Enum):
    INFO = "Info"
    WARNING = "Warning"
    CRITICAL = "Critical"


class AlertType(str, enum.Enum):
    HIGH_FAILURE_PROBABILITY = "High Failure Probability"
    ABNORMAL_TEMPERATURE = "Abnormal Temperature"
    LOW_BATTERY_HEALTH = "Low Battery Health"
    ABNORMAL_VIBRATION = "Abnormal Vibration"
    CALIBRATION_OVERDUE = "Calibration Overdue"


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    device_id: Mapped[str] = mapped_column(String(36), ForeignKey("devices.id", ondelete="CASCADE"), index=True)
    alert_type: Mapped[AlertType] = mapped_column(Enum(AlertType))
    severity: Mapped[AlertSeverity] = mapped_column(Enum(AlertSeverity))
    message: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    acknowledged: Mapped[bool] = mapped_column(Boolean, default=False)
    acknowledged_by: Mapped[str | None] = mapped_column(String(100), nullable=True)

    device: Mapped["Device"] = relationship(back_populates="alerts")
