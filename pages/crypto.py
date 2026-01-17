# 2025.01.17  18.00
import pandas as pd
import ccxt
from datetime import datetime
from fastapi import APIRouter
import dash
from dash import dcc, html, dash_table, callback
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
import plotly.express as px
from sqlalchemy import create_engine

# ----- 1. CONFIGURATION -----
DB_CONFIG = "postgresql://sql_admin:sql_pass@72.62.151.169:5432/n8n"
sql_engine = create_engine(DB_CONFIG, pool_size=10, max_overflow=20)
SYMBOLS = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "XRP/USDT", "ZEN/USDT", "LTC/USDT", "AVAX/USDT", "LINK/USDT", "HYPE/USDT", "BCH/USDT", "BNB/USDT", "AAVE/USDT"]

# ----- 2. FASTAPI  (n8n targets this) -----
router = APIRouter()
exchange = ccxt.bybit()

@router.get("/telegram")
def telegram():
    
    timeframe = '5m'  # Match your trigger interval
    limit = 101  # Fetch 101 to get the SMA100 and the current candle   
    results = []
    timestamp = exchange.milliseconds()
    
    for symbol in SYMBOLS:
        try:
            ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            closes = [candle[4] for candle in ohlcv]        
            sma_100 = sum(closes[-100:]) / 100
            current_price = closes[-1]
            curr_status = "ABOVE" if current_price > sma_100 else "BELOW"
            diff_percent = ((current_price - sma_100) / sma_100) * 100
        
            prev_close = closes[-2]
            prev_sma = sum(closes[-101:-1]) / 100  # SMA100 for previous candle
            
            prev_status = "ABOVE" if prev_close > prev_sma else "BELOW"
            
            if prev_status == "BELOW" and curr_status == "ABOVE":
                price_cross = "BULL-CROSS"
            elif prev_status == "ABOVE" and curr_status == "BELOW":
                price_cross = "BEAR-CROSS"
            else:
                price_cross = "NON-CROSS"
            
            coin_name = symbol.split('/')[0]
            results.append({"symbol": coin_name, "pair": symbol, "price": round(current_price, 2), "sma_100": round(sma_100, 2),
                "price_status": curr_status, "price_cross": price_cross, "percent_diff": round(diff_percent, 2), "timestamp": timestamp
            })
            
        except Exception as e:
            coin_name = symbol.split('/')[0]
            results.append({"symbol": coin_name, "pair": symbol, "price": 0, "price_status": "ERROR", "price_cross": "ERROR", 
            "error": str(e), "timestamp": timestamp
            })
                          
    return results

# ----- 3. THE FRONTEND (Dash Sidebar uses this) -----
dash.register_page(__name__, icon="fa-coins", name="Crypto Dash")

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
        html.H2("Crypto Market Info", className="text-light fw-bold mb-0"),
        html.P(id='metrics-update', className="text-muted small"),
    ], className="mb-4"),

    dcc.Interval(id='refresh', interval=60*1000), 

    html.Div(id='metrics-container', className="mb-4"),
    # gx-1 → small horizontal gutter
    # gy-2 → moderate vertical gutter
    # mb-2 → smaller bottom margin

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
    df = pd.read_sql("SELECT * FROM status_crypto_logs ORDER BY timestamp DESC LIMIT 120", conn)

    if df.empty:
        return html.Div("No data found", className="text-light fst-italic")
        #return dash.no_update, "No data found", {}, "No Data"    

    df["timestamp"] = df["timestamp"].dt.tz_localize("UTC").dt.tz_convert("Europe/Budapest").dt.strftime("%Y-%m-%d %H:%M:%S")     
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
        #chart_df["timestamp"] = pd.to_datetime(chart_df["timestamp"], unit="ms")
        
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
