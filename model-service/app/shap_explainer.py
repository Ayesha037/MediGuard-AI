"""
SHAP-based explainability — the model never returns a bare probability
without a reason. This is a direct, behavior-preserving port from the
main MediGuard ML pipeline.
"""
import shap
import pandas as pd

from app.constants import FEATURE_COLUMNS

EXPLANATION_TEMPLATES = {
    "temperature": "Temperature is elevated at {value:.1f}\u00b0C.",
    "temperature_7d_trend_pct": "Temperature has changed {pct:+.1f}% over the last week.",
    "vibration": "Vibration reading is {value:.1f}, above typical range.",
    "vibration_7d_trend_pct": "Vibration has changed {pct:+.1f}% over the last week.",
    "battery_health": "Battery health is at {value:.1f}%.",
    "battery_health_7d_trend_pct": "Battery health has changed {pct:+.1f}% over the last week.",
    "power_consumption": "Power consumption is at {value:.1f}W.",
    "power_consumption_7d_trend_pct": "Power consumption has changed {pct:+.1f}% over the last week.",
    "voltage": "Voltage reading is {value:.1f}V.",
    "fan_speed": "Fan speed is at {value:.0f} RPM.",
    "cpu_utilization": "CPU utilization is at {value:.1f}%.",
    "errors_7d": "{value:.0f} error events logged in the last 7 days.",
    "errors_30d": "{value:.0f} error events logged in the last 30 days.",
    "age_years": "Device is {value:.0f} years old.",
    "days_since_maint_cooling": "{value:.0f} days since the cooling fan was last serviced.",
    "days_since_maint_power": "{value:.0f} days since the power supply was last serviced.",
    "days_since_maint_sensor": "{value:.0f} days since sensor calibration was last performed.",
    "days_since_maint_battery": "{value:.0f} days since the battery was last replaced.",
}


def _humanize(feature: str, value: float) -> str:
    template = EXPLANATION_TEMPLATES.get(feature)
    if template is None:
        return f"{feature.replace('_', ' ').title()} is contributing to the risk score ({value:.2f})."
    try:
        return template.format(value=value, pct=value)
    except Exception:
        return f"{feature.replace('_', ' ').title()} is contributing to the risk score."


class ShapExplainer:
    def __init__(self, model):
        self.explainer = shap.TreeExplainer(model)

    def top_reasons(self, feature_row: dict, top_k: int = 5) -> list[dict]:
        X = pd.DataFrame([[feature_row[c] for c in FEATURE_COLUMNS]], columns=FEATURE_COLUMNS).astype(float)
        shap_values = self.explainer.shap_values(X)
        if isinstance(shap_values, list):
            shap_values = shap_values[0]
        contributions = shap_values[0]

        ranked = sorted(zip(FEATURE_COLUMNS, contributions), key=lambda x: -abs(x[1]))
        risk_increasing = [(f, v) for f, v in ranked if v > 0][:top_k]
        if len(risk_increasing) < top_k:
            remaining = [x for x in ranked if x not in risk_increasing][: top_k - len(risk_increasing)]
            risk_increasing.extend(remaining)

        results = []
        for feature, impact in risk_increasing:
            results.append({
                "feature": feature,
                "impact": round(float(impact), 4),
                "explanation": _humanize(feature, float(feature_row[feature])),
            })
        return results
