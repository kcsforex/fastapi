# 2026.01.17  17.00
import requests
import psycopg2
from sqlalchemy import create_engine
from fastapi import FastAPI, APIRouter
from fastapi.middleware.wsgi import WSGIMiddleware
from dash import Dash, html, dcc, Input, Output, State,  callback
import dash_bootstrap_components as dbc
import dash
import pandas as pd
import os
import time
import httpx
import asyncio

# ----- 1. CONFIGURATION -----
DB_CONFIG = "postgresql://sql_admin:sql_pass@72.62.151.169:5432/n8n"

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

async def fetch_route(client, token, origin, dest, flight_date, sem):
    url = f"https://api.lufthansa.com/v1/operations/customerflightinformation/route/{origin}/{dest}/{flight_date}"
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}

    async with sem:
        try:
            
            resp = await client.get(url, headers=headers)
            await asyncio.sleep(0.25)

            if resp.status_code == 429:
                print(f"Route {origin}-{dest}: Rate limited (429)")
                return None
            
            if resp.status_code == 401:
                print(f"Route {origin}-{dest}: Unauthorized - token may be expired")
                return None

            if resp.status_code != 200:
                return None

            json_data = resp.json()
            flights = (json_data.get("FlightInformation", {}).get("Flights", {}).get("Flight", []))
        
            if not flights:
                print(f"Route {origin}-{dest}: No flights available for {flight_date}")
                return None  # ← THIS is important

            df = pd.json_normalize(flights)
            df["route_key"] = f"{origin}-{dest}"
            return df

        except httpx.TimeoutException:
            logger.error(f"Route {origin}-{dest}: Timeout")
            return None
        except Exception as e:
            logger.error(f"Route {origin}-{dest}: Error - {type(e).__name__}: {str(e)}")
            return None
            

@router.get("/lh_flight/{flight_date}")
async def get_flightroute_details(flight_date: str):
    
    token = get_lufthansa_token()

    ROUTES_FULL = [
    # FRA Routes - Long Haul
    ("FRA", "SIN"), ("FRA", "HND"), ("FRA", "LAX"), ("FRA", "JFK"), ("FRA", "EWR"), ("FRA", "ORD"), ("FRA", "IAD"), ("FRA", "BOS"), ("FRA", "DEN"), ("FRA", "SFO"),
    ("FRA", "MIA"), ("FRA", "YYZ"), ("FRA", "MEX"), ("FRA", "DEL"), ("FRA", "BOM"), ("FRA", "BLR"), ("FRA", "HYD"), ("FRA", "ICN"), ("FRA", "GRU"), ("FRA", "DXB"),
    ("FRA", "CAI"), ("FRA", "TLV"), ("FRA", "BEY"), 
    # FRA Routes - European
    ("FRA", "LHR"), ("FRA", "LCY"), ("FRA", "CDG"), ("FRA", "AMS"), ("FRA", "MAD"), ("FRA", "BCN"), ("FRA", "LIS"), ("FRA", "ATH"), ("FRA", "IST"), ("FRA", "BER"),
    ("FRA", "HAM"), ("FRA", "DUS"), ("FRA", "MUC"), ("FRA", "VIE"), ("FRA", "ZRH"), ("FRA", "CPH"), ("FRA", "OSL"), ("FRA", "HEL"), ("FRA", "WAW"), ("FRA", "PRG"),
    ("FRA", "BUD"), ("FRA", "MXP"), ("FRA", "TLS"), ("FRA", "MAN"), ("FRA", "DUB"),
    # MUC Routes - Long Haul
    ("MUC", "LAX"), ("MUC", "SFO"), ("MUC", "DEN"), ("MUC", "ORD"), ("MUC", "EWR"), ("MUC", "JFK"), ("MUC", "BOS"), ("MUC", "DEL"), ("MUC", "BOM"), ("MUC", "BLR"),
    ("MUC", "BKK"), ("MUC", "JNB"), ("MUC", "CPT"), ("MUC", "DXB"),
    # MUC Routes - European
    ("MUC", "LHR"), ("MUC", "CDG"), ("MUC", "AMS"), ("MUC", "MAD"), ("MUC", "BCN"), ("MUC", "LIS"), ("MUC", "ATH"), ("MUC", "BER"), ("MUC", "HAM"), ("MUC", "DUS"),
    ("MUC", "FRA"), ("MUC", "VIE"), ("MUC", "ZRH"), ("MUC", "CPH"), ("MUC", "OSL"), ("MUC", "WAW"), ("MUC", "PRG"), ("MUC", "BUD"), ("MUC", "FCO"), ("MUC", "MXP"),
    ("MUC", "MAN"), ("MUC", "DUB"), ("MUC", "TLV"),
]           
                                                    
    sem = asyncio.Semaphore(4)  # rate-limit safety
    async with httpx.AsyncClient(timeout=45) as client:
        tasks = [fetch_route(client, token, o, d, flight_date, sem) for o, d in ROUTES_FULL]
        results = await asyncio.gather(*tasks)

    all_dataframes = [df for df in results if df is not None]
    
    if not all_dataframes:
        return []
        
    combined_df = pd.concat(all_dataframes, ignore_index=True)
    combined_df.columns = [c.replace('.', '_') for c in combined_df.columns]

    combined_df = combined_df.drop(columns=[
            "Departure_Terminal_Name", "Arrival_Terminal_Name", 
            "Departure_Status_Description", "Arrival_Status_Description", "Status_Description",
            "MarketingCarrierList_MarketingCarrier_AirlineID",
            "MarketingCarrierList_MarketingCarrier_FlightNumber",
            "MarketingCarrierList_MarketingCarrier",
    ], errors="ignore")
        
    combined_df["ingested_at"] = pd.Timestamp.now().isoformat()
    combined_df = combined_df.where(pd.notnull(combined_df), None)

    rename_map = {
            "Departure_AirportCode": "departure_airport_code",
            "Departure_Scheduled_Date": "departure_scheduled_date",
            "Departure_Scheduled_Time": "departure_scheduled_time",
            "Departure_Actual_Date": "departure_actual_date",
            "Departure_Actual_Time": "departure_actual_time",
            "Departure_Terminal_Gate": "departure_terminal_gate",
            "Departure_Status_Code": "departure_status_code",
            "Arrival_AirportCode": "arrival_airport_code",
            "Arrival_Scheduled_Date": "arrival_scheduled_date",
            "Arrival_Scheduled_Time": "arrival_scheduled_time",
            "Arrival_Actual_Date": "arrival_actual_date",
            "Arrival_Actual_Time": "arrival_actual_time",
            "Arrival_Terminal_Gate": "arrival_terminal_gate",
            "Arrival_Status_Code": "arrival_status_code",
            "OperatingCarrier_AirlineID": "operatingcarrier_airlineid",
            "OperatingCarrier_FlightNumber": "operatingcarrier_flightnumber",
            "Equipment_AircraftCode": "equipment_aircraftcode",
            "Status_Code": "status_code",
            "route_key": "route_key",
            "ingested_at": "ingested_at",
    }

    combined_df = combined_df.rename(columns=rename_map)
        
    return combined_df.to_dict(orient="records")

