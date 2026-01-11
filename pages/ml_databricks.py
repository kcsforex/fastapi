# 2026.01.11  12.00
import dash
from dash import dcc, html, Input, Output, State, callback, dash_table
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd
import requests
import time
from databricks import sql
from fastapi import APIRouter

# --- 1. FASTAPI ROUTER (If you want n8n to trigger the job) ---
router = APIRouter()

@router.post("/trigger")
def trigger_external_job():
    # Logic to trigger Databricks from n8n could go here
    return {"status": "Job trigger available via UI"}

# --- 2. CONFIGURATION ---
DATABRICKS_INSTANCE = 'dbc-9c577faf-b445.cloud.databricks.com' # Removed https:// for sql.connect
TOKEN = 'dapi04d3d1a0eb55db7ea63b2a6f3f2e1fa6' 
JOB_ID = '718482410766048'
HTTP_PATH = '/sql/1.0/warehouses/cbfc343eb927c998'

headers = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}

# --- 3. DASH REGISTRATION & UI ---
dash.register_page(__name__, icon="fa-brain", name="ML Databricks")

CARD_STYLE = {
    "background": "rgba(255, 255, 255, 0.03)",
    "backdrop-filter": "blur(10px)",
    "border-radius": "15px",
    "border": "1px solid rgba(255, 255, 255, 0.1)",
    "padding": "25px",
    "marginBottom": "20px"
}

layout = dbc.Container([
    html.Div([
        html.H2("Random Forest Engine", className="text-light fw-bold mb-0"),
        html.P("Remote Execution on Databricks Cluster", className="text-muted small"),
    ], className="mb-4"),

    dbc.Row([
        # Controls Sidebar
        dbc.Col([
            html.Div([
                html.Label("Number of Trees", className="text-info small"),
                dcc.Slider(id="numTrees", min=3, max=10, step=1, value=5, 
                           marks={i: {'label': str(i), 'style': {'color': 'white'}} for i in range(5, 26, 5)}),
                
                html.Label("Max Depth", className="text-info small mt-4"),
                dcc.Slider(id="maxDepth", min=2, max=5, step=1, value=3,
                           marks={i: {'label': str(i), 'style': {'color': 'white'}} for i in range(2, 11, 2)}),
                
                dbc.Button([
                    html.I(className="fas fa-play me-2"), "Run Model"
                ], id="run-btn", color="info", className="w-100 mt-5 fw-bold", style={"borderRadius": "10px"})
            ], style=CARD_STYLE)
        ], width=12, lg=4),

        # Results Area
        dbc.Col([
            html.Div([
                dcc.Loading(
                    dcc.Graph(id="rf-chart", config={'displayModeBar': False}),
                    type="graph", color="#00d1ff"
                )
            ], style=CARD_STYLE),
            
            html.Div(id="rf-table-container", style=CARD_STYLE)
        ], width=12, lg=8)
    ])
], fluid=True)

# --- 4. CALLBACKS ---
@callback(
    [Output("rf-chart", "figure"),
    Output("rf-table-container", "children")],
    [Input("run-btn", "n_clicks")],
    [State("numTrees", "value"),
     State("maxDepth", "value")],
    prevent_initial_call=True
)
def update_chart(n_clicks, numTrees, maxDepth):
    if not n_clicks:
        raise PreventUpdate

    # A. Trigger Databricks job
    run_now_url = f"https://{DATABRICKS_INSTANCE}/api/2.2/jobs/run-now"
    payload = {
        "job_id": JOB_ID, 
        "notebook_params": {"numTrees": str(numTrees), "maxDepth": str(maxDepth)}
    }

    response = requests.post(run_now_url, headers=headers, json=payload)
    if response.status_code != 200:
        return px.scatter(title=f"Error: {response.text}"), html.Div("Job Trigger Failed", className="text-danger")

    run_id = response.json().get("run_id")

    # B. Poll status (Simplified for 8GB RAM responsiveness)
    status_url = f"https://{DATABRICKS_INSTANCE}/api/2.2/jobs/runs/get?run_id={run_id}"
    for _ in range(20): # Timeout after ~60 seconds
        status_response = requests.get(status_url, headers=headers).json()
        state = status_response.get("state", {}).get("life_cycle_state")
        if state == "TERMINATED":
            break
        time.sleep(3)

    # C. Query Results using Databricks SQL
    try:
        connection = sql.connect(
            server_hostname=DATABRICKS_INSTANCE, 
            http_path=HTTP_PATH, 
            access_token=TOKEN
        )
        with connection.cursor() as cursor:
            cursor.execute("SELECT age, sex, bmi, bp, target, prediction FROM test_cat.test_db.diab_pred LIMIT 50")
            result_df = cursor.fetchall_arrow().to_pandas()
        connection.close()
    except Exception as e:
        return px.scatter(title=f"SQL Error: {e}"), html.Div(f"Query Error: {e}", className="text-danger")

    # D. Build Visuals
    fig = px.scatter(result_df, x="target", y="prediction", 
                     title=f"RF Results: Trees={numTrees} | Depth={maxDepth}",
                     template="plotly_dark")
    
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        font_color="white", margin=dict(t=50, b=0, l=0, r=0)
    )

    table = dash_table.DataTable(
        data=result_df.to_dict('records'),
        columns=[{"name": i.upper(), "id": i} for i in result_df.columns],
        page_size=10,
        style_header={'backgroundColor': 'rgba(0,0,0,0.5)', 'color': '#00d1ff', 'border': '1px solid #444'},
        style_cell={'backgroundColor': 'transparent', 'color': 'white', 'border': '1px solid #333'},
        style_table={'overflowX': 'auto'}
    )

    return fig, table
