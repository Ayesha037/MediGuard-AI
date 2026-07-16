"""
Loads the trained model artifacts once at process startup and serves
predictions from them. A module-level singleton, not re-loaded per
request — model loading (deserializing 5 files, building a SHAP
explainer) takes real time and should happen once per process, not once
per HTTP call.
"""
import json
import logging
import os

import joblib
import pandas as pd

from app.config import settings
from app.constants import FEATURE_COLUMNS, SENSOR_COLUMNS, SUBSYSTEMS
from app.shap_explainer import ShapExplainer
from app.recommendation_engine import generate_recommendations

logger = logging.getLogger("mediguard.inference")


class ModelNotLoadedError(RuntimeError):
    pass


class PredictionEngine:
    def __init__(self, artifact_dir: str):
        with open(os.path.join(artifact_dir, "latest.json")) as f:
            self.version = json.load(f)["version"]
        model_dir = os.path.join(artifact_dir, self.version)

        logger.info("Loading model artifacts from %s (version=%s)", model_dir, self.version)

        self.clf_7d = joblib.load(os.path.join(model_dir, "clf_7d.joblib"))
        self.clf_30d = joblib.load(os.path.join(model_dir, "clf_30d.joblib"))
        self.clf_90d = joblib.load(os.path.join(model_dir, "clf_90d.joblib"))
        self.rul_model = joblib.load(os.path.join(model_dir, "rul_regressor.joblib"))
        self.anomaly_model = joblib.load(os.path.join(model_dir, "anomaly_detector.joblib"))

        with open(os.path.join(model_dir, "metadata.json")) as f:
            self.metadata = json.load(f)
        self.associations = self.metadata["error_subsystem_associations"]

        assert self.metadata["feature_columns"] == FEATURE_COLUMNS, (
            "Feature schema mismatch between this service's constants.py and the "
            "model's training metadata -- predictions would be silently wrong. "
            "Update constants.py to match metadata.json exactly."
        )

        self.shap_explainer = ShapExplainer(self.clf_30d)
        logger.info("Model loaded successfully. Ready to serve predictions.")

    def _predict_subsystem(self, feature_row: dict) -> str:
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

    def predict(self, feature_row: dict) -> dict:
        X = pd.DataFrame([[feature_row[c] for c in FEATURE_COLUMNS]], columns=FEATURE_COLUMNS).astype(float)

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

        rul_days = max(0.0, float(self.rul_model.predict(X)[0]))

        sensor_X = pd.DataFrame([[feature_row[c] for c in SENSOR_COLUMNS]], columns=SENSOR_COLUMNS).astype(float)
        anomaly_score = float(self.anomaly_model.decision_function(sensor_X)[0])
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
            "is_anomaly": is_anomaly,
            "shap_explanations": shap_reasons,
            "recommendations": recommendations,
            "model_version": self.version,
        }


_engine: PredictionEngine | None = None


def load_engine() -> PredictionEngine:
    global _engine
    _engine = PredictionEngine(settings.ARTIFACT_DIR)
    return _engine


def get_engine() -> PredictionEngine:
    if _engine is None:
        raise ModelNotLoadedError("Model not loaded yet -- service is still starting up.")
    return _engine
