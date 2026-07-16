import argparse
import random
from datetime import datetime, date, timedelta

import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from app.core.database import SessionLocal, engine, Base
from app.models.device import Device, DeviceType, DeviceStatus
from app.models.telemetry import TelemetryReading
from app.models.event import ErrorLog, MaintenanceRecord, FailureEvent, Subsystem

random.seed(42)
np.random.seed(42)

MODEL_TO_DEVICE_TYPE = {
    "model1": DeviceType.PATIENT_MONITOR,
    "model2": DeviceType.INFUSION_PUMP,
    "model3": DeviceType.VENTILATOR,
    "model4": DeviceType.MRI_SCANNER,
}

MANUFACTURERS_BY_TYPE = {
    DeviceType.VENTILATOR: ["Philips Respironics", "Draeger", "Medtronic"],
    DeviceType.MRI_SCANNER: ["Siemens Healthineers", "GE HealthCare", "Canon Medical"],
    DeviceType.INFUSION_PUMP: ["BD Alaris", "Baxter", "B. Braun"],
    DeviceType.PATIENT_MONITOR: ["Philips IntelliVue", "GE HealthCare", "Mindray"],
}

DEPARTMENTS = ["ICU", "Emergency", "Radiology", "General Ward", "Operating Theatre", "Cardiology"]

COMP_TO_SUBSYSTEM = {
    "comp1": Subsystem.COOLING_FAN,
    "comp2": Subsystem.POWER_SUPPLY,
    "comp3": Subsystem.SENSOR_CALIBRATION,
    "comp4": Subsystem.BATTERY,
}

ERROR_MESSAGES = {
    "error1": "Sensor calibration drift detected",
    "error2": "Power supply voltage fluctuation",
    "error3": "Cooling fan RPM below expected range",
    "error4": "Battery discharge rate abnormal",
    "error5": "Communication timeout with monitoring hub",
}

EXPECTED_LIFESPAN_YEARS = {
    DeviceType.VENTILATOR: 10,
    DeviceType.MRI_SCANNER: 15,
    DeviceType.INFUSION_PUMP: 8,
    DeviceType.PATIENT_MONITOR: 7,
}


def build_devices(machines_df: pd.DataFrame) -> dict[int, Device]:
    devices = {}
    today = date.today()

    for _, row in machines_df.iterrows():
        machine_id = int(row["machineID"])
        device_type = MODEL_TO_DEVICE_TYPE[row["model"]]
        age_years = int(row["age"])
        manufacturer = random.choice(MANUFACTURERS_BY_TYPE[device_type])
        department = DEPARTMENTS[machine_id % len(DEPARTMENTS)]
        lifespan = EXPECTED_LIFESPAN_YEARS[device_type]

        purchase_date = today - timedelta(days=age_years * 365 + random.randint(0, 300))
        warranty_years = 2 if device_type != DeviceType.MRI_SCANNER else 3
        warranty_expiry = purchase_date + timedelta(days=warranty_years * 365)

        device = Device(
            source_machine_id=machine_id,
            device_name=f"{device_type.value} - {machine_id:03d}",
            device_type=device_type,
            manufacturer=manufacturer,
            model=row["model"],
            department=department,
            location=f"{department} - Room {100 + (machine_id % 20)}",
            purchase_date=purchase_date,
            warranty_expiry=warranty_expiry,
            expected_lifespan_years=lifespan,
            age_years=age_years,
            status=DeviceStatus.HEALTHY,
            current_failure_probability=0.0,
        )
        devices[machine_id] = device

    return devices


def engineer_extra_sensors(tel_row: pd.Series, device_age: int, rng: np.random.Generator) -> dict:
    temperature = 36 + (tel_row["pressure"] - 95) * 0.03 + tel_row["vibration"] * 0.02 + rng.normal(0, 0.5)
    temperature = float(np.clip(temperature, 30, 55))

    cpu_utilization = 30 + (tel_row["rotate"] - 400) * 0.05 + rng.normal(0, 3)
    cpu_utilization = float(np.clip(cpu_utilization, 5, 100))

    battery_health = 100 - device_age * 3.2 + rng.normal(0, 2)
    battery_health = float(np.clip(battery_health, 5, 100))

    network_status = bool(rng.random() > 0.02)  
    calibration_status = bool(rng.random() > 0.015)

    return {
        "temperature": round(temperature, 2),
        "cpu_utilization": round(cpu_utilization, 2),
        "battery_health": round(battery_health, 2),
        "network_status": network_status,
        "calibration_status": calibration_status,
    }


