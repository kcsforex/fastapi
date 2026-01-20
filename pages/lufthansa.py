# 2026.01.20  18.00
import dash
import pandas as pd
from dash import html, dcc, Input, Output, State, callback, no_update
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go

from apis.lufthansa_api import sql_engine
import pages.lufthansa_ml as lh_ml   

dash.register_page(__name__, icon="fa-plane", name="Lufthansa Tracker")

CARD_STYLE = {
    "background": "rgba(255, 255, 255, 0.03)",
    "backdrop-filter": "blur(10px)",
    "border-radius": "15px",
    "border": "1px solid rgba(255, 255, 255, 0.1)",
    "padding": "20px"
}

layout = dbc.Container([

    html.Div([
        html.H2("Lufthansa Flight Info", className="text-light fw-bold mb-0"),
        html.P(id='lh-metrics-update', className="text-muted small"),
    ], className="mb-4"),

    dcc.Interval(id='refresh', interval=60000),
    dcc.Store(id="lh-df-store"),

    html.Div([
        html.H5("Daily Ingestion Volume", className="text-light mb-3"),
        dcc.Graph(id='lh-daily-chart', config={'displayModeBar': False})
    ], style=CARD_STYLE, className="mb-4"),

    html.Div([
        html.H5("Execution Logs", className="text-light mb-3"),
        html.Div(id='lh-table-container',
            style={"height": "300px", "overflowY": "auto", "fontSize": "12px"})
    ], style=CARD_STYLE, className="mb-4"),

    
html.Div([
    html.Div([
        html.H5("ML Modeling", className="text-light mb-2"),

        dbc.Row([
            dbc.Col([
                html.Label("Regression Model", className="text-light small"),
                dbc.Select(
                    id="lh-reg-model",
                    options=[
                        {"label": "Linear Regression", "value": "lin"},
                        {"label": "Decision Tree (Reg)", "value": "tree_reg"},
                        {"label": "Random Forest (Reg)", "value": "rf_reg"},
                    ],
                    value="lin",
                    size="sm"
                )
            ], md=4),

            dbc.Col([
                html.Label("Classification Model", className="text-light small"),
                dbc.Select(
                    id="lh-clf-model",
                    options=[
                        {"label": "Logistic Regression", "value": "log"},
                        {"label": "Decision Tree (Clf)", "value": "tree_clf"},
                        {"label": "Random Forest (Clf)", "value": "rf_clf"},
                    ],
                    value="log",
                    size="sm"
                )
            ], md=4),

            dbc.Col([
                dbc.Button(
                    "Run ML Prediction",
                    id="run-ml",
                    color="primary",
                    size="sm",
                    n_clicks=0,
                    style={"marginTop": "20px"}
                )
            ], md=4),
        ], className="g-2"),

        html.Span(id="ml-status", className="text-muted small ms-2"),
    ], className="mb-3"),

    dbc.Row([
        dbc.Col(html.Div(id="ml-kpi-lin", className="text-light"), md=6),
        dbc.Col(html.Div(id="ml-kpi-log", className="text-light"), md=6),
    ], className="mb-3"),

    dbc.Row([
        dbc.Col(html.Div(id="lh-ml-table", className="text-light"))
    ])
], style=CARD_STYLE, className="mb-4")


], fluid=True)


