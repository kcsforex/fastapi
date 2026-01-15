import requests
from fastapi import FastAPI, APIRouter
from fastapi.middleware.wsgi import WSGIMiddleware
from dash import Dash, html, dcc, Input, Output, State
import dash_bootstrap_components as dbc
import dash
import os

router = APIRouter()

def get_lufthansa_token():
    # Assuming dbutils is available in your environment
    CLIENT_ID = os.getenv("LH_CLIENT_ID")
    CLIENT_SECRET = os.getenv("LH_CLIENT_SECRET")
    
    token_url = "https://api.lufthansa.com/v1/oauth/token"
    payload = { "grant_type": "client_credentials", "client_id": CLIENT_ID,  "client_secret": CLIENT_SECRET}
    
    resp = requests.post(token_url, data=payload)
    resp.raise_for_status()
    return resp.json()["access_token"]

@router.get("/flight/{flight_number}")
def get_flight_details(flight_number: str):
    token = 'vph5p8hm845j9fj5qhvxsr7h' #get_lufthansa_token()
    base_url = f"https://api.lufthansa.com/v1/operations/customerflightinformation/{flight_number}"
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    response = requests.get(base_url, headers=headers)
    return response.json()

# --- Dash UI Setup ---
dash.register_page(__name__, icon="fa-coins", name="Lufthansa")

layout = dbc.Container([
    html.H1("Lufthansa Flight Tracker", className="mt-4"),
    dbc.Input(id="flight-input", placeholder="Enter Flight Number (e.g., LH400)", type="text"),
    dbc.Button("Search", id="search-btn", color="primary", className="mt-2"),
    html.Hr(),
    html.Div(id="flight-output")
], fluid=True)

@callback(
    Output("flight-output", "children"),
    Input("search-btn", "n_clicks"),
    State("flight-input", "value"),
    prevent_initial_call=True
)

def update_output(n_clicks, flight_num):
    if not flight_num:
        return "Please enter a flight number."
    
    # Internal call to the FastAPI logic
    try:
        data = get_flight_details(flight_num)
        return html.Pre(str(data))
    except Exception as e:
        return f"Error: {str(e)}"

