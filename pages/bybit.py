# 2025.02.16  11.00
import pandas as pd
from datetime import datetime
from fastapi import APIRouter
import dash
from dash import dcc, html, dash_table, callback
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
import plotly.express as px
from apis.bybit_api import sql_engine, SYMBOLS


# ----- 3. THE FRONTEND (Dash Sidebar uses this) -----
dash.register_page(__name__, icon="fa-coins", name="Bybit Crypto Dash", order=1)

# Glassmorphism Card Style
CARD_STYLE = {
    "background": "rgba(255, 255, 255, 0.03)",
    "backdrop-filter": "blur(10px)",
    "border-radius": "15px",
    "border": "1px solid rgba(255, 255, 255, 0.1)",
    "padding": "20px"
}

layout = dbc.Container([
    html.Div([
        html.H2("ByBit Crypto Market", className="text-light fw-bold mb-0"),
        html.P(id='metrics-update', className="text-muted small"),
    ], className="mb-4"),

    dcc.Interval(id='refresh', interval=60*1000), 

    html.Div(id='metrics-container', className="mb-4"),

    dbc.Row(id='charts-grid', className="g-3 mb-3"),

    html.Div([
        html.H5("Execution Logs", className="text-light mb-3"),
        html.Div(id='status-table-container', 
            style={"height": "300px", "overflowY": "auto", "overflowX": "hidden", "backgroundColor": "transparent",  "fontSize": "12px"})
    ], style=CARD_STYLE)

], fluid=True)

@callback(
    [Output('metrics-update', 'children'),
    Output('metrics-container', 'children'), 
     Output('status-table-container', 'children'), 
     Output('charts-grid', 'children')],
    [Input('refresh', 'n_intervals')]
)

def update_dashboard(n_intervals):

    with sql_engine.connect() as conn:
        df = pd.read_sql("SELECT * FROM bybit_crypto ORDER BY timestamp DESC LIMIT 120", conn)

    if df.empty:
        return html.Div("No data found", className="text-light fst-italic")
        #return dash.no_update, "No data found", {}, "No Data"    

    #df["timestamp"] = pd.to_datetime(df["timestamp"])
    #df["timestamp"] = df["timestamp"].dt.tz_localize("UTC").dt.tz_convert("Europe/Budapest").dt.strftime("%Y-%m-%d %H:%M:%S") 

    df["timestamp"] = pd.to_numeric(df["timestamp"], errors='coerce')          
    df["timestamp"] = pd.to_datetime(df["timestamp"],unit="ms", utc=True).dt.tz_convert("Europe/Budapest").dt.strftime("%Y-%m-%d %H:%M:%S")   
    latest = df.sort_values("timestamp").groupby("symbol").last().reset_index() 

    # 0. Update Timestamp
    metrics_update = f"Updated -> {latest["timestamp"].iloc[0]}"
             
    # 1. Create Top Metrics (Quick visual check)
    metric_cols = [
    dbc.Col(
        html.Div([
            html.Small(s, className="text-muted"),
            html.H5(f"${latest.loc[latest['pair'] == s, 'price'].values[0]:.2f}", className="text-warning"),
            html.Small("SIGNAL", className="text-muted"),
            html.H6(latest.loc[latest['pair'] == s, 'price_status'].values[0], className=("text-success" if latest.loc[latest['pair'] == s, 'price_status'].values[0] == "ABOVE" else "text-danger"))     
        ]), width=2)
    for s in SYMBOLS[:6]
    ]
    metrics = dbc.Row(metric_cols, align="center")

    chart_cols = []
    for symbol in SYMBOLS:
        chart_df = df[df["pair"] == symbol].sort_values("timestamp")
        
        if chart_df.empty: continue

        fig = px.line(chart_df, x="timestamp", y="price", template="plotly_dark")
        fig.update_traces(line_color='#00d1ff', line_width=2)
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', 
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=0, r=0, t=0, b=0),
            height=150,
            xaxis=dict(showgrid=False, title="", showticklabels=True, tickformat="%H:%M"), 
            yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)', title="", side="right")
        )
        
        chart_cols.append(
            dbc.Col([
                html.Div([
                    html.H6(symbol, className="text-info mb-1"),
                    dcc.Graph(figure=fig, config={'displayModeBar': False})
                ], style=CARD_STYLE)
            ], width=3, className="mb-1")
        )
  
    # 3. Crypto Table
    display_df = df.copy()
    display_df.columns = [c.replace('_', ' ').upper() for c in display_df.columns]
    table = dbc.Table.from_dataframe(display_df[:120], striped=False, hover=True, responsive=True, borderless=True, className="text-light m-0", 
        style={"backgroundColor": "transparent",  "--bs-table-bg": "transparent", "--bs-table-accent-bg": "transparent", "color": "white"}
    )

    return metrics_update, metrics, table, chart_cols
