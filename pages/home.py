import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
import sys
import platform
from importlib.metadata import version, PackageNotFoundError

CARD_STYLE = {
    "background": "rgba(255, 255, 255, 0.03)",
    "backdrop-filter": "blur(10px)",
    "border-radius": "15px",
    "border": "1px solid rgba(255, 255, 255, 0.1)",
    "padding": "25px",
    "marginBottom": "20px"
}

PACKAGES = [
    "fastapi", "uvicorn", "dash", "dash-bootstrap-components",
    "pandas", "numpy", "scipy", "scikit-learn", "databricks-sql-connector"
]

def get_runtime_info():
    info_header = [
        ("Python", sys.version.split()[0]),
        ("Implementation", platform.python_implementation()),
        ("Platform", platform.platform())
    ]

    pkg_rows = []
    for p in PACKAGES:
        try:
            pkg_rows.append((p, version(p)))
        except PackageNotFoundError:
            pkg_rows.append((p, "not installed"))
    return info_header, pkg_rows

# Register this as the root page ('/')
dash.register_page(__name__, path='/', icon="fa-home", name="Overview")

layout = html.Div([
    html.H4("Runtime environment", className="text-light"),
    html.Div(id="env-table"),
    html.Hr(),
    html.H5("Package versions", className="text-light"),
    html.Div(id="packages-table"),
    dbc.Button("Refresh", id="refresh-btn", color="secondary", className="mt-3"),
], style=CARD_STYLE)

layout = dbc.Container([
    # Welcome Header
    html.Div([
        html.H1("System Control Center", className="text-light fw-bold"),
        html.P("Monitoring 4 Data Grabbers & 1 ML Engine", className="text-muted"),
    ], className="mb-5"),

    # Status Cards Row
    dbc.Row([
        # Card 1: Crypto Status
        dbc.Col(dbc.Card([
            dbc.CardBody([
                html.H5("Crypto Engine", className="card-title text-info"),
                html.P("Status: Active", className="mb-0 small"),
                html.Div("BTC: $96,432", className="h4 py-2"),
                dbc.Button("View Live", href="/crypto", size="sm", color="info", outline=True)
            ])
        ], style={"background": "rgba(255,255,255,0.05)", "border": "1px solid rgba(255,255,255,0.1)"}), width=4),

        # Card 2: Flight Data
        dbc.Col(dbc.Card([
            dbc.CardBody([
                html.H5("Lufthansa API", className="card-title text-warning"),
                html.P("Status: Syncing", className="mb-0 small"),
                html.Div("Last: 2m ago", className="h4 py-2"),
                dbc.Button("Logs", href="/flights", size="sm", color="warning", outline=True)
            ])
        ], style={"background": "rgba(255,255,255,0.05)", "border": "1px solid rgba(255,255,255,0.1)"}), width=4),

        # Card 3: ML Processing
        dbc.Col(dbc.Card([
            dbc.CardBody([
                html.H5("ML Engine", className="card-title text-success"),
                html.P("Backend: Databricks", className="mb-0 small"),
                html.Div("98% Acc", className="h4 py-2"),
                dbc.Button("Analyze", href="/ml-large", size="sm", color="success", outline=True)
            ])
        ], style={"background": "rgba(255,255,255,0.05)", "border": "1px solid rgba(255,255,255,0.1)"}), width=4),
    ], className="mb-4"),

    # Server Info Section
    html.Div([
        html.H6("HOSTING ENVIRONMENT", className="text-muted small mb-3"),
        dbc.ListGroup([
            dbc.ListGroupItem([
                html.Span("Server Type: ", className="text-muted"), "Hostinger KVM-V2"
            ], className="bg-transparent text-light border-0 ps-0"),
            dbc.ListGroupItem([
                html.Span("Resources: ", className="text-muted"), "2 vCPU / 8GB RAM"
            ], className="bg-transparent text-light border-0 ps-0"),
            dbc.ListGroupItem([
                html.Span("Database: ", className="text-muted"), "PostgreSQL (Shared with n8n)"
            ], className="bg-transparent text-light border-0 ps-0"),
        ])
    ], className="p-4 rounded-3", style={"background": "rgba(0,0,0,0.2)"})


], fluid=True)

@callback(
    Output("env-table", "children"),
    Output("packages-table", "children"),
    Input("refresh-btn", "n_clicks"),
    prevent_initial_call=False
)
def render_tables(_):
    info_header, pkg_rows = get_runtime_info()

    # Top table: Python / OS
    env_tbl = dbc.Table(
        [html.Thead(html.Tr([html.Th("Key"), html.Th("Value")]))] +
        [html.Tbody([html.Tr([html.Td(k), html.Td(v)]) for k, v in info_header])],
        bordered=False, hover=True, responsive=True, className="text-light m-0",
        style={
            "backgroundColor": "transparent",
            "--bs-table-bg": "transparent",
            "--bs-table-accent-bg": "transparent",
            "color": "white"
        }
    )

    # Packages table
    pkg_tbl = dbc.Table(
        [html.Thead(html.Tr([html.Th("Package"), html.Th("Version")]))] +
        [html.Tbody([html.Tr([html.Td(p), html.Td(v)]) for p, v in pkg_rows])],
        bordered=False, hover=True, responsive=True, className="text-light m-0",
        style={
            "backgroundColor": "transparent",
            "--bs-table-bg": "transparent",
            "--bs-table-accent-bg": "transparent",
            "color": "white"
        }
    )

    return env_tbl, pkg_tbl