@callback(
    Output('lh-metrics-update', 'children'),
    Output('lh-table-container', 'children'),
    Output('lh-daily-chart', 'figure'),
    Output('lh-df-store', 'data'),
    Input('refresh', 'n_intervals'),

)
def load_data_render(_):

    with sql_engine.connect() as conn:
        query = """
            SELECT DISTINCT ON (departure_scheduled_date, departure_scheduled_time, route_key) *
            FROM lh_flights
            ORDER BY departure_scheduled_date, departure_scheduled_time, route_key, id DESC
        """
        df = pd.read_sql(query, conn)

    if df.empty:
        return "No data", html.Div("No data", className="text-light"), go.Figure(), None

    # ---- Convert ingestion time ----
    df["ingested_at"] = pd.to_datetime(df["ingested_at"])
    df["ingested_at"] = (df["ingested_at"].dt.tz_localize("UTC").dt.tz_convert("Europe/Budapest").dt.strftime("%Y-%m-%d %H:%M:%S"))

    
    # ---- Build daily chart ----
    daily = df.groupby(df["departure_scheduled_date"]).size().reset_index(name="count")
    fig = px.bar(daily, x="departure_scheduled_date", y="count", template="plotly_dark")
    fig.update_layout(height=250,  plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', margin=dict(l=20, r=20, t=10, b=10))

    # ---- Logs table ----
    status_cols = [1, 2, 3, 4, 6, 10, 11, 13]
    table = dbc.Table.from_dataframe(df.iloc[-100:, status_cols], striped=False, hover=True, responsive=True, borderless=True,
        className="text-light m-0", style={"backgroundColor": "transparent",  "--bs-table-bg": "transparent", "--bs-table-accent-bg": "transparent", "color": "white"})

    return f"Updated → {df['ingested_at'].iloc[-1]}", table, fig, df.to_dict("records")

@callback(
        [Output('ml-status', 'children'),
        Output('ml-kpi-lin', 'children'),
        Output('ml-kpi-log', 'children'),
        Output('lh-ml-table', 'children')],
        [Input('run-ml', 'n_clicks')],   
        [State('lh-reg-model', 'value'),
        State('lh-clf-model', 'value'),
        State('lh-df-store','data')],
        prevent_initial_call=True)
    
def run_ml_clicks(n_clicks, reg_choice, clf_choice, data):  
    
    if not data:
        msg = "No data for ML"
        return msg, "-", "-", "-", "-"

    df = pd.DataFrame(data)
    data_ml = lh_ml.prepare(df)

    # -------------------------
    #   REGRESSION MODEL SWITCH
    # -------------------------
    if reg_choice == "lin":
        reg_model, reg_metrics = lh_ml.train_linear(data_ml)
    elif reg_choice == "tree_reg":
        reg_model, reg_metrics = lh_ml.train_tree_linear(data_ml)
    elif reg_choice == "rf_reg":
        reg_model, reg_metrics = lh_ml.train_rf_linear(data_ml)
    else:
        reg_model, reg_metrics = lh_ml.train_linear(data_ml)

    reg_kpi = html.Div([
        html.Div(f"RMSE: {reg_metrics['rmse']:.1f}"),
        html.Div(f"MAE: {reg_metrics['mae']:.1f}"),
        html.Div(f"R² : {reg_metrics['r2']:.3f}"),
    ])

    # Predict on latest rows
    reg_pred = lh_ml.predict_latest_linear(reg_model, data_ml, n=15)

    
    # -------------------------
    #   CLASSIFICATION MODEL SWITCH
    # -------------------------
    if clf_choice == "log":
        clf_model, clf_metrics = lh_ml.train_logistic(data_ml)
    elif clf_choice == "tree_clf":
        clf_model, clf_metrics = lh_ml.train_tree_logistic(data_ml)
    elif clf_choice == "rf_clf":
        clf_model, clf_metrics = lh_ml.train_rf_logistic(data_ml)
    else:
        clf_model, clf_metrics = lh_ml.train_logistic(data_ml)

    clf_kpi = html.Div([
        html.Div(f"Accuracy:  {clf_metrics['acc']:.3f}"),
        html.Div(f"Precision: {clf_metrics['prec']:.3f}"),
        html.Div(f"Recall:    {clf_metrics['rec']:.3f}"),
        html.Div(f"F1-score:  {clf_metrics['f1']:.3f}"),
    ])

    clf_pred = lh_ml.predict_latest_logistic(clf_model, data_ml, n=15)


    comp_table = pd.merge(reg_pred, clf_pred, on=["route_key", "dep_sched"], how="outer", validate="one_to_one", sort=False)
    reg_clf_table = dbc.Table.from_dataframe(comp_table, striped=False, hover=True, responsive=True, borderless=True, className="text-light m-0",      
        style={"height": "250px", "overflowY": "auto", "overflowX": "hidden",  "fontSize": "12px",
               "backgroundColor": "transparent",  "--bs-table-bg": "transparent", "--bs-table-accent-bg": "transparent"})
    
    return "ML ran successfully ✔", reg_kpi, clf_kpi, reg_clf_table



