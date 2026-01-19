
# flight_ml.py (minimal version)

import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error

# ---- Clean + feature engineering ----
def prepare(df: pd.DataFrame) -> pd.DataFrame:
    d = df.copy()

    d = d.replace({"null": np.nan})

    # datetime parsing
    d["dep_sched"] = pd.to_datetime(d["departure_scheduled_date"] + " " + d["departure_scheduled_time"], errors="coerce")
    d["dep_actual"] = pd.to_datetime(d["departure_actual_date"] + " " + d["departure_actual_time"], errors="coerce")
    d["arr_sched"] = pd.to_datetime(d["arrival_scheduled_date"] + " " + d["arrival_scheduled_time"], errors="coerce")
    d["arr_actual"] = pd.to_datetime(d["arrival_actual_date"] + " " + d["arrival_actual_time"], errors="coerce")

    d["arrival_delay"] = (d["arr_actual"] - d["arr_sched"]).dt.total_seconds() / 60
    d["dep_delay"]     = (d["dep_actual"] - d["dep_sched"]).dt.total_seconds() / 60

    # Simple model features
    d["dep_hour"] = d["dep_sched"].dt.hour
    d["dep_dow"]  = d["dep_sched"].dt.dayofweek

    return d


# ---- Train simple linear regression ----
def train_model(df: pd.DataFrame):
    df = df.dropna(subset=["arrival_delay"]).copy()

    X = df[["dep_delay", "dep_hour", "dep_dow"]]
    y = df["arrival_delay"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    model = LinearRegression()
    model.fit(X_train, y_train)

    pred = model.predict(X_test)

    metrics = {
        "rmse": float(np.sqrt(mean_squared_error(y_test, pred))),
        "mae":  float(mean_absolute_error(y_test, pred)),
        "r2":   float(r2_score(y_test, pred))
    }

    return model, metrics


# ---- Prediction table ----
def predict_latest(model, df: pd.DataFrame, n=15):
    latest = df.sort_values("dep_sched", ascending=False).head(n)
    X = latest[["dep_delay", "dep_hour", "dep_dow"]]
    latest["pred_delay"] = model.predict(X)
    return latest[[
        "id", "route_key", "dep_sched", "arr_sched",
        "arrival_delay", "pred_delay"
    ]]
