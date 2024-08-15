import pandas as pd
import numpy as np
from decimal import *
import calendar
import dash_ag_grid as dag
import dash_bootstrap_components as dbc
from dash_bootstrap_templates import load_figure_template
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import dash
from dash import Dash, html, dcc, callback, Input, Output, html, dash_table, Patch
from io import StringIO
from support_functions import get_table, float2dec, createCardV2

load_figure_template(["bootstrap"])
dash.register_page(__name__, external_stylesheets=[dbc.themes.FLATLY, dbc.icons.FONT_AWESOME], path='/car')

cat_table = dag.AgGrid(
        id="car_category",
        columnSize="responsiveSizeToFit",
        columnSizeOptions={
            },
        dashGridOptions = {"rowHeight": 30},
        className='ag-theme-alpine'
        )

cat_chart = dcc.Graph(
    id="cat_chart", 
    figure=go.Figure(), 
    className='py-0 my-0',
    style={'height': '100%'}
)

toggle = dcc.RadioItems(['Mileage', 'Partial distance'], 'Mileage', id='distance-toggle',inline=False)

cards = html.Div([
], id='fuel_cards')

card_icon = {
    "color": "white",
    "textAlign": "center",
    "fontSize": 30,
    "margin": "auto",
}

card1 = createCardV2("26876 km","Actual mileage", "fa-solid fa-road")

fuel_distance_chart = dcc.Graph(
    id="fuel_distance_chart", 
    figure=go.Figure(), 
    style={'height': '100%'},
    className='py-0 my-0'
)

layout = dbc.Container(
    [   
        dbc.Row([
            dbc.Col([
                cat_table,
            ],
                style={"border" : "2px solid white", "height" : "100%"},
                width=12, lg=3),
            dbc.Col([
                cat_chart
            ], style={"border" : "2px solid white", "height" : "100%"},
            width=12, lg=3),
            dbc.Col([
            ], id='car_card_1',
            style={"border" : "2px solid white", "height" : "100%"},
            width=6, lg=3),
            dbc.Col([
            ], id='car_card_2',
            style={"border" : "2px solid white", "height" : "100%"},
            width=6, lg=3),
        ], style={"border" : "2px solid white", "height" : "40%", "paddingTop" : "5px"}),
        html.Hr(),
        dbc.Row([
            dbc.Col([toggle], width=12, lg=1),
            dbc.Col([fuel_distance_chart], width=12, lg=11)
        ], style={"border" : "2px solid white", "height" : "60%", "paddingBottom" : "5px"})
    ],
    id='carContainer',
    fluid=True,
    className="dbc dbc-ag-grid px-4 py-0",
    style={"border" : "3px solid white"}
)

# Cost by category
@callback(
    Output('car_category', 'rowData'),
    Output('car_category', 'columnDefs'),
    Output('car_category', 'dashGridOptions'),
    Output('car_category', 'style'),
    Output('cat_chart', 'figure'),
    Input('df-trapay', 'data'))
def updateCarTable(data):
    # decode from json
    tra_pay = pd.read_json(StringIO(data))
    tra_pay_car = tra_pay[(tra_pay['Cat'] == 'Car')]
    tra_pay_car = tra_pay_car.groupby(['SubCat'])["Amount"].sum().reset_index().sort_values(['Amount'], ascending=[True])
    tra_pay_car['Amount'] = (tra_pay_car['Amount'].map(float2dec) * float2dec(1)).map(float2dec)

    totals_negative = tra_pay_car.sum()
    totals_negative.iloc[0] = 'Expenses'

    # Percentage of each category compared to total expense
    tra_pay_car['Exp %'] = 0.0
    tra_pay_car['Exp %'] = pd.to_numeric(abs(tra_pay_car['Amount'])) / pd.to_numeric(abs(totals_negative.iloc[-1]))*100
    tra_pay_car['Exp %'] = (tra_pay_car['Exp %'].map(float2dec) * float2dec(1)).map(float2dec).astype(str) + '%'

    rowData=tra_pay_car.to_dict("records")

    columnlist = tra_pay_car.columns

    columnDefs=[
                {
                "field": i, 
                "type": "rightAligned" if i != 'SubCat' else 'leftAligned',
                'valueFormatter': {"function":"""d3.format(".2f")(params.value)"""} if i == 'Amount' else False,
                "sort": "asc" if i == 'Total' else False
                } 
                for i in columnlist
            ]
    grid_option_patch = Patch()

    #resize tab so it's always the right size
    grid_style = {'height': (len(tra_pay_car.index)+1)*30+55}
    grid_option_patch["pinnedBottomRowData"] = [totals_negative.to_dict()]

    #make chart
    tra_pay_car['Amount'] = abs(tra_pay_car['Amount'])

    fig2 = go.Figure(data=[go.Pie(labels=tra_pay_car['SubCat'], values=tra_pay_car['Amount'], textinfo='label+value+percent',
                             insidetextorientation='horizontal', hole=0.3
                            )])

    fig2.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        showlegend=False
    )
    return rowData, columnDefs, grid_option_patch, grid_style, fig2

