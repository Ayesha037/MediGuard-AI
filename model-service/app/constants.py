"""
Constants that MUST match what the model was trained on. If you retrain
the model with a different feature set, update FEATURE_COLUMNS here (or
better, generate this file from the training run's metadata.json so it
can never silently drift out of sync — see scripts/sync_from_training.py).
"""
FEATURE_COLUMNS = [
    "voltage", "fan_speed", "power_consumption", "vibration",
    "temperature", "cpu_utilization", "battery_health",
    "temperature_7d_mean", "vibration_7d_mean", "power_consumption_7d_mean", "battery_health_7d_mean",
    "temperature_7d_trend_pct", "vibration_7d_trend_pct", "power_consumption_7d_trend_pct", "battery_health_7d_trend_pct",
    "errors_7d", "errors_30d",
    "days_since_maint_cooling", "days_since_maint_power", "days_since_maint_sensor", "days_since_maint_battery",
    "age_years",
]

SENSOR_COLUMNS = [
    "voltage", "fan_speed", "power_consumption", "vibration",
    "temperature", "cpu_utilization", "battery_health",
]

SUBSYSTEMS = ["Cooling Fan", "Power Supply Unit", "Sensor Calibration Module", "Battery"]