def ingest(csv_dir: str, telemetry_sample_hours: int | None = None):
    print("Reading CSVs...")
    machines_df = pd.read_csv(f"{csv_dir}/PdM_machines.csv")
    telemetry_df = pd.read_csv(f"{csv_dir}/PdM_telemetry.csv", parse_dates=["datetime"])
    errors_df = pd.read_csv(f"{csv_dir}/PdM_errors.csv", parse_dates=["datetime"])
    maint_df = pd.read_csv(f"{csv_dir}/PdM_maint.csv", parse_dates=["datetime"])
    failures_df = pd.read_csv(f"{csv_dir}/PdM_failures.csv", parse_dates=["datetime"])

    print("Creating tables...")
    Base.metadata.create_all(bind=engine)

    db: Session = SessionLocal()
    rng = np.random.default_rng(42)

    try:
        print(f"Building {len(machines_df)} devices...")
        devices = build_devices(machines_df)
        db.add_all(devices.values())
        db.flush() 
        if telemetry_sample_hours:
            cutoff = telemetry_df["datetime"].max() - pd.Timedelta(hours=telemetry_sample_hours)
            telemetry_df = telemetry_df[telemetry_df["datetime"] >= cutoff]

        print(f"Ingesting {len(telemetry_df):,} telemetry rows...")
  
        usage_counters = {mid: 0 for mid in devices}
        hours_counters = {mid: 0.0 for mid in devices}
        telemetry_df = telemetry_df.sort_values(["machineID", "datetime"])

        batch = []
        for _, row in telemetry_df.iterrows():
            mid = int(row["machineID"])
            device = devices[mid]
            usage_counters[mid] += 1
            hours_counters[mid] += 1.0

            extra = engineer_extra_sensors(row, device.age_years, rng)
            batch.append(TelemetryReading(
                device_id=device.id,
                recorded_at=row["datetime"],
                voltage=round(float(row["volt"]), 2),
                fan_speed=round(float(row["rotate"]), 2),
                power_consumption=round(float(row["pressure"]), 2),
                vibration=round(float(row["vibration"]), 2),
                operating_hours=hours_counters[mid],
                usage_count=usage_counters[mid],
                **extra,
            ))

            if len(batch) >= 5000:
                db.bulk_save_objects(batch)
                batch = []
        if batch:
            db.bulk_save_objects(batch)

        print(f"Ingesting {len(errors_df):,} error logs...")
        error_objs = [
            ErrorLog(
                device_id=devices[int(r["machineID"])].id,
                occurred_at=r["datetime"],
                error_code=r["errorID"],
                message=ERROR_MESSAGES[r["errorID"]],
            )
            for _, r in errors_df.iterrows() if int(r["machineID"]) in devices
        ]
        db.bulk_save_objects(error_objs)

        print(f"Ingesting {len(maint_df):,} maintenance records...")
        maint_objs = [
            MaintenanceRecord(
                device_id=devices[int(r["machineID"])].id,
                performed_at=r["datetime"],
                subsystem=COMP_TO_SUBSYSTEM[r["comp"]],
            )
            for _, r in maint_df.iterrows() if int(r["machineID"]) in devices
        ]
        db.bulk_save_objects(maint_objs)

        print(f"Ingesting {len(failures_df):,} failure events...")
        failure_objs = [
            FailureEvent(
                device_id=devices[int(r["machineID"])].id,
                occurred_at=r["datetime"],
                subsystem=COMP_TO_SUBSYSTEM[r["failure"]],
            )
            for _, r in failures_df.iterrows() if int(r["machineID"]) in devices
        ]
        db.bulk_save_objects(failure_objs)

        print("Backfilling maintenance schedule fields...")
        for mid, device in devices.items():
            device_maint = maint_df[maint_df["machineID"] == mid]
            if not device_maint.empty:
                last = device_maint["datetime"].max()
                device.last_maintenance_date = last.date()
                device.next_maintenance_date = (last + pd.Timedelta(days=180)).date()

        db.commit()
        print("Ingestion complete.")
        print(f"  Devices: {len(devices)}")
        print(f"  Telemetry rows: {len(telemetry_df):,}")
        print(f"  Errors: {len(errors_df):,} | Maintenance: {len(maint_df):,} | Failures: {len(failures_df):,}")

    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest Azure PdM dataset into MediGuard schema")
    parser.add_argument("--csv-dir", required=True, help="Directory containing PdM_*.csv files")
    parser.add_argument(
        "--sample-hours", type=int, default=None,
        help="Only load the most recent N hours of telemetry per device (omit for full year)",
    )
    args = parser.parse_args()
    ingest(args.csv_dir, telemetry_sample_hours=args.sample_hours)
