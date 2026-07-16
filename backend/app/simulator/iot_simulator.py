"""
Simulated IoT Data (spec feature #11).

Since the historical Azure PdM dataset stops at 2016-01-01, this simulator
generates *live* ticks going forward from each device's last known reading,
using the same statistical envelope (mean/std) as the real historical data
per device, so the live dashboard behaves consistently with the ingested
history rather than jumping to unrelated random numbers.

Occasionally (low probability, higher for older/already-degraded devices)
it injects a drift event — a gradual anomalous trend in one sensor — which
is what the ML prediction pipeline is meant to catch before a failure.
"""
import asyncio
import logging
from datetime import datetime, timezone

import numpy as np

from app.core.database import SessionLocal
from app.models.device import Device
from app.models.telemetry import TelemetryReading
from app.core.config import settings
from app.simulator.connection_manager import connection_manager

logger = logging.getLogger(__name__)

# Per-device drift state: device_id -> {"sensor": str, "magnitude": float, "ticks_remaining": int}
_drift_state: dict[str, dict] = {}
_rng = np.random.default_rng()


def _maybe_start_drift(device: Device):
    """Randomly start a degradation drift on a device, weighted by age."""
    if device.id in _drift_state:
        return
    base_prob = 0.0008 + (device.age_years / 20) * 0.003  # older devices drift more often
    if _rng.random() < base_prob:
        sensor = _rng.choice(["temperature", "vibration", "power_consumption", "battery_health"])
        _drift_state[device.id] = {
            "sensor": sensor,
            "magnitude": float(_rng.uniform(0.5, 2.0)),
            "ticks_remaining": int(_rng.integers(50, 300)),
        }
        logger.info("Drift started on device %s sensor=%s", device.device_name, sensor)


def _generate_tick(device: Device, last: TelemetryReading | None) -> dict:
    """Generate the next synthetic reading for a device."""
    _maybe_start_drift(device)
    drift = _drift_state.get(device.id)

    if last:
        voltage = last.voltage + _rng.normal(0, 2)
        fan_speed = last.fan_speed + _rng.normal(0, 5)
        power_consumption = last.power_consumption + _rng.normal(0, 2)
        vibration = last.vibration + _rng.normal(0, 1)
        temperature = last.temperature + _rng.normal(0, 0.3)
        cpu_utilization = last.cpu_utilization + _rng.normal(0, 2)
        battery_health = last.battery_health - abs(_rng.normal(0.01, 0.01))
        operating_hours = last.operating_hours + 1
        usage_count = last.usage_count + int(_rng.integers(0, 3))
    else:
        voltage, fan_speed, power_consumption, vibration = 170.0, 450.0, 100.0, 40.0
        temperature, cpu_utilization, battery_health = 37.0, 45.0, 90.0
        operating_hours, usage_count = 0.0, 0

    if drift:
        sensor, magnitude = drift["sensor"], drift["magnitude"]
        if sensor == "temperature":
            temperature += magnitude * 0.05
        elif sensor == "vibration":
            vibration += magnitude * 0.08
        elif sensor == "power_consumption":
            power_consumption += magnitude * 0.15
        elif sensor == "battery_health":
            battery_health -= magnitude * 0.03
        drift["ticks_remaining"] -= 1
        if drift["ticks_remaining"] <= 0:
            del _drift_state[device.id]

    return dict(
        voltage=round(float(np.clip(voltage, 100, 250)), 2),
        fan_speed=round(float(np.clip(fan_speed, 200, 600)), 2),
        power_consumption=round(float(np.clip(power_consumption, 60, 200)), 2),
        vibration=round(float(np.clip(vibration, 10, 80)), 2),
        temperature=round(float(np.clip(temperature, 30, 60)), 2),
        cpu_utilization=round(float(np.clip(cpu_utilization, 5, 100)), 2),
        battery_health=round(float(np.clip(battery_health, 0, 100)), 2),
        operating_hours=operating_hours,
        usage_count=usage_count,
        network_status=bool(_rng.random() > 0.02),
        calibration_status=bool(_rng.random() > 0.015),
    )


async def run_simulator_loop():
    """
    Background task: every SIMULATOR_TICK_SECONDS, generate one new reading
    per device, persist it, and broadcast it to connected WebSocket clients.
    Runs forever as an asyncio task started on FastAPI startup.
    """
    while True:
        try:
            db = SessionLocal()
            devices = db.query(Device).all()
            for device in devices:
                last = (
                    db.query(TelemetryReading)
                    .filter(TelemetryReading.device_id == device.id)
                    .order_by(TelemetryReading.recorded_at.desc())
                    .first()
                )
                tick = _generate_tick(device, last)
                reading = TelemetryReading(
                    device_id=device.id,
                    recorded_at=datetime.now(timezone.utc),
                    **tick,
                )
                db.add(reading)
                await connection_manager.broadcast({
                    "device_id": device.id,
                    "device_name": device.device_name,
                    "recorded_at": reading.recorded_at,
                    **tick,
                })
            db.commit()
            db.close()
        except Exception:
            logger.exception("Simulator tick failed")
        await asyncio.sleep(settings.SIMULATOR_TICK_SECONDS)
