from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import asc, desc

from app.core.database import get_db
from app.models.device import Device, DeviceType, DeviceStatus
from app.schemas.device import DeviceRead, DeviceSummary

router = APIRouter(prefix="/devices", tags=["Devices"])


@router.get("", response_model=list[DeviceSummary])
def list_devices(
    db: Session = Depends(get_db),
    department: str | None = None,
    device_type: DeviceType | None = None,
    status: DeviceStatus | None = None,
    limit: int = Query(100, le=500),
    offset: int = 0,
):
    query = db.query(Device)
    if department:
        query = query.filter(Device.department == department)
    if device_type:
        query = query.filter(Device.device_type == device_type)
    if status:
        query = query.filter(Device.status == status)
    return query.order_by(Device.device_name).offset(offset).limit(limit).all()


@router.get("/ranking", response_model=list[DeviceSummary])
def rank_devices(db: Session = Depends(get_db), order: str = Query("desc", enum=["asc", "desc"])):
    direction = desc if order == "desc" else asc
    return db.query(Device).order_by(direction(Device.current_failure_probability)).all()


@router.get("/{device_id}", response_model=DeviceRead)
def get_device(device_id: str, db: Session = Depends(get_db)):
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return device
