import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
from fastapi import FastAPI
from fastapi.middleware.wsgi import WSGIMiddleware

# Must happen BEFORE Dash initialization to ensure registration)
try:
    from pages.crypto import router as crypto_router
except ImportError:
    from fastapi import APIRouter
    crypto_router = APIRouter()
from pages.crypto import router as crypto_router

#from pages.ml_large import router as ml_router
#from pages.flights import router as flight_router
#from pages.ml_small_api import router as ml_small_router

# --- DASH INITIALIZATION ---
app = dash.Dash(
    __name__, 
    use_pages=True, 
    external_stylesheets=[
        dbc.themes.DARKLY,
        "https://use.fontawesome.com/releases/v5.15.4/css/all.css"
    ]
)

# Sidebar styling (Your Modern Layout)
SIDEBAR_STYLE = {
    "position": "fixed", "top": "20px", "left": "20px", "bottom": "20px",
    "width": "260px", "padding": "2rem 1rem",
    "background": "rgba(255, 255, 255, 0.05)",
    "backdrop-filter": "blur(15px)",
    "border-radius": "20px",
    "border": "1px solid rgba(255, 255, 255, 0.1)",
    "box-shadow": "0 8px 32px 0 rgba(0, 0, 0, 0.37)",
    "z-index": 1000,
}

sidebar = html.Div([
    html.H3("TRADING BOT", className="text-center mb-4", style={"letterSpacing": "2px", "color": "white"}),
    
    # User Profile Box
    html.Div([
        html.Div([
            html.I(className="fas fa-user-circle fa-2x text-info"),
            html.Div([
                html.P("Admin.Console", className="mb-0", style={"fontSize": "14px", "fontWeight": "bold"}),
                html.P("8GB KVM-V2", className="text-muted small mb-0")
            ], className="ms-3")
        ], className="d-flex align-items-center p-3", style={"background": "rgba(0,0,0,0.3)", "borderRadius": "15px"})
    ], className="mb-4"),

    html.Hr(style={"color": "rgba(255,255,255,0.1)"}),
    html.P("MENU", className="text-muted small ms-2 mb-3", style={"letterSpacing": "1px"}),

    dbc.Nav([
        dbc.NavLink([
            html.Div([
                html.I(className=f"fas {page.get('icon', 'fa-chart-line')} me-3"),
                html.Span(page["name"]),
            ], className="d-flex align-items-center")
        ], href=page["relative_path"], active="exact", className="mb-2 py-2 rounded-3 text-light")
        for page in dash.page_registry.values()
    ], vertical=True, pills=True),
], style=SIDEBAR_STYLE)

app.layout = html.Div([
    html.Style(".nav-link.active { background-color: rgba(59, 130, 246, 0.5) !important; border: 1px solid rgba(255,255,255,0.2) !important; }"),
    sidebar,
    html.Div(dash_container := dash.page_container, style={
        "marginLeft": "300px", "padding": "2rem",
        "background": "linear-gradient(135deg, #0f0c29, #302b63, #24243e)",
        "minHeight": "100vh"
    })
])

# --- FASTAPI WRAPPER ---
server = FastAPI(title="Dash Main App")

# Mount the 3 local API routers
server.include_router(crypto_router, prefix="/api/crypto", tags=["Crypto"])
#server.include_router(ml_router, prefix="/api/ml", tags=["Machine Learning"])
#server.include_router(flight_router, prefix="/api/flights")
#server.include_router(ml_small_router, prefix="/api/ml-small")

# Mount Dash to FastAPI
server.mount("/", WSGIMiddleware(app.server))

if __name__ == "__main__":
    import uvicorn
    # Use uvicorn to run the 'server' object
    uvicorn.run(server, host="0.0.0.0", port=8050)
