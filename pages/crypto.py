import dash
from dash import dcc, html, dash_table, callback
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
from fastapi import APIRouter
import plotly.express as px
import pandas as pd
import psycopg2

# --- 1. CONFIGURATION ---
DB_CONFIG = "postgresql://sql_admin:sql_pass@72.62.151.169:5432/n8n"
SYMBOLS = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "XRP/USDT", "SUI/USDT"]

# --- 2. FASTAPI  (n8n targets this) ---
router = APIRouter()
exchange = ccxt.bybit()

@router.get("/analyze/pivot")
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
            #payload[f"{col}_cross"] = bool(prev['c'] <= prev['sma100'] and curr['c'] > curr['sma100'])
        
        except Exception as e:
            payload[f"{symbol}_error"] = str(e)
    return payload

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
        html.H2("Market Intelligence", className="text-light fw-bold mb-0"),
        html.P("Live Bybit SMA100 Analysis", className="text-muted small"),
    ], className="mb-4"),

    dcc.Interval(id='refresh', interval=60*1000), 

    # Top Metrics Row
    html.Div(id='metrics-container', className="mb-4"),

    # Main Graph Card
    html.Div([
        html.H5("BTC Price Action", className="text-info mb-3"),
        dcc.Graph(id='main-chart', config={'displayModeBar': False})
    ], style=CARD_STYLE, className="mb-4"),

    # Table Card
    html.Div([
        html.H5("Execution Logs", className="text-light mb-3"),
        html.Div(id='status-table-container')
    ], style=CARD_STYLE)

], fluid=True)

@callback(
    [Output('metrics-container', 'children'), 
     Output('status-table-container', 'children'), 
     Output('main-chart', 'figure')],
    [Input('refresh', 'n_intervals')]
)
def update_dashboard(n):
    try:
        conn = psycopg2.connect("postgresql://sql_admin:sql_pass@72.62.151.169:5432/n8n")
        df = pd.read_sql("SELECT * FROM status_pivot_logs ORDER BY timestamp DESC LIMIT 30", conn)
        conn.close()

        # 1. Create Top Metrics (Quick visual check)
        latest = df.iloc[0]
        metrics = dbc.Row([
            dbc.Col(html.Div([
                html.Small("BTC/USDT", className="text-muted"),
                html.H4(f"${latest['btc_price']:,.2f}", className="text-info")
            ])),
            dbc.Col(html.Div([
                html.Small("ETH/USDT", className="text-muted"),
                html.H4(f"${latest['eth_price']:,.2f}", className="text-primary")
            ])),
            dbc.Col(html.Div([
                html.Small("SIGNAL", className="text-muted"),
                html.H4(latest['btc_status'], className="text-success" if latest['btc_status'] == "ABOVE" else "text-danger")
            ]))
        ])

        # 2. Graph Styling
        fig = px.line(df, x="timestamp", y="btc_price", template="plotly_dark")
        fig.update_traces(line_color='#00d1ff', line_width=3)
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=0, r=0, t=10, b=0), height=300,
            xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)')
        )

        # 3. Table Styling
        table = dash_table.DataTable(
            data=df.to_dict('records'),
            columns=[{"name": i.replace('_', ' ').upper(), "id": i} for i in df.columns],
            style_as_list_view=True,
            style_header={'backgroundColor': 'transparent', 'color': '#00d1ff', 'fontWeight': 'bold', 'borderBottom': '1px solid #333'},
            style_cell={'backgroundColor': 'transparent', 'color': 'white', 'padding': '12px', 'fontSize': '13px'},
            page_size=10
        )

        return metrics, table, fig
    except Exception as e:
        return html.Div(f"Error: {e}", className="text-danger"), "", px.scatter()
