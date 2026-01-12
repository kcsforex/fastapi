import dash
from dash import html
import dash_bootstrap_components as dbc

dash.register_page(__name__, icon="fa-th-large", name="Home0")

def create_status_card(title, value, status, color, icon):
    return dbc.Col(html.Div([
        html.Div([
            html.I(className=f"fas {icon} fa-lg text-{color}"),
            html.Span(status, className=f"badge rounded-pill bg-{color} ms-auto", style={"fontSize": "10px"})
        ], className="d-flex align-items-center mb-3"),
        html.H6(title, className="text-muted mb-1", style={"fontSize": "12px"}),
        html.H3(value, className="text-light fw-bold")
    ], style={
        "background": "rgba(255,255,255,0.03)",
        "border": "1px solid rgba(255,255,255,0.1)",
        "padding": "20px",
        "border-radius": "15px"
    }), width=12, lg=3, className="mb-3")

layout = dbc.Container([
    html.Div([
        html.H1("Command Center", className="text-light fw-bold mb-0"),
        html.P("8GB KVM-V2 Cluster Management", className="text-muted")
    ], className="py-5"),

    # Real-time Stats Row
    dbc.Row([
        create_status_card("ACTIVE ASSETS", "5 Tokens", "LIVE", "info", "fa-coins"),
        create_status_card("SYSTEM LOAD", "12%", "STABLE", "success", "fa-microchip"),
        create_status_card("API UPTIME", "99.9%", "ONLINE", "primary", "fa-network-wired"),
        create_status_card("n8n SYNC", "Active", "SYNC", "warning", "fa-sync"),
    ], className="mb-5"),

    # Navigation Cards
    html.H5("System Applications", className="text-light mb-4"),
    dbc.Row([
        dbc.Col(dbc.Button([
            html.I(className="fas fa-chart-line mb-3 fa-2x"),
            html.Div("Crypto Monitor")
        ], href="/crypto", className="w-100 py-4 btn-dark", style={"borderRadius": "15px", "background": "rgba(0,0,0,0.2)"}), width=6, lg=3),
        
        dbc.Col(dbc.Button([
            html.I(className="fas fa-plane mb-3 fa-2x"),
            html.Div("Flight Logs")
        ], href="/flights", className="w-100 py-4 btn-dark", style={"borderRadius": "15px", "background": "rgba(0,0,0,0.2)"}), width=6, lg=3),

        dbc.Col(dbc.Button([
            html.I(className="fas fa-brain mb-3 fa-2x"),
            html.Div("ML Engine")
        ], href="/ml-large", className="w-100 py-4 btn-dark", style={"borderRadius": "15px", "background": "rgba(0,0,0,0.2)"}), width=6, lg=3),

        dbc.Col(dbc.Button([
            html.I(className="fas fa-database mb-3 fa-2x"),
            html.Div("DB Manager")
        ], href="/db-admin", className="w-100 py-4 btn-dark", style={"borderRadius": "15px", "background": "rgba(0,0,0,0.2)"}), width=6, lg=3),
    ])

], fluid=True)
