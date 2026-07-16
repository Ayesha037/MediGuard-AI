"""
Tests run against the REAL trained model artifacts shipped in
app/artifacts/ — not mocks. If these pass, the exact model that would be
deployed is verified end to end.
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app

VALID_KEY = "changeme-generate-a-real-key"

GOOD_PAYLOAD = {
    "device_id": "ventilator-023",
    "voltage": 191.3, "fan_speed": 410.0, "power_consumption": 108.2,
    "vibration": 48.5, "temperature": 39.1, "cpu_utilization": 62.0,
    "battery_health": 45.3,
    "temperature_7d_mean": 38.4, "temperature_7d_trend_pct": 4.2,
    "vibration_7d_mean": 46.0, "vibration_7d_trend_pct": 6.1,
    "power_consumption_7d_mean": 102.0, "power_consumption_7d_trend_pct": 8.6,
    "battery_health_7d_mean": 47.0, "battery_health_7d_trend_pct": -3.4,
    "errors_7d": 3, "errors_30d": 9,
    "days_since_maint_cooling": 210, "days_since_maint_power": 60,
    "days_since_maint_sensor": 45, "days_since_maint_battery": 300,
    "age_years": 17,
}


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def test_liveness(client):
    r = client.get("/health/live")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_readiness_reports_model_version(client):
    r = client.get("/health/ready")
    assert r.status_code == 200
    assert r.json()["model_version"] is not None


def test_predict_requires_api_key(client):
    r = client.post("/predict", json=GOOD_PAYLOAD)
    assert r.status_code == 401


def test_predict_rejects_wrong_api_key(client):
    r = client.post("/predict", headers={"X-API-Key": "not-the-real-key"}, json=GOOD_PAYLOAD)
    assert r.status_code == 401


def test_predict_returns_valid_prediction(client):
    r = client.post("/predict", headers={"X-API-Key": VALID_KEY}, json=GOOD_PAYLOAD)
    assert r.status_code == 200
    body = r.json()
    assert body["device_id"] == "ventilator-023"
    assert 0.0 <= body["failure_probability"] <= 1.0
    assert body["risk_level"] in {"Low", "Medium", "High"}
    assert len(body["shap_explanations"]) == 5
    assert 1 <= len(body["recommendations"]) <= 5
    assert body["remaining_useful_life_days"] >= 0


def test_predict_rejects_out_of_range_input(client):
    bad = {**GOOD_PAYLOAD, "temperature": 500}
    r = client.post("/predict", headers={"X-API-Key": VALID_KEY}, json=bad)
    assert r.status_code == 422


def test_predict_rejects_missing_field(client):
    bad = {k: v for k, v in GOOD_PAYLOAD.items() if k != "voltage"}
    r = client.post("/predict", headers={"X-API-Key": VALID_KEY}, json=bad)
    assert r.status_code == 422


def test_batch_predict(client):
    payload = {"devices": [GOOD_PAYLOAD, {**GOOD_PAYLOAD, "device_id": "mri-05"}]}
    r = client.post("/predict/batch", headers={"X-API-Key": VALID_KEY}, json=payload)
    assert r.status_code == 200
    body = r.json()
    assert body["count"] == 2
    assert {p["device_id"] for p in body["predictions"]} == {"ventilator-023", "mri-05"}


def test_batch_predict_rejects_empty_list(client):
    r = client.post("/predict/batch", headers={"X-API-Key": VALID_KEY}, json={"devices": []})
    assert r.status_code == 422


def test_model_info_requires_auth(client):
    r = client.get("/model-info")
    assert r.status_code == 401


def test_model_info_returns_metrics(client):
    r = client.get("/model-info", headers={"X-API-Key": VALID_KEY})
    assert r.status_code == 200
    body = r.json()
    assert "7d" in body["classifier_metrics"]
    assert "30d" in body["classifier_metrics"]
    assert "90d" in body["classifier_metrics"]


def test_response_has_request_id_header(client):
    r = client.get("/health/live")
    assert "X-Request-ID" in r.headers
