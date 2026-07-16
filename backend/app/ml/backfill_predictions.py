from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.config import settings
from app.models.device import Device, DeviceStatus
from app.models.prediction import Prediction, RiskLevel
from app.models.alert import Alert, AlertType, AlertSeverity
from app.ml.feature_engineering import build_feature_table
from app.ml.inference import get_prediction_engine

RISK_TO_STATUS = {
    "Low": DeviceStatus.HEALTHY,
    "Medium": DeviceStatus.WARNING,
    "High": DeviceStatus.CRITICAL,
}
RISK_TO_ENUM = {"Low": RiskLevel.LOW, "Medium": RiskLevel.MEDIUM, "High": RiskLevel.HIGH}


def _generate_alerts(db: Session, device: Device, prediction_result: dict, feature_row) -> None:
    now = datetime.now(timezone.utc)
    alerts = []

    if prediction_result["failure_probability"] > settings.FAILURE_PROB_HIGH_THRESHOLD:
        alerts.append(Alert(
            device_id=device.id, alert_type=AlertType.HIGH_FAILURE_PROBABILITY,
            severity=AlertSeverity.CRITICAL, created_at=now,
            message=f"{device.device_name} has a {prediction_result['failure_probability']:.0%} failure probability.",
        ))

    if feature_row["temperature"] > 45:
        alerts.append(Alert(
            device_id=device.id, alert_type=AlertType.ABNORMAL_TEMPERATURE,
            severity=AlertSeverity.WARNING, created_at=now,
            message=f"{device.device_name} temperature reading is abnormal ({feature_row['temperature']:.1f}\u00b0C).",
        ))

    if feature_row["battery_health"] < 20:
        alerts.append(Alert(
            device_id=device.id, alert_type=AlertType.LOW_BATTERY_HEALTH,
            severity=AlertSeverity.WARNING, created_at=now,
            message=f"{device.device_name} battery health is low ({feature_row['battery_health']:.0f}%).",
        ))

    if prediction_result.get("is_anomaly") and feature_row["vibration"] > 55:
        alerts.append(Alert(
            device_id=device.id, alert_type=AlertType.ABNORMAL_VIBRATION,
            severity=AlertSeverity.WARNING, created_at=now,
            message=f"{device.device_name} vibration reading is abnormal ({feature_row['vibration']:.1f}).",
        ))

    calib_col = "days_since_maint_sensor"
    if feature_row[calib_col] > 180:
        alerts.append(Alert(
            device_id=device.id, alert_type=AlertType.CALIBRATION_OVERDUE,
            severity=AlertSeverity.WARNING, created_at=now,
            message=f"{device.device_name} calibration is overdue ({int(feature_row[calib_col])} days since last check).",
        ))

    for alert in alerts:
        db.add(alert)


def run_backfill():
    print("Building current feature snapshot for all devices...")
    feature_table = build_feature_table()
    latest_per_device = feature_table.sort_values("date").groupby("device_id").tail(1)
    print(f"  {len(latest_per_device)} device snapshots ready")

    print("Loading prediction engine (latest trained model)...")
    engine = get_prediction_engine()
    print(f"  Using model version: {engine.version}")

    db = SessionLocal()
    try:
        devices = {d.id: d for d in db.query(Device).all()}
        now = datetime.now(timezone.utc)
        predictions_written = 0
        alerts_written_before = db.query(Alert).count()

        for _, row in latest_per_device.iterrows():
            device = devices.get(row["device_id"])
            if device is None:
                continue

            result = engine.predict(row)

            prediction = Prediction(
                device_id=device.id,
                predicted_at=now,
                failure_probability=result["failure_probability"],
                risk_level=RISK_TO_ENUM[result["risk_level"]],
                remaining_useful_life_days=result["remaining_useful_life_days"],
                prob_failure_7d=result["prob_failure_7d"],
                prob_failure_30d=result["prob_failure_30d"],
                prob_failure_90d=result["prob_failure_90d"],
                predicted_subsystem=result["predicted_subsystem"],
                model_version=result["model_version"],
                shap_explanations=result["shap_explanations"],
                recommendations=result["recommendations"],
            )
            db.add(prediction)
            predictions_written += 1

            device.status = RISK_TO_STATUS[result["risk_level"]]
            device.current_failure_probability = result["failure_probability"]
            device.current_rul_days = result["remaining_useful_life_days"]

            _generate_alerts(db, device, result, row)

        db.commit()
        alerts_written = db.query(Alert).count() - alerts_written_before

        print(f"\nBackfill complete.")
        print(f"  Predictions written: {predictions_written}")
        print(f"  Alerts generated: {alerts_written}")

        risk_counts = db.query(Device.status, Device.id).all()
        from collections import Counter
        counts = Counter(status for status, _ in risk_counts)
        print(f"  Device status distribution: {dict(counts)}")

    finally:
        db.close()


if __name__ == "__main__":
    run_backfill()
