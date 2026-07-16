from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.device import Device, DeviceStatus
from app.models.event import FailureEvent, MaintenanceRecord
from app.models.prediction import Prediction

router = APIRouter(prefix="/analytics", tags=["Analytics"])

AVG_UNPLANNED_FAILURE_COST_USD = 8500
AVG_UNPLANNED_DOWNTIME_HOURS = 14


@router.get("/overview")
def get_overview(db: Session = Depends(get_db)):
    total = db.query(func.count(Device.id)).scalar()
    healthy = db.query(func.count(Device.id)).filter(Device.status == DeviceStatus.HEALTHY).scalar()
    warning = db.query(func.count(Device.id)).filter(Device.status == DeviceStatus.WARNING).scalar()
    critical = db.query(func.count(Device.id)).filter(Device.status == DeviceStatus.CRITICAL).scalar()
    avg_prob = db.query(func.avg(Device.current_failure_probability)).scalar() or 0.0

    preventive_actions = db.query(func.count(MaintenanceRecord.id)).scalar()
    est_cost_saved = preventive_actions * AVG_UNPLANNED_FAILURE_COST_USD
    est_downtime_saved_hours = preventive_actions * AVG_UNPLANNED_DOWNTIME_HOURS

    return {
        "total_devices": total,
        "healthy_devices": healthy,
        "warning_devices": warning,
        "critical_devices": critical,
        "average_failure_probability": round(float(avg_prob), 4),
        "estimated_maintenance_cost_saved_usd": est_cost_saved,
        "estimated_downtime_saved_hours": est_downtime_saved_hours,
        "cost_model_note": "Illustrative estimate based on industry-average unplanned failure cost; not a clinical or audited financial figure.",
    }


@router.get("/failure-trends")
def get_monthly_failure_trends(db: Session = Depends(get_db)):
    rows = (
        db.query(
            func.date_trunc("month", FailureEvent.occurred_at).label("month"),
            func.count(FailureEvent.id).label("failure_count"),
        )
        .group_by("month")
        .order_by("month")
        .all()
    )
    return [{"month": r.month.strftime("%Y-%m"), "failure_count": r.failure_count} for r in rows]


@router.get("/department-health")
def get_department_health(db: Session = Depends(get_db)):
   
    results = []
    for dept, in db.query(Device.department).distinct():
        devices = db.query(Device).filter(Device.department == dept).all()
        results.append({
            "department": dept,
            "total_devices": len(devices),
            "average_failure_probability": round(
                sum(d.current_failure_probability for d in devices) / len(devices), 4
            ) if devices else 0,
            "critical_count": sum(1 for d in devices if d.status == DeviceStatus.CRITICAL),
            "warning_count": sum(1 for d in devices if d.status == DeviceStatus.WARNING),
            "healthy_count": sum(1 for d in devices if d.status == DeviceStatus.HEALTHY),
        })
    return results


@router.get("/manufacturer-comparison")
def get_manufacturer_comparison(db: Session = Depends(get_db)):
    results = []
    for manufacturer, in db.query(Device.manufacturer).distinct():
        devices = db.query(Device).filter(Device.manufacturer == manufacturer).all()
        results.append({
            "manufacturer": manufacturer,
            "total_devices": len(devices),
            "average_failure_probability": round(
                sum(d.current_failure_probability for d in devices) / len(devices), 4
            ) if devices else 0,
        })
    return sorted(results, key=lambda r: r["average_failure_probability"], reverse=True)
