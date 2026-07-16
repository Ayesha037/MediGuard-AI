from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.alert import Alert, AlertSeverity
from app.schemas.prediction import AlertRead

router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.get("", response_model=list[AlertRead])
def list_alerts(
    db: Session = Depends(get_db),
    severity: AlertSeverity | None = None,
    acknowledged: bool | None = None,
    device_id: str | None = None,
    limit: int = Query(100, le=500),
):
    query = db.query(Alert)
    if severity:
        query = query.filter(Alert.severity == severity)
    if acknowledged is not None:
        query = query.filter(Alert.acknowledged == acknowledged)
    if device_id:
        query = query.filter(Alert.device_id == device_id)
    return query.order_by(Alert.created_at.desc()).limit(limit).all()


@router.post("/{alert_id}/acknowledge", response_model=AlertRead)
def acknowledge_alert(alert_id: int, acknowledged_by: str = "Biomedical Engineer", db: Session = Depends(get_db)):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.acknowledged = True
    alert.acknowledged_by = acknowledged_by
    db.commit()
    db.refresh(alert)
    return alert
