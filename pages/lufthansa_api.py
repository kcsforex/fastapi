import os
import httpx
import asyncio
import pandas as pd
import requests
from fastapi import APIRouter
from sqlalchemy import create_engine

# ----- CONFIGURATION -----
DB_CONFIG = "postgresql://sql_admin:sql_pass@72.62.151.169:5432/n8n"
sql_engine = create_engine(DB_CONFIG, pool_size=10, max_overflow=20)

router = APIRouter()

def get_lufthansa_token():
    CLIENT_ID = os.getenv("LH_CLIENT_ID")
    CLIENT_SECRET = os.getenv("LH_CLIENT_SECRET")
    token_url = "https://api.lufthansa.com/v1/oauth/token"
    payload = {"grant_type": "client_credentials", "client_id": CLIENT_ID, "client_secret": CLIENT_SECRET}
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
            if resp.status_code != 200: return None
            
            json_data = resp.json()
            flights = json_data.get("FlightInformation", {}).get("Flights", {}).get("Flight", [])
            if not flights: return None

            df = pd.json_normalize(flights)
            df["route_key"] = f"{origin}-{dest}"
            return df
        except Exception:
            return None

@router.get("/lh_flight/{flight_date}")
async def get_flightroute_details(flight_date: str):
    token = get_lufthansa_token()
    # ... (Keep your ROUTES_FULL list here) ...
    ROUTES_FULL = [("FRA", "SIN"), ("FRA", "HND"), ("MUC", "LAX")] # Truncated for brevity
    
    sem = asyncio.Semaphore(4)
    async with httpx.AsyncClient(timeout=45) as client:
        tasks = [fetch_route(client, token, o, d, flight_date, sem) for o, d in ROUTES_FULL]
        results = await asyncio.gather(*tasks)

    all_dataframes = [df for df in results if df is not None]
    if not all_dataframes: return []
        
    combined_df = pd.concat(all_dataframes, ignore_index=True)
    combined_df.columns = [c.replace('.', '_') for c in combined_df.columns]
    combined_df["ingested_at"] = pd.Timestamp.now().isoformat()
    # ... (Keep your rename_map logic here) ...
    
    return combined_df.to_dict(orient="records")
