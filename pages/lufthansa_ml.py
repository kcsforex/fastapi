
# 2026.01.20  14.00
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.tree import DecisionTreeRegressor, DecisionTreeClassifier
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier

from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error,  accuracy_score, precision_score, recall_score, f1_score

# ---- Clean + feature engineering ----
def prepare(df: pd.DataFrame) -> pd.DataFrame:
    
    d = df.copy()
    d = d.replace({"null": np.nan})
    d["dep_sched"] = pd.to_datetime(d["departure_scheduled_date"].astype(str) + " " + d["departure_scheduled_time"].astype(str), errors="coerce")
    d["dep_actual"] = pd.to_datetime(d["departure_actual_date"].astype(str) + " " + d["departure_actual_time"].astype(str), errors="coerce")
    d["arr_sched"] = pd.to_datetime(d["arrival_scheduled_date"].astype(str) + " " + d["arrival_scheduled_time"].astype(str), errors="coerce")
    d["arr_actual"] = pd.to_datetime(d["arrival_actual_date"].astype(str) + " " + d["arrival_actual_time"].astype(str), errors="coerce")

    d["arrival_delay"] = (d["arr_actual"] - d["arr_sched"]).dt.total_seconds() / 60
    d["dep_delay"]     = (d["dep_actual"] - d["dep_sched"]).dt.total_seconds() / 60
    d["dep_hour"] = d["dep_sched"].dt.hour
    d["dep_dow"]  = d["dep_sched"].dt.dayofweek
    d["is_delayed"] = (d["arrival_delay"] >= 15).astype("Int64")  # allow NA

    return d

# ========= Regression (arrival_delay minutes) =========
def reg_metrics(y_true, y_pred):
    metrics = { "rmse": float(np.sqrt(mean_squared_error(y_test, y_pred))),
                "mae":  float(mean_absolute_error(y_test, y_pred)),
                "r2":   float(r2_score(y_test, y_pred)) }   
    return mertics

def train_reg_linear(df: pd.DataFrame):
    df = df.dropna(subset=["arrival_delay"]).copy()
    X = df[["dep_delay", "dep_hour", "dep_dow"]].fillna(0)
    y = df["arrival_delay"].astype(float)
    X = X.fillna({"dep_delay": 0.0, "dep_hour": X["dep_hour"].median(), "dep_dow": X["dep_dow"].median()})
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    return regfit_and_metrics(LinearRegression(), X_tr, X_te, y_tr, y_te)

def train_rf_linear(df: pd.DataFrame, n_estimators: int = 200, max_depth: int | None = None, random_state: int = 42):
    d = df.dropna(subset=["arrival_delay"]).copy()
    X = d[["dep_delay", "dep_hour", "dep_dow"]].fillna(0)
    y = d["arrival_delay"].astype(float)
    X = X.fillna({"dep_delay": 0.0, "dep_hour": X["dep_hour"].median(), "dep_dow": X["dep_dow"].median()})
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, random_state=42)
    rf_model = RandomForestRegressor(n_estimators=n_estimators, max_depth=max_depth, random_state=random_state, n_jobs=-1)
    return _reg_fit_and_metrics(rf_model, X_tr, X_te, y_tr, y_te)


# ========= Classification (is_delayed >= 15 min) =========
def clf_metrics(y_true, y_pred):
    metrics = { "acc":  float(accuracy_score(y_true, y_pred)),
                "prec": float(precision_score(y_true, y_pred, zero_division=0)),
                "rec":  float(recall_score(y_true, y_pred, zero_division=0)),
                "f1":   float(f1_score(y_true, y_pred, zero_division=0)) }
    return metrics

def train_logistic(df: pd.DataFrame):
    d = df.dropna(subset=["is_delayed"]).copy()
    X = d[["dep_delay", "dep_hour", "dep_dow"]].fillna(0)
    y = d["is_delayed"].astype(int)
    X = X.fillna({"dep_delay": 0.0, "dep_hour": X["dep_hour"].median(), "dep_dow": X["dep_dow"].median()})
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
    log_model = LogisticRegression(max_iter=200, class_weight="balanced")
    return clffit_metrics(log_model, X_tr, X_te, y_tr, y_te)

def train_tree_logistic(df: pd.DataFrame, max_depth: int | None = None, random_state: int = 42):
    d = df.dropna(subset=["is_delayed"]).copy()
    X = d[["dep_delay", "dep_hour", "dep_dow"]].fillna(0)
    y = d["is_delayed"].astype(int)
    X = X.fillna({"dep_delay": 0.0, "dep_hour": X["dep_hour"].median(), "dep_dow": X["dep_dow"].median()})
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
    treelog_model = DecisionTreeClassifier(max_depth=max_depth, random_state=random_state)
    return clffit_metrics(treelog_model, X_tr, X_te, y_tr, y_te)


def train_rf_logistic(df: pd.DataFrame, n_estimators: int = 300, max_depth: int | None = None, random_state: int = 42):
    d = df.dropna(subset=["is_delayed"]).copy()
    X = d[["dep_delay", "dep_hour", "dep_dow"]].fillna(0)
    y = d["is_delayed"].astype(int)
    X = X.fillna({"dep_delay": 0.0, "dep_hour": X["dep_hour"].median(), "dep_dow": X["dep_dow"].median()})
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)  
    rflog_model = RandomForestClassifier(n_estimators=n_estimators, max_depth=max_depth, random_state=random_state, n_jobs=-1, class_weight="balanced")
    return clffit_metrics(rflog_model, X_tr, X_te, y_tr, y_te)




# ---- Prediction table ----
def predict_linear(model, df: pd.DataFrame, n=15):
    latest = df.sort_values("dep_sched", ascending=False).head(n).copy()
    X = latest[["dep_delay", "dep_hour", "dep_dow"]].fillna(0)
    latest["pred_delay"] = model.predict(X)
    return latest[["route_key", "dep_sched", "arrival_delay", "pred_delay"]]

def predict_logistic(model, df: pd.DataFrame, n=15):
    latest = df.sort_values("dep_sched", ascending=False).head(n).copy()
    X = latest[["dep_delay", "dep_hour", "dep_dow"]].fillna(0)
    latest["pred_prob_delay"] = model.predict_proba(X)[:, 1]
    latest["pred_flag_delay"] = (latest["pred_prob_delay"] >= 0.5).astype(int)
    return latest[["route_key", "dep_sched", "pred_prob_delay", "pred_flag_delay"]]



