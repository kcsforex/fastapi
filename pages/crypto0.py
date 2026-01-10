import dash
from dash import html
from fastapi import APIRouter

# --- THE BACKEND (n8n targets this) ---
router = APIRouter()

@router.get("/status")
def get_crypto_status():
    return {"status": "BTC is above SMA100"}

# --- THE FRONTEND (Dash Sidebar uses this) ---
dash.register_page(__name__, icon="fa-coins", name="Crypto Dash 0")

layout = html.Div([
    html.H1("Crypto Dashboard", className="text-light"),
    html.P("Real-time data from Bybit/PostgreSQL")
])

