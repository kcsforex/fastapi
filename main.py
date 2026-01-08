import pandas as pd
import ccxt
from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.wsgi import WSGIMiddleware
from dash import Dash, dcc, html, dash_table
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
import psycopg2

# --- 1. CONFIGURATION ---
DB_CONFIG = "postgresql://user:password@postgresql:5432/n8n"
SYMBOLS = ["BTC/USDT", "ETH/USDT", "SOL/USDT"]

# --- 2. FASTAPI "BRAIN" ---
fastapi_app = FastAPI()
exchange = ccxt.bybit()

@fastapi_app.get("/analyze/pivot")
def analyze_pivot():
    payload = {"timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    for symbol in SYMBOLS:
        try:
            bars = exchange.fetch_ohlcv(symbol, timeframe='5m', limit=110)
            df = pd.DataFrame(bars, columns=['ts', 'o', 'h', 'l', 'c', 'v'])
            df['sma100'] = df['c'].rolling(window=100).mean()
            
            curr, prev = df.iloc[-1], df.iloc[-2]
            col = symbol.split('/')[0]
            
            payload[f"{col}_price"] = float(curr['c'])
            payload[f"{col}_status"] = "ABOVE" if curr['c'] > curr['sma100'] else "BELOW"
            payload[f"{col}_cross"] = bool(prev['c'] <= prev['sma100'] and curr['c'] > curr['sma100'])
        except Exception as e:
            payload[f"{symbol}_error"] = str(e)
    return payload

# --- 3. DASH "UI" ---
dash_app = Dash(__name__, 
                requests_pathname_prefix='/', 
                external_stylesheets=[dbc.themes.CYBORG])

dash_app.layout = dbc.Container([
    html.H1("Crypto SMA100 Monitor", className="text-center my-4"),
    dcc.Interval(id='refresh', interval=60*1000), # Refresh UI every minute
    html.Div(id='status-table-container'),
    dcc.Graph(id='main-chart')
], fluid=True)

@dash_app.callback(
    [Output('status-table-container', 'children'), Output('main-chart', 'figure')],
    [Input('refresh', 'n_intervals')]
)
def update_dashboard(n):
    conn = psycopg2.connect(DB_CONFIG)
    # Query the pivot table n8n is writing to
    df = pd.read_sql("SELECT * FROM status_pivot_logs ORDER BY timestamp DESC LIMIT 20", conn)
    conn.close()
    
    # Simple table for current status
    table = dash_table.DataTable(
        data=df.to_dict('records'),
        columns=[{"name": i, "id": i} for i in df.columns],
        style_header={'backgroundColor': 'rgb(30, 30, 30)', 'color': 'white'},
        style_cell={'backgroundColor': 'rgb(50, 50, 50)', 'color': 'white'}
    )
    return table, {} # Add Plotly logic here as needed

# --- 4. THE MOUNTING ---
# We wrap the Dash (Flask) server in WSGI and mount it to FastAPI
fastapi_app.mount("/", WSGIMiddleware(dash_app.server))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(fastapi_app, host="0.0.0.0", port=8000)
