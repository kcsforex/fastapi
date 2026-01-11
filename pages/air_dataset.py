# 2025.11.30  11.00
from dash import dash, html, dcc, Output, Input, callback
import dash_bootstrap_components as dbc
from databricks import sql
import pandas as pd
import os

SERVER_HOSTNAME = 'dbc-9c577faf-b445.cloud.databricks.com' 
HTTP_PATH = '/sql/1.0/warehouses/cbfc343eb927c998' 
ACCESS_TOKEN = 'dapif047182091035d8ea79cd0f22ddd6bee' 
delta_path = '/Volumes/test_cat/test_db/test_vol/bronze/delta_air_dataset/'

#app = Dash()
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = html.Div(
    [ 
        #dcc.Loading(dcc.Graph(id="sample-chart-2")),
        dcc.Input(id="selector-1", type="number", min=10, max=200, step=10, value=150),
        dcc.Dropdown(id="selector-2",options=['SpiceJet', 'AirAsia', 'Air_India', 'Vistara', 'Indigo'],value='Indigo'),
        #dcc.Input(id="selector-2", type="text", value=list('SpiseJet','AirAsia', 'Air_India')),
         dbc.Container([    html.Div(id="table")], fluid=True)
    ],
    style={"background-color": "white", "height": "100vh"},
)


@callback(Output("table", "children"), Input("selector-1", "value"), Input("selector-2", "value"))
def create_table(val1, val2):
    connection = sql.connect(
        server_hostname=SERVER_HOSTNAME, http_path=HTTP_PATH, access_token=ACCESS_TOKEN
    )
    cursor = connection.cursor()
    cursor.execute(
        f"SELECT * FROM delta.`{delta_path}`WHERE airline = '{val2}' LIMIT {val1}"
        #f"SELECT * FROM {DB_NAME}.{TABLE_NAME} WHERE age > {selected_val} LIMIT 100"
    )
    df = cursor.fetchall_arrow()
    result_df = df.to_pandas()

    cursor.close()
    connection.close()

    return dbc.Table.from_dataframe(result_df, striped=True, bordered=True, hover=True)
    #return dash_table.DataTable(df.to_dict("records"), [{"name": i, "id": i} for i in df.columns])
    #asset_table = dbc.Table.from_dataframe(binance_data, striped=True, bordered=True, hover=True)
    #return asset_table


if __name__ == "__main__":
    app.run(debug=True)
