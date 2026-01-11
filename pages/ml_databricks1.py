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

# --------------------------------------------------
# 1. FASTAPI ROUTER
# --------------------------------------------------
router = APIRouter()

@router.post("/trigger")
def trigger_external_job():
    return {"status": "Job trigger available via UI"}

# --------------------------------------------------
# 2. CONFIGURATION
# --------------------------------------------------
DATABRICKS_INSTANCE = "dbc-9c577faf-b445.cloud.databricks.com"
TOKEN = "dapi04d3d1a0eb55db7ea63b2a6f3f2e1fa6"
JOB_ID = "718482410766048"
HTTP_PATH = "/sql/1.0/warehouses/cbfc343eb927c998"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json",
}

# --------------------------------------------------
# 3. SQL WAREHOUSE LOADER
# --------------------------------------------------
def load_sql_results(limit=50):
    connection = sql.connect(
        server_hostname=DATABRICKS_INSTANCE,
        http_path=HTTP_PATH,
        access_token=TOKEN,
    )
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT age, sex, bmi, bp, target, prediction
                FROM test_cat.test_db.diab_pred
                LIMIT {limit}
                """
            )
            df = cursor.fetchall_arrow().to_pandas()
    finally:
        connection.close()

    return df

# --------------------------------------------------
# 4. LOAD INITIAL DATA (ONCE)
# --------------------------------------------------
try:
    initial_df = load_sql_results()
except Exception as e:
    print("Initial SQL load failed:", e)
    initial_df = pd.DataFrame()

# --------------------------------------------------
# 5. INITIAL FIGURE & TABLE
# --------------------------------------------------
if not initial_df.empty:
    initial_fig = px.scatter(
        initial_df,
        x="target",
        y="prediction",
        title="Initial Model Results",
        template="plotly_dark",
    )
else:
    initial_fig = px.scatter(title="No data available")

initial_fig.update_layout(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font_color="white",
    margin=dict(t=50, b=0, l=0, r=0),
)

initial_table = (
    dbc.Table.from_dataframe(
        initial_df,
        striped=False,
        hover=True,
        responsive=True,
        borderless=True,
        className="text-light m-0",
    )
    if not initial_df.empty
    else html.Div("No data available", className="text-muted")
)

# --------------------------------------------------
# 6. DASH REGISTRATION & UI
# --------------------------------------------------
dash.register_page(__name__, icon="fa-brain", name="ML Databricks")

CARD_STYLE = {
    "background": "rgba(255, 255, 255, 0.03)",
    "backdrop-filter": "blur(10px)",
    "border-radius": "15px",
    "border": "1px solid rgba(255, 255, 255, 0.1)",
    "padding": "25px",
    "marginBottom": "20px",
}

layout = dbc.Container(
    [
        html.Div(
            [
                html.H2("Random Forest Engine", className="text-light fw-bold mb-0"),
                html.P(
                    "Remote Execution on Databricks Cluster",
                    className="text-muted small",
                ),
            ],
            className="mb-4",
        ),
        dbc.Row(
            [
                # Controls
                dbc.Col(
                    [
                        html.Div(
                            [
                                html.Label("Number of Trees",
