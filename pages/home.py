import dash
from dash import html, callback, Output, Input
import dash_bootstrap_components as dbc

import sys
import platform
import os
import shutil
import psutil

from importlib.metadata import version, PackageNotFoundError


# =========================
# Styling
# =========================

CARD_STYLE = {
    "background": "rgba(255, 255, 255, 0.03)",
    "backdropFilter": "blur(10px)",
    "borderRadius": "15px",
    "border": "1px solid rgba(255, 255, 255, 0.1)",
    "padding": "25px",
    "marginBottom": "20px"
}


# =========================
# Packages to inspect
# =========================

PACKAGES = [
    "fastapi", "uvicorn", "dash", "dash-bootstrap-components",
    "pandas", "numpy", "scipy", "scikit-learn", "databricks-sql-connector"
]


# =========================
# Runtime info
# =========================

def get_runtime_info():
    info_header = [
        ("Python Version", sys.version.split()[0]),
        ("Implementation", platform.python_implementation()),
        ("OS Platform", platform.platform()),
    ]

    pkg_rows = []
    for p in PACKAGES:
        try:
            pkg_rows.append((p, version(p)))
        except PackageNotFoundError:
            pkg_rows.append((p, "not installed"))

    return info_header, pkg_rows


# =========================
# Host metrics
# =========================

def get_host_metrics():
    cpu = psutil.cpu_percent(interval=0.5)
    mem = psutil.virtual_memory()
    disk = shutil.disk_usage("/")

    return [
        ("CPU Usage", f"{cpu} %"),
        ("CPU Cores", psutil.cpu_count(logical=True)),
        ("Memory Usage", f"{mem.percent} %"),
        ("Memory Total", f"{mem.total / (1024**3):.1f} GB"),
        ("Disk Usage", f"{disk.used / disk.total * 100:.1f} %"),
        ("Disk Total", f"{disk.total / (1024**3):.1f} GB"),
    ]


# =========================
# Page registration
# =========================

dash.register_page(
    __name__,
    path="/",
    name="Overview",
    icon="fa-home"
)


# =========================
# Layout
# =========================

layout = dbc.Container([

    # Header
    html.Div([
        html.H1("System Control Center", className="text-light fw-bold"),
        html.P("Monitoring 4 Data Grabbers & 1 ML Engine", className="text-muted"),
    ], className="mb-5"),

    # Status cards
    dbc.Row([
        dbc.Col(dbc.Card(
            dbc.CardBody([
                html.H5("Crypto Engine", className="text-info"),
                html.P("Status: Active", className="small"),
                html.Div("BTC: $96,432", className="h4"),
            ]),
            style={"background": "rgba(255,255,255,0.05)"}
        ), width=4),

        dbc.Col(dbc.Card(
            dbc.CardBody([
                html.H5("Lufthansa API", className="text-warning"),
                html.P("Status: Syncing", className="small"),
                html.Div("Last: 2m ago", className="h4"),
            ]),
            style={"background": "rgba(255,255,255,0.05)"}
        ), width=4),

        dbc.Col(dbc.Card(
            dbc.CardBody([
                html.H5("ML Engine", className="text-success"),
                html.P("Backend: Databricks", className="small"),
                html.Div("98% Acc", className="h4"),
            ]),
            style={"background": "rgba(255,255,255,0.05)"}
        ), width=4),
    ], className="mb-5"),

    # Runtime environment card
    dbc.Row([

    # Runtime Environment (LEFT)
    dbc.Col(
        dbc.Card(
            dbc.CardBody([
                html.H4("Runtime Environment", className="text-light"),
                html.Div(id="env-table"),
                dbc.Button("Refresh", id="refresh-btn", color="secondary", outline=True, size="sm", className="mt-3")
            ]),
            style=CARD_STYLE
        ),
        width=6
    ),

    # Package Versions (RIGHT)
    dbc.Col(
        dbc.Card(
            dbc.CardBody([
                html.H4("Package Versions", className="text-light"),
                html.Div(id="packages-table"),
            ]),
            style=CARD_STYLE
        ),
        width=6
    ),

], className="mb-4")


], fluid=True)


# =========================
# Callback
# =========================

@callback(
    Output("env-table", "children"),
    Output("packages-table", "children"),
    Input("refresh-btn", "n_clicks"),
)
def render_tables(_):

    runtime_info, pkg_rows = get_runtime_info()
    host_metrics = get_host_metrics()

    env_rows = runtime_info + host_metrics

    env_tbl = dbc.Table(
        [
            html.Thead(html.Tr([
                html.Th("Metric"),
                html.Th("Value")
            ])),
            html.Tbody([
                html.Tr([
                    html.Td(k),
                    html.Td(v)
                ]) for k, v in env_rows
            ])
        ],
        hover=True,
        responsive=True,
        className="table-sm text-light",
        style={"backgroundColor": "transparent"}
    )

    pkg_tbl = dbc.Table(
        [
            html.Thead(html.Tr([
                html.Th("Package"),
                html.Th("Version")
            ])),
            html.Tbody([
                html.Tr([
                    html.Td(p),
                    html.Td(v)
                ]) for p, v in pkg_rows
            ])
        ],
        hover=True,
        responsive=True,
        className="table-sm text-light",
        style={"backgroundColor": "transparent"}
    )

    return env_tbl, pkg_tbl
