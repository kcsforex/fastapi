
# 2026.01.20  15.00
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

def train_reg_linear(df):
    df = df.dropna(subset=["arrival_delay"]).copy()
    X = df[["dep_delay", "dep_hour", "dep_dow"]].fillna(0)
    y = df["arrival_delay"].astype(float)
    X = X.fillna({"dep_delay": 0.0, "dep_hour": X["dep_hour"].median(), "dep_dow": X["dep_dow"].median()})
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, random_state=42)
    model = LinearRegression().fit(X_tr, y_tr)
    return model, reg_metrics(y_te, model.predict(X_te))

def train_rf_linear(df):
    d = df.dropna(subset=["arrival_delay"]).copy()
    X = d[["dep_delay", "dep_hour", "dep_dow"]].fillna(0)
    y = d["arrival_delay"].astype(float)
    X = X.fillna({"dep_delay": 0.0, "dep_hour": X["dep_hour"].median(), "dep_dow": X["dep_dow"].median()})
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, random_state=42)
    model = DecisionTreeRegressor(max_depth=max_depth, random_state=random_state).fit(X_tr, y_tr)
    return model, reg_metrics(y_te, model.predict(X_te))


# ========= Classification (is_delayed >= 15 min) =========
def clf_metrics(y_true, y_pred):
    metrics = { "acc":  float(accuracy_score(y_true, y_pred)),
                "prec": float(precision_score(y_true, y_pred, zero_division=0)),
                "rec":  float(recall_score(y_true, y_pred, zero_division=0)),
                "f1":   float(f1_score(y_true, y_pred, zero_division=0)) }
    return metrics

def train_logistic(df):
    d = df.dropna(subset=["is_delayed"]).copy()
    X = d[["dep_delay", "dep_hour", "dep_dow"]].fillna(0)
    y = d["is_delayed"].astype(int)
    X = X.fillna({"dep_delay": 0.0, "dep_hour": X["dep_hour"].median(), "dep_dow": X["dep_dow"].median()})   
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
    model = LogisticRegression(max_iter=200, class_weight="balanced").fit(X_tr, y_tr)
    return model, clf_metrics(y_te, model.predict(X_te))

def train_tree_logistic(df, max_depth=None, random_state=42):
    d = df.dropna(subset=["is_delayed"]).copy()
    X = d[["dep_delay", "dep_hour", "dep_dow"]].fillna(0)
    y = d["is_delayed"].astype(int)
    X = X.fillna({"dep_delay": 0.0, "dep_hour": X["dep_hour"].median(), "dep_dow": X["dep_dow"].median()}) 
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
    model = DecisionTreeClassifier(max_depth=max_depth, random_state=random_state).fit(X_tr, y_tr)
    return model, clf_metrics(y_te, model.predict(X_te))

def train_rf_logistic(df, n_estimators=300, max_depth=None, random_state=42):
    d = df.dropna(subset=["is_delayed"]).copy()
    X = d[["dep_delay", "dep_hour", "dep_dow"]].fillna(0)
    y = d["is_delayed"].astype(int)
    X = X.fillna({"dep_delay": 0.0, "dep_hour": X["dep_hour"].median(), "dep_dow": X["dep_dow"].median()})  
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
    model = RandomForestClassifier(n_estimators=n_estimators,max_depth=max_depth,random_state=random_state,class_weight="balanced").fit(X_tr, y_tr)
    return model, clf_metrics(y_te, model.predict(X_te))


# ======================================================
#  Comparison Table (same subset for linear + logistic)
# ======================================================

def predict_linear_subset(model, df_subset):
    X = _fill_X(df_subset[["dep_delay", "dep_hour", "dep_dow"]])
    out = df_subset[["route_key", "dep_sched"]].copy()
    out["arrival_delay"] = df_subset["arrival_delay"]
    out["pred_delay"] = model.predict(X)
    return out

def predict_logistic_subset(model, df_subset):
    X = _fill_X(df_subset[["dep_delay", "dep_hour", "dep_dow"]])
    out = df_subset[["route_key", "dep_sched"]].copy()
    proba = model.predict_proba(X)[:, 1]
    out["pred_prob_delay"] = proba
    out["pred_flag_delay"] = (proba >= 0.5).astype(int)
    return out

def build_comparison_table(df, lin_model, log_model, n=12):
    """Produce a single table showing Linear + Logistic predictions."""
    subset = df.sort_values("dep_sched", ascending=False).head(n).copy()

    lin = predict_linear_subset(lin_model, subset)
    log = predict_logistic_subset(log_model, subset)

    comp = pd.merge(lin, log, on=["route_key", "dep_sched"], how="outer")

    # Nice formatting
    if "arrival_delay" in comp:
        comp["arrival_delay"] = comp["arrival_delay"].round(1)
    if "pred_delay" in comp:
        comp["pred_delay"] = comp["pred_delay"].round(1)
    if "pred_prob_delay" in comp:
        comp["pred_prob_delay"] = comp["pred_prob_delay"].round(3)

    return comp