# --- Dash UI Setup ---
dash.register_page(__name__, icon="fa-coins", name="Lufthansa")

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
        html.H2("Crypto Market Info", className="text-light fw-bold mb-0") 
    ], className="mb-4"),

    dcc.Interval(id='refresh', interval=60*1000), 

    html.Div([
        html.H5("Execution Logs", className="text-light mb-3"),
        html.Div(id='status-table-container1', 
            style={"height": "300px", "overflowY": "auto", "overflowX": "hidden", "backgroundColor": "transparent",  "fontSize": "12px"})
    ], style=CARD_STYLE)

], fluid=True)

@callback(
    [Output('status-table-container1', 'children')],
    [Input('refresh', 'n_intervals')]
)

def update_dashboard(n):
    conn = psycopg2.connect(DB_CONFIG)
    df = pd.read_sql("SELECT * FROM lh_flights ORDER BY id DESC LIMIT 120", conn)
    conn.close()
    if df.empty:
        return html.Div(
            "No data found",
            className="text-light fst-italic"
        )

    #df["timestamp"] = pd.to_datetime(df["timestamp"],unit="ms", utc=True).dt.tz_convert("Europe/Budapest").dt.strftime("%Y-%m-%d %H:%M:%S")       
    #latest = df.sort_values("timestamp").groupby("symbol").last().reset_index() 

    # 0. Update Timestamp
    #metrics_update = f"Updated -> {latest["timestamp"].iloc[0]}"
    # metrics_update = pd.to_datetime(latest.loc["btc", "timestamp"],unit="ms").strftime("%Y-%m-%d %H:%M")             
  
    # 3. Crypto Table
    display_df = df.copy()
    display_df.columns = [c.replace('_', ' ').upper() for c in display_df.columns]
    table = dbc.Table.from_dataframe(display_df[:120], striped=False, hover=True, responsive=True, borderless=True, className="text-light m-0", 
        style={"backgroundColor": "transparent",  "--bs-table-bg": "transparent", "--bs-table-accent-bg": "transparent", "color": "white"}
    )

    return table
