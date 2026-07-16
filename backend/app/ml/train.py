import json
import os
from datetime import datetime, timezone

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.metrics import roc_auc_score, precision_score, recall_score, f1_score, mean_absolute_error
from xgboost import XGBClassifier
from lightgbm import LGBMRegressor

from app.ml.feature_engineering import build_feature_table, FEATURE_COLUMNS, SUBSYSTEMS

ARTIFACT_ROOT = os.path.join(os.path.dirname(__file__), "artifacts")


def time_based_split(df: pd.DataFrame, split_date: str):
    train = df[df["date"] < split_date].copy()
    test = df[df["date"] >= split_date].copy()
    return train, test


def train_failure_classifiers(train_df, test_df):
    """One XGBoost classifier per horizon (7d/30d/90d)."""
    models, metrics = {}, {}
    for horizon in ["7d", "30d", "90d"]:
        label_col = f"failure_{horizon}"
        X_train, y_train = train_df[FEATURE_COLUMNS], train_df[label_col]
        X_test, y_test = test_df[FEATURE_COLUMNS], test_df[label_col]

        model = XGBClassifier(
            n_estimators=200, max_depth=4, learning_rate=0.05,
            subsample=0.8, colsample_bytree=0.8,
            eval_metric="logloss", random_state=42,
        )
        model.fit(X_train, y_train)

        proba = model.predict_proba(X_test)[:, 1]
        preds = (proba >= 0.5).astype(int)

        metrics[horizon] = {
            "auc": float(roc_auc_score(y_test, proba)) if y_test.nunique() > 1 else None,
            "precision": float(precision_score(y_test, preds, zero_division=0)),
            "recall": float(recall_score(y_test, preds, zero_division=0)),
            "f1": float(f1_score(y_test, preds, zero_division=0)),
            "positive_rate_test": float(y_test.mean()),
        }
        models[horizon] = model
        print(f"  [{horizon}] AUC={metrics[horizon]['auc']:.4f}  "
              f"P={metrics[horizon]['precision']:.3f}  R={metrics[horizon]['recall']:.3f}  "
              f"F1={metrics[horizon]['f1']:.3f}")
    return models, metrics


def train_rul_regressor(train_df, test_df):
    X_train, y_train = train_df[FEATURE_COLUMNS], train_df["rul_days"]
    X_test, y_test = test_df[FEATURE_COLUMNS], test_df["rul_days"]

    model = LGBMRegressor(n_estimators=300, max_depth=5, learning_rate=0.05, random_state=42, verbose=-1)
    model.fit(X_train, y_train)

    preds = model.predict(X_test)
    mae = float(mean_absolute_error(y_test, preds))
    print(f"  RUL regressor MAE = {mae:.2f} days")
    return model, {"mae_days": mae}


def train_anomaly_detector(train_df):
    """Unsupervised — trained on ALL data assuming most operating time is
    normal (standard predictive-maintenance assumption: failures are rare
    events relative to total operating hours)."""
    from app.ml.feature_engineering import SENSOR_COLS
    X = train_df[SENSOR_COLS]
    model = IsolationForest(n_estimators=200, contamination=0.05, random_state=42)
    model.fit(X)
    return model


def build_error_subsystem_associations(train_df: pd.DataFrame) -> dict:
    associations = {}
    positive = train_df[train_df["failure_7d"] == 1]
    for subsystem in SUBSYSTEMS:
        subset = positive[positive["failure_subsystem"] == subsystem]
        associations[subsystem] = {
            "avg_errors_7d_before_failure": float(subset["errors_7d"].mean()) if len(subset) else 0.0,
            "avg_days_since_maint_before_failure": float(
                subset[f"days_since_maint_{subsystem.split()[0].lower()}"].mean()
            ) if len(subset) else 0.0,
            "share_of_failures": float(len(subset) / len(positive)) if len(positive) else 0.25,
        }
    return associations


def run_training():
    print("Loading engineered feature table...")
    df = build_feature_table()
    print(f"  {df.shape[0]:,} rows, {df.shape[1]} columns")

    split_date = "2015-10-01"  
    train_df, test_df = time_based_split(df, split_date)
    print(f"  Train: {len(train_df):,} rows | Test: {len(test_df):,} rows (split at {split_date})")

    print("\nTraining failure probability classifiers (7d / 30d / 90d)...")
    classifiers, clf_metrics = train_failure_classifiers(train_df, test_df)

    print("\nTraining RUL regressor...")
    rul_model, rul_metrics = train_rul_regressor(train_df, test_df)

    print("\nTraining anomaly detector...")
    anomaly_model = train_anomaly_detector(train_df)

    print("\nBuilding error->subsystem associations...")
    associations = build_error_subsystem_associations(train_df)

    version = datetime.now(timezone.utc).strftime("v%Y%m%d_%H%M%S")
    out_dir = os.path.join(ARTIFACT_ROOT, version)
    os.makedirs(out_dir, exist_ok=True)

    joblib.dump(classifiers["7d"], os.path.join(out_dir, "clf_7d.joblib"))
    joblib.dump(classifiers["30d"], os.path.join(out_dir, "clf_30d.joblib"))
    joblib.dump(classifiers["90d"], os.path.join(out_dir, "clf_90d.joblib"))
    joblib.dump(rul_model, os.path.join(out_dir, "rul_regressor.joblib"))
    joblib.dump(anomaly_model, os.path.join(out_dir, "anomaly_detector.joblib"))

    with open(os.path.join(out_dir, "metadata.json"), "w") as f:
        json.dump({
            "version": version,
            "trained_at": datetime.now(timezone.utc).isoformat(),
            "feature_columns": FEATURE_COLUMNS,
            "split_date": split_date,
            "classifier_metrics": clf_metrics,
            "rul_metrics": rul_metrics,
            "error_subsystem_associations": associations,
        }, f, indent=2)

    latest_path = os.path.join(ARTIFACT_ROOT, "latest.json")
    with open(latest_path, "w") as f:
        json.dump({"version": version}, f)

    print(f"\nArtifacts saved to {out_dir}")
    print(f"Latest pointer updated -> {version}")
    return version


if __name__ == "__main__":
    run_training()
