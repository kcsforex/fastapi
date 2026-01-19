# 2026.01.19  12.00
import dash
import pandas as pd
from dash import html, dcc, Input, Output, callback
import dash_bootstrap_components as dbc
import plotly.express as px 
import plotly.graph_objects as go
from apis.lufthansa_api import sql_engine 
import pages.flight_ml as fml

dash.register_page(__name__, icon="fa-plane", name="Lufthansa Tracker")

CARD_STYLE = {
    "background": "rgba(255, 255, 255, 0.03)",
    "backdrop-filter": "blur(10px)",
    "border-radius": "15px",
    "border": "1px solid rgba(255, 255, 255, 0.1)",
    "padding": "20px"
}


# simple in-memory cache for current process
_IN_MEMORY_SIG = {"value": None}
_IN_MEMORY_MODELS: dict[str, fml.TrainedModels] = {}


layout = dbc.Container([
    html.Div([
        html.H2("Lufthansa Flight Info", className="text-light fw-bold mb-0"),
        html.P(id='metrics-update1', className="text-muted small"),
    ], className="mb-4"),

    dcc.Interval(id='refresh', interval=60*1000),
    dcc.Store(id='state_store', storage_type='memory'),

    # --- Your original chart ---
    html.Div([
        html.H5("Daily Ingestion Volume", className="text-light mb-3"),
        dcc.Graph(id='daily-count-chart', config={'displayModeBar': False})
    ], style=CARD_STYLE, className="mb-4"),

    # --- Your original execution logs ---
    html.Div([
        html.H5("Execution Logs", className="text-light mb-3"),
        html.Div(
            id='status-table-container1',
            style={
                "height": "300px",
                "overflowY": "auto",
                "backgroundColor": "transparent",
                "fontSize": "12px"
            }
        )
    ], style=CARD_STYLE, className="mb-4"),

    # --- New: ML Insights ---
    html.Div([
        html.H5("ML Insights — Delay Modeling", className="text-light mb-3"),

        dbc.Row([
            dbc.Col(html.Div(id='reg-kpi', className="text-light"), md=6),
            dbc.Col(html.Div(id='clf-kpi', className="text-light"), md=6),
        ], className="mb-3"),

        dbc.Row([
            dbc.Col(dcc.Graph(id='reg_scatter', config={'displayModeBar': False}), md=6),
            dbc.Col(dcc.Graph(id='clf_confusion', config={'displayModeBar': False}), md=6),
        ], className="mb-3"),

        html.Div(id='pred-table-container', className="text-light"),
    ], style=CARD_STYLE, className="mb-4")
], fluid=True)

