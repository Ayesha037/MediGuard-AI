import numpy as np
import pandas as pd
from sqlalchemy import create_engine

from app.core.config import settings

SENSOR_COLS = ["voltage", "fan_speed", "power_consumption", "vibration",
               "temperature", "cpu_utilization", "battery_health"]
TREND_SENSORS = ["temperature", "vibration", "power_consumption", "battery_health"]
SUBSYSTEMS = ["Cooling Fan", "Power Supply Unit", "Sensor Calibration Module", "Battery"]

RUL_CAP_DAYS = 120


def _load_raw_tables():
    engine = create_engine(settings.DATABASE_URL)
    devices = pd.read_sql("SELECT id as device_id, source_machine_id, age_years FROM devices", engine)
    telemetry = pd.read_sql(
        "SELECT device_id, recorded_at, voltage, fan_speed, power_consumption, vibration, "
        "temperature, cpu_utilization, battery_health FROM telemetry_readings", engine,
    )
    errors = pd.read_sql("SELECT device_id, occurred_at, error_code FROM error_logs", engine)
    maint = pd.read_sql("SELECT device_id, performed_at, subsystem FROM maintenance_records", engine)
    failures = pd.read_sql("SELECT device_id, occurred_at, subsystem FROM failure_events", engine)
    return devices, telemetry, errors, maint, failures


def _daily_sensor_aggregates(telemetry: pd.DataFrame) -> pd.DataFrame:
    telemetry = telemetry.copy()
    telemetry["date"] = pd.to_datetime(telemetry["recorded_at"]).dt.date
    daily = telemetry.groupby(["device_id", "date"])[SENSOR_COLS].mean().reset_index()
    daily["date"] = pd.to_datetime(daily["date"])
    daily = daily.sort_values(["device_id", "date"])
    return daily


def _add_rolling_trend_features(daily: pd.DataFrame) -> pd.DataFrame:
    daily = daily.copy()
    for col in TREND_SENSORS:

        rolling_mean = daily.groupby("device_id")[col].transform(lambda s: s.rolling(7, min_periods=1).mean())
        prior_mean = daily.groupby("device_id")[col].transform(lambda s: s.shift(7).rolling(7, min_periods=1).mean())
        daily[f"{col}_7d_mean"] = rolling_mean
        daily[f"{col}_7d_trend_pct"] = ((rolling_mean - prior_mean) / prior_mean.replace(0, np.nan)) * 100
        daily[f"{col}_7d_trend_pct"] = daily[f"{col}_7d_trend_pct"].fillna(0)
    return daily


def _add_error_counts(daily: pd.DataFrame, errors: pd.DataFrame) -> pd.DataFrame:
    errors = errors.copy()
    errors["date"] = pd.to_datetime(errors["occurred_at"]).dt.date
    errors["date"] = pd.to_datetime(errors["date"])

    daily = daily.copy()
    daily["errors_7d"] = 0
    daily["errors_30d"] = 0

    for device_id, group in daily.groupby("device_id"):
        dev_errors = errors[errors["device_id"] == device_id].sort_values("date")
        if dev_errors.empty:
            continue
        err_dates = dev_errors["date"].values
        for idx, row in group.iterrows():
            d = row["date"]
            daily.loc[idx, "errors_7d"] = int(((err_dates <= np.datetime64(d)) & (err_dates > np.datetime64(d - pd.Timedelta(days=7)))).sum())
            daily.loc[idx, "errors_30d"] = int(((err_dates <= np.datetime64(d)) & (err_dates > np.datetime64(d - pd.Timedelta(days=30)))).sum())
    return daily


def _add_days_since_maintenance(daily: pd.DataFrame, maint: pd.DataFrame) -> pd.DataFrame:
    maint = maint.copy()
    maint["date"] = pd.to_datetime(maint["performed_at"]).dt.date
    maint["date"] = pd.to_datetime(maint["date"])

    daily = daily.copy()
    for subsystem in SUBSYSTEMS:
        col = f"days_since_maint_{subsystem.split()[0].lower()}"
        daily[col] = 999  
    for device_id, group in daily.groupby("device_id"):
        dev_maint = maint[maint["device_id"] == device_id]
        for subsystem in SUBSYSTEMS:
            col = f"days_since_maint_{subsystem.split()[0].lower()}"
            sub_dates = dev_maint[dev_maint["subsystem"] == subsystem]["date"].values
            if len(sub_dates) == 0:
                continue
            for idx, row in group.iterrows():
                d = np.datetime64(row["date"])
                past = sub_dates[sub_dates <= d]
                if len(past) > 0:
                    days_since = (d - past.max()).astype("timedelta64[D]").astype(int)
                    daily.loc[idx, col] = days_since
    return daily


def _add_labels(daily: pd.DataFrame, failures: pd.DataFrame) -> pd.DataFrame:
    failures = failures.copy()
    failures["date"] = pd.to_datetime(failures["occurred_at"]).dt.date
    failures["date"] = pd.to_datetime(failures["date"])

    daily = daily.copy()
    daily["failure_7d"] = 0
    daily["failure_30d"] = 0
    daily["failure_90d"] = 0
    daily["failure_subsystem"] = None
    daily["rul_days"] = RUL_CAP_DAYS

    for device_id, group in daily.groupby("device_id"):
        dev_failures = failures[failures["device_id"] == device_id].sort_values("date")
        fail_dates = dev_failures["date"].values
        fail_subsystems = dev_failures["subsystem"].values
        for idx, row in group.iterrows():
            d = np.datetime64(row["date"])
            future_mask = fail_dates > d
            if future_mask.any():
                future_dates = fail_dates[future_mask]
                future_subs = fail_subsystems[future_mask]
                next_failure_date = future_dates.min()
                next_idx = np.argmin(future_dates)
                days_to_failure = (next_failure_date - d).astype("timedelta64[D]").astype(int)

                daily.loc[idx, "rul_days"] = min(days_to_failure, RUL_CAP_DAYS)
                daily.loc[idx, "failure_subsystem"] = future_subs[next_idx]
                daily.loc[idx, "failure_7d"] = int(days_to_failure <= 7)
                daily.loc[idx, "failure_30d"] = int(days_to_failure <= 30)
                daily.loc[idx, "failure_90d"] = int(days_to_failure <= 90)
    return daily


def build_feature_table() -> pd.DataFrame:

    devices, telemetry, errors, maint, failures = _load_raw_tables()

    daily = _daily_sensor_aggregates(telemetry)
    daily = _add_rolling_trend_features(daily)
    daily = _add_error_counts(daily, errors)
    daily = _add_days_since_maintenance(daily, maint)
    daily = _add_labels(daily, failures)

    daily = daily.merge(devices[["device_id", "age_years"]], on="device_id", how="left")

    return daily


FEATURE_COLUMNS = (
    SENSOR_COLS
    + [f"{c}_7d_mean" for c in TREND_SENSORS]
    + [f"{c}_7d_trend_pct" for c in TREND_SENSORS]
    + ["errors_7d", "errors_30d"]
    + [f"days_since_maint_{s.split()[0].lower()}" for s in SUBSYSTEMS]
    + ["age_years"]
)


if __name__ == "__main__":
    df = build_feature_table()
    print(f"Feature table shape: {df.shape}")
    print(f"Failure rate (30d label): {df['failure_30d'].mean():.4f}")
    df.to_parquet("/home/claude/mediguard-ai/ml-pipeline/data/feature_table.parquet")
    print("Saved to ml-pipeline/data/feature_table.parquet")
