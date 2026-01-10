# 2026.01.10  10.00
import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
from fastapi import FastAPI
from fastapi.middleware.wsgi import WSGIMiddleware

#from pages.ml_large import router as ml_router
#from pages.flights import router as flight_router
#from pages.ml_small_api import router as ml_small_router

# ----- 1. DASH INITIALIZATION -----
app = dash.Dash(__name__, use_pages=True, external_stylesheets=[dbc.themes.DARKLY, "https://use.fontawesome.com/releases/v5.15.4/css/all.css"])

# ----- 2. NOW IMPORT YOUR PAGES -----
# By importing them here, 'app' already exists when dash.register_page is called
from pages import crypto, crypto0, home  # This triggers register_page correctly

# ----- 3. FASTAPI WRAPPER -----
server = FastAPI(title="Dash Main App")

# ----- 4. Use the router directly from the imported module -----
server.include_router(crypto.router, prefix="/api/crypto", tags=["Crypto"])
#server.include_router(ml_router, prefix="/api/ml", tags=["Machine Learning"])
#server.include_router(flight_router, prefix="/api/flights")
#server.include_router(ml_small_router, prefix="/api/ml-small")

# ----- 5. SIDEBAR & LAYOUT  (Your Modern Layout) -----
SIDEBAR_STYLE = {
    "position": "fixed", "top": "15px", "left": "15px", "bottom": "15px",
    "width": "220px", "padding": "2rem 1rem",
    "background": "rgba(255, 255, 255, 0.1)",
    "backdrop-filter": "blur(15px)",
    "border-radius": "20px",
    "border": "1px solid rgba(255, 255, 255, 0.1)",
    "box-shadow": "0 8px 32px 0 rgba(0, 0, 0, 0.5)",
    "z-index": 1000,
}

sidebar = html.Div([
    html.H4("PETROSOFTEU CLOUD", className="text-center mb-4", style={"letterSpacing": "2px", "color": "ivory"}),
    
    # User Profile Box
    html.Div([
        html.Div([
            html.I(className="fas fa-user-circle fa-2x text-info"),
            html.Div([
                html.P("Admin Console", className="mb-0", style={"fontSize": "14px", "fontWeight": "bold"}),
                html.P("8GB KVM2", className="text-muted small mb-0")
            ], className="ms-3")
        ], className="d-flex align-items-center p-3", style={"background": "rgba(0,0,0,0.3)", "borderRadius": "15px"})
    ], className="mb-4"),

    html.Hr(style={"color": "rgba(255,255,255,0.3)"}),

    dbc.Nav([
        dbc.NavLink([
            html.Div([
                html.I(className=f"fas {page.get('icon', 'fa-chart-line')} me-2"),
                html.Span(page["name"]),
            ], className="d-flex align-items-center")
        ], href=page["relative_path"], active="exact", className="mb-2 py-2 ps-2 rounded-3 text-light")
        for page in dash.page_registry.values()
    ], vertical=True, pills=True),
], style=SIDEBAR_STYLE)

app.layout = html.Div([
    sidebar,
    html.Div(dash_container := dash.page_container, style={
        "marginLeft": "250px", "padding": "2rem",
        "background": "linear-gradient(135deg, #0f0c29, #302b63, #24243e)",
        "minHeight": "100vh"
    })
])

# ----- 6. Mount Dash to FastAPI -----
server.mount("/", WSGIMiddleware(app.server))

if __name__ == "__main__":
    import uvicorn
    # Use uvicorn to run the 'server' object
    uvicorn.run(server, host="0.0.0.0", port=8050)
