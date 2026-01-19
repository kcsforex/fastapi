# 2026.01.19  15.00
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
        html.P(id='metrics-update1', className="text-muted small"),
    ], className="mb-4"),

    dcc.Interval(id='refresh', interval=60000),

    dcc.Store(id="df-store", storage_type="memory"),

    # -------- Original content -------
    html.Div([
        html.H5("Daily Ingestion Volume", className="text-light mb-3"),
        dcc.Graph(id='daily-count-chart', config={'displayModeBar': False})
    ], style=CARD_STYLE, className="mb-4"),

    html.Div([
        html.H5("Execution Logs", className="text-light mb-3"),
        html.Div(id='status-table-container1',
            style={"height": "300px", "overflowY": "auto", "fontSize": "12px"})
    ], style=CARD_STYLE, className="mb-4"),

    # -------- NEW: ML linear regression -------
    #html.Div([
    #    html.H5("ML Prediction (Linear Regression)", className="text-light mb-3"),
    #    html.Div(id="ml-kpi", className="text-light mb-3"),
    #    html.Div(id="ml-table", className="text-light", style={"height": "300px", "overflowY": "auto"}),
    #], style=CARD_STYLE, className="mb-4")


 # New: ML controls + output
    html.Div([
        html.Div([
            html.H5("ML Modeling", className="text-light mb-2"),
            dbc.Button("Run ML Prediction", id="run-ml", color="primary", size="sm", n_clicks=0),
            html.Span(id="ml-status", className="text-muted small ms-2")
        ], className="mb-3"),

        dbc.Row([
            dbc.Col(html.Div(id="ml-kpi-lin", className="text-light"), md=6),
            dbc.Col(html.Div(id="ml-kpi-log", className="text-light"), md=6),
        ], className="mb-3"),
       
        dbc.Row([
            dbc.Col(html.Div(id="ml-table-lin", className="text-light"), md=6),
            dbc.Col(html.Div(id="ml-table-log", className="text-light"), md=6),
        ])
    ], style=CARD_STYLE, className="mb-4")

], fluid=True)


@callback(
    [
        Output('metrics-update1', 'children'),
        Output('status-table-container1', 'children'),
        Output('daily-count-chart', 'figure'),
        Output('df-store', 'data')],
    [Input('refresh', 'n_intervals')],
    prevent_initial_call=False
)
def load_data_render(n_intervals):

    # ---- Load SQL ----
    with sql_engine.connect() as conn:
        query = """
            SELECT DISTINCT ON (departure_scheduled_date, departure_scheduled_time, route_key) *
            FROM lh_flights
            ORDER BY departure_scheduled_date, departure_scheduled_time, route_key, id DESC
        """
        df = pd.read_sql(query, conn)

    if df.empty:
        empty_div = html.Div("No data found", className="text-light fst-italic")
        empty_fig = go.Figure()
        return "No data", empty_div, empty_fig, None

    # ---- Convert ingestion time ----
    df["ingested_at"] = pd.to_datetime(df["ingested_at"])
    df["ingested_at"] = (df["ingested_at"].dt.tz_localize("UTC").dt.tz_convert("Europe/Budapest").dt.strftime("%Y-%m-%d %H:%M:%S"))

    # ---- Build daily chart ----
    daily_counts = df.groupby(df["departure_scheduled_date"]).size().reset_index(name="count")
    fig_daily = px.bar(daily_counts, x="departure_scheduled_date", y="count", template="plotly_dark")
    fig_daily.update_layout(height=250,  plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', margin=dict(l=20, r=20, t=10, b=10))

    metrics_update1 = f"Updated → {df['ingested_at'].iloc[-1]}"

    # ---- Logs table ----
    status_cols = [1, 2, 3, 4, 6, 10, 11, 13]
    status_cols = [c for c in status_cols if c < df.shape[1]]

    table_logs = dbc.Table.from_dataframe(df.iloc[-100:, status_cols], striped=False, hover=True, responsive=True, borderless=True,
        className="text-light m-0", style={"backgroundColor": "transparent",  "--bs-table-bg": "transparent", "--bs-table-accent-bg": "transparent", "color": "white"})

    df_store = df.to_dict("records")
    return metrics_update1, table_logs, fig_daily, df_store

@callback(
        outputs=[Output('ml-status', 'children'),
        Output('ml-kpi-lin', 'children'),
        Output('ml-kpi-log', 'children'),
        Output('ml-table-lin', 'children'),
        Output('ml-table-log', 'children')],
        inputs=[Input('run-ml', 'n_clicks')],
        state=[State('df_store','data')],
        prevent_initial_call=True)
    
def run_ml_clicks(n_clicks, df_store):  
    if not n_clicks:
        return no_update, no_update, no_update, no_update, no_update

    if not df_store:
        msg = "No data"
        empty = html.Div("-", classname="text-light")
        return msg, empty, empty,  empty, empty

    df = pd.Dataframe(df_store)

    # ---- ML PART ----
    data = lh_ml.prepare(df)
    lin_model, lin_metrics = lh_ml.train_linear(data)
    pred_lin = lh_ml.predict_linear(lin_model, data, n=15)

    
    lin_kpi = html.Div([
        html.Div(f"RMSE: {lin_metrics['rmse']:.1f} min" if pd.notna(lin_metrics['rmse']) else "RMSE: n/a"),
        html.Div(f"MAE:  {lin_metrics['mae']:.1f} min" if pd.notna(lin_metrics['mae']) else "MAE: n/a"),
        html.Div(f"R²:   {lin_metrics['r2']:.3f}" if pd.notna(lin_metrics['r2']) else "R²: n/a"),
    ])


    lin_table = dbc.Table.from_dataframe(pred_lin, striped=False, hover=True, responsive=True, borderless=True, className="text-light m-0",
        style={"height": "250px", "overflowY": "auto", "overflowX": "hidden",  "fontSize": "12px",
               "backgroundColor": "transparent",  "--bs-table-bg": "transparent", "--bs-table-accent-bg": "transparent"})

    
   # Logistic Regression
    log_model, log_metrics = lh_ml.train_logistic(data)
    pred_log = lh_ml.predict_logistic(log_model, data, n=15)

    log_kpi = html.Div([
        html.Div(f"Accuracy:  {log_metrics['acc']:.3f}" if pd.notna(log_metrics['acc']) else "Accuracy: n/a"),
        html.Div(f"Precision: {log_metrics['prec']:.3f}" if pd.notna(log_metrics['prec']) else "Precision: n/a"),
        html.Div(f"Recall:    {log_metrics['rec']:.3f}" if pd.notna(log_metrics['rec']) else "Recall: n/a"),
        html.Div(f"F1:        {log_metrics['f1']:.3f}" if pd.notna(log_metrics['f1']) else "F1: n/a"),
    ])

    
    log_table = dbc.Table.from_dataframe(pred_log, striped=False, hover=True, responsive=True, borderless=True, className="text-light m-0",      
        style={"height": "250px", "overflowY": "auto", "overflowX": "hidden",  "fontSize": "12px",
               "backgroundColor": "transparent",  "--bs-table-bg": "transparent", "--bs-table-accent-bg": "transparent"})

    return "ML ran just now", lin_kpi, log_kpi, lin_table, log_table

    #return metrics, table, fig, ml_kpi, ml_table
