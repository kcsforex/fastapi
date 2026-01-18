import dash
import pandas as pd
from dash import html, dcc, Input, Output, callback
import dash_bootstrap_components as dbc
from apis.lufthansa_api import sql_engine 

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

    dcc.Interval(id='refresh', interval=60*1000), 

    html.Div([
        html.H5("Execution Logs", className="text-light mb-3"),
        html.Div(id='status-table-container1', 
            style={"height": "300px", "overflowY": "auto", "backgroundColor": "transparent", "fontSize": "12px"})
    ], style=CARD_STYLE)
], fluid=True)

@callback(
    [Output('metrics-update1', 'children'),
     Output('status-table-container1', 'children')],
    [Input('refresh', 'n_intervals')]
)
def update_dashboard(n_intervals):
    with sql_engine.connect() as conn:
        df = pd.read_sql("SELECT * FROM lh_flights ORDER BY id DESC LIMIT 120", conn)

    if df.empty:
        return "No data found", html.Div("No data found", className="text-light fst-italic")

    # Fixed Date logic
    df["ingested_at"] = pd.to_datetime(df["ingested_at"])
    if df["ingested_at"].dt.tz is None:
        df["ingested_at"] = df["ingested_at"].dt.tz_localize("UTC")
    
    df["ingested_at"] = df["ingested_at"].dt.tz_convert("Europe/Budapest").dt.strftime("%Y-%m-%d %H:%M:%S")

    metrics_update = f"Updated -> {df['ingested_at'].iloc[0]}"          
  
    table = dbc.Table.from_dataframe(
        df, striped=False, hover=True, responsive=True, borderless=True, 
        className="text-light m-0",  
        style={"backgroundColor": "transparent",  "--bs-table-bg": "transparent", "--bs-table-accent-bg": "transparent", "color": "white"}
    )

    return metrics_update, table