#Fuel consumption and distance
@callback(
    Output('fuel_distance_chart', 'figure'),
    Output('car_card_1', 'children'),
    Output('car_card_2', 'children'), 
    Input('df-trapay', 'data'),
    Input('distance-toggle', 'value'))
def updateFuelChart(data, dist,):
    # decode from json
    tra_pay = pd.read_json(StringIO(data))
    tra_pay_car_fuel = tra_pay[
        (tra_pay['Cat'] == 'Car') &
        (tra_pay['SubCat'] == 'Fuel')
    ]
    tra_pay_car_fuel = tra_pay_car_fuel[['Date', 'Year', 'Month', 'Amount', 'Memo']]

    tra_pay_car_fuel['Distance'] = pd.to_numeric(tra_pay_car_fuel['Memo'].str.split(expand=True)[0].str[2:])

    tra_pay_car_fuel['Liters'] = pd.to_numeric(tra_pay_car_fuel['Memo'].str.split(expand=True)[1].str[2:])

    tra_pay_car_fuel['FuelPrice'] = abs(tra_pay_car_fuel['Amount'])/pd.to_numeric(tra_pay_car_fuel['Liters'])
    tra_pay_car_fuel['FuelPrice'] = (tra_pay_car_fuel['FuelPrice'].map(float2dec) * float2dec(1)).map(float2dec)
    tra_pay_car_fuel['DeltaD'] = abs(tra_pay_car_fuel['Distance'].diff()).shift(-1)
    tra_pay_car_fuel['FuelEfficicency'] = (tra_pay_car_fuel['DeltaD']/tra_pay_car_fuel['Liters']).map(float2dec)

    tra_pay_car_fuel = tra_pay_car_fuel.loc[tra_pay_car_fuel['FuelEfficicency']>0, :]

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    if dist == 'Mileage':
        fig.add_trace(
            go.Scatter(
                x=tra_pay_car_fuel['Date'],
                y=tra_pay_car_fuel['Distance'],
                text=round(tra_pay_car_fuel['Distance']/1000,1).astype(str) + "k",
                textposition='top center',
                name="Mileage",
                mode="markers+lines+text",
            ),
            secondary_y=False
        )
        #set max and min
        fig.update_layout(yaxis_range=[0.95*min(pd.to_numeric(tra_pay_car_fuel['Distance'])),1.02*max(pd.to_numeric(tra_pay_car_fuel['Distance']))])
    else:
        fig.add_trace(
            go.Bar(
                x=tra_pay_car_fuel['Date'],
                y=tra_pay_car_fuel['DeltaD'],
                name="Partial distance [km]",
                text=tra_pay_car_fuel['DeltaD'],
                textposition='auto',
            ),
            secondary_y=False
        )
        #set max and min
        fig.update_layout(yaxis_range=[0.95*min(pd.to_numeric(tra_pay_car_fuel['DeltaD'])),1.02*max(pd.to_numeric(tra_pay_car_fuel['DeltaD']))])

    fig.add_trace(
    go.Scatter(
        x=tra_pay_car_fuel['Date'],
        y=tra_pay_car_fuel['FuelEfficicency'],
        text=tra_pay_car_fuel['FuelEfficicency'],
        textposition='top center',
        mode="markers+lines+text",
        name="Fuel efficiency [km/l]",
        line=dict(
            color="red"
        )
    ),
    secondary_y=True
    )

    fig.update_layout(
    margin=dict(l=20, r=20, t=0, b=20),
    )

    fig.update_layout(
    font=dict(
        size=15,
        )
    )

    #card values
    distance_end = tra_pay_car_fuel['Distance'].max()
    distance_start = tra_pay_car_fuel['Distance'].min()
    distance_start_date = tra_pay_car_fuel[tra_pay_car_fuel['Distance']==distance_start]['Date'].item()

    total_distance = tra_pay_car_fuel['DeltaD'].sum()
    total_fuel_efficiency = float2dec(total_distance/tra_pay_car_fuel['Liters'].sum())

    card1 = createCardV2(str(distance_end)+' km',"Actual mileage", "fa-solid fa-road")
    card2 = createCardV2(str(total_distance)+' km',"Measured distance", "fa-solid fa-gauge-high")
    card3 = createCardV2(str(total_fuel_efficiency)+' km/l',"Fuel efficiency", "fa-solid fa-gas-pump")

    tra_pay_car = tra_pay[(tra_pay['Cat'] == 'Car')]
    total_cost_km = float2dec(-tra_pay_car[tra_pay_car['Date']>=distance_start_date]['Amount'].sum()/total_distance)

    card4 = createCardV2(str(total_cost_km)+' €/km',"Travel cost", "fa-solid fa-euro-sign")

    return fig, [card1, card2], [card3, card4]