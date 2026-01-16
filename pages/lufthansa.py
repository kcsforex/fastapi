# 2026.01.15  18.00
import requests
from fastapi import FastAPI, APIRouter
from fastapi.middleware.wsgi import WSGIMiddleware
from dash import Dash, html, dcc, Input, Output, State,  callback
import dash_bootstrap_components as dbc
import dash
import pandas as pd
import os
import time

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

@router.get("/lh_flight/{flight_date}")
def get_flightroute_details(flight_date: str):
    
    token = 'vph5p8hm845j9fj5qhvxsr7h' #get_lufthansa_token()

    ROUTES_FULL = [("FRA", "SIN"),  ("FRA", "CDG"), ("FRA", "MUC"), ("FRA", "AMS"), ("FRA", "BUD")]

    all_dataframes = []

    for origin, dest in ROUTES_FULL:
        try:
            base_url = f'https://api.lufthansa.com/v1/operations/customerflightinformation/route/{origin}/{dest}/{flight_date}'
            headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
            response = requests.get(base_url, headers=headers)
            time.sleep(0.25)
       
            if response.status_code == 200:
                json_data = response.json()
                pdf = pd.json_normalize(json_data['FlightInformation']['Flights']['Flight'])
                pdf['route_key'] = f"{origin}-{dest}"
                all_dataframes.append(pdf)
    
            elif response.status_code == 400:
                print(f"Bad Request: {response.text}")
                break
            elif response.status_code == 401:
                print(f"Unauthorized API Access: {response.text}")
                break  
            elif response.status_code == 403:
                print(f"API Forbidden: {response.text}")
                break              
            elif response.status_code == 404:
                print(f"Skipping: No data found for {origin}-{dest} on {TARGET_DATE}")
            else:
                print(f"API Warning ({response.status_code}): {response.text}")
                    
        except Exception as e:
            print(f"Error {origin}-{dest}: {e}")
    
    if all_dataframes:
        combined_df = pd.concat(all_dataframes, ignore_index=True)
        combined_df.columns = [c.replace('.', '_') for c in combined_df.columns]
        combined_df["ingested_at"] = pd.Timestamp.now().isoformat()
        
        return combined_df.to_dict(orient="records")
    else:
        return []

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

def update_output(n_clicks, flight_date):
    if not flight_date:
        return "Please enter a flight date."
    
    # Internal call to the FastAPI logic
    try:
        data = get_flightroute_details(flight_date)
        return html.Pre(str(data))
    except Exception as e:
        return f"Error: {str(e)}"

