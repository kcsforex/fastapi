import dash
from dash import html, callback, Output, Input
import dash_bootstrap_components as dbc
import sys
import platform
from importlib.metadata import version, PackageNotFoundError

CARD_STYLE = {
    "background": "rgba(255, 255, 255, 0.03)",
    "backdropFilter": "blur(10px)",
    "borderRadius": "15px",
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


dash.register_page(__name__, path='/', icon="fa-home", name="Overview")

layout = dbc.Container([

    # Header
    html.Div([
        html.H1("System Control Center", className="text-light fw-bold"),
        html.P("Monitoring 4 Data Grabbers & 1 ML Engine", className="text-muted"),
    ], className="mb-5"),

    # Status Cards
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

    # Runtime Environment Card
    dbc.Card([
        dbc.CardBody([
            html.H4("Runtime Environment", className="text-light"),
            html.Div(id="env-table"),
            html.Hr(className="border-secondary"),
            html.H5("Package Versions", className="text-light"),
            html.Div(id="packages-table"),
            dbc.Button(
                "Refresh",
                id="refresh-btn",
                color="secondary",
                outline=True,
                size="sm",
                className="mt-3"
            )
        ])
    ], style=CARD_STYLE)

], fluid=True)


@callback(
    Output("env-table", "children"),
    Output("packages-table", "children"),
    Input("refresh-btn", "n_clicks"),
)
def render_tables(_):

    info_header, pkg_rows = get_runtime_info()

    env_tbl = dbc.Table(
        [
            html.Thead(html.Tr([
                html.Th("Key"),
                html.Th("Value")
            ])),
            html.Tbody([
                html.Tr([html.Td(k), html.Td(v)]) for k, v in info_header
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
                html.Tr([html.Td(p), html.Td(v)]) for p, v in pkg_rows
            ])
        ],
        hover=True,
        responsive=True,
        className="table-sm text-light",
        style={"backgroundColor": "transparent"}
    )

    return env_tbl, pkg_tbl



