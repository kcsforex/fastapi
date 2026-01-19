# flight_ml.py
# ---------------------------------------------
# Reusable ML utilities for flight delay modeling
# ---------------------------------------------

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Tuple

import numpy as np
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    mean_absolute_error, mean_squared_error, r2_score,
    confusion_matrix, roc_auc_score
)

# ---------- Feature config ----------
FEATURE_COLS = [
    "route_key",
    "departure_airport_code",
    "arrival_airport_code",
    "operatingcarrier_airlineid",
    "operatingcarrier_flightnumber",
    "equipment_aircraftcode",
    "departure_terminal_gate",
    "dep_delay_min",
    "dep_hour",
    "dep_dow",
]
NUM_FEATURES = ["dep_delay_min", "dep_hour", "dep_dow"]
CAT_FEATURES = list(sorted(set(FEATURE_COLS) - set(NUM_FEATURES)))


@dataclass
class RegressionMetrics:
    mae: float
    rmse: float
    r2: float

@dataclass
class ClassificationMetrics:
    confusion: np.ndarray
    auc: Optional[float]

@dataclass
class TrainedModels:
    reg_pipe: Pipeline
    clf_pipe: Pipeline
    reg_metrics: RegressionMetrics
    clf_metrics: ClassificationMetrics


# ---------- Cleaning & features ----------
def clean_and_feature_engineer(df: pd.DataFrame) -> pd.DataFrame:
    data = df.copy()
    data = data.replace({"null": np.nan, "NULL": np.nan, "Null": np.nan})

    # Coerce to string for safe concat
    for c in [
        "departure_scheduled_date","departure_scheduled_time",
        "departure_actual_date","departure_actual_time",
        "arrival_scheduled_date","arrival_scheduled_time",
        "arrival_actual_date","arrival_actual_time"
    ]:
        if c in data.columns:
            data[c] = data[c].astype(str)

    def combine_dt(date_col: str, time_col: str, out_col: str):
        data[out_col] = pd.to_datetime(
            data[date_col].str.strip() + " " + data[time_col].str.strip(),
            errors="coerce"
        )

    combine_dt("departure_scheduled_date", "departure_scheduled_time", "dep_sched_dt")
    combine_dt("departure_actual_date", "departure_actual_time", "dep_actual_dt")
    combine_dt("arrival_scheduled_date", "arrival_scheduled_time", "arr_sched_dt")
    combine_dt("arrival_actual_date", "arrival_actual_time", "arr_actual_dt")

    # Targets & time features
    data["arrival_delay_min"] = (data["arr_actual_dt"] - data["arr_sched_dt"]).dt.total_seconds() / 60.0
    data["dep_delay_min"]     = (data["dep_actual_dt"] - data["dep_sched_dt"]).dt.total_seconds() / 60.0
    data["dep_hour"] = data["dep_sched_dt"].dt.hour
    data["dep_dow"]  = data["dep_sched_dt"].dt.dayofweek
    data["is_delayed"] = (data["arrival_delay_min"] >= 15).astype(int)
    return data


# ---------- Pipelines ----------
def _make_ohe() -> OneHotEncoder:
    try:
        return OneHotEncoder(handle_unknown="ignore", sparse_output=True)
    except TypeError:
        return OneHotEncoder(handle_unknown="ignore", sparse=True)

def build_preprocess() -> ColumnTransformer:
    num = Pipeline([("imputer", SimpleImputer(strategy="median"))])
    cat = Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("ohe", _make_ohe())
    ])
    return ColumnTransformer([
        ("num", num, NUM_FEATURES),
        ("cat", cat, CAT_FEATURES)
    ])

def make_regression_pipeline() -> Pipeline:
    return Pipeline([
        ("preprocess", build_preprocess()),
        ("model", LinearRegression())
    ])

def make_classification_pipeline() -> Pipeline:
    return Pipeline([
        ("preprocess", build_preprocess()),
        ("model", LogisticRegression(max_iter=200, class_weight="balanced"))
    ])


