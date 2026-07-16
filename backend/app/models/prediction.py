import enum
from datetime import datetime

from sqlalchemy import String, Float, DateTime, ForeignKey, Enum, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class RiskLevel(str, enum.Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


class Prediction(Base):
    __tablename__ = "predictions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    device_id: Mapped[str] = mapped_column(String(36), ForeignKey("devices.id", ondelete="CASCADE"), index=True)
    predicted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)

    failure_probability: Mapped[float] = mapped_column(Float) 
    risk_level: Mapped[RiskLevel] = mapped_column(Enum(RiskLevel))
    remaining_useful_life_days: Mapped[float] = mapped_column(Float)

    prob_failure_7d: Mapped[float] = mapped_column(Float)
    prob_failure_30d: Mapped[float] = mapped_column(Float)
    prob_failure_90d: Mapped[float] = mapped_column(Float)

    predicted_subsystem: Mapped[str | None] = mapped_column(String(50), nullable=True) 
    model_version: Mapped[str] = mapped_column(String(30))

    shap_explanations: Mapped[list] = mapped_column(JSON)

    recommendations: Mapped[list] = mapped_column(JSON)

    device: Mapped["Device"] = relationship(back_populates="predictions")
