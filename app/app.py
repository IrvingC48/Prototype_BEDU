import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import numpy as np

import geopandas as gpd
import json

from dash.dependencies import Input, Output
import plotly.graph_objects as go
import plotly.express as px
import plotly.figure_factory as ff
from plotly.graph_objs import *
from datetime import datetime as dt


app = dash.Dash(
    __name__, meta_tags=[{"name": "viewport", "content": "width=device-width"}],
)
app.title = "Sistema de alerta temprana por contaminación del aire"
server = app.server

MAPBOX_TOKEN = 'pk.eyJ1IjoiaW5mcmFieXRlIiwiYSI6ImNrcWg3MXJtaDJoYWkycGxjcHp4OHdma2UifQ.14i_FtiSXg7ExZ2jKhDZyg'

# Data
estaciones_cords = pd.read_csv('./data/estaciones_cords.csv', dtype=object)
geodf = gpd.read_file('./data/zmvm1.shx')

df_2019 = pd.read_csv('./data/prueba_2019.csv')
# Convert the date to datetime64
df_2019["date"] = pd.to_datetime(df_2019["date"]).dt.strftime('%Y-%m-%d')

df_2021 = pd.read_csv('./data/datos_2021.csv')
# Convert the date to datetime64
df_2021["date"] = pd.to_datetime(df_2021["date"]).dt.strftime('%Y-%m-%d')



# Layout principal
app.layout = html.Div(
    #Hijo 1
    children= [
        html.Div(
            className="row",
            # Hijo 2
            children = [
                # Columna de controles
                html.Div(
                    className = "four columns div-user-controls",
                    # Hijo 3
                    children = [
                        html.Img(
                            className = "logo", src="./assets/air-pollution.png"
                        ),
                        html.H2("Sistema de alerta temprana por contaminación del aire"),
                        # html.P(
                        #     """Select different days using the date picker or by selecting
                        #     different time frames on the histogram."""
                        # ),
                        html.P("Elije un año:"),
                        html.Div(
                            className="div-for-dropdown",
                            children = [
                                    dcc.RadioItems(
                                    id='year', 
                                    options=[
                                        {'label': '2019', 'value': 2019},
                                        {'label': '2021', 'value': 2021},
                                    ],
                                    value=2019,
                                    labelStyle={'display': 'inline-block'}
                                ),
                            ]
                        ),
                        html.Div(
                            className="div-for-dropdown",
                            children=[
                                dcc.DatePickerSingle(
                                    id="date_pick",
                                    min_date_allowed=dt(2019, 1, 1),
                                    max_date_allowed=dt(2021, 12, 31),
                                    initial_visible_month=dt(2019, 1, 1),
                                    date=dt(2019, 1, 1).date(),
                                    # display_format="MMMM D, YYYY",
                                    style={"border": "0px solid black"},
                                )
                            ],
                        ),
                        # Change to side-by-side for mobile layout
                        html.Div(
                            className="row",
                            children=[
                                html.Div(
                                    className="div-for-dropdown",
                                    children=[
                                        # Dropdown to select times
                                        dcc.Graph(id="datatable"),
                                    ],
                                ),
                            ],
                        ),
                        dcc.Markdown(
                            children=[
                                "Source: [Direccion de Monitoreo Atmosferico](http://www.aire.cdmx.gob.mx/default.php?opc=%27aKBh%27)"
                            ]
                        ),
                    ]
                ),
                # Column for app graphs and plots
                html.Div(
                    className="eight columns div-for-charts bg-grey",
                    children=[
                        dcc.Graph(id="map-graph"),
                    ],
                ),
            ]
        )
    ]
)

# Update Map Graph based on date-picker, selected data on histogram and location dropdown
@app.callback(
    Output("map-graph", "figure"), 
    [
        Input("date_pick", "date"),
        Input('year', 'value')
    ]
)
def display_choropleth(date, year):
    zoom = 9.0
    latInitial = 19.4978
    lonInitial = -99.1269
    bearing = 0    

    if date:

        if year == 2019:
            df_query = df_2019.query(f"date == '{date}'")
        elif year == 2021:
            df_query = df_2021.query(f"date == '{date}'")
            # print(df_2021.head())
        
        # print(df_query)
        selected_est = df_query['id_station']

        cordenadas = pd.DataFrame()

        for i in selected_est:
            cordenadas =  cordenadas.append(estaciones_cords.loc[estaciones_cords['cve_estac'] == i], ignore_index = True)


        fig = go.Figure(go.Scattermapbox(
                lat=cordenadas.latitud,
                lon=cordenadas.longitud,
                mode='markers',
                marker=go.scattermapbox.Marker(
                    color=df_query.indice_pred,
                    size=20,
                        colorbar=dict(
                        title="indice_pred",
                        x=0.93,
                        xpad=0,
                        nticks=150,
                        dtick = 5,
                        tickfont=dict(color="#d8d8d8"),
                        titlefont=dict(color="#d8d8d8"),
                        # thicknessmode="pixels",
                    ),
                ),
                text=cordenadas.cve_estac,
            ))

        fig.update_layout(
            margin={"r":0,"t":0,"l":0,"b":0},
            # hovermode='closest',
            mapbox=dict(
                accesstoken=MAPBOX_TOKEN,
                bearing=0,
                center=go.layout.mapbox.Center(
                    lat=19.4978,
                    lon=-99.1269
                ),
                pitch=0,
                zoom=9,
                style = "dark"
            )
        )
        
        
        return fig

@app.callback(
    [
        Output('date_pick', 'initial_visible_month'),
        Output('date_pick', 'date'),
    ], 
    [Input('year', 'value')],
)
def updateDataPicker(dropdown_value):
    if dropdown_value == 2019:
        return dt(2019, 1, 1).date(), dt(2019, 1, 1).date()
    elif dropdown_value == 2021:
        return dt(2021, 1, 1).date(), dt(2021, 1, 1).date()

# Clear Selected Data if Click Data is used
@app.callback(Output("datatable", "figure"), 
    [
        Input("date_pick", "date"),
        Input('year', 'value')
    ]
)
def update_datatable(date, year):            
    if date:
        if year == 2019:                     
            df_query = df_2019.query(f"date == '{date}'")
        elif year == 2021:
            df_query = df_2021.query(f"date == '{date}'")
        fig = ff.create_table(df_query)

        return fig


if __name__ == "__main__":
    app.run_server(debug=True)