# ---------- Training & evaluation ----------
def train_models(
    data: pd.DataFrame,
    time_aware: bool = False,
    time_split_ratio: float = 0.8,
    random_state: int = 42
) -> TrainedModels:

    reg_df = data.dropna(subset=["arrival_delay_min"]).copy()
    clf_df = reg_df.dropna(subset=["is_delayed"]).copy()

    Xr, yr = reg_df[FEATURE_COLS], reg_df["arrival_delay_min"].astype(float)
    Xc, yc = clf_df[FEATURE_COLS], clf_df["is_delayed"].astype(int)

    # Choose split
    if time_aware:
        reg_df = reg_df.sort_values("dep_sched_dt")
        clf_df = clf_df.sort_values("dep_sched_dt")
        r_idx = int(len(reg_df) * time_split_ratio)
        c_idx = int(len(clf_df) * time_split_ratio)
        Xr_train, Xr_test = reg_df[FEATURE_COLS].iloc[:r_idx], reg_df[FEATURE_COLS].iloc[r_idx:]
        yr_train, yr_test = reg_df["arrival_delay_min"].iloc[:r_idx], reg_df["arrival_delay_min"].iloc[r_idx:]
        Xc_train, Xc_test = clf_df[FEATURE_COLS].iloc[:c_idx], clf_df[FEATURE_COLS].iloc[c_idx:]
        yc_train, yc_test = clf_df["is_delayed"].iloc[:c_idx], clf_df["is_delayed"].iloc[c_idx:]
    else:
        Xr_train, Xr_test, yr_train, yr_test = train_test_split(Xr, yr, test_size=0.2, random_state=random_state)
        try:
            Xc_train, Xc_test, yc_train, yc_test = train_test_split(Xc, yc, test_size=0.25, random_state=random_state, stratify=yc)
        except ValueError:
            Xc_train, Xc_test, yc_train, yc_test = train_test_split(Xc, yc, test_size=0.25, random_state=random_state)

    reg_pipe = make_regression_pipeline()
    clf_pipe = make_classification_pipeline()

    reg_pipe.fit(Xr_train, yr_train)
    clf_pipe.fit(Xc_train, yc_train)

    yr_pred = reg_pipe.predict(Xr_test)
    reg_metrics = RegressionMetrics(
        mae=float(mean_absolute_error(yr_test, yr_pred)),
        rmse=float(mean_squared_error(yr_test, yr_pred, squared=False)),
        r2=float(r2_score(yr_test, yr_pred))
    )

    y_prob = clf_pipe.predict_proba(Xc_test)[:, 1]
    y_pred = (y_prob >= 0.5).astype(int)
    conf = confusion_matrix(yc_test, y_pred)
    try:
        auc = float(roc_auc_score(yc_test, y_prob))
    except ValueError:
        auc = None

    clf_metrics = ClassificationMetrics(confusion=conf, auc=auc)
    return TrainedModels(reg_pipe, clf_pipe, reg_metrics, clf_metrics)


# ---------- Predictions ----------
def predict_latest(models: TrainedModels, data: pd.DataFrame, n_rows: int = 20, threshold: float = 0.5) -> pd.DataFrame:
    recent = data.sort_values("dep_sched_dt", ascending=False).head(n_rows).copy()
    recent["pred_delay_min"] = models.reg_pipe.predict(recent[FEATURE_COLS])
    recent["pred_delay_prob"] = models.clf_pipe.predict_proba(recent[FEATURE_COLS])[:, 1]
    recent["pred_delay_flag"] = (recent["pred_delay_prob"] >= threshold).astype(int)

    keep = [
        "id", "route_key",
        "dep_sched_dt", "arr_sched_dt",
        "arrival_delay_min", "is_delayed",
        "operatingcarrier_airlineid", "operatingcarrier_flightnumber",
        "equipment_aircraftcode",
        "pred_delay_min", "pred_delay_prob", "pred_delay_flag"
    ]
    return recent[[c for c in keep if c in recent.columns]]
