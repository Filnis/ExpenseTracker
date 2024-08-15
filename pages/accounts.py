import pandas as pd
from decimal import *
import dash
from dash import dcc, callback, Input, Output, Patch
import dash_ag_grid as dag
import dash_bootstrap_components as dbc
from dash_bootstrap_templates import load_figure_template
import plotly.express as px
import plotly.graph_objects as go
from io import StringIO
from support_functions import float2dec

load_figure_template(["bootstrap"])
dash.register_page(__name__, external_stylesheets=[dbc.themes.FLATLY, dbc.icons.FONT_AWESOME], path='/accounts')

accounts_chart = dcc.Graph(
    id="accounts_chart", 
    figure=go.Figure(), 
    style={'height': '100%'},
    className='py-0 my-0'
)

acc_table = dag.AgGrid(
        id="acc_table",
        columnSize="responsiveSizeToFit",
        columnSizeOptions={
            },
        dashGridOptions = {"rowHeight": 30},
        className="ag-theme-alpine"
        )

layout = dbc.Container(
    [   
        dbc.Row([
            dbc.Col([], width=0, lg=4,  style={"height" : "100%"}),
            dbc.Col([acc_table,
            ], width=12, lg=4, style={"height" : "100%","display":"flex","justifyContent":"center","alignItems":"center"}),
            dbc.Col([], width=0, lg=4,  style={"height" : "100%"}),
        ], style={"display":"flex", "justifyContent" : "center", "alignItems" : "center" ,"height" : "40%"}),
        dbc.Row([
            dbc.Col([accounts_chart,
            ], width=12),
        ], style={"height" : "60%", "marginBottom" : "0", "marginTop" : "10"})
    ],
    id='invContainer',
    fluid=True,
    className="dbc dbc-ag-grid px-4 py-0",
    style={"border" : "3px solid white"}
)

@callback(
    Output('accounts_chart', 'figure'),
    Input('df-accounts', 'data'))
def updateAccountChart(data):
    # decode from json
    account_prog = pd.read_json(StringIO(data))
    account_prog = account_prog[
        (account_prog['Day_num'].isin([1]))
        ]
    account_prog['RT'] = (account_prog['RT'].map(float2dec) * float2dec(1)).map(float2dec)

    fig = px.bar(account_prog, x="Date", y="RT", color="Account", title="Account worth")
    fig.update_layout(legend=dict(
        orientation="h",
        yanchor="top",
        y=1.02,
        xanchor="left"
    ))
    fig.update_layout(
    margin=dict(l=20, r=20, t=0, b=20),
    )

    return fig

@callback(
    Output('acc_table', 'rowData'),
    Output('acc_table', 'columnDefs'),
    Output('acc_table', 'dashGridOptions'),
    Output('acc_table', 'style'),
    Input('df-accounts', 'data')
)
def updateAccountTable(data):
    account_prog = pd.read_json(StringIO(data))
    end_date = account_prog['Date'].max()

    account_prog = account_prog[account_prog["Date"] == end_date]
    account_prog = account_prog[["Account", "RT"]]
    
    #set total row
    totals_row = account_prog.sum()
    totals_row.iloc[0] = "Totals"
    totals_row['RT'] = round(totals_row['RT'],2)

    account_prog['%'] = account_prog['RT']/totals_row.iloc[1] 
    totals_row['%'] = 1
    rowData=account_prog.to_dict("records")
    columnlist = account_prog.columns

    columnDefs=[
                {
                "field": i, 
                "type": "rightAligned" if i != 'SubCat' else 'leftAligned',
                "sort": "asc" if i == 'Total' else False,
                'valueFormatter': {"function":"""d3.format(".2f")(params.value)"""} if i == "RT" else 
                                    {"function":"""d3.format(".0%")(params.value)"""} if i == "%" else False,
                'cellStyle': {
                    "function": "params.value < 0 || params.value.includes('-') ? {'color': 'red'} : {'color': 'green'}",
                    } if i in ['Var €', 'Var %'] else False
                } 
                for i in columnlist
            ]
    grid_option_patch = Patch()

    grid_option_patch["pinnedBottomRowData"] = [totals_row.to_dict()]
    #resize tab so it's always the right size
    grid_style = {'height': ((len(account_prog.index)+2)*30+4)}

    return rowData, columnDefs, grid_option_patch, grid_style