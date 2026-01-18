# 2026.01.18  18.00
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
        html.H5("Daily Ingestion Volume", className="text-light mb-3"),
        dcc.Graph(id='daily-count-chart', config={'displayModeBar': False})
    ], style=CARD_STYLE, className="mb-4"),

    html.Div([
        html.H5("Execution Logs", className="text-light mb-3"),
        html.Div(id='status-table-container1', 
            style={"height": "300px", "overflowY": "auto", "backgroundColor": "transparent", "fontSize": "12px"})
    ], style=CARD_STYLE)
], fluid=True)

@callback(
    [Output('metrics-update1', 'children'),
     Output('status-table-container1', 'children'),
    Output('daily-count-chart', 'figure')],
    [Input('refresh', 'n_intervals')]
)
def update_dashboard(n_intervals):
    with sql_engine.connect() as conn:
        df = pd.read_sql("SELECT * FROM lh_flights ORDER BY id DESC LIMIT 120", conn)

    if df.empty:
        return "No data found", html.Div("No data found", className="text-light fst-italic")

    # 1. Date Processing
    df["ingested_at"] = pd.to_datetime(df["ingested_at"])
    
    if df["ingested_at"].dt.tz is None:
        df["ingested_at"] = df["ingested_at"].dt.tz_localize("UTC")
    
    #df["ingested_at_local"] = df["ingested_at"].dt.tz_convert("Europe/Budapest")  
    df["ingested_at"] = df["ingested_at"].dt.tz_convert("Europe/Budapest").dt.strftime("%Y-%m-%d %H:%M:%S")

    # 2. Create the Chart Data (Daily Aggregation)
    # We group by the date part of the localized timestamp and count 'id'
    daily_counts = df.groupby(df["ingested_at_local"].dt.date).size().reset_index(name='count')
    daily_counts.columns = ['Date', 'Flight Count']

    # 3. Build the Figure
    fig = px.bar(daily_counts, x='Date', y='Flight Count',template='plotly_dark', color_discrete_sequence=['#003366'])
    
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=20, r=20, t=10, b=20), height=250)

    metrics_update = f"Updated -> {df['ingested_at'].iloc[0]}"          

    # 4. Table Formatting
    table = dbc.Table.from_dataframe(
        df, striped=False, hover=True, responsive=True, borderless=True, 
        className="text-light m-0",  
        style={"backgroundColor": "transparent",  "--bs-table-bg": "transparent", "--bs-table-accent-bg": "transparent", "color": "white"}
    )

    return metrics_update, table, fig
