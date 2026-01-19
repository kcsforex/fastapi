# 2026.01.19  12.00

# pages/lufthansa.py (simplified with linear regression)

import dash
import pandas as pd
from dash import html, dcc, Input, Output, callback
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go

from apis.lufthansa_api import sql_engine
import pages.flight_ml as fml     # <<--- ML MODULE

dash.register_page(__name__, icon="fa-plane", name="Lufthansa Tracker")

CARD_STYLE = {
    "background": "rgba(255, 255, 255, 0.03)",
    "backdrop-filter": "blur(10px)",
    "border-radius": "15px",
    "border": "1px solid rgba(255, 255, 255, 0.1)",
    "padding": "20px"
}

layout = dbc.Container([

    html.Div([
        html.H2("Lufthansa Flight Info", className="text-light fw-bold mb-0"),
        html.P(id='metrics-update1', className="text-muted small"),
    ], className="mb-4"),

    dcc.Interval(id='refresh', interval=60000),

    # -------- Original content -------
    html.Div([
        html.H5("Daily Ingestion Volume", className="text-light mb-3"),
        dcc.Graph(id='daily-count-chart', config={'displayModeBar': False})
    ], style=CARD_STYLE, className="mb-4"),

    html.Div([
        html.H5("Execution Logs", className="text-light mb-3"),
        html.Div(id='status-table-container1',
            style={"height": "300px", "overflowY": "auto",
                   "backgroundColor": "transparent", "fontSize": "12px"})
    ], style=CARD_STYLE, className="mb-4"),

    # -------- NEW: ML linear regression -------
    html.Div([
        html.H5("ML Prediction (Linear Regression)", className="text-light mb-3"),
        html.Div(id="ml-kpi", className="text-light mb-3"),
        html.Div(id="ml-table", className="text-light"),
    ], style=CARD_STYLE, className="mb-4")

], fluid=True)


@callback(
    [
        Output('metrics-update1', 'children'),
        Output('status-table-container1', 'children'),
        Output('daily-count-chart', 'figure'),
        Output('ml-kpi', 'children'),
        Output('ml-table', 'children'),
    ],
    [Input('refresh', 'n_intervals')]
)
def update_dashboard(_):

    # ---- Load SQL ----
    with sql_engine.connect() as conn:
        query = """
            SELECT DISTINCT ON (departure_scheduled_date, departure_scheduled_time, route_key) *
            FROM lh_flights
            ORDER BY departure_scheduled_date, departure_scheduled_time, route_key, id DESC
        """
        df = pd.read_sql(query, conn)

    if df.empty:
        empty = html.Div("No data found", className="text-light fst-italic")
        empty_fig = go.Figure()
        return "No data", empty, empty_fig, empty, empty

    # ---- Convert ingestion time ----
    df["ingested_at"] = pd.to_datetime(df["ingested_at"])
    df["ingested_at"] = (df["ingested_at"]
                         .dt.tz_localize("UTC")
                         .dt.tz_convert("Europe/Budapest")
                         .dt.strftime("%Y-%m-%d %H:%M:%S"))

    # ---- Build daily chart ----
    daily_counts = df.groupby(df["departure_scheduled_date"]).size().reset_index(name="count")
    fig = px.bar(daily_counts, x="departure_scheduled_date", y="count", template="plotly_dark")
    fig.update_layout(height=260, margin=dict(l=20, r=20, t=10, b=10))

    metrics = f"Updated → {df['ingested_at'].iloc[-1]}"

    # ---- Logs table ----
    status_cols = [1, 2, 3, 4, 6, 10, 11, 13]
    status_cols = [c for c in status_cols if c < df.shape[1]]

    table = dbc.Table.from_dataframe(
        df.iloc[-100:, status_cols],
        striped=False, hover=True, responsive=True, borderless=True,
        className="text-light m-0"
    )

    # ---- ML PART ----
    d = fml.prepare(df)
    model, metrics_ml = fml.train_model(d)
    pred_df = fml.predict_latest(model, d, n=12)

    ml_kpi = html.Div([
        html.Div(f"RMSE: {metrics_ml['rmse']:.1f} min"),
        html.Div(f"MAE:  {metrics_ml['mae']:.1f} min"),
        html.Div(f"R²:   {metrics_ml['r2']:.3f}"),
    ])

    ml_table = dbc.Table.from_dataframe(
        pred_df,
        striped=False, hover=True, responsive=True, borderless=True,
        className="text-light m-0", style={"fontSize": "12px"}
    )

    return metrics, table, fig, ml_kpi, ml_table