@callback(
    [Output('metrics-update1', 'children'),
    Output('status-table-container1', 'children'),
    Output('daily-count-chart', 'figure'),  
    Output('reg-kpi', 'children'),
    Output('clf-kpi', 'children'),
    Output('reg_scatter', 'figure'),
    Output('clf_confusion', 'figure'),
    Output('pred-table-container', 'children'),
    Output('state_store', 'data')],
    [Input('refresh', 'n_intervals')],
    [dash.State('state_store', 'data')]
)
def update_dashboard(n_intervals):
    with sql_engine.connect() as conn:
        #df = pd.read_sql("SELECT * FROM lh_flights ORDER BY id DESC", conn)
        query = """
            SELECT DISTINCT ON (departure_scheduled_date, departure_scheduled_time, route_key) * FROM lh_flights 
            ORDER BY departure_scheduled_date, departure_scheduled_time, route_key, id DESC
            """
        df = pd.read_sql(query, conn)

    
    if df.empty:
        return ("No data found", empty_div, empty_fig, empty_div, empty_div, empty_fig, empty_fig, empty_div, state)

    # --- DELETE DUPLICATES HERE with pandas ---
    #df = df.drop_duplicates(subset=["departure_scheduled_date", "departure_scheduled_time", "route_key"], keep="first" )

    # 1. Date Processing
    df["ingested_at"] = pd.to_datetime(df["ingested_at"])       
    df["ingested_at"] = df["ingested_at"].dt.tz_localize("UTC").dt.tz_convert("Europe/Budapest").dt.strftime("%Y-%m-%d %H:%M:%S")

    # 2. Create the Chart Data (Daily Aggregation)
    # We group by the date part of the localized timestamp and count 'id'
    daily_counts = df.groupby(df["departure_scheduled_date"]).size().reset_index(name='count')
    daily_counts.columns = ['Date', 'Flight Count']

    # 3. Build the Figure
    fig = px.bar(daily_counts, x='Date', y='Flight Count',template='plotly_dark') #, color_discrete_sequence=['#003366'])
    
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=20, r=20, t=10, b=20), height=250)

    metrics_update = f"Updated -> {df["ingested_at"].iloc[-1]}"

    # 4. Table Formatting
    table = dbc.Table.from_dataframe( #df.iloc[:, [0, 2, 5]] total rows
        df.iloc[-100:, [1, 2, 3, 4, 6,10, 11, 13]], striped=False, hover=True, responsive=True, borderless=True, 
        className="text-light m-0",  
        style={"backgroundColor": "transparent",  "--bs-table-bg": "transparent", "--bs-table-accent-bg": "transparent", "color": "white"}
    )

    
    # ---------- 3) ML: clean/features, (re)train, visuals ----------
    data = fml.clean_and_feature_engineer(df)

    # Simple signature based on size & latest scheduled dep to avoid redundant training
    sig = f"{len(data)}|{str(pd.to_datetime(data['dep_sched_dt']).max())}|{data.get('route_key', pd.Series(dtype=str)).nunique()}"
    prev_sig = (state or {}).get("sig")
    need_retrain = sig != prev_sig

    if (not need_retrain) and (_IN_MEMORY_SIG["value"] == sig) and (sig in _IN_MEMORY_MODELS):
        models_obj = _IN_MEMORY_MODELS[sig]
    else:
        models_obj = fml.train_models(data, time_aware=False)
        _IN_MEMORY_MODELS.clear()
        _IN_MEMORY_MODELS[sig] = models_obj
        _IN_MEMORY_SIG["value"] = sig
    
    # KPIs
    rmse = models_obj.reg_metrics.rmse
    mae  = models_obj.reg_metrics.mae
    r2   = models_obj.reg_metrics.r2
    auc  = models_obj.clf_metrics.auc

    reg_kpi = html.Div([
        html.H6("Linear Regression (Arrival delay)", className="mb-1"),
        html.Div(f"MAE:  {mae:.1f} min" if np.isfinite(mae) else "MAE: n/a"),
        html.Div(f"RMSE: {rmse:.1f} min" if np.isfinite(rmse) else "RMSE: n/a"),
        html.Div(f"R²:   {r2:.3f}" if np.isfinite(r2) else "R²: n/a"),
    ])
    
    clf_kpi = html.Div([
        html.H6("Logistic Regression (Delayed ≥15m)", className="mb-1"),
        html.Div(f"ROC AUC: {auc:.3f}" if auc is not None else "ROC AUC: n/a"),
    ])

    # Scatter: actual vs predicted (fresh split for the plot only)
    try:
        reg_df = data.dropna(subset=["arrival_delay_min"]).copy()
        Xr = reg_df[fml.FEATURE_COLS]
        yr = reg_df["arrival_delay_min"].astype(float)
        Xr_tr, Xr_te, yr_tr, yr_te = train_test_split(Xr, yr, test_size=0.2, random_state=42)
        yr_pred = models_obj.reg_pipe.predict(Xr_te)

        reg_fig = px.scatter(
            x=yr_te, y=yr_pred,
            labels={"x": "Tény késés (perc)", "y": "Becsült késés (perc)"},
            title="Actual vs Predicted Arrival Delay (Test Split)",
            template="plotly_dark"
        )
        lo = float(np.nanmin([yr_te.min(), yr_pred.min()]))
        hi = float(np.nanmax([yr_te.max(), yr_pred.max()]))
        reg_fig.add_trace(go.Scatter(x=[lo, hi], y=[lo, hi],
                                     mode="lines",
                                     line=dict(color="red", dash="dash"),
                                     name="Ideal"))
        reg_fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
    except Exception:
        reg_fig = empty_fig

    # Confusion matrix
    conf = models_obj.clf_metrics.confusion
    conf_fig = go.Figure(data=go.Heatmap(
        z=conf, x=["Pred 0", "Pred 1"], y=["True 0", "True 1"],
        colorscale="Blues", showscale=True
    ))
    conf_fig.update_layout(
        title="Confusion Matrix (threshold 0.5)",
        template="plotly_dark",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )

    # Predictions table (latest 20)
    pred_df = fml.predict_latest(models_obj, data, n_rows=20, threshold=0.5)
    pred_table = dbc.Table.from_dataframe(
        pred_df,
        striped=False, hover=True, responsive=True, borderless=True,
        className="text-light m-0",
        style={
            "backgroundColor": "transparent",
            "--bs-table-bg": "transparent",
            "--bs-table-accent-bg": "transparent",
            "color": "white",
            "fontSize": "12px"
        }
    )

    # New store state
    state = {"sig": sig}

    # ---------- 4) Return everything ----------
    return (
        metrics_update,
        status_table,
        fig_daily,
        reg_kpi,
        clf_kpi,
        reg_fig,
        conf_fig,
        pred_table,
        state
    )

