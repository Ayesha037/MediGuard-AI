"""
Rule-based recommendation engine — auditable by design. A medical
equipment company's biomedical engineering team needs to be able to trace
"why did the system tell us to replace this battery" back to a fixed rule,
not a second black-box model.
"""
SUBSYSTEM_ACTIONS = {
    "Cooling Fan": "Inspect and clean/replace cooling fan",
    "Power Supply Unit": "Inspect power supply unit for voltage irregularities",
    "Sensor Calibration Module": "Recalibrate sensors",
    "Battery": "Replace battery",
}

FEATURE_ACTIONS = {
    "temperature": "Investigate elevated operating temperature",
    "temperature_7d_trend_pct": "Investigate rising temperature trend",
    "vibration": "Inspect for mechanical wear causing abnormal vibration",
    "vibration_7d_trend_pct": "Inspect for developing mechanical wear",
    "battery_health": "Schedule battery health check",
    "battery_health_7d_trend_pct": "Schedule battery replacement evaluation",
    "power_consumption": "Inspect power supply for abnormal draw",
    "errors_7d": "Review recent error logs with biomedical engineering team",
    "errors_30d": "Review recent error logs with biomedical engineering team",
    "days_since_maint_cooling": "Schedule overdue cooling fan maintenance",
    "days_since_maint_power": "Schedule overdue power supply maintenance",
    "days_since_maint_sensor": "Schedule overdue sensor recalibration",
    "days_since_maint_battery": "Schedule overdue battery replacement",
}


def generate_recommendations(
    risk_level: str,
    predicted_subsystem: str | None,
    shap_reasons: list[dict],
    rul_days: float,
) -> list[str]:
    recommendations: list[str] = []

    if predicted_subsystem and predicted_subsystem in SUBSYSTEM_ACTIONS:
        recommendations.append(SUBSYSTEM_ACTIONS[predicted_subsystem])

    for reason in shap_reasons[:3]:
        action = FEATURE_ACTIONS.get(reason["feature"])
        if action and action not in recommendations:
            recommendations.append(action)

    if risk_level == "High":
        recommendations.append(f"Schedule preventive maintenance within {max(1, min(5, int(rul_days)))} days")
    elif risk_level == "Medium":
        recommendations.append("Schedule preventive maintenance within 2 weeks")
    else:
        recommendations.append("Continue routine monitoring — no immediate action required")

    seen = set()
    deduped = []
    for r in recommendations:
        if r not in seen:
            deduped.append(r)
            seen.add(r)
    return deduped[:5]
