# 2026.01.12  18.00
import dash
from dash import dcc, html, Input, Output, State, callback, dash_table
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd
import requests
import time
import os
from databricks import sql
from fastapi import APIRouter

# --- 1. FASTAPI ROUTER (If you want n8n to trigger the job) ---
router = APIRouter()

@router.post("/trigger")
def trigger_external_job():
    # Logic to trigger Databricks from n8n could go here
    return {"status": "Job trigger available via UI"}

# --- 2. CONFIGURATION ---
DBX_HOST = os.getenv("DBX_HOST")
DBX_HTTP_PATH = os.getenv("DBX_HTTP_PATH")
DBX_TOKEN = os.getenv("DBX_TOKEN")
KEEPALIVE_INTERVAL = int(os.getenv("DBX_KEEPALIVE_INTERVAL", "180"))
DBX_JOB_ID = os.getenv("DBX_JOB_ID")

headers = {"Authorization": f"Bearer {DBX_TOKEN}", "Content-Type": "application/json"}

# --- 3. DASH REGISTRATION & UI ---
dash.register_page(__name__, icon="fa-brain", name="ML Databricks")
#dash.register_page( __name__, name="ML Databricks", icon="fa-brain", path="/databricks")

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

    # ----- A. Trigger Databricks job -----
    run_now_url = f"https://{DBX_HOST}/api/2.2/jobs/run-now"
    payload = { "job_id": DBX_JOB_ID, "notebook_params": {"numTrees": str(numTrees), "maxDepth": str(maxDepth)}}

    response = requests.post(run_now_url, headers=headers, json=payload)
    if response.status_code != 200:
        return px.scatter(title=f"Error: {response.text}"), html.Div("Job Trigger Failed", className="text-danger")

    run_id = response.json().get("run_id")

    # ----- B. Poll status (Simplified for 8GB RAM responsiveness) -----
    status_url = f"https://{DBX_HOST}/api/2.2/jobs/runs/get?run_id={run_id}"
    for _ in range(20): # Timeout after ~60 seconds
        status_response = requests.get(status_url, headers=headers).json()
        state = status_response.get("state", {}).get("life_cycle_state")
        if state == "TERMINATED":
            break
        time.sleep(3)

    # ----- C. Query Results using Databricks SQL -----
    try:
        connection = sql.connect(server_hostname=DBX_HOST, http_path=DBX_HTTP_PATH, access_token=DBX_TOKEN)
        with connection.cursor() as cursor:
            cursor.execute("SELECT age, sex, bmi, bp, target, prediction FROM test_cat.test_db.diab_pred LIMIT 15")
            result_df = cursor.fetchall_arrow().to_pandas()
        connection.close()
    except Exception as e:
        return px.scatter(title=f"SQL Error: {e}"), html.Div(f"Query Error: {e}", className="text-danger")

    fig = px.scatter(result_df, x="target", y="prediction", title=f"RF Results: Trees={numTrees} | Depth={maxDepth}", template="plotly_dark")
    
    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',font_color="white", margin=dict(t=50, b=0, l=0, r=0))

    #result_df_formatted = result_df.copy()
    #for col in result_df_formatted.columns:
    #    result_df_formatted[col] = pd.to_numeric(result_df_formatted[col], errors='ignore')
    #result_df_formatted = result_df_formatted.round(3)

    table_df = result_df.copy()
    numeric_cols = table_df.select_dtypes(include="number").columns
    table_df[numeric_cols] = table_df[numeric_cols].round(3)

    table = dbc.Table.from_dataframe(table_df, striped=False, hover=True, responsive=True, borderless=True, className="text-light m-0", 
        style={"backgroundColor": "transparent", "--bs-table-bg": "transparent", "--bs-table-accent-bg": "transparent", "color": "white"}
    )

    return fig, table
