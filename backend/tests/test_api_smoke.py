import pytest
from datetime import date, datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

import app.core.database as dbmod


@pytest.fixture
def client():
    dbmod.engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    dbmod.SessionLocal = sessionmaker(bind=dbmod.engine)

    from app.core.config import settings
    settings.SIMULATOR_ENABLED = False

    import app.models dbmod.Base.metadata.create_all(bind=dbmod.engine)

    _seed(dbmod.SessionLocal())

    from app.main import app
    return TestClient(app)


def _seed(db):
    from app.models.device import Device, DeviceType, DeviceStatus
    from app.models.telemetry import TelemetryReading
    from app.models.prediction import Prediction, RiskLevel
    from app.models.alert import Alert, AlertType, AlertSeverity

    device = Device(
        source_machine_id=1, device_name="Ventilator - 001", device_type=DeviceType.VENTILATOR,
        manufacturer="Draeger", model="model3", department="ICU", location="ICU - Room 101",
        purchase_date=date(2020, 1, 1), warranty_expiry=date(2023, 1, 1), expected_lifespan_years=10,
        age_years=5, status=DeviceStatus.WARNING, current_failure_probability=0.42, current_rul_days=45,
    )
    db.add(device)
    db.commit()
    db.refresh(device)

    db.add(TelemetryReading(
        device_id=device.id, recorded_at=datetime.now(timezone.utc), voltage=175, fan_speed=430,
        power_consumption=105, vibration=42, temperature=38.5, cpu_utilization=55, battery_health=80,
        operating_hours=1000, usage_count=500, network_status=True, calibration_status=True,
    ))
    db.add(Prediction(
        device_id=device.id, predicted_at=datetime.now(timezone.utc), failure_probability=0.42,
        risk_level=RiskLevel.MEDIUM, remaining_useful_life_days=45, prob_failure_7d=0.05,
        prob_failure_30d=0.25, prob_failure_90d=0.5, predicted_subsystem="Cooling Fan",
        model_version="v1.0.0-test",
        shap_explanations=[{"feature": "temp_trend", "impact": 0.18, "explanation": "Temperature increased 18% over the last week."}],
        recommendations=["Inspect cooling fan", "Schedule preventive maintenance within 5 days"],
    ))
    db.add(Alert(
        device_id=device.id, alert_type=AlertType.ABNORMAL_TEMPERATURE, severity=AlertSeverity.WARNING,
        message="Temperature abnormal on Ventilator - 001", created_at=datetime.now(timezone.utc),
    ))
    db.commit()
    db.close()


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_device_list(client):
    r = client.get("/api/v1/devices")
    assert r.status_code == 200
    devices = r.json()
    assert len(devices) == 1
    assert devices[0]["device_name"] == "Ventilator - 001"


def test_device_ranking(client):
    r = client.get("/api/v1/devices/ranking")
    assert r.status_code == 200
    assert r.json()[0]["current_failure_probability"] == 0.42


def test_analytics_overview(client):
    r = client.get("/api/v1/analytics/overview")
    assert r.status_code == 200
    body = r.json()
    assert body["total_devices"] == 1
    assert body["warning_devices"] == 1


def test_alerts_list(client):
    r = client.get("/api/v1/alerts")
    assert r.status_code == 200
    assert len(r.json()) == 1
    assert r.json()[0]["acknowledged"] is False


def test_digital_twin_aggregates_everything(client):
    device_id = client.get("/api/v1/devices").json()[0]["id"]
    r = client.get(f"/api/v1/digital-twin/{device_id}")
    assert r.status_code == 200
    body = r.json()
    assert body["device"]["device_name"] == "Ventilator - 001"
    assert len(body["telemetry_trend"]) == 1
    assert len(body["prediction_history"]) == 1
    assert body["prediction_history"][0]["predicted_subsystem"] == "Cooling Fan"


def test_alert_acknowledge_roundtrip(client):
    alert_id = client.get("/api/v1/alerts").json()[0]["id"]
    r = client.post(f"/api/v1/alerts/{alert_id}/acknowledge", params={"acknowledged_by": "Test Engineer"})
    assert r.status_code == 200
    assert r.json()["acknowledged"] is True
    assert r.json()["acknowledged_by"] == "Test Engineer"

    r2 = client.get("/api/v1/alerts", params={"acknowledged": True})
    assert len(r2.json()) == 1


def test_device_not_found_returns_404(client):
    r = client.get("/api/v1/devices/does-not-exist")
    assert r.status_code == 404
