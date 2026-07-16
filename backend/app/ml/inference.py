import json
import os

import joblib
import numpy as np
import pandas as pd

from app.core.config import settings
from app.ml.feature_engineering import FEATURE_COLUMNS, SUBSYSTEMS
from app.ml.shap_explainer import ShapExplainer
from app.ml.recommendation_engine import generate_recommendations

ARTIFACT_ROOT = os.path.join(os.path.dirname(__file__), "artifacts")


class PredictionEngine:
    def __init__(self, version: str | None = None):
        if version is None:
            with open(os.path.join(ARTIFACT_ROOT, "latest.json")) as f:
                version = json.load(f)["version"]
        self.version = version
        model_dir = os.path.join(ARTIFACT_ROOT, version)

        self.clf_7d = joblib.load(os.path.join(model_dir, "clf_7d.joblib"))
        self.clf_30d = joblib.load(os.path.join(model_dir, "clf_30d.joblib"))
        self.clf_90d = joblib.load(os.path.join(model_dir, "clf_90d.joblib"))
        self.rul_model = joblib.load(os.path.join(model_dir, "rul_regressor.joblib"))
        self.anomaly_model = joblib.load(os.path.join(model_dir, "anomaly_detector.joblib"))

        with open(os.path.join(model_dir, "metadata.json")) as f:
            self.metadata = json.load(f)
        self.associations = self.metadata["error_subsystem_associations"]

        self.shap_explainer = ShapExplainer(self.clf_30d)

    def _predict_subsystem(self, feature_row: pd.Series) -> str:

        scores = {}
        for subsystem in SUBSYSTEMS:
            assoc = self.associations[subsystem]
            col = f"days_since_maint_{subsystem.split()[0].lower()}"
            days_since = feature_row[col]
            errors = feature_row["errors_7d"]

            maint_gap = abs(days_since - assoc["avg_days_since_maint_before_failure"])
            error_gap = abs(errors - assoc["avg_errors_7d_before_failure"])
            score = assoc["share_of_failures"] / (1 + maint_gap * 0.01 + error_gap * 0.5)
            scores[subsystem] = score
        return max(scores, key=scores.get)

    def predict(self, feature_row: pd.Series) -> dict:
        X = feature_row[FEATURE_COLUMNS].to_frame().T.astype(float)

        prob_7d = float(self.clf_7d.predict_proba(X)[0, 1])
        prob_30d = float(self.clf_30d.predict_proba(X)[0, 1])
        prob_90d = float(self.clf_90d.predict_proba(X)[0, 1])

        failure_probability = prob_30d

        if failure_probability >= settings.FAILURE_PROB_HIGH_THRESHOLD:
            risk_level = "High"
        elif failure_probability >= settings.FAILURE_PROB_MEDIUM_THRESHOLD:
            risk_level = "Medium"
        else:
            risk_level = "Low"

        rul_days = float(self.rul_model.predict(X)[0])
        rul_days = max(0.0, rul_days)

        anomaly_score = float(self.anomaly_model.decision_function(feature_row[
            ["voltage", "fan_speed", "power_consumption", "vibration",
             "temperature", "cpu_utilization", "battery_health"]
        ].to_frame().T.astype(float))[0])
        is_anomaly = anomaly_score < 0

        predicted_subsystem = self._predict_subsystem(feature_row)
        shap_reasons = self.shap_explainer.top_reasons(feature_row, top_k=5)

        if is_anomaly:
            shap_reasons.insert(0, {
                "feature": "anomaly_score",
                "impact": round(abs(anomaly_score), 4),
                "explanation": "Sensor readings deviate from the device's normal operating envelope (anomaly detected).",
            })
            shap_reasons = shap_reasons[:5]

        recommendations = generate_recommendations(risk_level, predicted_subsystem, shap_reasons, rul_days)

        return {
            "failure_probability": round(failure_probability, 4),
            "risk_level": risk_level,
            "remaining_useful_life_days": round(rul_days, 1),
            "prob_failure_7d": round(prob_7d, 4),
            "prob_failure_30d": round(prob_30d, 4),
            "prob_failure_90d": round(prob_90d, 4),
            "predicted_subsystem": predicted_subsystem,
            "model_version": self.version,
            "shap_explanations": shap_reasons,
            "recommendations": recommendations,
            "is_anomaly": is_anomaly,
        }


_engine_singleton: PredictionEngine | None = None


def get_prediction_engine() -> PredictionEngine:
    global _engine_singleton
    if _engine_singleton is None:
        _engine_singleton = PredictionEngine()
    return _engine_singleton
