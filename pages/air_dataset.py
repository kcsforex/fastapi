# 2025.11.30  11.00
import dash
from dash import html, dcc, Output, Input, callback
import dash_bootstrap_components as dbc
from databricks import sql
import pandas as pd
import os
import requests
from fastapi import APIRouter

# --- 1. FASTAPI ROUTER (If you want n8n to trigger the job) ---
router = APIRouter()

@router.post("/airtrigger")
def trigger_external_job():
    # Logic to trigger Databricks from n8n could go here
    return {"status": "Air trigger available via UI"}

SERVER_HOSTNAME = 'dbc-9c577faf-b445.cloud.databricks.com' 
HTTP_PATH = '/sql/1.0/warehouses/cbfc343eb927c998' 
ACCESS_TOKEN = 'dapi04d3d1a0eb55db7ea63b2a6f3f2e1fa6' 
delta_path = '/Volumes/test_cat/test_db/test_vol/bronze/kg_airdelay_bronze/'

dash.register_page(__name__, icon="fa-brain", name="Air Dataset")

CARD_STYLE = {
    "background": "rgba(255, 255, 255, 0.03)",
    "backdrop-filter": "blur(10px)",
    "border-radius": "15px",
    "border": "1px solid rgba(255, 255, 255, 0.1)",
    "padding": "25px",
    "marginBottom": "20px"
}


layout = html.Div(
    [ 
        #dcc.Loading(dcc.Graph(id="sample-chart-2")),
        dcc.Input(id="selector-1", type="number", min=10, max=200, step=10, value=50),
        #dcc.Input(id="selector-2", type="text", value=list('SpiseJet','AirAsia', 'Air_India')),
         dbc.Container([    html.Div(id="table")], fluid=True)
    ],
    style=CARD_STYLE,
)


@callback(Output("table", "children"), Input("selector-1", "value"))
def create_table(val1):
    connection = sql.connect(
        server_hostname=SERVER_HOSTNAME, http_path=HTTP_PATH, access_token=ACCESS_TOKEN
    )
    cursor = connection.cursor()
    cursor.execute(
        f"SELECT * FROM delta.`{delta_path}` LIMIT {val1}"
    )
    df = cursor.fetchall_arrow()
    result_df = df.to_pandas()

    cursor.close()
    connection.close()

    table = dbc.Table.from_dataframe(
        result_df, 
        striped=False, 
        hover=True, 
        responsive=True,
        borderless=True,
        className="text-light m-0", 
        style={
            "backgroundColor": "transparent", 
            "--bs-table-bg": "transparent", # Overrides Bootstrap 5 background variable
            "--bs-table-accent-bg": "transparent",
            "color": "white"
        }
    )

    return table

